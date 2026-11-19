# backend/main.py (FastAPI入口：CORS 白名单 + 管理端 IP 白名单)
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from database import init_models
import os
import ipaddress

from routers import auth, jobs, user, ads, upload, merchant, admin, audit, notifications, meta, services, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_models()
    from scheduler import start_scheduler, shutdown_scheduler
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(lifespan=lifespan)

ENV = os.environ.get("ENV", "dev").lower().strip()

# ==========================================
# CORS 白名单
# ==========================================
ALLOW_ORIGINS_STR = os.environ.get("ALLOW_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
ALLOW_ORIGINS = [origin.strip() for origin in ALLOW_ORIGINS_STR.split(",") if origin.strip()]
if "*" in ALLOW_ORIGINS and ENV != "dev":
    raise ValueError("🚨 致命错误：CORS 白名单不能配置为 '*'！")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,
    # 🚨 收口：只放行实际用到的方法与请求头（原来 methods/headers 都是 "*"）
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-City-Id", "X-Client-Type"],
)

# ==========================================
# 管理端 IP 白名单
# ==========================================
# 修复点：
#   1) 原实现直接 split(',') 不 strip，"127.0.0.1, ::1" 会带前导空格导致永不匹配
#   2) 原实现取 request.client.host，CloudBase/Nginx 反代后拿到的是代理 IP，切到 prod 会把真管理员全拦掉
#   3) 原实现用 IS_STAGING 整段跳过，白名单等于从未生效；改为显式开关，默认仅生产强制
ALLOWED_ADMIN_IPS = [ip.strip() for ip in
                     os.environ.get("ALLOWED_ADMIN_IPS", "127.0.0.1,::1").split(",") if ip.strip()]

_enforce_raw = os.environ.get("ENFORCE_ADMIN_IP", "").strip().lower()
if _enforce_raw in ("1", "true", "yes", "on"):
    ENFORCE_ADMIN_IP = True
elif _enforce_raw in ("0", "false", "no", "off"):
    ENFORCE_ADMIN_IP = False
else:
    # 未显式配置时：生产强制开启，其余环境关闭（便于本地与 Staging 调试）
    ENFORCE_ADMIN_IP = (ENV == "prod")


def get_client_ip(request: Request) -> str:
    """取真实客户端 IP：反代场景下 request.client.host 只是网关地址"""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else ""


def ip_allowed(client_ip: str) -> bool:
    """精确 IP 或 CIDR 网段匹配"""
    if not client_ip:
        return False
    for rule in ALLOWED_ADMIN_IPS:
        try:
            if "/" in rule:
                if ipaddress.ip_address(client_ip) in ipaddress.ip_network(rule, strict=False):
                    return True
            elif client_ip == rule:
                return True
        except ValueError:
            continue
    return False


@app.middleware("http")
async def admin_ip_whitelist_middleware(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/admin/") or path.startswith("/api/audit/"):
        if not ENFORCE_ADMIN_IP:
            return await call_next(request)
        if not ip_allowed(get_client_ip(request)):
            return JSONResponse(status_code=403, content={"detail": "非法 IP 访问管理接口"})
    return await call_next(request)


@app.get("/health")
def health_check():
    return {"status": "ok", "env": os.environ.get("ENV", "dev")}


app.include_router(notifications.router)
app.include_router(meta.router)
app.include_router(services.router)
app.include_router(tasks.router)
app.include_router(auth.router)
app.include_router(jobs.router)
app.include_router(user.router)
app.include_router(ads.router)
app.include_router(upload.router)
app.include_router(merchant.router)
app.include_router(admin.router)
app.include_router(audit.router)
