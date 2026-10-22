# routers/jobs.py
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from database import get_db
from models import Job, JobApplication, User
from routers.auth import require_user

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


# --- 请求体模型 ---
class JobCreateIn(BaseModel):
    title: str
    salary: str
    location: str
    tags: str
    description: Optional[str] = None


class JobApplyIn(BaseModel):
    jobId: int


# 1. 发布招工信息
@router.post("/create")
async def create_job(
        body: JobCreateIn,
        authorization: str = Header(..., alias="Authorization"),
        db: AsyncSession = Depends(get_db)
):
    uid = require_user(authorization)
    job = Job(
        publisher_id=uid,
        title=body.title,
        salary=body.salary,
        location=body.location,
        tags=body.tags,
        description=body.description
    )
    db.add(job)
    await db.commit()
    return {"code": 0, "message": "发布成功", "data": {"job_id": job.id}}


# 2. 获取招工列表 (所有人可看)
@router.get("/list")
async def list_jobs(db: AsyncSession = Depends(get_db)):
    # 连表查询发布者的手机号或昵称
    r = await db.execute(
        select(Job, User.nickname).join(User, Job.publisher_id == User.id)
        .where(Job.status == 1)
        .order_by(Job.id.desc())
        .limit(50)
    )
    rows = r.all()
    data = []
    for job, publisher_name in rows:
        data.append({
            "id": job.id,
            "title": job.title,
            "salary": job.salary,
            "location": job.location,
            "tags": job.tags.split(",") if job.tags else [],
            "description": job.description,
            "publisher": publisher_name or "个人发布",
            "created_at": job.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return {"code": 0, "data": data}


# 3. 用户投递职位
@router.post("/apply")
async def apply_job(
        body: JobApplyIn,
        authorization: str = Header(..., alias="Authorization"),
        db: AsyncSession = Depends(get_db)
):
    uid = require_user(authorization)

    # 检查是否重复投递
    exist = await db.execute(
        select(JobApplication).where(
            JobApplication.job_id == body.jobId,
            JobApplication.user_id == uid
        )
    )
    if exist.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="你已投递过该岗位，请勿重复操作")

    apply_record = JobApplication(job_id=body.jobId, user_id=uid)
    db.add(apply_record)
    await db.commit()
    return {"code": 0, "message": "投递成功"}


# 4. 获取我的投递记录
@router.get("/my-applications")
async def my_applications(
        authorization: str = Header(..., alias="Authorization"),
        db: AsyncSession = Depends(get_db)
):
    uid = require_user(authorization)
    r = await db.execute(
        select(JobApplication, Job.title, Job.salary, Job.location)
        .join(Job, JobApplication.job_id == Job.id)
        .where(JobApplication.user_id == uid)
        .order_by(JobApplication.id.desc())
    )
    rows = r.all()
    data = []
    for app, title, salary, location in rows:
        status_map = {1: "待处理", 2: "已录用", 3: "已拒绝"}
        data.append({
            "id": app.id,
            "title": title,
            "salary": salary,
            "location": location,
            "status": status_map.get(app.status, "未知"),
            "created_at": app.created_at.strftime("%Y-%m-%d %H:%M")
        })
    return {"code": 0, "data": data}