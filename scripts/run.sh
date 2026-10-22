#!/usr/bin/env bash
# 扣子部署运行阶段：等待 DB 就绪 → 建表 → 灌测试数据 → 启动 uvicorn
set -e
cd "$(dirname "$0")/.."

PORT="${DEPLOY_RUN_PORT:-${PORT:-3000}}"

# Neon/Postgres 冷启动偶发连接失败，重试等待 DATABASE_URL 可连通
python3 - <<'PY'
import os, sys, time
url = os.environ.get("DATABASE_URL")
if not url:
    print("❌ 缺少环境变量 DATABASE_URL（Neon 连接串）", file=sys.stderr)
    sys.exit(1)
if url.startswith("postgres://"):
    url = url.replace("postgres://", "postgresql://", 1)
os.environ["DATABASE_URL"] = url
for attempt in range(1, 16):
    try:
        import asyncio
        from database import engine
        from sqlalchemy import text
        async def ping():
            async with engine.connect() as c:
                await c.execute(text("SELECT 1"))
        asyncio.get_event_loop().run_until_complete(ping())
        print(f"✅ database reachable (attempt {attempt})")
        sys.exit(0)
    except Exception as e:
        print(f"⏳ db not ready ({attempt}/15): {e}")
        time.sleep(2)
print("❌ 数据库连接失败，请检查 DATABASE_URL", file=sys.stderr)
sys.exit(1)
PY

# 建表 + 幂等灌测试数据
python3 -c "import main, seed; import asyncio; asyncio.get_event_loop().run_until_complete(seed.seed())"

exec uvicorn main:app --host 0.0.0.0 --port "$PORT"