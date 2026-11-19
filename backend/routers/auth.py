# backend/routers/auth.py (登录：修复新用户 roles_list 未定义导致的 500，并为单城阶段落默认城市)
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import User, CooperationEntity, GlobalConfig
from core.security import create_access_token, SELF_REGISTER_ROLES, get_current_user
from services.captcha import create_captcha, verify_captcha, captcha_enabled
import datetime
import os

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginReq(BaseModel):
    phone: str
    target_role: str = "worker"
    # 图形验证码（ENABLE_CAPTCHA=false 时可不传）
    captcha_id: str = ""
    captcha_code: str = ""


@router.get("/captcha")
async def get_captcha():
    """获取图形验证码（SVG），为后续短信验证码预留同一套存储"""
    return {"code": 0, "data": await create_captcha()}


class SwitchRoleReq(BaseModel):
    target_role: str


@router.post("/switch-role")
async def switch_role(req: SwitchRoleReq, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    """已登录用户切换身份（意图驱动：同一账号可在求职者/商家间切换）

    仅允许切换到 available_roles 里已开通的身份；
    切换会 +1 token_version，旧 Token 立即失效并下发新 Token。
    """
    target = (req.target_role or "").strip().lower()
    roles = [r.strip().lower() for r in (current_user.available_roles or "worker").split(",") if r.strip()]

    if target not in roles:
        raise HTTPException(
            status_code=403,
            detail=f"您的账号尚未开通「{req.target_role}」身份，请先完成相应的资质认证"
        )

    if current_user.role != target:
        current_user.role = target
        current_user.token_version += 1
        await db.commit()
        await db.refresh(current_user)

    return {
        "code": 0,
        "message": "身份已切换",
        "data": {
            "token": create_access_token(current_user.id, current_user.role,
                                         current_user.city_id or "", current_user.token_version),
            "role": current_user.role,
            "roles": roles,
        }
    }


# 单城阶段兜底：GlobalConfig 缺失时使用，生产多城市前必须改为必填
DEFAULT_CITY_FALLBACK = os.environ.get("DEFAULT_CITY_ID", "410185")


async def resolve_default_city_id(db: AsyncSession) -> str:
    """读取全局默认城市（GlobalConfig.DEFAULT_CITY_ID），异常时回退环境变量/登封。"""
    try:
        row = await db.execute(select(GlobalConfig).where(GlobalConfig.key == "DEFAULT_CITY_ID"))
        cfg = row.scalar_one_or_none()
        if cfg and cfg.value:
            return cfg.value
    except Exception:
        pass
    return DEFAULT_CITY_FALLBACK


@router.post("/login")
async def login(req: LoginReq, db: AsyncSession = Depends(get_db)):
    # 🚨 图形验证码（默认关闭）：开关打开后必须先过人机校验
    if captcha_enabled():
        if not await verify_captcha(req.captcha_id, req.captcha_code):
            raise HTTPException(status_code=400, detail="图形验证码错误或已过期")

    result = await db.execute(select(User).where(User.phone == req.phone))
    user = result.scalar_one_or_none()

    target_role_clean = (req.target_role or "worker").strip().lower()
    default_city_id = await resolve_default_city_id(db)

    if not user:
        # 🚨 管理端角色禁止自助注册，必须由平台开通（否则任何人都能注册成 hq_ops）
        if target_role_clean not in SELF_REGISTER_ROLES:
            raise HTTPException(
                status_code=403,
                detail=f"越权拦截：{req.target_role} 为管理端角色，不支持自助注册，请联系平台开通"
            )

        # 身份不叠加：注册时只获得当前选择的身份（服务商的双能力由角色本身实现，不加额外属性）

        # 🚨 单城阶段：新用户直接落默认城市，否则 jobs.city_id 为 NULL，C 端列表永远查不到
        user = User(
            phone=req.phone,
            nickname="新用户",
            role=target_role_clean,
            available_roles=target_role_clean,
            city_id=default_city_id,
        )
        db.add(user)
        await db.flush()

        file_no = "DA-" + datetime.datetime.now().strftime("%Y%m%d") + "-" + str(user.id).zfill(3)
        db.add(CooperationEntity(
            user_id=user.id,
            city_id=default_city_id,
            file_no=file_no,
            type="company",
            name="请完善名称",
            status="unverified"
        ))
        await db.commit()
        await db.refresh(user)

        # 🚨 修复：原实现只在 else 分支赋值 roles_list，新用户登录会 UnboundLocalError -> 500
        roles_list = [target_role_clean]
    else:
        # 🚨 修复核心：处理可能存在的空格，全部去除并转小写比对
        raw_roles = user.available_roles or "worker"
        roles_list = [r.strip().lower() for r in raw_roles.split(',') if r.strip()]

        if target_role_clean not in roles_list:
            # 意图驱动登录：提示要具体到「缺哪个身份」，前端据此引导认证
            if target_role_clean == "merchant":
                detail = "该手机号尚未开通商家身份，请先完成企业认证"
            elif target_role_clean == "provider":
                detail = "该手机号尚未开通服务商身份，请先完成服务商认证"
            else:
                detail = f"该手机号尚未开通「{req.target_role}」身份"
            raise HTTPException(status_code=403, detail=detail)

        needs_commit = False

        # 如果拥有该权限，且当前激活角色不同，则更新并踢下线旧Token
        if user.role != target_role_clean:
            user.role = target_role_clean
            user.token_version += 1
            needs_commit = True

        # 🚨 存量脏数据兜底：历史账号 city_id 为空时补默认城市
        if not user.city_id:
            user.city_id = default_city_id
            needs_commit = True

        if needs_commit:
            await db.commit()
            await db.refresh(user)

    return {
        "code": 0,
        "data": {
            "token": create_access_token(user.id, user.role, user.city_id or "", user.token_version),
            "roles": roles_list,
            "nickname": user.nickname,
            "city_id": user.city_id
        }
    }
