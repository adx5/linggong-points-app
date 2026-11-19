# backend/routers/services.py (同城服务：类目 / 师傅列表 / 详情 / 评价 / 下单)
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import (
    City, ProviderCertificate, ProviderProfile, ProviderService,
    ServiceCategory, ServiceOrder, ServiceReview, User,
)
from core.security import (
    get_current_user, get_optional_user, require_roles, verify_resource_city,
)

router = APIRouter(prefix="/api/services", tags=["services"])


class OrderCreateReq(BaseModel):
    provider_profile_id: int
    title: str = ""
    description: str = ""
    address: str = ""
    contact_phone: str = ""
    scheduled_at: str = ""


class ReviewCreateReq(BaseModel):
    order_id: int
    rating: int = 5
    content: str = ""


class ServiceCreateReq(BaseModel):
    category_id: Optional[int] = None
    title: str
    price: float = 0
    price_unit: str = "次"
    description: str = ""
    images: list = []
    # 一键直发采集的结构化信息
    meta: dict = {}


async def _resolve_city(db: AsyncSession, x_city_id: Optional[str]) -> str:
    active = (await db.execute(
        select(City.id).where(City.status == "active"))).scalars().all()
    if not active:
        raise HTTPException(status_code=503, detail="城市字典未初始化")
    city = x_city_id or active[0]
    if city not in active:
        raise HTTPException(status_code=400, detail="当前城市暂未开放")
    return city


# --------------------------------------------------------------
# 类目
# --------------------------------------------------------------
@router.get("/categories")
async def list_categories(
        x_city_id: Optional[str] = Header(None),
        db: AsyncSession = Depends(get_db),
):
    city = await _resolve_city(db, x_city_id)
    res = await db.execute(
        select(ServiceCategory)
        .where(ServiceCategory.status == "active")
        .where((ServiceCategory.city_id == city) | (ServiceCategory.city_id.is_(None)))
        .order_by(ServiceCategory.sort_no, ServiceCategory.id)
    )
    items = res.scalars().all()
    return {"code": 0, "data": [{"id": c.id, "name": c.name, "icon": c.icon} for c in items]}


# --------------------------------------------------------------
# 师傅列表（P5 同城服务页）
# --------------------------------------------------------------
@router.get("/providers")
async def list_providers(
        category_id: Optional[int] = None,
        district: Optional[str] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        size: int = 20,
        x_city_id: Optional[str] = Header(None),
        db: AsyncSession = Depends(get_db),
):
    city = await _resolve_city(db, x_city_id)

    query = select(ProviderProfile, ServiceCategory.name).outerjoin(
        ServiceCategory, ProviderProfile.category_id == ServiceCategory.id
    ).where(ProviderProfile.city_id == city)

    if category_id:
        query = query.where(ProviderProfile.category_id == category_id)
    if district:
        query = query.where(ProviderProfile.district.contains(district))
    if keyword:
        query = query.where(ProviderProfile.display_name.contains(keyword) |
                            ProviderProfile.intro.contains(keyword))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(
        query.order_by(ProviderProfile.rating.desc(), ProviderProfile.id.desc())
        .offset((page - 1) * size).limit(size)
    )
    rows = result.all()

    # 聚合每位师傅在架服务的最低价与数量（B 端上架的服务要能反映到 C 端卡片）
    price_map = {}
    uids = [p.user_id for p, _ in rows]
    if uids:
        agg = await db.execute(
            select(
                ProviderService.provider_id,
                func.min(ProviderService.price),
                func.count(ProviderService.id),
            ).where(
                ProviderService.provider_id.in_(uids),
                ProviderService.status == "active",
            ).group_by(ProviderService.provider_id)
        )
        price_map = {uid: (min_price, cnt) for uid, min_price, cnt in agg.all()}

    data = []
    for p, category_name in rows:
        min_price, svc_count = price_map.get(p.user_id, (None, 0))
        data.append({
            "id": p.id,
            "display_name": p.display_name,
            "avatar": p.avatar or "",
            "category_id": p.category_id,
            "category_name": category_name or "同城服务",
            "district": p.district or "",
            "intro": p.intro or "",
            "rating": round(p.rating or 0, 1),
            "orders_done": p.orders_done or 0,
            "verify_status": p.verify_status or "unverified",
            "min_price": round(min_price, 0) if min_price is not None else None,
            "service_count": svc_count or 0,
        })
    return {"code": 0, "data": data, "total": total}


