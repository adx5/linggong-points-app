# backend/core/security.py (安全核心：JWT生成校验、角色权限拦截、城市隔离过滤、游客放行)
import os
import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db, redis_client
from models import User

_ENV = os.environ.get("ENV", "dev").lower().strip()
SECRET_KEY = os.environ.get("SECRET_KEY", "").strip()

# 🚨 修复：原实现回退到硬编码 "linggong_secret"，未配置时可被离线伪造 JWT。
# 生产环境必须显式配置，缺失直接拒绝启动（fail-closed）；非生产用固定值便于本地调试。
if not SECRET_KEY:
    if _ENV == "prod":
        raise RuntimeError("🚨 致命错误：生产环境必须配置 SECRET_KEY，拒绝启动")
    SECRET_KEY = "linggong_secret_dev_only"

ALGORITHM = "HS256"

# 🚨 核心配置：auto_error=False 允许没带 Token 时返回 None（供游客接口使用）
security = HTTPBearer(auto_error=False)


def create_access_token(user_id: int, role: str, city_id: str, token_version: int):
    payload = {
        "user_id": user_id,
        "role": role,
        "city_id": city_id,
        "token_version": token_version,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


async def _decode_and_verify_user(token: str, db: AsyncSession) -> User:
    """内部方法：解析 Token 并强校验数据库中的版本号"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        token_version = payload.get("token_version")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="身份凭证无效")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    # 校验版本号（角色切换、被冻结等场景会递增此版本号使旧 Token 失效）
    if user.token_version != token_version:
        raise HTTPException(status_code=401, detail="权限已变更，请重新登录")

    return user


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
) -> User:
    """强制登录依赖：未带 Token 或 Token 失效直接 401"""
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供身份凭证")
    return await _decode_and_verify_user(credentials.credentials, db)


async def get_optional_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: AsyncSession = Depends(get_db)
) -> User | None:
    """
    游客放行依赖（仅限白名单接口使用）：
    1. 未携带 Token -> 返回 None（视作游客）
    2. 携带了 Token 但无效/过期 -> 抛出 401（绝不降级为游客，防止伪造绕过）
    """
    if not credentials:
        return None

    return await _decode_and_verify_user(credentials.credentials, db)


# 兼容老接口的依赖
async def get_current_user_id(current_user: User = Depends(get_current_user)) -> int:
    return current_user.id


def require_roles(allowed_roles: list[str], deny_message: str | None = None):
    """角色权限校验工厂

    deny_message：用于意图驱动登录的友好提示。
    例如求职者误点「发布岗位」时，后端应回「请完成商家认证」而不是笼统的权限不足。
    """

    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            detail = deny_message or "权限不足，无权访问此接口"
            raise HTTPException(status_code=403, detail=detail)
        return current_user

    return role_checker


# 管理端角色：hq_* 为总台（全局可见），city_* 为属地（按城市隔离）
ADMIN_ROLES = ["hq_ops", "hq_admin", "city_ops", "city_gov", "city_admin"]

# 管理端统一鉴权依赖（/api/admin、/api/audit 使用）
admin_required = require_roles(ADMIN_ROLES)

# 可自助注册的角色白名单：管理端角色必须由平台开通，禁止自助注册
SELF_REGISTER_ROLES = ["worker", "merchant", "provider"]


def is_hq_role(current_user: User | None) -> bool:
    """是否总台角色（可跨城查看）"""
    return bool(current_user and current_user.role.startswith("hq_"))


def scope_city_query(query, current_user: User, model):
    """管理端通用城市范围过滤：总台看全量，属地只看本城"""
    if is_hq_role(current_user):
        return query
    return query.where(model.city_id == current_user.city_id)


def apply_city_filter(query, current_user: User | None, model: any):
    """统一的城市过滤查询"""
    # 总部角色全局查看
    if current_user and current_user.role.startswith("hq_"):
        return query
    # C端 Worker/游客跨城，不限制列表查看（具体过滤由接口内部的 city_id 参数决定）
    if not current_user or current_user.role in ["worker", "user"]:
        return query
    # 单城角色/B端，强制限制
    return query.where(model.city_id == current_user.city_id)


def verify_resource_city(resource_city_id: str, current_user: User | None):
    """单条资源的归属校验"""
    if not current_user or current_user.role.startswith("hq_") or current_user.role in ["worker", "user"]:
        return True
    if resource_city_id != current_user.city_id:
        raise HTTPException(status_code=403, detail="越权拦截：无权操作其他城市的数据")
    return True


async def check_rate_limit(key: str, limit: int, window_seconds: int):
    """通用 Redis 频控：超阈值抛 429。Redis 不可用时静默放行（与广告接口降级策略一致）"""
    if redis_client is None:
        return True
    try:
        current = await redis_client.incr(key)
        if current == 1:
            await redis_client.expire(key, window_seconds)
        if current > limit:
            raise HTTPException(status_code=429, detail="操作过于频繁，请稍后再试")
    except HTTPException:
        raise
    except Exception:
        # Redis 抖动不应阻断主流程
        return True
    return True


async def check_and_lock_ad(user_id: int, trans_id: str):
    """广告防抖锁"""
    if redis_client is None:
        return True
    is_locked = await redis_client.set(f"ad_lock:{user_id}:{trans_id}", "1", ex=10, nx=True)
    if not is_locked:
        raise HTTPException(status_code=429, detail="请求过于频繁")
    return True