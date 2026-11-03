# (合规审核接口)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import CooperationEntity, Job, Notification
from pydantic import BaseModel
from core.security import get_current_user_id

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/gov-dashboard")
async def get_gov_dashboard():
    return {"code": 0, "data": {"disputes": 12, "blacklist": 3, "shell_companies": 1}}


class VerifyReq(BaseModel):
    entity_id: int
    pass_verify: bool
    reject_reason: str = ""


@router.post("/verify")
async def verify_entity(req: VerifyReq, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(CooperationEntity).where(CooperationEntity.id == req.entity_id))
    entity = res.scalar_one_or_none()
    if not entity: raise HTTPException(status_code=404, detail="档案不存在")

    if req.pass_verify:
        entity.status = "active"
        entity.reject_reason = ""

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

    await db.commit()
    return {"code": 0, "message": msg}