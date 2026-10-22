"""
routers/auth.py - 登录鉴权（兼容原单页前端的三端登录契约）
- POST /api/auth/login        {role, code, phone?, storeCode?} -> {token, role, user|store}
- GET  /api/auth/verify-token -> 当前身份
- POST /api/auth/send-code    发送验证码（DEV_MODE 固定 123456）
演示模式 token 存在进程内存；生产请换 JWT。
"""
import os
import random
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import AdminUser, PointsBucket, Store, User
from services import available_points, member_level

router = APIRouter(prefix="/api/auth", tags=["auth"])

DEV_MODE = os.environ.get("DEV_MODE", "true").lower() == "true"
DEV_FIXED_CODE = os.environ.get("DEV_FIXED_CODE", "123456")

# token 表：token -> user_id
_tokens: dict[str, int] = {}
# 门店 token 表：token -> store_id
_store_tokens: dict[str, int] = {}
# 管理员 token 表：token -> admin_id
_admin_tokens: dict[str, int] = {}


def make_token(prefix: str, table: dict, oid: int) -> str:
    token = f"{prefix}{oid}_{random.randint(100000, 999999)}"
    table[token] = oid
    return token


def _bearer(authorization: str) -> str:
    return authorization.replace("Bearer", "", 1).strip()


def current_role(authorization: Optional[str]) -> str:
    if not authorization:
        return ""
    t = _bearer(authorization)
    if t in _tokens:
        return "user"
    if t in _store_tokens:
        return "store"
    if t in _admin_tokens:
        return "admin"
    return ""


def require_user(token: str) -> int:
    uid = _tokens.get(_bearer(token))
    if not uid:
        raise HTTPException(status_code=401, detail="invalid or expired token")
    return uid


def require_store(token: str) -> int:
    sid = _store_tokens.get(_bearer(token))
    if not sid:
        raise HTTPException(status_code=401, detail="invalid or expired token")
    return sid


def require_admin(token: str) -> int:
    aid = _admin_tokens.get(_bearer(token))
    if not aid:
        raise HTTPException(status_code=401, detail="invalid or expired token")
    return aid


# ---------- schemas ----------
class PhoneIn(BaseModel):
    phone: str


class LoginIn(BaseModel):
    role: str = "user"
    code: str = ""
    phone: Optional[str] = None
    storeCode: Optional[str] = None
    referrer_id: Optional[int] = None


# ---------- 登录 ----------
@router.post("/login")
async def login(body: LoginIn, db: AsyncSession = Depends(get_db)):
    if body.role == "store":
        if not body.storeCode:
            raise HTTPException(status_code=400, detail="缺少门店码")
        r = await db.execute(select(Store).where(Store.code == body.storeCode))
        store = r.scalar_one_or_none()
        if not store or not store.is_active:
            raise HTTPException(status_code=401, detail="门店不存在或已停用")
        token = make_token("st_", _store_tokens, store.id)
        return {
            "code": 0,
            "message": "ok",
            "data": {
                "token": token,
                "role": "store",
                "store": {
                    "id": store.id,
                    "store_code": store.code,
                    "store_name": store.name,
                    "contact": store.contact,
                },
            },
        }

    if body.role == "admin":
        username = body.phone or "admin"
        r = await db.execute(select(AdminUser).where(AdminUser.username == username))
        admin = r.scalar_one_or_none()
        if not admin or admin.password_hash != body.code:
            raise HTTPException(status_code=401, detail="账号或密码错误")
        token = make_token("adm_", _admin_tokens, admin.id)
        return {
            "code": 0,
            "message": "ok",
            "data": {"token": token, "role": "admin", "nickname": admin.username},
        }

    # C 端用户
    phone = (body.phone or "").strip()
    if not phone:
        raise HTTPException(status_code=400, detail="缺少手机号")
    if DEV_MODE and body.code != DEV_FIXED_CODE:
        raise HTTPException(status_code=400, detail="验证码错误或已过期")

    r = await db.execute(select(User).where(User.phone == phone))
    user = r.scalar_one_or_none()
    if not user:
        referrer_id = body.referrer_id
        if referrer_id is not None:
            rr = await db.execute(select(User.id).where(User.id == referrer_id))
            if rr.scalar_one_or_none() is None:
                referrer_id = None
        user = User(
            phone=phone,
            nickname=f"用户{phone[-4:]}",
            referrer_id=referrer_id,
            growth_value=0,
            total_earned=0,
            total_spent=0,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    pts = await available_points(db, user.id)
    lv, lv_name = member_level(user.growth_value or 0)
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "token": make_token("tk_", _tokens, user.id),
            "role": "user",
            "user": {
                "id": user.id,
                "phone": user.phone,
                "nickname": user.nickname,
                "available_points": pts,
                "growth_value": user.growth_value,
                "member_level": lv,
                "level_name": lv_name,
                "referrer_id": user.referrer_id,
            },
        },
    }


@router.get("/verify-token")
async def verify_token(authorization: str = Header("", alias="Authorization"), db: AsyncSession = Depends(get_db)):
    role = current_role(authorization)
    if not role:
        raise HTTPException(status_code=401, detail="token 无效")

    if role == "user":
        uid = require_user(authorization)
        user = await db.get(User, uid)
        if not user:
            raise HTTPException(status_code=401, detail="用户不存在")
        pts = await available_points(db, uid)
        lv, lv_name = member_level(user.growth_value or 0)
        return {
            "code": 0,
            "data": {
                "role": "user",
                "user": {
                    "id": user.id,
                    "phone": user.phone,
                    "nickname": user.nickname,
                    "available_points": pts,
                    "growth_value": user.growth_value,
                    "member_level": lv,
                    "level_name": lv_name,
                },
            },
        }

    if role == "store":
        sid = require_store(authorization)
        store = await db.get(Store, sid)
        return {
            "code": 0,
            "data": {
                "role": "store",
                "store": {
                    "id": store.id,
                    "store_code": store.code,
                    "store_name": store.name,
                    "contact": store.contact,
                },
            },
        }

    aid = require_admin(authorization)
    admin = await db.get(AdminUser, aid)
    return {"code": 0, "data": {"role": "admin", "nickname": admin.username}}


@router.post("/send-code")
async def send_code(body: PhoneIn):
    """演示模式：验证码固定 123456（生产接短信网关）"""
    code = DEV_FIXED_CODE if DEV_MODE else f"{random.randint(100000, 999999)}"
    return {"code": 0, "message": "ok", "data": {"debug_code": code}}