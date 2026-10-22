"""
routers/referral.py - 拉新 / 推荐关系
- GET /api/referral/summary      下线数 + 累计奖励
- GET /api/referral/my-downlines 下线明细（settled=1 表示已发放奖励）
"""
from fastapi import APIRouter, Depends, Header
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import PointsLedger, User, VerifyLog
from routers.auth import require_user
from services import available_points

router = APIRouter(prefix="/api/referral", tags=["referral"])


@router.get("/summary")
async def summary(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    uid = require_user(authorization)
    cnt = (
        await db.execute(
            select(func.count()).select_from(User).where(User.referrer_id == uid)
        )
    ).scalar()
    reward = (
        await db.execute(
            select(func.coalesce(func.sum(PointsLedger.delta), 0)).where(
                PointsLedger.user_id == uid,
                PointsLedger.ref_type == "referral",
            )
        )
    ).scalar()
    return {
        "code": 0,
        "data": {"downline_count": int(cnt or 0), "total_reward": int(reward or 0)},
    }


@router.get("/my-downlines")
async def my_downlines(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    uid = require_user(authorization)
    r = await db.execute(
        select(User).where(User.referrer_id == uid).order_by(User.id.desc()).limit(200)
    )
    users = r.scalars().all()
    out = []
    for u in users:
        first = (
            await db.execute(
                select(func.count())
                .select_from(VerifyLog)
                .where(VerifyLog.user_id == u.id)
            )
        ).scalar()
        settled = 1 if int(first or 0) > 0 else 0
        out.append(
            {
                "user_id": u.id,
                "user_phone": u.phone,
                "nickname": u.nickname,
                "level": 1,
                "settled": settled,
                "pending_points": 0 if settled else 100,
                "created_at": u.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    return {"code": 0, "data": out}


@router.get("/downlines")
async def downlines_alias(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """兼容别名：等价于 /my-downlines"""
    return await my_downlines(authorization, db)