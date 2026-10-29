"""
routers/ads.py - 广告按组结算（PRD v0.2.2）
- GET  /api/ads/status      -> 各组当前用户的完成进度 {groups:[{id,current,settled}]}
- POST /api/ads/pre-reward -> 前端看完一条广告的回调
流程：写 ad_callback_log(status=0) → 统计该用户该组 status=0 累计
     → 达到 callbacks_required(10) 时把这 10 条置为 status=1 并发放 points_per_group(5)
     全部在同一事务内完成，并用 FOR UPDATE 保证并发安全
"""
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import AdCallbackLog, AdGroup, User
from routers.auth import require_user
from services import grant_points

router = APIRouter(prefix="/api/ads", tags=["ads"])


class PreRewardIn(BaseModel):
    adGroupId: int
    transId: str = ""


async def _groups_for_user(db: AsyncSession, uid: int):
    r = await db.execute(
        select(AdGroup).where(AdGroup.is_active == True).order_by(AdGroup.id.asc())  # noqa: E712
    )
    groups = r.scalars().all()
    out = []
    for g in groups:
        cnt_r = await db.execute(
            select(func.count())
            .select_from(AdCallbackLog)
            .where(
                AdCallbackLog.user_id == uid,
                AdCallbackLog.ad_group_id == g.id,
                AdCallbackLog.status == 0,
            )
        )
        pending = int(cnt_r.scalar() or 0)
        out.append(
            {
                "id": g.id,
                "code": g.code,
                "title": g.title,
                "current": pending,
                "required": g.callbacks_required,
                "points": g.points_per_group,
                "settled": pending >= g.callbacks_required,
            }
        )
    return out


@router.get("/groups")
async def list_groups(
    authorization: str = Header("", alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    uid = require_user(authorization) if authorization else None
    return {"code": 0, "data": {"groups": await _groups_for_user(db, uid) if uid else []}}


@router.get("/status")
async def ad_status(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    uid = require_user(authorization)
    return {"code": 0, "data": {"groups": await _groups_for_user(db, uid)}}


@router.post("/pre-reward")
async def pre_reward(
        body: PreRewardIn,
        authorization: str = Header(..., alias="Authorization"),
        db: AsyncSession = Depends(get_db)
):
    uid = require_user(authorization)

    # 🌟 新增：校验今日广告观看总次数（限制 10 次）
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    count_r = await db.execute(
        select(func.count()).select_from(AdCallbackLog)
        .where(AdCallbackLog.user_id == uid, AdCallbackLog.created_at >= today_start)
    )
    today_count = count_r.scalar() or 0
    if today_count >= 10:
        raise HTTPException(status_code=400, detail="今日观看广告次数已达上限，明天再来吧~")

    # 幂等：同一 transId 只记一次
    if body.transId:
        dup_r = await db.execute(
            select(AdCallbackLog.id).where(
                AdCallbackLog.user_id == uid,
                AdCallbackLog.ad_code == body.transId,
            )
        )
        if dup_r.scalar_one_or_none():
            return {
                "code": 0,
                "message": "重复回调，已忽略",
                "data": {"credited": False, "points_awarded": 0},
            }

    log = AdCallbackLog(
        user_id=uid,
        ad_group_id=group.id,
        ad_code=body.transId or f"{group.code}-{uuid.uuid4().hex[:8]}",
        status=0,
    )
    db.add(log)
    await db.flush()

    cnt_r = await db.execute(
        select(func.count())
        .select_from(AdCallbackLog)
        .where(
            AdCallbackLog.user_id == uid,
            AdCallbackLog.ad_group_id == group.id,
            AdCallbackLog.status == 0,
        )
    )
    pending_count = int(cnt_r.scalar() or 0)

    credited = False
    points_awarded = 0

    if pending_count >= group.callbacks_required:
        # 行锁锁住前 N 条待结算记录，全部置为 status=1
        rows_r = await db.execute(
            select(AdCallbackLog)
            .where(
                AdCallbackLog.user_id == uid,
                AdCallbackLog.ad_group_id == group.id,
                AdCallbackLog.status == 0,
            )
            .order_by(AdCallbackLog.id.asc())
            .limit(group.callbacks_required)
            .with_for_update()
        )
        rows = rows_r.scalars().all()
        for row in rows:
            row.status = 1

        user = await db.get(User, uid)
        await grant_points(
            db,
            user,
            group.points_per_group,
            source="ad",
            source_ref=f"ad_group:{group.code}",
            tx_type="earn",
            ref_type="ad_group",
            ref_id=group.id,
            note=f"广告组 {group.title} 完成结算",
        )
        credited = True
        points_awarded = group.points_per_group

    await db.commit()
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "credited": credited,
            "points_awarded": points_awarded,
            "current": pending_count,
            "required": group.callbacks_required,
        },
    }