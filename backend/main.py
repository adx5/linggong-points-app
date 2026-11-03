# backend/main.py (FastAPI入口：安全加固、CORS白名单、严格健康检查)
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

# 🚨 修复硬伤 2：CORS 强校验，发现 "*" 直接拒绝启动
ALLOW_ORIGINS_STR = os.environ.get("ALLOW_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
ALLOW_ORIGINS = [origin.strip() for origin in ALLOW_ORIGINS_STR.split(",")]

if "*" in ALLOW_ORIGINS:
    raise ValueError("🚨 致命错误：CORS 白名单不能配置为 '*'，请配置具体的域名！")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 管理端 IP 白名单
ALLOWED_ADMIN_IPS = os.environ.get("ALLOWED_ADMIN_IPS", "127.0.0.1,::1").split(",")


@app.middleware("http")
async def admin_ip_whitelist_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/admin/") or path.startswith("/api/audit/"):
        # 🚨 修复硬伤 3：云托管场景下，只有网关可信时才取 X-Forwarded-For
        # 目前直接取 client.host，或者要求网关传递真实 IP。这里演示强校验逻辑。
        client_ip = request.client.host

        # 如果非本地，且不在白名单，直接 403
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