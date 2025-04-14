from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from routers.router import router

app = FastAPI()

# mount static files (CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates directory
templates = Jinja2Templates(directory="templates")

app.include_router(router)

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/trading-engine", response_class=HTMLResponse)
def trading_engine(request: Request):
    return templates.TemplateResponse("trading_engine.html", {"request": request})
