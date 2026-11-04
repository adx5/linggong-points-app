# backend/routers/user.py (用户业务接口：查询积分、扣减积分、多套简历维护)
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from sqlalchemy.orm.attributes import flag_modified
from database import get_db
from models import User
from core.security import get_current_user_id

router = APIRouter(prefix="/api/user", tags=["user"])


class ResumeReq(BaseModel):
    basic: Dict[str, Any]  # 通用信息: name, phone, email, skills, education
    jobs: List[Dict[str, Any]]  # 岗位专属简历列表: 包含 id, target_job, target_city, work_experience, self_evaluation


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


@router.get("/resume")
async def get_resume(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 结构兜底
    resume_data = user.resume_data or {}
    if "basic" not in resume_data:
        resume_data["basic"] = {"name": "", "phone": "", "email": "", "skills": "", "education": ""}
    if "jobs" not in resume_data:
        resume_data["jobs"] = []

    return {"code": 0, "data": resume_data}


@router.put("/resume")
async def save_resume(req: ResumeReq, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.resume_data = req.dict()
    flag_modified(user, "resume_data")
    await db.commit()
    return {"code": 0, "message": "简历保存成功"}