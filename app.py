from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="FloNote Landing")
app.mount("/", StaticFiles(directory="public", html=True), name="static")
