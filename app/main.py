from pathlib import path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = path(__file__).resolve().parent.parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

app = FastAPI(
    title="Delivery Tracking Dashboard",
    description="Delivery management system",
    version="0.1.o",
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)

@app.get("/", response_class=RedirectResponse)
async def root():
    return RedirectResponse(
        url="/dashboard",
        status_code=307,
    )

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "page_title": "Dashboard",
        },
    )

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
    }