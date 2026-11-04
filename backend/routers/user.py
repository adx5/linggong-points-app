# backend/routers/user.py (用户业务接口：查询积分、扣减积分、简历维护)
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from sqlalchemy.orm.attributes import flag_modified
from database import get_db
from models import User
from core.security import get_current_user_id

router = APIRouter(prefix="/api/user", tags=["user"])


class ResumeReq(BaseModel):
    name: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""
    target_job: Optional[str] = ""
    target_city: Optional[str] = ""
    skills: Optional[str] = ""
    work_experience: Optional[str] = ""
    project_experience: Optional[str] = ""
    education: Optional[str] = ""
    self_evaluation: Optional[str] = ""


@router.get("/points")
async def get_points(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    user = await db.get(User, user_id)
    return {"code": 0, "data": {"points": user.total_points if user else 0}}


@router.post("/exchange")
async def exchange_item(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    stmt = (
        update(User)
        .where(User.id == user_id, User.total_points >= 50)
        .values(total_points=User.total_points - 50)
    )
    result = await db.execute(stmt)
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=400, detail="积分不足")
    return {"code": 0, "message": "兑换成功，已生成提货码"}


# 🚨 新增：获取简历
@router.get("/resume")
async def get_resume(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    # 如果没填过，返回空字典，前端做兜底
    return {"code": 0, "data": user.resume_data or {}}


# 🚨 新增：保存/更新简历
@router.put("/resume")
async def save_resume(req: ResumeReq, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.resume_data = req.dict()
    flag_modified(user, "resume_data")  # 通知 SQLAlchemy JSONB 字段已变更
    await db.commit()
    return {"code": 0, "message": "简历保存成功"}