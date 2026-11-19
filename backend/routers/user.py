# backend/routers/user.py (用户业务：积分、简历、实名认证（含人脸核验）、人才库)
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select, desc
from sqlalchemy.orm.attributes import flag_modified
from database import get_db
from models import User, PointTransaction, Verification, AuditLog
from core.security import get_current_user_id, require_roles
from services.liveness import get_liveness_provider

router = APIRouter(prefix="/api/user", tags=["user"])


class ResumeReq(BaseModel):
    basic: Dict[str, Any]
    jobs: List[Dict[str, Any]]


class VerifyReq(BaseModel):
    real_name: str
    id_card: str
    id_front_img: str
    id_back_img: str


class LivenessReq(BaseModel):
    face_image: str = ""
    scene: str = "register"


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
            "id": tx.id, "amount": tx.amount, "balance_after": tx.balance_after,
            "biz_type": tx.biz_type, "remark": tx.remark or "系统变更",
            "created_at": tx.created_at.strftime("%Y-%m-%d %H:%M") if tx.created_at else ""
        })
    return {"code": 0, "data": data}


@router.post("/exchange")
async def exchange_item(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    stmt = update(User).where(User.id == user_id, User.total_points >= 50).values(total_points=User.total_points - 50)
    result = await db.execute(stmt)
    if result.rowcount == 0:
        await db.rollback()
        raise HTTPException(status_code=400, detail="积分不足")
    user = await db.get(User, user_id)
    import uuid
    db.add(PointTransaction(
        user_id=user_id, city_id=user.city_id, amount=-50, balance_after=user.total_points,
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
    resume_data = user.resume_data or {}
    gender = resume_data.get("gender") or "未知"
    if gender == "未知" and user.id_card and len(user.id_card) >= 17:
        try:
            gender_num = int(user.id_card[16])
            gender = "男" if gender_num % 2 != 0 else "女"
        except (ValueError, TypeError):
            pass
    return {"code": 0, "data": {
        "real_name": user.real_name,
        "verify_status": user.verify_status,
        "gender": gender,
        # 已打码，仅用于「资质与实名认证」页展示
        "id_card_masked": user.id_card or "",
    }}


@router.get("/verify-status")
async def get_verify_status(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    user = await db.get(User, user_id)
    if not user: raise HTTPException(status_code=404, detail="用户不存在")

    # 最近一次人脸核验记录（前端据此展示"转人工/被拒/通过"）
    res = await db.execute(
        select(Verification)
        .where(Verification.user_id == user_id, Verification.provider != "info")
        .order_by(Verification.id.desc())
        .limit(1)
    )
    last = res.scalar_one_or_none()

    return {"code": 0, "data": {
        "status": user.verify_status,
        "real_name": user.real_name,
        "need_liveness": user.verify_status != "verified",
        "last_check": {
            "status": last.status,
            "provider": last.provider,
            "reason": last.reject_reason,
            "liveness_score": last.liveness_score,
            "created_at": last.created_at.strftime("%Y-%m-%d %H:%M") if last and last.created_at else "",
        } if last else None,
    }}


# --------------------------------------------------------------
# 实名认证第 1 步：提交身份信息（不再直接置 verified）
# --------------------------------------------------------------
@router.post("/verify")
async def submit_verify(req: VerifyReq, db: AsyncSession = Depends(get_db),
                        user_id: int = Depends(get_current_user_id)):
    user = await db.get(User, user_id)
    if not user: raise HTTPException(status_code=404, detail="用户不存在")

    if user.verify_status == "verified":
        return {"code": 0, "message": "您已完成实名认证"}

    raw_id = (req.id_card or "").strip()
    if len(raw_id) < 15:
        raise HTTPException(status_code=400, detail="身份证号格式不正确")

    user.real_name = req.real_name

    # 性别先算后存：原实现从打码后的身份证取位，导致恒为「未知」
    gender_text = "未知"
    if len(raw_id) >= 17 and raw_id[16].isdigit():
        gender_text = "男" if int(raw_id[16]) % 2 != 0 else "女"

    if len(raw_id) >= 8:
        user.id_card = raw_id[:4] + "*" * (len(raw_id) - 8) + raw_id[-4:]
    else:
        user.id_card = "*" * len(raw_id)

    # ⚠️ 关键变更：提交身份信息只到 pending，必须再过人脸核验才算 verified
    user.verify_status = "pending"

    if not user.resume_data: user.resume_data = {}
    user.resume_data["gender"] = gender_text
    user.resume_data["id_front_img"] = req.id_front_img
    user.resume_data["id_back_img"] = req.id_back_img
    flag_modified(user, "resume_data")

    import uuid
    db.add(Verification(
        user_id=user.id, city_id=user.city_id, scene="register", provider="info",
        biz_no=f"info-{uuid.uuid4().hex[:16]}", status="pending",
        raw_result={"gender": gender_text, "has_front": bool(req.id_front_img),
                    "has_back": bool(req.id_back_img)},
    ))
    await db.commit()

    return {"code": 0, "message": "身份信息已提交，请完成人脸核验",
            "data": {"status": user.verify_status, "need_liveness": True}}


# --------------------------------------------------------------
# 实名认证第 2 步：人脸活体核验（第三方 Provider，当前为 mock 实现）
# --------------------------------------------------------------
@router.post("/verify/liveness")
async def submit_liveness(req: LivenessReq, db: AsyncSession = Depends(get_db),
                          user_id: int = Depends(get_current_user_id)):
    user = await db.get(User, user_id)
    if not user: raise HTTPException(status_code=404, detail="用户不存在")

    if user.verify_status == "verified":
        return {"code": 0, "message": "您已完成实名认证", "data": {"status": "verified"}}

    if not user.real_name or not user.id_card:
        raise HTTPException(status_code=400, detail="请先提交实名信息（姓名 / 身份证 / 证件照）")

    provider = get_liveness_provider()
    result = await provider.verify(
        user_id=user.id,
        real_name=user.real_name,
        id_card=user.id_card,
        face_image=req.face_image,
        scene=req.scene,
    )

    db.add(Verification(
        user_id=user.id, city_id=user.city_id, scene=req.scene, provider=result.provider,
        biz_no=result.biz_no, status=result.status,
        liveness_score=result.liveness_score, similarity_score=result.similarity_score,
        raw_result=result.raw, reject_reason=result.reason,
    ))

    # 三条分支都落库，状态以 provider 结果为准
    user.verify_status = result.status
    await db.commit()

    messages = {
        "verified": "人脸核验通过，实名认证完成",
        "rejected": f"人脸核验未通过：{result.reason}",
        "manual_review": "已转人工复核，请耐心等待审核结果",
    }
    return {"code": 0, "message": messages.get(result.status, "处理完成"),
            "data": {"status": result.status, "reason": result.reason,
                     "liveness_score": result.liveness_score}}


def _mask_phone(phone: Optional[str]) -> str:
    """手机号脱敏：138****1234"""
    if not phone or len(phone) < 8:
        return phone or ""
    return f"{phone[:3]}****{phone[-4:]}"


# 🚨 新增：B端拉取公共人才库（列表只返回脱敏手机号）
@router.get("/talents")
async def get_talents(
        keyword: Optional[str] = None,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_roles(["merchant", "provider"]))
):
    # 只查已实名的求职者
    query = select(User).where(User.verify_status == 'verified')

    # 🚨 修复：原实现返回全平台求职者的手机号+真实姓名+简历，无任何城市隔离（PIPL 风险）
    if not current_user.role.startswith("hq_"):
        query = query.where(User.city_id == current_user.city_id)

    # 简单的关键词过滤
    if keyword:
        # 因为 resume_data 是 JSONB，直接做简单匹配
        query = query.where(User.resume_data['basic']['name'].astext.contains(keyword) |
                            User.resume_data['basic']['skills'].astext.contains(keyword))

    result = await db.execute(query.order_by(User.id.desc()))
    users = result.scalars().all()

    data = []
    for u in users:
        rd = u.resume_data or {}
        data.append({
            "id": u.id,
            # 🚨 列表默认脱敏，完整号码需单独调用 /talents/{id}/contact 并留痕
            "phone": _mask_phone(u.phone),
            "phone_masked": True,
            "nickname": u.nickname,
            "real_name": u.real_name,
            "resume_data": rd
        })
    return {"code": 0, "data": data}


class ContactReq(BaseModel):
    reason: str = ""


@router.post("/talents/{talent_id}/contact")
async def get_talent_contact(
        talent_id: int,
        req: ContactReq = None,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(require_roles(["merchant", "provider"]))
):
    """获取求职者完整联系方式：按城市鉴权 + 写审计日志（谁、何时、看了谁）"""
    target = await db.get(User, talent_id)
    if not target or target.verify_status != "verified":
        raise HTTPException(status_code=404, detail="求职者不存在或未完成实名认证")

    if not current_user.role.startswith("hq_") and target.city_id != current_user.city_id:
        raise HTTPException(status_code=403, detail="越权拦截：该求职者不在您所属城市")

    db.add(AuditLog(
        operator_id=current_user.id,
        city_id=target.city_id,
        action="查看求职者联系方式",
        target_type="user",
        target_id=target.id,
        detail=(req.reason if req else "") or "",
    ))
    await db.commit()

    return {"code": 0, "data": {"phone": target.phone, "real_name": target.real_name}}
