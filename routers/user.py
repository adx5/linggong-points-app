"""
routers/user.py - 个人资料 / 积分总览 / 积分流水
- GET /api/user/points  -> {available_points, growth_value, member_level, ...}
- GET /api/user/flow    -> 最近积分流水（前端首页表格）
- GET /api/user/me      -> 完整资料
- GET /api/user/buckets -> 未过期分桶明细
"""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import PointsBucket, PointsLedger, User
from routers.auth import require_user
from services import available_points, get_active_buckets, member_level, now

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/points")
async def user_points(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    uid = require_user(authorization)
    user = await db.get(User, uid)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    total = await available_points(db, uid)
    lv, lv_name = member_level(user.growth_value or 0)
    return {
        "code": 0,
        "data": {
            "available_points": total,
            "growth_value": user.growth_value,
            "member_level": lv,
            "level_name": lv_name,
            "total_earned": user.total_earned,
            "total_spent": user.total_spent,
        },
    }


@router.get("/flow")
async def user_flow(
    limit: int = 20,
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    uid = require_user(authorization)
    r = await db.execute(
        select(PointsLedger)
        .where(PointsLedger.user_id == uid)
        .order_by(PointsLedger.id.desc())
        .limit(min(limit, 100))
    )
    rows = r.scalars().all()
    return {
        "code": 0,
        "data": [
            {
                "id": x.id,
                "flow_type": 1 if x.delta > 0 else 2,
                "points": x.delta,
                "balance_after": x.balance_after,
                "remark": x.note or "",
                "created_at": x.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for x in rows
        ],
    }


@router.get("/me")
async def me(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    uid = require_user(authorization)
    user = await db.get(User, uid)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    total = await available_points(db, uid)
    lv, lv_name = member_level(user.growth_value or 0)
    return {
        "code": 0,
        "data": {
            "id": user.id,
            "phone": user.phone,
            "nickname": user.nickname,
            "available_points": total,
            "growth_value": user.growth_value,
            "member_level": lv,
            "level_name": lv_name,
            "total_earned": user.total_earned,
            "total_spent": user.total_spent,
            "referrer_id": user.referrer_id,
            "created_at": user.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        },
    }


@router.get("/buckets")
async def buckets(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    uid = require_user(authorization)
    rows = await get_active_buckets(db, uid)
    return {
        "code": 0,
        "data": [
            {
                "id": b.id,
                "balance": b.balance,
                "source": b.source,
                "source_ref": b.source_ref,
                "expire_date": b.expire_date.strftime("%Y-%m-%d"),
            }
            for b in rows
        ],
    }