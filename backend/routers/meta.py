# backend/routers/meta.py (公共元数据：城市字典等)
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import City, GlobalConfig, Job, ProviderProfile

router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("/cities")
async def list_cities(db: AsyncSession = Depends(get_db)):
    """已开放城市列表（C 端首页城市切换用）"""
    res = await db.execute(select(City).where(City.status == "active").order_by(City.id))
    cities = res.scalars().all()

    cfg = await db.execute(select(GlobalConfig).where(GlobalConfig.key == "DEFAULT_CITY_ID"))
    default_cfg = cfg.scalar_one_or_none()

    return {"code": 0, "data": {
        "default_city_id": default_cfg.value if default_cfg else None,
        "list": [{"id": c.id, "name": c.name} for c in cities],
    }}


@router.get("/districts")
async def list_districts(city_id: str = "410185", db: AsyncSession = Depends(get_db)):
    """区/镇列表：从岗位与服务商档案里聚合，供「附近」筛选使用"""
    job_districts = (await db.execute(
        select(Job.district).where(
            Job.city_id == city_id, Job.district.is_not(None), Job.district != "")
        .distinct())).scalars().all()

    provider_districts = (await db.execute(
        select(ProviderProfile.district).where(
            ProviderProfile.city_id == city_id,
            ProviderProfile.district.is_not(None),
            ProviderProfile.district != "")
        .distinct())).scalars().all()

    merged = sorted({d for d in list(job_districts) + list(provider_districts) if d})
    return {"code": 0, "data": merged}
