import os, json
from typing import Optional, List, Any, Dict
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy.orm import Session
from db import engine, Base, get_db, SessionLocal
from models import Template
from llm import extract_with_llm

ALLOWED_ORIGINS=os.getenv('ALLOWED_ORIGINS','*').split(',')
Base.metadata.create_all(bind=engine)
limiter=Limiter(key_func=get_remote_address)
app=FastAPI(title='FloNote V1')

@app.exception_handler(RateLimitExceeded)
def ratelimit_handler(request, exc):
    return JSONResponse(status_code=429, content={'detail':'Rate limit exceeded'})

app.add_middleware(CORSMiddleware,allow_origins=['*'] if ALLOWED_ORIGINS==['*'] else ALLOWED_ORIGINS,
                   allow_methods=['GET','POST','PUT','DELETE','OPTIONS'],allow_headers=['*'])

app.mount('/', StaticFiles(directory='public', html=True), name='public')

# Seed templates
def seed():
    db=SessionLocal()
    try:
        if db.query(Template).count()>0: return
        seeddata=[
            ('htn','Primary hypertension','I10','templates/htn.md'),
            ('cap','Community-acquired pneumonia','J18.9','templates/cap.md'),
            ('t2dm','Type 2 diabetes mellitus','E11.9','templates/t2dm.md')
        ]
        for slug,title,icd,path in seeddata:
            with open(path,'r',encoding='utf-8') as f: body=f.read()
            row=Template(slug=slug,title=title,diagnosis_icd10=icd,body_md=body,variables=None,links=json.dumps([]),status='published',version=1,updated_by='seed')
            db.add(row)
        db.commit()
    finally:
        db.close()
seed()

from fastapi import APIRouter
api=APIRouter(prefix='/api')

class ExtractReq(BaseModel): transcript:str

@api.post('/extract_assessment')
async def extract_assessment(req: ExtractReq):
    data=extract_with_llm(req.transcript)
    if data:
        if not data.get('mapping'):
            data['mapping']=[
                {'key':'subjective.chief_complaint','target_path':'#cc'},
                {'key':'subjective.hpi','target_path':'#hpi'},
                {'key':'subjective.ros','target_path':'#ros'},
                {'key':'objective.exam','target_path':'#exam'},
                {'key':'objective.labs','target_path':'#labs'},
                {'key':'objective.imaging','target_path':'#imaging'}
            ]
        return data

    # heuristic fallback
    t=req.transcript.lower()
    dx=[]
    if 'pneumonia' in t or 'crackles' in t: dx.append({'label':'Community-acquired pneumonia','icd10':'J18.9','status':'confirmed'})
    if 'diabetes' in t or 'a1c' in t: dx.append({'label':'Type 2 diabetes mellitus','icd10':'E11.9','status':'suspected'})
    if 'hypertension' in t or 'bp' in t: dx.append({'label':'Primary hypertension','icd10':'I10','status':'suspected'})
    if not dx: dx.append({'label':'Encounter for exam','icd10':'Z00.00','status':'suspected'})

    def get_num(tag, default=None):
        import re
        m=re.search(rf'{tag}\s*(\d+)', t)
        return int(m.group(1)) if m else default
    vitals={'bp_systolic':get_num('bp',128),'bp_diastolic':78,'hr':get_num('hr',90),'rr':get_num('rr',18),
            'temp_c':38.0 if 'fever' in t else 36.9,'spo2':92 if 'short of breath' in t else 97}

    return {'patient':{'id':'demo','name':'Demo'},'subjective':{'chief_complaint':'','hpi':req.transcript,'ros':''},
            'objective':{'vitals':vitals,'exam':'','labs':'','imaging':''},
            'assessment':dx,'plan':[{'for':dx[0]['label']}],
            'mapping':[
                {'key':'subjective.chief_complaint','target_path':'#cc'},
                {'key':'subjective.hpi','target_path':'#hpi'},
                {'key':'objective.vitals.bp_systolic','target_path':'#bp_sys'},
                {'key':'objective.vitals.bp_diastolic','target_path':'#bp_dia'},
                {'key':'objective.vitals.hr','target_path':'#hr'},
                {'key':'objective.vitals.rr','target_path':'#rr'},
                {'key':'objective.vitals.temp_c','target_path':'#temp_c'},
                {'key':'objective.vitals.spo2','target_path':'#spo2'},
                {'key':'objective.exam','target_path':'#exam'},
                {'key':'objective.labs','target_path':'#labs'},
                {'key':'objective.imaging','target_path':'#imaging'}
            ]}

