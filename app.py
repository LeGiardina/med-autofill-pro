from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

app = FastAPI()
# serve /public at /public and html
app.mount("/public", StaticFiles(directory="public", html=True), name="public")

@app.get("/", include_in_schema=False)
def root():
    # always serve landing page
    return FileResponse("public/index.html")

# Optional: friendly redirects for clean paths
@app.get("/dashboard", include_in_schema=False)
def dash_redirect(): return RedirectResponse("/public/dashboard.html")

@app.get("/record", include_in_schema=False)
def rec_redirect(): return RedirectResponse("/public/record.html")

@app.get("/studio", include_in_schema=False)
def stu_redirect(): return RedirectResponse("/public/studio.html")
