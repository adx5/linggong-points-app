# backend/main.py (FastAPI入口：纯图床模式，无需本地静态挂载，保持完整)
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from database import init_models
import os

from routers import auth, jobs, user, ads, upload, merchant, admin, audit, notifications

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    from scheduler import start_scheduler, shutdown_scheduler
    start_scheduler()
    yield
    shutdown_scheduler()

app = FastAPI(lifespan=lifespan)

ALLOW_ORIGINS_STR = os.environ.get("ALLOW_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
ALLOW_ORIGINS = [origin.strip() for origin in ALLOW_ORIGINS_STR.split(",")]
if "*" in ALLOW_ORIGINS and os.environ.get("ENV") != "dev":
    raise ValueError("🚨 致命错误：CORS 白名单不能配置为 '*'！")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_ADMIN_IPS = os.environ.get("ALLOWED_ADMIN_IPS", "127.0.0.1,::1").split(",")
IS_STAGING = os.environ.get("ENV", "dev") != "prod"

@app.middleware("http")
async def admin_ip_whitelist_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/admin/") or path.startswith("/api/audit/"):
        if IS_STAGING:
            return await call_next(request)
        client_ip = request.client.host
        if client_ip not in ALLOWED_ADMIN_IPS:
            return JSONResponse(status_code=403, content={"detail": "非法 IP 访问管理接口"})
    return await call_next(request)

@app.get("/health")
def health_check():
    return {"status": "ok", "env": os.environ.get("ENV", "dev")}

app.include_router(notifications.router)
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(user.router)
app.include_router(ads.router)
app.include_router(upload.router)
app.include_router(merchant.router)
app.include_router(admin.router)
app.include_router(audit.router)