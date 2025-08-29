
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
import os, uuid

app = FastAPI(title="FloNote ClinicSuite")
app.mount("/", StaticFiles(directory="public", html=True), name="static")

# In-memory template store (swap to DB later)
TEMPLATES = []
SEQ = 1

class Template(BaseModel):
    id: Optional[int] = None
    title: str
    slug: str = ""
    icd: str = ""
    body: str

class ExtractIn(BaseModel):
    text: str

@app.post("/api/extract")
def extract(payload: ExtractIn):
    text = payload.text.lower()
    dx = []
    if "pneumonia" in text or "cap" in text: dx.append({"code":"J18.9","name":"Community-acquired pneumonia"})
    subj = {"cc":"", "hpi":"", "ros":""}
    if "cough" in text: subj["cc"]="Cough"
    obj = {"bp_sys":"","bp_dia":"","hr":"","rr":"","temp":"","spo2":"","exam":"","labs":"","imaging":""}
    email = "Dear Patient,\\n\\nThanks for visiting. Monitor your symptoms and follow up.\\n\\nBest,\\nProvider"
    codes = [{"code":"J18.9","name":"Pneumonia, unspecified organism"}] if dx else []
    return {"subjective":subj,"objective":obj,"plan":"", "diagnoses":dx, "email":email, "codes":codes}

@app.get("/api/templates")
def list_templates(q: str=""):
    ql = q.lower()
    return [t for t in TEMPLATES if ql in t["title"].lower()]

@app.post("/api/templates")
def create_template(t: Template):
    global SEQ
    d=t.dict(); d["id"]=SEQ; SEQ+=1
    TEMPLATES.append(d); return d

@app.put("/api/templates")
def update_template(t: Template):
    for i,old in enumerate(TEMPLATES):
        if old["id"]==t.id:
            TEMPLATES[i]=t.dict(); return TEMPLATES[i]
    return JSONResponse({"error":"not found"}, status_code=404)

@app.post("/api/templates/publish")
def publish(t: Template):
    # noop: ensure one exists
    existing=[x for x in TEMPLATES if x.get("slug")==t.slug]
    if not existing: create_template(t)
    return {"ok": True}

class DxList(BaseModel):
    diagnoses: List[str] = []

@app.post("/api/templates/for-dx")
def for_dx(body: DxList):
    blocks=[]
    for d in body.diagnoses:
        if "pneumonia" in d.lower(): blocks.append("- CAP: empiric abx; CXR; f/u 48h.")
    return blocks

class Ask(BaseModel):
    q: str

@app.post("/api/assistant")
def assistant(a: Ask):
    # simple echo assistant placeholder
    return {"a": f"I'd draft a clear plan and ensure follow-up. You asked: {a.q}"}

# FHIR mock endpoint: accept any resource and return an ID
@app.post("/api/emr/fhir/{resource}")
def post_fhir(resource: str, req: Request):
    # This would forward to EMR/EHR using FHIR API with OAuth; mocked here
    rid = str(uuid.uuid4())
    return {"resourceType": resource, "id": rid}
