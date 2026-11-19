# backend/routers/tasks.py (任务中心：推广赚积分)
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Job, JobApplication, JobPromotion, PointTransaction, User
from core.security import get_current_user
from services.promotion import PROMOTION_REWARD_POINTS

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/promotion")
async def promotion_stats(db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    """任务中心 · 我的推广：推广数 / 已结算 / 累计积分 / 最近结算记录"""
    promoted = (await db.execute(
        select(func.count()).select_from(JobPromotion)
        .where(JobPromotion.promoter_id == current_user.id))).scalar() or 0

    settled = (await db.execute(
        select(func.count()).select_from(JobApplication).where(
            JobApplication.promoter_id == current_user.id,
            JobApplication.status == 8))).scalar() or 0

    total_points = (await db.execute(
        select(func.coalesce(func.sum(PointTransaction.amount), 0)).where(
            PointTransaction.user_id == current_user.id,
            PointTransaction.biz_type == "promotion_reward"))).scalar() or 0

    rows = (await db.execute(
        select(JobApplication.id, Job.title, JobApplication.finish_time)
        .join(Job, Job.id == JobApplication.job_id)
        .where(
            JobApplication.promoter_id == current_user.id,
            JobApplication.status == 8)
        .order_by(JobApplication.id.desc()).limit(10))).all()

    records = [{
        "application_id": app_id,
        "job_title": title,
        "finished_at": finished.strftime("%m-%d %H:%M") if finished else "",
    } for app_id, title, finished in rows]

    return {"code": 0, "data": {
        "reward_points": PROMOTION_REWARD_POINTS,
        "promoted": promoted,
        "settled": settled,
        "total_points": int(total_points),
        "records": records,
    }}
