# backend/routers/admin.py (运营端接口：鉴权 + 城市隔离 + 风控/实名人工复核)
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database import get_db
from models import User, CooperationEntity, Job, Verification, AuditLog, ProviderCertificate
from core.security import admin_required, is_hq_role

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _city_scope(query, current_user: User, model):
    """总台角色看全量，属地角色只看本城"""
    if is_hq_role(current_user):
        return query
    return query.where(model.city_id == current_user.city_id)


def _check_city(resource_city_id, current_user: User):
    if not is_hq_role(current_user) and resource_city_id != current_user.city_id:
        raise HTTPException(status_code=403, detail="越权拦截：无权操作其他城市的数据")


# ==============================================================
# 概览
# ==============================================================
@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(admin_required)):
    total_users = (await db.execute(
        _city_scope(select(func.count(User.id)), current_user, User))).scalar()

    total_jobs = (await db.execute(
        _city_scope(select(func.count(Job.id)), current_user, Job))).scalar()

    pending_query = select(func.count(CooperationEntity.id)).where(
        CooperationEntity.status == 'pending')
    pending_companies = (await db.execute(
        _city_scope(pending_query, current_user, CooperationEntity))).scalar()

    # 风控/实名待办（新增，供管理端「待办」展示用）
    risk_query = select(func.count(Job.id)).where(Job.risk_status == 'review')
    risk_jobs = (await db.execute(_city_scope(risk_query, current_user, Job))).scalar()

    verify_query = select(func.count(Verification.id)).where(Verification.status == 'manual_review')
    pending_verifications = (await db.execute(
        _city_scope(verify_query, current_user, Verification))).scalar()

    return {"code": 0, "data": {
        "total_users": total_users,
        "total_jobs": total_jobs,
        "pending_companies": pending_companies,
        "risk_jobs": risk_jobs,
        "pending_verifications": pending_verifications,
    }}


@router.get("/companies")
async def get_companies(db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(admin_required)):
    query = select(CooperationEntity).order_by(
        CooperationEntity.status.asc(), CooperationEntity.id.desc())
    query = _city_scope(query, current_user, CooperationEntity)
    res = await db.execute(query)
    return {"code": 0, "data": res.scalars().all()}


@router.get("/jobs")
async def get_all_jobs(db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(admin_required)):
    query = select(Job, CooperationEntity.name).join(
        CooperationEntity, Job.merchant_id == CooperationEntity.user_id).order_by(
        Job.id.desc())
    query = _city_scope(query, current_user, Job)

    result = await db.execute(query)
    data = []
    for job, entity_name in result.all():
        job_dict = job.__dict__.copy()
        job_dict.pop("_sa_instance_state", None)
        job_dict["company_name"] = entity_name
        data.append(job_dict)
    return {"code": 0, "data": data}


class CertificateReviewReq(BaseModel):
    pass_verify: bool
    reason: str = ""


@router.get("/certificates")
async def list_certificates(status: str = "pending",
                            db: AsyncSession = Depends(get_db),
                            current_user: User = Depends(admin_required)):
    """服务商技能证书待审列表"""
    query = select(ProviderCertificate, User.phone, User.real_name).join(
        User, ProviderCertificate.provider_id == User.id
    ).where(ProviderCertificate.status == status).order_by(ProviderCertificate.id.desc()).limit(200)
    query = _city_scope(query, current_user, ProviderCertificate)

    rows = (await db.execute(query)).all()
    return {"code": 0, "data": [{
        "id": c.id,
        "provider_id": c.provider_id,
        "phone": phone,
        "provider_name": real_name or "服务商",
        "title": c.title,
        "image_url": c.image_url,
        "status": c.status,
        "created_at": c.created_at.strftime("%Y-%m-%d") if c.created_at else "",
    } for c, phone, real_name in rows]}


@router.post("/certificates/{cert_id}/review")
async def review_certificate(cert_id: int, req: CertificateReviewReq,
                             db: AsyncSession = Depends(get_db),
                             current_user: User = Depends(admin_required)):
    cert = await db.get(ProviderCertificate, cert_id)
    if not cert:
        raise HTTPException(status_code=404, detail="证书不存在")
    _check_city(cert.city_id, current_user)

    cert.status = "verified" if req.pass_verify else "rejected"

    db.add(AuditLog(
        operator_id=current_user.id,
        city_id=cert.city_id,
        action="服务商证书审核通过" if req.pass_verify else "服务商证书审核驳回",
        target_type="provider_certificate",
        target_id=cert.id,
        detail=f"{cert.title}；{req.reason}",
    ))
    await db.commit()
    return {"code": 0, "message": "已通过" if req.pass_verify else "已驳回"}


# ==============================================================
# 风控人工复核（第一层规则命中 review / blocked 的岗位）
# ==============================================================
class RiskReviewReq(BaseModel):
    pass_risk: bool
    reason: str = ""


