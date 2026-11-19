# backend/routers/audit.py (合规审核接口：需管理端鉴权，属地角色只能审本城，且操作留痕)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import (
    Blacklist, CooperationEntity, Job, JobApplication, Notification,
    ProviderCertificate, User, AuditLog, Verification,
)
from pydantic import BaseModel
from core.security import admin_required, is_hq_role

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/gov-dashboard")
async def get_gov_dashboard(db: AsyncSession = Depends(get_db),
                            current_user: User = Depends(admin_required)):
    """监管看板：全部来自真实业务数据（属地角色只看本城）"""

    def scoped(query, model):
        if is_hq_role(current_user):
            return query
        return query.where(model.city_id == current_user.city_id)

    disputes = (await db.execute(scoped(
        select(func.count()).select_from(JobApplication).where(JobApplication.status == 9),
        JobApplication))).scalar() or 0

    pending_companies = (await db.execute(scoped(
        select(func.count()).select_from(CooperationEntity).where(CooperationEntity.status == "pending"),
        CooperationEntity))).scalar() or 0

    pending_verifications = (await db.execute(scoped(
        select(func.count()).select_from(Verification).where(Verification.status == "manual_review"),
        Verification))).scalar() or 0

    pending_certificates = (await db.execute(scoped(
        select(func.count()).select_from(ProviderCertificate).where(ProviderCertificate.status == "pending"),
        ProviderCertificate))).scalar() or 0

    blacklist = (await db.execute(scoped(
        select(func.count()).select_from(Blacklist), Blacklist))).scalar() or 0

    risk_jobs = (await db.execute(scoped(
        select(func.count()).select_from(Job).where(Job.risk_status.in_(["blocked", "review"])),
        Job))).scalar() or 0

    return {"code": 0, "data": {
        "disputes": disputes,
        "pending_companies": pending_companies,
        "pending_verifications": pending_verifications,
        "pending_certificates": pending_certificates,
        "blacklist": blacklist,
        "risk_jobs": risk_jobs,
        # 兼容旧字段名
        "shell_companies": pending_companies,
    }}


class VerifyReq(BaseModel):
    entity_id: int
    pass_verify: bool
    reject_reason: str = ""


@router.post("/verify")
async def verify_entity(req: VerifyReq, db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(admin_required)):
    res = await db.execute(select(CooperationEntity).where(CooperationEntity.id == req.entity_id))
    entity = res.scalar_one_or_none()
    if not entity: raise HTTPException(status_code=404, detail="档案不存在")

    # 属地角色只能审核本城企业
    if not is_hq_role(current_user) and entity.city_id != current_user.city_id:
        raise HTTPException(status_code=403, detail="越权拦截：无权审核其他城市的企业")

    # 不能审核自己名下的企业（防自批）
    if entity.user_id == current_user.id:
        raise HTTPException(status_code=403, detail="越权拦截：不能审核自己名下的企业档案")

    if req.pass_verify:
        entity.status = "active"
        entity.reject_reason = ""

        # 🚨 审核通过 = 为企业主的账号开通商家身份，
        # 否则他即使备案通过也切不到 merchant，发不了岗（意图驱动登录的前提）
        owner = await db.get(User, entity.user_id)
        if owner:
            roles = [r.strip().lower() for r in (owner.available_roles or "worker").split(",") if r.strip()]
            if "merchant" not in roles:
                roles.append("merchant")
                owner.available_roles = ",".join(roles)

        # 🚨 绝不自动改草稿状态！发消息通知 HR 自己去上架
        noti = Notification(
            user_id=entity.user_id,
            title="企业资质已通过认证",
            content="您的企业备案已审核通过！草稿箱中的岗位现已解锁，请尽快前往【岗位管理】手动发布上架。"
        )
        db.add(noti)
        msg = "审核通过，已发送通知给企业"
    else:
        entity.status = "rejected"
        entity.reject_reason = req.reject_reason

        noti = Notification(
            user_id=entity.user_id,
            title="企业资质审核被驳回",
            content=f"您的备案申请未通过。原因：{req.reject_reason}。请修改资料后重新提交。"
        )
        db.add(noti)
        msg = "已驳回并通知企业"

    # 审核留痕（原实现只改状态，无任何审计记录）
    db.add(AuditLog(
        operator_id=current_user.id,
        city_id=entity.city_id,
        action="企业资质审核通过" if req.pass_verify else "企业资质审核驳回",
        target_type="cooperation_entity",
        target_id=entity.id,
        detail=("通过" if req.pass_verify else f"驳回原因：{req.reject_reason}")
    ))

    await db.commit()
    return {"code": 0, "message": msg}
