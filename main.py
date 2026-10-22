"""
main.py - FastAPI 应用入口
- 启动时自动建表（init_models）
- 注册全部路由
- 通过 StaticFiles 托管 static/ 下的 Vue 3 单页前端
- 提供 /api/health 健康检查

启动：
    uvicorn main:app --host 0.0.0.0 --port $PORT
"""
import os
import sys
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from pathlib import Path

# ==========================================
# ⚠️ 关键修复：针对 Windows 系统
# psycopg 异步模式不支持 Windows 默认的 ProactorEventLoop
# 必须在导入 FastAPI 和 database 之前强制切换
# ==========================================
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from database import init_models
from routers import admin, ads, auth, exchange, referral, tasks, user, verify

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动即建表（幂等）
    await init_models()
    yield


app = FastAPI(
    title="看广告赚积分App API",
    description="PRD v0.2.2 · FastAPI + PostgreSQL(Neon)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- 统一错误响应：前端约定 {code, message, data} ----------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": f"服务器内部错误: {exc}", "data": None},
        )
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


# ---------- API 路由 ----------
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(tasks.router)
app.include_router(ads.router)
app.include_router(verify.router)
app.include_router(exchange.router)
app.include_router(referral.router)
app.include_router(admin.router)


@app.get("/api/health")
async def health():
    return {"code": 0, "message": "ok", "time": datetime.utcnow().isoformat()}


# ---------- 前端静态托管 ----------
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def index():
    f = STATIC_DIR / "index.html"
    if not f.exists():
        return JSONResponse(
            status_code=404,
            content={"code": 404, "message": "index.html 不存在，请检查 static/ 目录"},
        )
    return FileResponse(str(f))


@app.get("/favicon.ico")
async def favicon():
    return JSONResponse(status_code=204, content=None)