# --------------------------------------------------------------
# 师傅详情（P6b 服务详情页）
# --------------------------------------------------------------
@router.get("/providers/{profile_id}")
async def get_provider(profile_id: int, db: AsyncSession = Depends(get_db)):
    profile = await db.get(ProviderProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="服务商不存在")

    category = await db.get(ServiceCategory, profile.category_id) if profile.category_id else None

    # 评分分布
    dist_res = await db.execute(
        select(ServiceReview.rating, func.count(ServiceReview.id))
        .where(ServiceReview.provider_id == profile.user_id)
        .group_by(ServiceReview.rating)
    )
    dist_map = {int(r): int(c) for r, c in dist_res.all()}
    total_reviews = sum(dist_map.values())
    good = dist_map.get(5, 0) + dist_map.get(4, 0)

    reviews_res = await db.execute(
        select(ServiceReview)
        .where(ServiceReview.provider_id == profile.user_id)
        .order_by(ServiceReview.id.desc()).limit(3)
    )
    reviews = reviews_res.scalars().all()

    svc_res = await db.execute(
        select(ProviderService).where(
            ProviderService.provider_id == profile.user_id,
            ProviderService.status == "active",
        ).order_by(ProviderService.id.desc())
    )
    services = svc_res.scalars().all()

    return {"code": 0, "data": {
        "profile": {
            "id": profile.id,
            "user_id": profile.user_id,
            "display_name": profile.display_name,
            "avatar": profile.avatar or "",
            "intro": profile.intro or "",
            "district": profile.district or "",
            "rating": round(profile.rating or 0, 1),
            "orders_done": profile.orders_done or 0,
            "verify_status": profile.verify_status or "unverified",
            "category_id": profile.category_id,
            "category_name": category.name if category else "同城服务",
        },
        "stats": {
            "total_reviews": total_reviews,
            "good_rate": round(good / total_reviews * 100) if total_reviews else 100,
            "distribution": {
                "5": dist_map.get(5, 0),
                "4": dist_map.get(4, 0),
                "3": dist_map.get(3, 0),
            },
        },
        "recent_reviews": [_review_dict(r) for r in reviews],
        "services": [{
            "id": s.id,
            "title": s.title,
            "price": s.price or 0,
            "price_unit": s.price_unit or "次",
            "description": s.description or "",
        } for s in services],
    }}


def _review_dict(r: ServiceReview):
    return {
        "id": r.id,
        "customer_name": r.customer_name or "匿名用户",
        "rating": r.rating,
        "content": r.content or "",
        "images": r.images or [],
        "created_at": r.created_at.strftime("%Y-%m-%d") if r.created_at else "",
    }


# --------------------------------------------------------------
# 评价列表（P6c）
# --------------------------------------------------------------
@router.get("/providers/{profile_id}/reviews")
async def list_provider_reviews(profile_id: int, page: int = 1, size: int = 20,
                                db: AsyncSession = Depends(get_db)):
    profile = await db.get(ProviderProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="服务商不存在")

    query = select(ServiceReview).where(ServiceReview.provider_id == profile.user_id)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    res = await db.execute(
        query.order_by(ServiceReview.id.desc()).offset((page - 1) * size).limit(size))
    rows = res.scalars().all()

    return {"code": 0, "total": total,
            "data": [_review_dict(r) for r in rows]}


