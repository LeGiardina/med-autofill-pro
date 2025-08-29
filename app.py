
import os, json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="FloNote")

# Serve static front-end
app.mount("/", StaticFiles(directory="public", html=True), name="static")

# ---- simple in-memory/flat storage for demo ----
TEMPLATES = []
ID = 1

class Template(BaseModel):
    id: Optional[int] = None
    title: str
    slug: str = ""
    icd: str = ""
    snomed: str = ""
    body: str

class ExtractIn(BaseModel):
    text: str

@app.post("/api/extract")
def extract(payload: ExtractIn):
    text = payload.text.lower()
    def find_any(keys): return any(k in text for k in keys)
    dx = []
    if find_any(["pneumonia", "cap"]): dx.append({"code":"J18.9","name":"Community-acquired pneumonia"})
    if find_any(["diabetes","t2dm"]): dx.append({"code":"E11.9","name":"Type 2 diabetes mellitus"})
    subj = {"cc":"", "hpi":"", "ros":""}
    if "cough" in text: subj["cc"]="Cough"
    if "fever" in text: subj["hpi"]= (subj["hpi"]+" Febrile.").strip()
    obj = {"bp_sys":"","bp_dia":"","hr":"","rr":"","temp":"","spo2":"","exam":"","labs":"","imaging":""}
    if "bp" in text: obj["bp_sys"]="120"; obj["bp_dia"]="75"
    if "o2" in text or "spo2" in text: obj["spo2"]="96"
    plan = ""
    return {"subjective":subj, "objective":obj, "diagnoses":dx, "plan":plan}

@app.get("/api/templates")
def list_templates(q: str = ""):
    ql = q.lower()
    return [t for t in TEMPLATES if ql in t["title"].lower()]

@app.post("/api/templates")
def create_template(t: Template):
    global ID
    data = t.dict()
    data["id"] = ID; ID += 1
    TEMPLATES.append(data)
    return data

@app.put("/api/templates")
def update_template(t: Template):
    for i, it in enumerate(TEMPLATES):
        if it["id"] == t.id:
            TEMPLATES[i] = t.dict()
            return TEMPLATES[i]
    return JSONResponse({"error":"not found"}, status_code=404)

@app.post("/api/templates/publish")
def publish(t: Template):
    # For demo we just ensure present in list
    existing = [it for it in TEMPLATES if it.get("slug")==t.slug]
    if not existing:
        create_template(t)
    return {"ok": True}

class ForDx(BaseModel):
    diagnoses: List[str] = []

@app.post("/api/templates/for-dx")
def for_dx(body: ForDx):
    # naive demo: return sample plan blocks for each diagnosis text
    blocks = []
    for d in body.diagnoses:
        if "pneumonia" in d.lower():
            blocks.append("- CAP: start empiric abx; CXR if not done; f/u 48h.")
        if "diabetes" in d.lower():
            blocks.append("- T2DM: start metformin unless contraindicated; A1c q3mo.")
    return blocks
