# backend/core/config_helper.py (全局配置获取及监控告警)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import GlobalConfig

async def get_config(db: AsyncSession, key: str, default: str = None) -> str:
    result = await db.execute(select(GlobalConfig).where(GlobalConfig.key == key))
    config = result.scalar_one_or_none()
    if not config:
        # 🚨 监控告警：配置缺失
        print(f"🚨 [ALERT] 监控告警：缺失核心配置 {key}，使用保底值 {default}")
        return default
    return config.value