# --------------------------------------------------------------
# 下单（C 端）
# --------------------------------------------------------------
@router.post("/orders")
async def create_order(req: OrderCreateReq, db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(require_roles(
                           ["worker", "user"],
                           deny_message="当前账号不是求职者身份，请切换到 C 端身份后再下单"))):
    profile = await db.get(ProviderProfile, req.provider_profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="服务商不存在")
    if profile.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能给自己下单")

    order = ServiceOrder(
        city_id=profile.city_id or current_user.city_id,
        customer_id=current_user.id,
        provider_id=profile.user_id,
        category_id=profile.category_id,
        title=req.title or f"{profile.display_name} 同城服务",
        description=req.description,
        price=0.0,
        address=req.address,
        contact_phone=req.contact_phone or current_user.phone or "",
        scheduled_at=req.scheduled_at,
        status="pending",
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return {"code": 0, "message": "下单成功，等待服务商确认", "data": {"order_id": order.id}}


@router.get("/orders/my")
async def my_orders(db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    res = await db.execute(
        select(ServiceOrder).where(ServiceOrder.customer_id == current_user.id)
        .order_by(ServiceOrder.id.desc()).limit(50))
    rows = res.scalars().all()
    return {"code": 0, "data": [{
        "id": o.id, "title": o.title, "status": o.status, "price": o.price,
        "address": o.address, "created_at": o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else "",
    } for o in rows]}


# --------------------------------------------------------------
# 评价（订单完成后，C 端）
# --------------------------------------------------------------
@router.post("/reviews")
async def create_review(req: ReviewCreateReq, db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    order = await db.get(ServiceOrder, req.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="越权拦截：只能评价自己的订单")
    if order.status != "finished":
        raise HTTPException(status_code=400, detail="订单完成后才能评价")

    exist = await db.execute(
        select(ServiceReview).where(ServiceReview.order_id == order.id))
    if exist.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该订单已评价")

    review = ServiceReview(
        city_id=order.city_id,
        order_id=order.id,
        provider_id=order.provider_id,
        customer_id=current_user.id,
        customer_name="匿名用户",
        rating=max(1, min(5, req.rating)),
        content=req.content,
        images=[],
    )
    db.add(review)

    # 更新师傅综合评分
    agg = await db.execute(
        select(func.avg(ServiceReview.rating)).where(
            ServiceReview.provider_id == order.provider_id))
    avg_rating = agg.scalar()
    profile_res = await db.execute(
        select(ProviderProfile).where(ProviderProfile.user_id == order.provider_id))
    profile = profile_res.scalar_one_or_none()
    if profile and avg_rating:
        profile.rating = float(avg_rating)

    await db.commit()
    return {"code": 0, "message": "评价成功"}


# ==============================================================
# B 端：服务项目（一键直发产物）
# ==============================================================
def _svc_dict(s: ProviderService):
    return {
        "id": s.id,
        "category_id": s.category_id,
        "title": s.title,
        "price": s.price or 0,
        "price_unit": s.price_unit or "次",
        "description": s.description or "",
        "images": s.images or [],
        "meta": s.meta or {},
        "status": s.status or "active",
        "created_at": s.created_at.strftime("%Y-%m-%d") if s.created_at else "",
    }


def _require_provider(current_user: User):
    if current_user.role not in ("provider", "merchant"):
        raise HTTPException(status_code=403, detail="仅服务商身份可管理服务，请先完成服务商认证")


@router.get("/my-profile")
async def my_profile(db: AsyncSession = Depends(get_db),
                     current_user: User = Depends(get_current_user)):
    """服务商自己的档案（我的主页展示页使用）"""
    profile = (await db.execute(
        select(ProviderProfile).where(ProviderProfile.user_id == current_user.id)
    )).scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="服务商档案不存在，请先完成入驻")

    category = await db.get(ServiceCategory, profile.category_id) if profile.category_id else None

    titles = (await db.execute(
        select(ProviderService.title).where(
            ProviderService.provider_id == current_user.id,
            ProviderService.status == "active")
    )).scalars().all()

    return {"code": 0, "data": {
        "id": profile.id,
        "display_name": profile.display_name,
        "avatar": profile.avatar or "",
        "intro": profile.intro or "",
        "district": profile.district or "",
        "rating": round(profile.rating or 0, 1),
        "orders_done": profile.orders_done or 0,
        "verify_status": profile.verify_status or "unverified",
        "category_name": category.name if category else "同城服务",
        "tags": list(titles)[:6],
    }}


@router.get("/my-services")
async def my_services(db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    _require_provider(current_user)
    res = await db.execute(
        select(ProviderService).where(ProviderService.provider_id == current_user.id)
        .order_by(ProviderService.id.desc()))
    rows = res.scalars().all()
    return {"code": 0, "data": [_svc_dict(s) for s in rows]}


@router.post("/my-services")
async def create_service(req: ServiceCreateReq, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    _require_provider(current_user)
    if not req.title.strip():
        raise HTTPException(status_code=400, detail="服务名称不能为空")

    svc = ProviderService(
        provider_id=current_user.id,
        city_id=current_user.city_id,
        category_id=req.category_id,
        title=req.title.strip(),
        price=req.price or 0,
        price_unit=req.price_unit or "次",
        description=req.description or "",
        images=req.images or [],
        meta=req.meta or {},
        status="active",
    )
    db.add(svc)
    await db.commit()
    await db.refresh(svc)
    return {"code": 0, "message": "服务已上架", "data": {"id": svc.id}}


class ServiceUpdateReq(BaseModel):
    title: Optional[str] = None
    price: Optional[float] = None
    price_unit: Optional[str] = None
    description: Optional[str] = None
    images: Optional[list] = None
    category_id: Optional[int] = None


@router.put("/my-services/{service_id}")
async def update_service(service_id: int, req: ServiceUpdateReq,
                         db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    """编辑服务信息（名称 / 价格 / 计价单位 / 描述 / 图片）"""
    _require_provider(current_user)
    svc = await db.get(ProviderService, service_id)
    if not svc or svc.provider_id != current_user.id:
        raise HTTPException(status_code=404, detail="服务不存在")

    if req.title is not None:
        if not req.title.strip():
            raise HTTPException(status_code=400, detail="服务名称不能为空")
        svc.title = req.title.strip()
    if req.price is not None:
        if req.price < 0:
            raise HTTPException(status_code=400, detail="价格不能为负数")
        svc.price = req.price
    if req.price_unit is not None:
        svc.price_unit = req.price_unit
    if req.description is not None:
        svc.description = req.description
    if req.images is not None:
        svc.images = req.images
    if req.category_id is not None:
        svc.category_id = req.category_id

    await db.commit()
    return {"code": 0, "message": "服务信息已更新", "data": _svc_dict(svc)}


@router.put("/my-services/{service_id}/status")
async def toggle_service(service_id: int, status: str = "off",
                         db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    _require_provider(current_user)
    svc = await db.get(ProviderService, service_id)
    if not svc or svc.provider_id != current_user.id:
        raise HTTPException(status_code=404, detail="服务不存在")

    svc.status = "active" if status == "active" else "off"
    await db.commit()
    return {"code": 0, "message": "已上架" if svc.status == "active" else "已下架"}


# ==============================================================
# B 端：技能证书（图片走已有图床，这里只存 URL）
# ==============================================================
class CertificateReq(BaseModel):
    title: str
    image_url: str


def _cert_dict(c: ProviderCertificate):
    return {
        "id": c.id,
        "title": c.title,
        "image_url": c.image_url,
        "status": c.status or "pending",
        "created_at": c.created_at.strftime("%Y-%m-%d") if c.created_at else "",
    }


@router.get("/my-certificates")
async def my_certificates(db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    _require_provider(current_user)
    res = await db.execute(
        select(ProviderCertificate).where(ProviderCertificate.provider_id == current_user.id)
        .order_by(ProviderCertificate.id.desc()))
    return {"code": 0, "data": [_cert_dict(c) for c in res.scalars().all()]}


@router.post("/my-certificates")
async def add_certificate(req: CertificateReq, db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    _require_provider(current_user)

    title = (req.title or "").strip()
    url = (req.image_url or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="请填写证书名称")
    if not url.startswith("http"):
        raise HTTPException(status_code=400, detail="证书图片地址无效，请重新上传")

    cert = ProviderCertificate(
        provider_id=current_user.id,
        city_id=current_user.city_id,
        title=title[:100],
        image_url=url,
        status="pending",
    )
    db.add(cert)
    await db.commit()
    await db.refresh(cert)
    return {"code": 0, "message": "证书已提交，等待平台审核", "data": _cert_dict(cert)}


# ==============================================================
# B 端：服务订单（咨询中 / 服务中）
# ==============================================================
@router.get("/orders/provider")
async def provider_orders(status: Optional[str] = None,
                          db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    _require_provider(current_user)

    query = select(ServiceOrder).where(ServiceOrder.provider_id == current_user.id)
    if status:
        query = query.where(ServiceOrder.status == status)
    res = await db.execute(query.order_by(ServiceOrder.id.desc()).limit(100))
    rows = res.scalars().all()

    return {"code": 0, "data": [{
        "id": o.id,
        "title": o.title,
        "status": o.status,
        "price": o.price or 0,
        "address": o.address or "",
        "contact_phone": o.contact_phone or "",
        "scheduled_at": o.scheduled_at or "",
        "created_at": o.created_at.strftime("%m-%d %H:%M") if o.created_at else "",
    } for o in rows]}


@router.put("/orders/{order_id}/accept")
async def accept_order(order_id: int, db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    _require_provider(current_user)
    order = await db.get(ServiceOrder, order_id)
    if not order or order.provider_id != current_user.id:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "pending":
        raise HTTPException(status_code=400, detail="该订单当前不可接单")

    order.status = "accepted"
    await db.commit()
    return {"code": 0, "message": "已接单，请按时上门"}


@router.put("/orders/{order_id}/finish")
async def finish_order(order_id: int, db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    _require_provider(current_user)
    order = await db.get(ServiceOrder, order_id)
    if not order or order.provider_id != current_user.id:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status != "accepted":
        raise HTTPException(status_code=400, detail="订单未在服务中，不可完工")

    order.status = "finished"

    profile = (await db.execute(
        select(ProviderProfile).where(ProviderProfile.user_id == current_user.id))).scalar_one_or_none()
    if profile:
        profile.orders_done = (profile.orders_done or 0) + 1

    await db.commit()
    return {"code": 0, "message": "已完工报备，等待客户评价"}
