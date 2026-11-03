# (运营端接口)
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import User, CooperationEntity, Job
from core.security import get_current_user_id

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    total_jobs = (await db.execute(select(func.count(Job.id)))).scalar()
    pending_companies = (await db.execute(
        select(func.count(CooperationEntity.id)).where(CooperationEntity.status == 'pending'))).scalar()

    return {"code": 0, "data": {
        "total_users": total_users, "total_jobs": total_jobs, "pending_companies": pending_companies
    }}


@router.get("/companies")
async def get_companies(db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(CooperationEntity).order_by(CooperationEntity.status.asc(), CooperationEntity.id.desc()))
    return {"code": 0, "data": res.scalars().all()}


@router.get("/jobs")
async def get_all_jobs(db: AsyncSession = Depends(get_db)):
    query = select(Job, CooperationEntity.name).join(CooperationEntity,
                                                     Job.merchant_id == CooperationEntity.user_id).order_by(
        Job.id.desc())
    result = await db.execute(query)
    data = []
    for job, entity_name in result.all():
        job_dict = job.__dict__.copy()
        job_dict.pop("_sa_instance_state", None)
        job_dict["company_name"] = entity_name
        data.append(job_dict)
    return {"code": 0, "data": data}