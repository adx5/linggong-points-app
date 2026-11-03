# backend/routers/auth.py (修复多角色切换的空格解析Bug)
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import User, CooperationEntity
from core.security import create_access_token
import datetime

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginReq(BaseModel):
    phone: str
    target_role: str = "worker"


@router.post("/login")
async def login(req: LoginReq, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.phone == req.phone))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            phone=req.phone,
            nickname="新用户",
            role=req.target_role,
            available_roles=req.target_role
        )
        db.add(user)
        await db.flush()

        file_no = "DA-" + datetime.datetime.now().strftime("%Y%m%d") + "-" + str(user.id).zfill(3)
        db.add(CooperationEntity(
            user_id=user.id,
            file_no=file_no,
            type="company",
            name="请完善名称",
            status="unverified"
        ))
        await db.commit()
        await db.refresh(user)
    else:
        # 🚨 修复核心：处理可能存在的空格，全部去除并转小写比对
        raw_roles = user.available_roles or "worker"
        roles_list = [r.strip().lower() for r in raw_roles.split(',') if r.strip()]

        target_role_clean = req.target_role.strip().lower()

        if target_role_clean not in roles_list:
            raise HTTPException(status_code=403, detail=f"越权拦截：您的账号未开通 {req.target_role} 权限，无法登录该端")

        # 如果拥有该权限，且当前激活角色不同，则更新并踢下线旧Token
        if user.role != target_role_clean:
            user.role = target_role_clean
            user.token_version += 1
            await db.commit()
            await db.refresh(user)

    return {
        "code": 0,
        "data": {
            "token": create_access_token(user.id, user.role, user.city_id or "", user.token_version),
            "roles": roles_list if user else [req.target_role],
            "nickname": user.nickname
        }
    }