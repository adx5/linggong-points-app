# backend/routers/ads.py (广告业务：强制写入积分流水 + 降级模式防刷)
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db, redis_client
from models import User, PointTransaction
from core.security import get_current_user_id
from pydantic import BaseModel
from datetime import datetime
import uuid
import os

router = APIRouter(prefix="/api/ads", tags=["ads"])

REQUIRE_APP_SIGNATURE = os.environ.get("REQUIRE_APP_SIGNATURE", "true").lower() == "true"
IS_STAGING = os.environ.get("ENV", "dev").lower() != "prod"

AD_REWARD_POINTS = 5
# 降级模式下每人每日领取上限（原实现无上限，可无限刷）
FALLBACK_DAILY_LIMIT = 20


class AdWatchReq(BaseModel):
    ad_token: str


async def _grant_ad_reward(db: AsyncSession, user_id: int, ref_no: str, remark: str) -> int:
    """发放广告奖励并写流水（统一补齐 city_id）"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.total_points = (user.total_points or 0) + AD_REWARD_POINTS
    db.add(PointTransaction(
        user_id=user_id,
        city_id=user.city_id,
        amount=AD_REWARD_POINTS,
        balance_after=user.total_points,
        biz_type="ad_reward",
        ref_no=ref_no,
        remark=remark,
    ))
    await db.commit()
    return user.total_points


async def _fallback_grant(db: AsyncSession, user_id: int) -> int:
    """Redis 不可用时的降级发放：校验固定 token + 每日上限，避免被无限刷"""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    granted = (await db.execute(
        select(func.count()).select_from(PointTransaction).where(
            PointTransaction.user_id == user_id,
            PointTransaction.biz_type == "ad_reward",
            PointTransaction.created_at >= today,
        ))).scalar() or 0

    if granted >= FALLBACK_DAILY_LIMIT:
        raise HTTPException(status_code=429, detail="今日积分领取已达上限")

    ref_no = f"ad_fallback:{user_id}:{today:%Y%m%d}:{granted}"
    return await _grant_ad_reward(db, user_id, ref_no, "看广告奖励(降级)")


@router.post("/get-token")
async def get_ad_token(request: Request, user_id: int = Depends(get_current_user_id)):
    if REQUIRE_APP_SIGNATURE:
        client_type = request.headers.get("X-Client-Type")
        if client_type != "app":
            raise HTTPException(status_code=403, detail="仅限 App 客户端调用 (默认拒绝策略)")

    if not redis_client:
        if IS_STAGING:
            return {"code": 0, "data": {"ad_token": f"fallback_{user_id}"}}
        raise HTTPException(status_code=500, detail="系统防刷服务异常，无法获取凭证")

    rate_key = f"ad_rate:{user_id}"
    try:
        await redis_client.ping()
        req_count = await redis_client.incr(rate_key)
        if req_count == 1:
            await redis_client.expire(rate_key, 60)
        if req_count > 10:
            raise HTTPException(status_code=429, detail="获取 Token 过于频繁，请稍后再试")
    except HTTPException:
        raise
    except Exception as e:
        print(f"⚠️ Redis连接异常: {e}")
        if IS_STAGING:
            return {"code": 0, "data": {"ad_token": f"fallback_{user_id}"}}
        raise HTTPException(status_code=500, detail="防刷服务连接受限")

    token = uuid.uuid4().hex
    try:
        await redis_client.set(f"ad_token:{token}", user_id, ex=300)
    except Exception:
        if IS_STAGING:
            return {"code": 0, "data": {"ad_token": f"fallback_{user_id}"}}
        raise HTTPException(status_code=500, detail="凭证存储失败")
    return {"code": 0, "data": {"ad_token": token}}


@router.post("/watch-ad")
async def watch_ad(req: AdWatchReq, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    if req.ad_token.startswith("fallback_"):
        if not IS_STAGING:
            raise HTTPException(status_code=400, detail="无效的广告凭证")

        # 🚨 修复：原实现任何以 fallback_ 开头的 token 都能换积分，且 ref_no 由客户端自带，
        # 攻击者可构造 fallback_1、fallback_2… 无限刷分。这里强校验为本人 token 并加每日上限。
        if req.ad_token != f"fallback_{user_id}":
            raise HTTPException(status_code=400, detail="无效的广告凭证")

        points = await _fallback_grant(db, user_id)
        return {"code": 0, "message": "观看成功(降级)，积分+5", "current_points": points}

    if not redis_client:
        raise HTTPException(status_code=500, detail="防刷服务异常，无法发放积分")

    try:
        cache_user_id = await redis_client.get(f"ad_token:{req.ad_token}")
        if not cache_user_id or int(cache_user_id) != user_id:
            raise HTTPException(status_code=400, detail="无效或已过期的广告凭证，请重新获取")
        await redis_client.delete(f"ad_token:{req.ad_token}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"⚠️ 验签 Redis 异常: {e}")
        if IS_STAGING:
            points = await _fallback_grant(db, user_id)
            return {"code": 0, "message": "观看成功(降级)，积分+5", "current_points": points}
        raise HTTPException(status_code=500, detail="防刷服务异常")

    points = await _grant_ad_reward(db, user_id, req.ad_token, "看广告奖励")
    return {"code": 0, "message": "观看成功，积分+5", "current_points": points}
