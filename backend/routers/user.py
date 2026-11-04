# backend/routers/user.py (用户业务：兑换扣积分时写入流水)
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, desc
from sqlalchemy.orm.attributes import flag_modified
from database import get_db
from models import User, PointTransaction
from core.security import get_current_user_id

router = APIRouter(prefix="/api/user", tags=["user"])


class ResumeReq(BaseModel):
    basic: Dict[str, Any]
    jobs: List[Dict[str, Any]]


class VerifyReq(BaseModel):
    real_name: str
    id_card: str
    id_front_img: str
    id_back_img: str


@router.get("/points")
async def get_points(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    user = await db.get(User, user_id)
    return {"code": 0, "data": {"points": user.total_points if user else 0}}


@router.get("/points/history")
async def get_points_history(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    query = select(PointTransaction).where(PointTransaction.user_id == user_id).order_by(
        desc(PointTransaction.created_at))
    result = await db.execute(query)
    tx_list = result.scalars().all()

    data = []
    for tx in tx_list:
        data.append({
            "id": tx.id,
            "amount": tx.amount,
            "balance_after": tx.balance_after,
            "biz_type": tx.biz_type,
            "remark": tx.remark or "系统变更",
            "created_at": tx.created_at.strftime("%Y-%m-%d %H:%M") if tx.created_at else ""
        })
    return {"code": 0, "data": data}


@router.post("/exchange")
async def exchange_item(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    stmt = (
        update(User)
        .where(User.id == user_id, User.total_points >= 50)
        .values(total_points=User.total_points - 50)
    )
    result = await db.execute(stmt)

    if result.rowcount == 0:
        await db.rollback()
        raise HTTPException(status_code=400, detail="积分不足")

    # 🚨 修复：写入扣减流水
    user = await db.get(User, user_id)
    import uuid
    db.add(PointTransaction(
        user_id=user_id, amount=-50, balance_after=user.total_points,
        biz_type="exchange", ref_no=f"ex_{uuid.uuid4().hex[:8]}", remark="积分商城兑换"
    ))

    await db.commit()
    return {"code": 0, "message": "兑换成功，已生成提货码"}


@router.get("/resume")
async def get_resume(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    user = await db.get(User, user_id)
    if not user: raise HTTPException(status_code=404, detail="用户不存在")
    resume_data = user.resume_data or {}
    if "basic" not in resume_data: resume_data["basic"] = {"name": "", "phone": "", "email": "", "skills": "",
                                                           "education": ""}
    if "jobs" not in resume_data: resume_data["jobs"] = []
    return {"code": 0, "data": resume_data}


@router.put("/resume")
async def save_resume(req: ResumeReq, db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    user = await db.get(User, user_id)
    if not user: raise HTTPException(status_code=404, detail="用户不存在")
    user.resume_data = req.dict()
    flag_modified(user, "resume_data")
    await db.commit()
    return {"code": 0, "message": "简历保存成功"}


@router.get("/profile")
async def get_profile(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    user = await db.get(User, user_id)
    if not user: raise HTTPException(status_code=404, detail="用户不存在")

    gender = "未知"
    if user.id_card and len(user.id_card) >= 17:
        try:
            gender_num = int(user.id_card[16])
            gender = "男" if gender_num % 2 != 0 else "女"
        except ValueError:
            pass

    return {
        "code": 0,
        "data": {
            "real_name": user.real_name,
            "verify_status": user.verify_status,
            "gender": gender
        }
    }


@router.get("/verify-status")
async def get_verify_status(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    user = await db.get(User, user_id)
    return {"code": 0, "data": {"status": user.verify_status, "real_name": user.real_name}}


@router.post("/verify")
async def submit_verify(req: VerifyReq, db: AsyncSession = Depends(get_db),
                        user_id: int = Depends(get_current_user_id)):
    user = await db.get(User, user_id)
    if not user: raise HTTPException(status_code=404, detail="用户不存在")

    user.real_name = req.real_name
    if len(req.id_card) >= 18:
        user.id_card = req.id_card[:4] + "**********" + req.id_card[-4:]
    else:
        user.id_card = req.id_card

    user.verify_status = "verified"

    if not user.resume_data: user.resume_data = {}
    user.resume_data["id_front_img"] = req.id_front_img
    user.resume_data["id_back_img"] = req.id_back_img
    flag_modified(user, "resume_data")

    await db.commit()
    return {"code": 0, "message": "实名认证成功"}