"""Alembic 迁移环境（异步 engine + Windows Selector 事件循环）

要点：
1. 连接串统一从 backend/.env 的 DATABASE_URL 读取，不在 alembic.ini 里写密码。
2. 项目用 psycopg 异步驱动，Windows 下必须切 WindowsSelectorEventLoopPolicy，
   否则会报 "Psycopg cannot use the 'ProactorEventLoop'"。
3. target_metadata 取 database.Base.metadata，import models 确保所有表已注册。
4. LEGACY_TABLES 保护：库中存在一批 models.py 未声明的历史表（早期版本遗留），
   必须让 autogenerate 忽略它们，否则一条 "自动迁移" 就会把它们 DROP 掉。
"""
import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(BACKEND_DIR / ".env")

from database import Base, ASYNC_DATABASE_URL  # noqa: E402
import models  # noqa: F401,E402  # 确保所有表注册到 metadata

config = context.config

if config.config_file_name:
    try:
        fileConfig(config.config_file_name)
    except Exception:
        pass

target_metadata = Base.metadata

# ⚠️ 数据库里存在、但 models.py 从未声明的历史表（疑似上一代实现残留）。
# 这些表不属于当前应用，绝不能由 autogenerate 删除。
LEGACY_TABLES = {
    "ad_groups",
    "ad_callback_log",
    "ad_callback_logs",
    "points_buckets",
    "points_ledger",
    "task_defs",
    "task_log",
    "exchange_items",
    "exchange_log",
    "admin_users",
    "sms_codes",
    "stores",
    "verify_log",
    "provider_infos",
}


def include_object(obj, name, type_, reflected, compare_to):
    """autogenerate 过滤钩子：跳过遗留表"""
    if type_ == "table" and name in LEGACY_TABLES:
        return False
    return True


def get_url() -> str:
    """优先 alembic.ini 的 sqlalchemy.url，否则用 .env 的异步连接串"""
    return config.get_main_option("sqlalchemy.url") or ASYNC_DATABASE_URL


def run_migrations_offline() -> None:
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        include_object=include_object,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        include_object=include_object,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(get_url(), poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_migrations_online())
