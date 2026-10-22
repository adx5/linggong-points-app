"""
routers/tasks.py - 每日福利任务
- GET  /api/tasks/today   -> {task_code: 0|1}（前端首页/任务中心）
- POST /api/tasks/{code}  -> 领取积分（写分桶 + 流水）
任务按天重置：task_log.log_date = 今天
"""
from datetime import date

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import TaskDef, TaskLog, User
from routers.auth import require_user
from services import grant_points

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


async def _today_map(db: AsyncSession, uid: int):
    r = await db.execute(
        select(TaskDef).where(TaskDef.is_active == True).order_by(  # noqa: E712
            TaskDef.sort_no.asc(), TaskDef.id.asc()
        )
    )
    tasks = r.scalars().all()
    done_r = await db.execute(
        select(TaskLog.task_id).where(
            TaskLog.user_id == uid, TaskLog.log_date == date.today()
        )
    )
    done = set(done_r.scalars().all())
    return {t.code: (1 if t.id in done else 0) for t in tasks}


@router.get("/today")
async def today_tasks(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    uid = require_user(authorization)
    return {"code": 0, "data": await _today_map(db, uid)}


@router.get("/list")
async def list_tasks(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    uid = require_user(authorization)
    r = await db.execute(
        select(TaskDef)
        .where(TaskDef.is_active == True)  # noqa: E712
        .order_by(TaskDef.sort_no.asc(), TaskDef.id.asc())
    )
    tasks = r.scalars().all()
    done_r = await db.execute(
        select(TaskLog.task_id).where(
            TaskLog.user_id == uid, TaskLog.log_date == date.today()
        )
    )
    done = set(done_r.scalars().all())
    return {
        "code": 0,
        "data": [
            {
                "id": t.id,
                "code": t.code,
                "title": t.title,
                "description": t.description,
                "reward_points": t.reward_points,
                "completed": t.id in done,
            }
            for t in tasks
        ],
    }


@router.post("/{code}")
async def complete_task(
    code: str,
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    uid = require_user(authorization)
    r = await db.execute(select(TaskDef).where(TaskDef.code == code))
    task = r.scalar_one_or_none()
    if not task or not task.is_active:
        raise HTTPException(status_code=404, detail="任务不存在")

    existing_r = await db.execute(
        select(TaskLog).where(
            TaskLog.user_id == uid,
            TaskLog.task_id == task.id,
            TaskLog.log_date == date.today(),
        )
    )
    if existing_r.scalar_one_or_none():
        return {"code": 0, "message": "今日已完成", "data": {"reward": 0}}

    user = await db.get(User, uid)
    await grant_points(
        db,
        user,
        task.reward_points,
        source="task",
        source_ref=f"task:{task.code}",
        tx_type="earn",
        ref_type="task",
        ref_id=task.id,
        note=f"完成任务: {task.title}",
    )
    db.add(
        TaskLog(
            user_id=uid,
            task_id=task.id,
            reward=task.reward_points,
            log_date=date.today(),
        )
    )
    await db.commit()
    return {
        "code": 0,
        "message": f"任务完成 +{task.reward_points}分",
        "data": {"reward": task.reward_points},
    }