class RenderReq(BaseModel):
    diagnoses: List[Dict[str, Any]]
    context: Dict[str, Any]

@api.post('/render_template')
async def render_template(req: RenderReq, db: Session = Depends(get_db)):
    links=[]; parts=[]
    for dx in req.diagnoses:
        icd=dx.get('icd10')
        if not icd: continue
        row=db.query(Template).filter(Template.diagnosis_icd10==icd, Template.status=='published').first()
        if row: parts.append(row.body_md)
    return {'html':'\n\n'.join(parts), 'links':links}

# Studio endpoints
class Link(BaseModel): title:str; url:str
class Variable(BaseModel):
    key:str; label:str; required:bool=False; defaultValue:Optional[str]=None
class TemplateIn(BaseModel):
    slug:str; title:str
    diagnosis_icd10: Optional[str]=None
    diagnosis_snomed: Optional[str]=None
    tags: List[str]=[]
    body_md: str
    variables: List[Variable]=[]
    links: List[Link]=[]
    change_note: Optional[str]=None

@api.post('/studio/templates')
async def create_template(t: TemplateIn, db: Session = Depends(get_db)):
    from sqlalchemy import select
    if db.query(Template).filter(Template.slug==t.slug).first(): raise HTTPException(400,'Slug exists')
    import json
    row=Template(slug=t.slug,title=t.title,diagnosis_icd10=t.diagnosis_icd10,diagnosis_snomed=t.diagnosis_snomed,
                 tags=",".join(t.tags) if t.tags else None, body_md=t.body_md,
                 variables=json.dumps([v.model_dump() for v in t.variables]) if t.variables else None,
                 links=json.dumps([l.model_dump() for l in t.links]) if t.links else None,
                 status='draft', version=1, updated_by='editor')
    db.add(row); db.commit(); db.refresh(row); return row.to_dict()

@api.get('/studio/templates')
async def list_templates(q: Optional[str]=Query(None), db: Session = Depends(get_db)):
    from sqlalchemy import or_
    qry=db.query(Template)
    if q: qry=qry.filter(or_(Template.title.like(f'%{q}%'), Template.slug.like(f'%{q}%')))
    rows=qry.order_by(Template.id.desc()).all()
    return [r.to_dict() for r in rows]

@api.get('/studio/templates/{slug}')
async def get_template(slug:str, db: Session = Depends(get_db)):
    row=db.query(Template).filter(Template.slug==slug).first()
    if not row: raise HTTPException(404,'Not found')
    return row.to_dict()

@api.put('/studio/templates/{slug}')
async def update_template(slug:str, t: TemplateIn, db: Session = Depends(get_db)):
    row=db.query(Template).filter(Template.slug==slug).first()
    if not row: raise HTTPException(404,'Not found')
    import json
    row.title=t.title; row.diagnosis_icd10=t.diagnosis_icd10; row.diagnosis_snomed=t.diagnosis_snomed
    row.tags=",".join(t.tags) if t.tags else None; row.body_md=t.body_md
    row.variables=json.dumps([v.model_dump() for v in t.variables]) if t.variables else None
    row.links=json.dumps([l.model_dump() for l in t.links]) if t.links else None
    row.updated_by='editor'; row.change_note=t.change_note
    db.add(row); db.commit(); db.refresh(row); return row.to_dict()

@api.post('/studio/templates/{slug}/submit')
async def submit_template(slug:str, db: Session = Depends(get_db)):
    row=db.query(Template).filter(Template.slug==slug).first()
    if not row: raise HTTPException(404,'Not found')
    row.status='in_review'; db.add(row); db.commit(); return row.to_dict()

@api.post('/studio/templates/{slug}/publish')
async def publish_template(slug:str, db: Session = Depends(get_db)):
    row=db.query(Template).filter(Template.slug==slug).first()
    if not row: raise HTTPException(404,'Not found')
    row.status='published'; row.version=row.version+1; db.add(row); db.commit(); return row.to_dict()

app.include_router(api)
