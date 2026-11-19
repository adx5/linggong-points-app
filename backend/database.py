# backend/database.py (数据库基建：增加连接池上限、超时与保活)
import os
from typing import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import select
import redis.asyncio as aioredis

load_dotenv()
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL 未设置")
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# 🚨 修复硬伤 4：增加连接池限制、超时与回收
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=1800
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
try:
    redis_client = aioredis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True, socket_connect_timeout=2)
except Exception:
    redis_client = None
    print("⚠️ Redis连接失败，防刷降级")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_models():
    import models

    # 建表策略：Alembic 接管 schema 后，生产环境不应再自动建表。
    # DB_AUTO_CREATE=true  → 启动时 create_all（本地开发方便）
    # DB_AUTO_CREATE=false → 完全交给 `alembic upgrade head`
    # 未配置时：非生产环境开、生产环境关。
    auto_create = os.environ.get("DB_AUTO_CREATE", "").strip().lower()
    if auto_create in ("0", "false", "no", "off"):
        do_create = False
    elif auto_create in ("1", "true", "yes", "on"):
        do_create = True
    else:
        do_create = os.environ.get("ENV", "dev").lower() != "prod"

    if do_create:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    else:
        print("ℹ️ DB_AUTO_CREATE 已关闭，表结构由 Alembic 管理（部署前请执行 alembic upgrade head）")

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(models.City))
        if not result.scalars().first():
            cities = [
                models.City(id="410185", name="登封"),
                models.City(id="410173", name="航空港"),
                models.City(id="411300", name="南阳")
            ]
            session.add_all(cities)

        result_cfg = await session.execute(select(models.GlobalConfig))
        if not result_cfg.scalars().first():
            configs = [
                models.GlobalConfig(key="DEFAULT_CITY_ID", value="410185", description="默认城市ID"),
                models.GlobalConfig(key="CITY_CRAWL_THRESHOLD", value="3", description="防爬阈值"),
            ]
            session.add_all(configs)

        await session.commit()
        print("✅ 城市字典与全局配置初始化完成")