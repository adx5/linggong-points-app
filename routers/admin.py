"""
routers/admin.py - A 端总部测试后台
- POST /api/admin/login           admin / 123456
- GET  /api/admin/dashboard       数据看板
- GET  /api/admin/users           用户列表
- GET  /api/admin/all-verify      全部核销记录
- POST /api/admin/add-points      手动加积分（测试用）
- POST /api/admin/trigger-settle  手动触发广告组结算（测试用）
- POST /api/admin/reset           清空业务流水（测试用，保留 3 个测试用户）
"""
import random
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import (
    AdCallbackLog,
    AdGroup,
    AdminUser,
    ExchangeLog,
    PointsBucket,
    PointsLedger,
    SmsCode,
    Store,
    TaskLog,
    User,
    VerifyLog,
)
from routers.auth import make_token, require_admin
from routers.auth import _admin_tokens
from services import available_points, grant_points, member_level

router = APIRouter(prefix="/api/admin", tags=["admin"])


class AdminLoginIn(BaseModel):
    username: str
    password: str


class AddPointsIn(BaseModel):
    userId: int
    points: int = 100
    remark: str = "后台手动发放"


class TriggerSettleIn(BaseModel):
    userId: int
    adGroupId: int


@router.post("/login")
async def admin_login(body: AdminLoginIn, db: AsyncSession = Depends(get_db)):
    """A 端登录：账号密码查库校验（生产请改 bcrypt + JWT）"""
    r = await db.execute(
        select(AdminUser).where(AdminUser.username == body.username)
    )
    admin = r.scalar_one_or_none()
    if not admin or admin.password_hash != body.password:
        raise HTTPException(status_code=401, detail="账号或密码错误")
    token = make_token("adm_", _admin_tokens, admin.id)
    return {"code": 0, "message": "ok", "data": {"token": token, "role": admin.role}}