@router.get("/risk/jobs")
async def list_risk_jobs(status: str = "review",
                         db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(admin_required)):
    """status: review(待复核) / blocked(已拦截) / pass(已放行)"""
    query = select(Job, CooperationEntity.name).join(
        CooperationEntity, Job.merchant_id == CooperationEntity.user_id
    ).where(Job.risk_status == status).order_by(Job.id.desc()).limit(200)
    query = _city_scope(query, current_user, Job)

    result = await db.execute(query)
    data = []
    for job, company_name in result.all():
        data.append({
            "id": job.id,
            "title": job.title,
            "company_name": company_name,
            "city_id": job.city_id,
            "salary": job.salary,
            "publish_status": job.publish_status,
            "risk_status": job.risk_status,
            "risk_score": job.risk_score,
            "risk_points": job.risk_points,
            "created_at": job.created_at.strftime("%Y-%m-%d %H:%M") if job.created_at else "",
        })
    return {"code": 0, "data": data}


@router.post("/risk/jobs/{job_id}/review")
async def review_risk_job(job_id: int, req: RiskReviewReq,
                          db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(admin_required)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="岗位不存在")

    _check_city(job.city_id, current_user)

    job.risk_status = "pass" if req.pass_risk else "blocked"
    job.risk_checked_at = datetime.utcnow()

    db.add(AuditLog(
        operator_id=current_user.id,
        city_id=job.city_id,
        action="岗位风控放行" if req.pass_risk else "岗位风控拦截",
        target_type="job",
        target_id=job.id,
        detail=req.reason or "",
    ))

    await db.commit()
    return {"code": 0, "message": "已放行，企业可自行上架" if req.pass_risk else "已维持拦截"}


class RechargeReq(BaseModel):
    points: float
    reason: str = ""


@router.post("/companies/{entity_id}/recharge")
async def recharge_promotion(entity_id: int, req: RechargeReq,
                             db: AsyncSession = Depends(get_db),
                             current_user: User = Depends(admin_required)):
    """企业推广余额充值（线下对公转账后由运营记账，平台不做资金代收付）"""
    entity = await db.get(CooperationEntity, entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="企业不存在")
    _check_city(entity.city_id, current_user)

    if req.points <= 0:
        raise HTTPException(status_code=400, detail="充值积分必须大于 0")

    entity.promotion_balance = (entity.promotion_balance or 0) + req.points

    db.add(AuditLog(
        operator_id=current_user.id,
        city_id=entity.city_id,
        action="企业推广余额充值",
        target_type="cooperation_entity",
        target_id=entity.id,
        detail=f"+{req.points} 分，余额 {entity.promotion_balance} 分；{req.reason}",
    ))
    await db.commit()
    return {"code": 0, "message": "充值成功", "data": {"promotion_balance": entity.promotion_balance}}


# ==============================================================
# 实名认证人工复核（人脸比对失败 / 证件模糊 / 疑似冒用）
# ==============================================================
class VerifyReviewReq(BaseModel):
    pass_verify: bool
    reason: str = ""


@router.get("/verifications")
async def list_verifications(status: str = "manual_review",
                             db: AsyncSession = Depends(get_db),
                             current_user: User = Depends(admin_required)):
    query = select(Verification, User.phone, User.real_name, User.nickname).join(
        User, Verification.user_id == User.id
    ).where(Verification.status == status).order_by(Verification.id.desc()).limit(200)
    query = _city_scope(query, current_user, Verification)

    result = await db.execute(query)
    data = []
    for rec, phone, real_name, nickname in result.all():
        data.append({
            "id": rec.id,
            "user_id": rec.user_id,
            "phone": phone,
            "real_name": real_name or nickname,
            "city_id": rec.city_id,
            "scene": rec.scene,
            "provider": rec.provider,
            "status": rec.status,
            "liveness_score": rec.liveness_score,
            "similarity_score": rec.similarity_score,
            "reject_reason": rec.reject_reason,
            "created_at": rec.created_at.strftime("%Y-%m-%d %H:%M") if rec.created_at else "",
        })
    return {"code": 0, "data": data}


@router.post("/verifications/{verification_id}/review")
async def review_verification(verification_id: int, req: VerifyReviewReq,
                              db: AsyncSession = Depends(get_db),
                              current_user: User = Depends(admin_required)):
    rec = await db.get(Verification, verification_id)
    if not rec:
        raise HTTPException(status_code=404, detail="核验记录不存在")

    _check_city(rec.city_id, current_user)

    # 不能审核自己的实名记录
    if rec.user_id == current_user.id:
        raise HTTPException(status_code=403, detail="越权拦截：不能审核自己的实名记录")

    new_status = "verified" if req.pass_verify else "rejected"
    rec.status = new_status
    rec.reviewer_id = current_user.id
    rec.reviewed_at = datetime.utcnow()
    rec.reject_reason = "" if req.pass_verify else (req.reason or "人工复核未通过")

    user = await db.get(User, rec.user_id)
    if user:
        user.verify_status = new_status

    db.add(AuditLog(
        operator_id=current_user.id,
        city_id=rec.city_id,
        action="实名人工复核通过" if req.pass_verify else "实名人工复核驳回",
        target_type="verification",
        target_id=rec.id,
        detail=req.reason or "",
    ))

    await db.commit()
    return {"code": 0, "message": "已通过" if req.pass_verify else "已驳回"}
