# (用户业务接口：查询积分余额、扣减积分兑换商品)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from database import get_db
from models import User
from core.security import get_current_user_id

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/points")
async def get_points(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    user = await db.get(User, user_id)
    return {"code": 0, "data": {"points": user.total_points if user else 0}}


@router.post("/exchange")
async def exchange_item(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # 🚨 已修复：利用 SQL 的原子性进行扣减，防止高并发下积分超发变成负数
    # 只有当用户积分 >= 50 时，才会执行扣减
    stmt = (
        update(User)
        .where(User.id == user_id, User.total_points >= 50)
        .values(total_points=User.total_points - 50)
    )
    result = await db.execute(stmt)
    await db.commit()

    # result.rowcount 为 0，说明没有命中 where 条件（即积分不足）
    if result.rowcount == 0:
        raise HTTPException(status_code=400, detail="积分不足")

    return {"code": 0, "message": "兑换成功，已生成提货码"}