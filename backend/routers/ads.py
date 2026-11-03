# backend/routers/ads.py (广告业务接口：服务端短期 Token 校验、高频防刷降级)
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, redis_client
from models import User
from core.security import get_current_user_id
from pydantic import BaseModel
import uuid
import os

router = APIRouter(prefix="/api/ads", tags=["ads"])

REQUIRE_APP_SIGNATURE = os.environ.get("REQUIRE_APP_SIGNATURE", "true").lower() == "true"
IS_STAGING = os.environ.get("ENV", "dev").lower() != "prod"

class AdWatchReq(BaseModel):
    ad_token: str

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
        user = await db.get(User, user_id)
        user.total_points += 5
        await db.commit()
        return {"code": 0, "message": "观看成功(降级)，积分+5", "current_points": user.total_points}

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
            user = await db.get(User, user_id)
            user.total_points += 5
            await db.commit()
            return {"code": 0, "message": "观看成功(降级)，积分+5", "current_points": user.total_points}
        raise HTTPException(status_code=500, detail="防刷服务异常")

    user = await db.get(User, user_id)
    user.total_points += 5
    await db.commit()
    return {"code": 0, "message": "观看成功，积分+5", "current_points": user.total_points}