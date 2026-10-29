"""
routers/verify.py - B 端门店核销（PRD v0.2.2）
- POST /api/verify/query    输入手机号查该用户可用积分
- POST /api/verify/confirm  确认扣减：FIFO（expire_date 升序 + FOR UPDATE）
                            + growth_value 累加 + 写 verify_log
                            + 下线首次核销 → 给上线发 100 积分
- GET  /api/verify/history  门店核销流水
"""
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Store, User, VerifyLog
from routers.auth import require_store
from services import (
    InsufficientPoints,
    available_points,
    is_first_verify,
    member_level,
    reward_referrer,
    spend_points_fifo,
)

router = APIRouter(prefix="/api/verify", tags=["verify"])


class QueryIn(BaseModel):
    phone: str


class ConfirmIn(BaseModel):
    phone: str
    totalPoints: int
    verifyCode: str = ""
    batchNo: str = ""


@router.post("/query")
async def query_user(
    body: QueryIn,
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    require_store(authorization)
    r = await db.execute(select(User).where(User.phone == body.phone))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    total = await available_points(db, user.id)
    lv, lv_name = member_level(user.growth_value or 0)
    # 在 routers/verify.py 的 query_user 函数里修改：
    return {
        "code": 0,
        "data": {
            "id": user.id,
            "phone": user.phone[:3] + "****" + user.phone[-4:],  # 🌟 脱敏处理
            # ...
        }
    }


@router.post("/confirm")
async def confirm_verify(
    body: ConfirmIn,
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    store_id = require_store(authorization)
    if body.totalPoints <= 0:
        raise HTTPException(status_code=400, detail="核销积分必须大于 0")

    store = await db.get(Store, store_id)
    if not store:
        raise HTTPException(status_code=404, detail="门店不存在")

    r = await db.execute(select(User).where(User.phone == body.phone))
    user = r.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    first_verify = await is_first_verify(db, user.id)

    # FIFO 扣减（FOR UPDATE）
    try:
        balance_after = await spend_points_fifo(
            db,
            user.id,
            body.totalPoints,
            ref_type="verify",
            ref_id=store.id,
            note=f"门店核销 {store.name}",
        )
    except InsufficientPoints as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    # 成长值累加（核销 1 分 = 1 成长值）
    user.growth_value = (user.growth_value or 0) + body.totalPoints
    user.total_spent = (user.total_spent or 0) + body.totalPoints

    log = VerifyLog(
        store_id=store.id,
        user_id=user.id,
        points_spent=body.totalPoints,
        growth_delta=body.totalPoints,
        verify_code=body.verifyCode,
        batch_no=body.batchNo,
        operator_name=store.name,
        note=f"{store.name} 核销",
        is_first_verify=first_verify,
    )
    db.add(log)
    await db.flush()

    # 拉新：下线首次核销 → 上线 +100
    referrer_rewarded = False
    if first_verify:
        referrer_rewarded = await reward_referrer(db, user, 100)

    await db.commit()
    return {
        "code": 0,
        "message": "核销成功",
        "data": {
            "verify_id": log.id,
            "points_spent": body.totalPoints,
            "remaining_points": balance_after,
            "growth_value": user.growth_value,
            "first_verify": first_verify,
            "referrer_rewarded": referrer_rewarded,
        },
    }


@router.get("/history")
async def history(
    limit: int = 20,
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    store_id = require_store(authorization)
    r = await db.execute(
        select(VerifyLog)
        .where(VerifyLog.store_id == store_id)
        .order_by(VerifyLog.id.desc())
        .limit(min(limit, 100))
    )
    logs = r.scalars().all()
    users = {}
    for x in logs:
        if x.user_id not in users:
            u = await db.get(User, x.user_id)
            users[x.user_id] = u.phone if u else ""
    return {
        "code": 0,
        "data": [
            {
                "id": x.id,
                "user_phone": users.get(x.user_id, ""),
                "total_points": x.points_spent,
                "verify_code": x.verify_code or "",
                "batch_no": x.batch_no or "",
                "operator_name": x.operator_name or "",
                "verify_time": x.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for x in logs
        ],
    }