"""
routers/exchange.py - C 端积分兑换
- GET  /api/exchange/list       可兑换商品
- POST /api/exchange/order      下单（FIFO 扣积分 + 生成核销码 + 扣库存）
- GET  /api/exchange/my-orders  我的兑换记录
"""
import random

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import ExchangeItem, ExchangeLog
from routers.auth import require_user
from services import InsufficientPoints, available_points, spend_points_fifo

router = APIRouter(prefix="/api/exchange", tags=["exchange"])

TYPE_NAME = {1: "实物·门店提货", 2: "团购券", 3: "VIP卡密"}


class OrderIn(BaseModel):
    productId: int


@router.get("/list")
async def list_items(db: AsyncSession = Depends(get_db)):
    r = await db.execute(
        select(ExchangeItem)
        .where(ExchangeItem.is_active == True)  # noqa: E712
        .order_by(ExchangeItem.id.asc())
    )
    items = r.scalars().all()
    return {
        "code": 0,
        "data": [
            {
                "id": i.id,
                "name": i.name,
                "description": i.description,
                "type": i.item_type,
                "type_name": TYPE_NAME.get(i.item_type, "实物"),
                "points": i.points_cost,
                "stock": i.stock,
            }
            for i in items
        ],
    }


@router.post("/order")
async def create_order(
    body: OrderIn,
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    uid = require_user(authorization)
    item = await db.get(ExchangeItem, body.productId)
    if not item or not item.is_active:
        raise HTTPException(status_code=404, detail="商品不存在")
    if item.stock <= 0:
        raise HTTPException(status_code=400, detail="库存不足")

    try:
        balance_after = await spend_points_fifo(
            db,
            uid,
            item.points_cost,
            ref_type="exchange",
            ref_id=item.id,
            note=f"兑换 {item.name}",
        )
    except InsufficientPoints as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    verify_code = f"{random.randint(100000, 999999)}"
    item.stock -= 1
    log = ExchangeLog(
        user_id=uid,
        item_id=item.id,
        points_spent=item.points_cost,
        verify_code=verify_code,
        status=1,
    )
    db.add(log)
    await db.commit()
    return {
        "code": 0,
        "message": f"兑换成功，扣除 {item.points_cost} 积分",
        "data": {
            "exchange_id": log.id,
            "verify_code": verify_code,
            "remaining_points": balance_after,
        },
    }


@router.get("/my-orders")
async def my_orders(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    uid = require_user(authorization)
    r = await db.execute(
        select(ExchangeLog)
        .where(ExchangeLog.user_id == uid)
        .order_by(ExchangeLog.id.desc())
        .limit(50)
    )
    logs = r.scalars().all()
    names = {}
    for x in logs:
        if x.item_id not in names:
            it = await db.get(ExchangeItem, x.item_id)
            names[x.item_id] = it.name if it else ""
    return {
        "code": 0,
        "data": [
            {
                "id": x.id,
                "product_name": names.get(x.item_id, ""),
                "points_cost": x.points_spent,
                "verify_code": x.verify_code or "",
                "status": x.status,
                "created_at": x.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for x in logs
        ],
    }


@router.get("/items")
async def items_alias(db: AsyncSession = Depends(get_db)):
    """兼容别名：等价于 /list"""
    return await list_items(db)