@router.get("/dashboard")
async def dashboard(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    require_admin(authorization)
    today_start = datetime.combine(date.today(), datetime.min.time())

    total_users = (
        await db.execute(select(func.count()).select_from(User))
    ).scalar() or 0
    total_points = (
        await db.execute(
            select(func.coalesce(func.sum(PointsBucket.balance), 0)).where(
                PointsBucket.balance > 0,
                PointsBucket.expire_date > datetime.utcnow(),
            )
        )
    ).scalar() or 0
    active_buckets = (
        await db.execute(
            select(func.count())
            .select_from(PointsBucket)
            .where(
                PointsBucket.balance > 0,
                PointsBucket.expire_date > datetime.utcnow(),
            )
        )
    ).scalar() or 0
    task_today = (
        await db.execute(
            select(func.count())
            .select_from(TaskLog)
            .where(TaskLog.log_date == date.today())
        )
    ).scalar() or 0
    ad_today = (
        await db.execute(
            select(func.count())
            .select_from(AdCallbackLog)
            .where(AdCallbackLog.created_at >= today_start)
        )
    ).scalar() or 0
    verify_cnt = (
        await db.execute(
            select(func.count())
            .select_from(VerifyLog)
            .where(VerifyLog.created_at >= today_start)
        )
    ).scalar() or 0
    verify_pts = (
        await db.execute(
            select(func.coalesce(func.sum(VerifyLog.points_spent), 0)).where(
                VerifyLog.created_at >= today_start
            )
        )
    ).scalar() or 0

    return {
        "code": 0,
        "data": {
            "total_users": int(total_users),
            "total_points": int(total_points),
            "total_active_buckets": int(active_buckets),
            "total_task_today": int(task_today),
            "total_ad_today": int(ad_today),
            "total_verify_today_count": int(verify_cnt),
            "total_verify_today_points": int(verify_pts),
        },
    }


@router.get("/users")
async def list_users(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    require_admin(authorization)
    r = await db.execute(select(User).order_by(User.id.desc()).limit(200))
    users = r.scalars().all()
    out = []
    for u in users:
        pts = await available_points(db, u.id)
        lv, _ = member_level(u.growth_value or 0)
        out.append(
            {
                "id": u.id,
                "phone": u.phone,
                "nickname": u.nickname,
                "available_points": pts,
                "growth_value": u.growth_value,
                "member_level": lv,
                "referrer_id": u.referrer_id,
            }
        )
    return {"code": 0, "data": out}


@router.get("/all-verify")
async def all_verify(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    require_admin(authorization)
    r = await db.execute(select(VerifyLog).order_by(VerifyLog.id.desc()).limit(200))
    logs = r.scalars().all()
    out = []
    for x in logs:
        u = await db.get(User, x.user_id)
        s = await db.get(Store, x.store_id) if x.store_id else None
        out.append(
            {
                "id": x.id,
                "user_phone": u.phone if u else "",
                "store_name": s.name if s else "",
                "total_points": x.points_spent,
                "verify_code": x.verify_code or "",
                "operator_name": x.operator_name or "",
                "verify_time": x.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
    return {"code": 0, "data": out}


@router.post("/add-points")
async def add_points(
    body: AddPointsIn,
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    require_admin(authorization)
    user = await db.get(User, body.userId)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    await grant_points(
        db,
        user,
        body.points,
        source="admin",
        source_ref=f"admin:{body.remark}",
        tx_type="adjust",
        ref_type="admin",
        ref_id=body.userId,
        note=body.remark,
    )
    await db.commit()
    return {"code": 0, "message": f"已发放 {body.points} 分", "data": {}}


@router.post("/trigger-settle")
async def trigger_settle(
    body: TriggerSettleIn,
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """测试用：把该用户该组不足的回调条数补齐到阈值并立即结算"""
    require_admin(authorization)
    user = await db.get(User, body.userId)
    group = await db.get(AdGroup, body.adGroupId)
    if not user or not group:
        raise HTTPException(status_code=404, detail="用户或广告组不存在")

    cnt_r = await db.execute(
        select(func.count())
        .select_from(AdCallbackLog)
        .where(
            AdCallbackLog.user_id == user.id,
            AdCallbackLog.ad_group_id == group.id,
            AdCallbackLog.status == 0,
        )
    )
    pending = int(cnt_r.scalar() or 0)
    need = group.callbacks_required - pending

    for i in range(max(need, 0)):
        db.add(
            AdCallbackLog(
                user_id=user.id,
                ad_group_id=group.id,
                ad_code=f"MANUAL-{group.code}-{i}",
                status=1,
            )
        )
    if need > 0:
        await grant_points(
            db,
            user,
            group.points_per_group,
            source="ad",
            source_ref=f"ad_group:{group.code}",
            tx_type="earn",
            ref_type="ad_group",
            ref_id=group.id,
            note=f"广告组 {group.title} 手动结算",
        )
    await db.commit()
    return {
        "code": 0,
        "message": "ok",
        "data": {"completed": need > 0, "points_awarded": group.points_per_group if need > 0 else 0},
    }


@router.post("/reset")
async def reset(
    authorization: str = Header(..., alias="Authorization"),
    db: AsyncSession = Depends(get_db),
):
    """测试用：清空全部业务流水，保留 3 个测试用户与基础配置"""
    require_admin(authorization)
    for model in (
        PointsLedger,
        PointsBucket,
        AdCallbackLog,
        VerifyLog,
        ExchangeLog,
        TaskLog,
        SmsCode,
    ):
        await db.execute(delete(model))

    keep = ["13800000001", "13800000002", "13800000003"]
    r = await db.execute(select(User).where(User.phone.in_(keep)))
    keepers = list(r.scalars().all())
    keep_ids = {u.id for u in keepers}
    # 删除其余用户
    all_u = await db.execute(select(User))
    for u in all_u.scalars().all():
        if u.id not in keep_ids:
            await db.delete(u)
    # 恢复初始状态
    initial = {u.phone: u for u in keepers}
    for phone, points in (
        ("13800000001", 100),
        ("13800000002", 0),
        ("13800000003", 200),
    ):
        u = initial.get(phone)
        if not u:
            continue
        u.growth_value = points
        u.total_earned = points
        u.total_spent = 0
        if points:
            db.add(
                PointsBucket(
                    user_id=u.id,
                    balance=points,
                    source="admin",
                    source_ref="seed",
                    expire_date=datetime.utcnow() + timedelta(days=365),
                )
            )
    await db.commit()
    return {"code": 0, "message": "重置完成：已保留 3 个测试用户", "data": {}}