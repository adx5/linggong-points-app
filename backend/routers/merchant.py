# (企业业务接口：信息维护与备案提交)
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from database import get_db
from models import CooperationEntity
from core.security import get_current_user_id
from sqlalchemy.orm.attributes import flag_modified

router = APIRouter(prefix="/api/merchant", tags=["merchant"])


class MerchantInfoReq(BaseModel):
    company_name: str
    industry: str
    cover_image: Optional[str] = ""
    intro: str
    intro_images: Optional[str] = ""
    province: str
    city: str
    district: str
    address_detail: str
    landmark: Optional[str] = ""
    contact_phone: str
    phone_time: str


@router.get("/info")
async def get_merchant_info(db: AsyncSession = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    res = await db.execute(select(CooperationEntity).where(CooperationEntity.user_id == user_id))
    entity = res.scalar_one_or_none()
    if not entity: raise HTTPException(status_code=404, detail="档案不存在")
    return {"code": 0, "data": entity}


@router.put("/info")
async def update_merchant_info(req: MerchantInfoReq, db: AsyncSession = Depends(get_db),
                               user_id: int = Depends(get_current_user_id)):
    res = await db.execute(select(CooperationEntity).where(CooperationEntity.user_id == user_id))
    entity = res.scalar_one_or_none()
    if not entity: raise HTTPException(status_code=404, detail="档案不存在")

    entity.name = req.company_name
    images_list = req.intro_images.split(",") if req.intro_images else []

    entity.ext_info = {
        "industry": req.industry, "cover_image": req.cover_image, "intro": req.intro,
        "intro_images": images_list, "province": req.province, "city": req.city,
        "district": req.district, "address_detail": req.address_detail,
        "landmark": req.landmark, "contact_phone": req.contact_phone, "phone_time": req.phone_time
    }
    flag_modified(entity, "ext_info")
    await db.commit()
    return {"code": 0, "message": "公开信息保存成功"}


class VerifyReq(BaseModel):
    license_img: str
    credit_code: str
    contact_name: str
    id_front: str
    id_back: str
    contact_phone: str


@router.post("/verify")
async def submit_verify(req: VerifyReq, db: AsyncSession = Depends(get_db),
                        user_id: int = Depends(get_current_user_id)):
    res = await db.execute(select(CooperationEntity).where(CooperationEntity.user_id == user_id))
    entity = res.scalar_one_or_none()
    if not entity: raise HTTPException(status_code=404, detail="档案不存在")

    if not entity.ext_info: entity.ext_info = {}
    entity.ext_info.update({
        "license_img": req.license_img, "credit_code": req.credit_code,
        "contact_name": req.contact_name, "id_front": req.id_front,
        "id_back": req.id_back, "contact_phone": req.contact_phone
    })
    flag_modified(entity, "ext_info")

    entity.status = "pending"
    entity.reject_reason = ""  # 重提清空驳回原因
    await db.commit()

    return {"code": 0, "message": "资料已提交，等待平台审核"}