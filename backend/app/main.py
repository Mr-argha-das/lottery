from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from .config import get_settings
from .database import Base, engine
from .routers import auth, api, admin

s=get_settings(); Base.metadata.create_all(engine)
app=FastAPI(title="DhanLaxmi Lottery API",version="1.0.0",docs_url="/docs" if s.enable_docs else None,redoc_url=None)
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in s.cors_origins.split(",")],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
app.include_router(auth.router); app.include_router(api.router); app.include_router(admin.router)
app.mount("/static",StaticFiles(directory="backend/app/admin/static"),name="static")
templates=Jinja2Templates(directory="backend/app/admin/templates")
@app.middleware("http")
async def headers(request:Request,call_next):
    response=await call_next(request); response.headers.update({"X-Content-Type-Options":"nosniff","X-Frame-Options":"DENY","Referrer-Policy":"no-referrer","Permissions-Policy":"camera=(), microphone=(), geolocation=()"}); return response
@app.exception_handler(Exception)
async def unexpected(_,exc): return JSONResponse(status_code=500,content={"success":False,"message":"Internal server error","error_code":"INTERNAL_ERROR"})
@app.get("/health")
def health(): return {"status":"ok","environment":s.app_env}
@app.get("/admin",include_in_schema=False)
def dashboard(request:Request): return templates.TemplateResponse(request,"index.html")

