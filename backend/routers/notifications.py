# (消息通知接口)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from database import get_db
from models import Notification
from core.security import get_current_user_id

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

@router.get("/list")
async def get_notifications(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    query = select(Notification).where(Notification.user_id == user_id).order_by(Notification.id.desc())
    result = await db.execute(query)
    return {"code": 0, "data": result.scalars().all()}

# 🚨 新增：获取未读数量
@router.get("/unread-count")
async def get_unread_count(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    count = (await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
    )).scalar()
    return {"code": 0, "data": {"count": count}}

@router.put("/read/{noti_id}")
async def read_notification(noti_id: int, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    await db.execute(update(Notification).where(Notification.id == noti_id, Notification.user_id == user_id).values(is_read=True))
    await db.commit()
    return {"code": 0, "message": "已读"}

@router.put("/read-all")
async def read_all(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    await db.execute(update(Notification).where(Notification.user_id == user_id).values(is_read=True))
    await db.commit()
    return {"code": 0, "message": "全部已读"}