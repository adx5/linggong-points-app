"""
seed.py - 测试数据 Seed（幂等，可重复执行）
运行：
    python seed.py
或：
    python -m seed

测试账号：
    C端 13800000001 (用户A, 100分) / 13800000002 (用户B, 0分) / 13800000003 (用户C, 200分)
    B端 门店码 store001
    A端 admin / 123456
    验证码 123456（DEV_MODE=true）
"""
import sys
import asyncio
from datetime import datetime, timedelta

# ==========================================
# ⚠️ 关键修复：针对 Windows 系统
# psycopg 异步模式不支持默认的 ProactorEventLoop
# ==========================================
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import func, select

from database import AsyncSessionLocal, init_models
from models import (
    AdGroup,
    AdminUser,
    ExchangeItem,
    PointsBucket,
    Store,
    TaskDef,
    User,
)


async def seed() -> None:
    await init_models()
    async with AsyncSessionLocal() as db:
        # ---------- 管理员 ----------
        admin = (
            await db.execute(select(AdminUser).where(AdminUser.username == "admin"))
        ).scalar_one_or_none()
        if not admin:
            db.add(AdminUser(username="admin", password_hash="123456", role="admin"))
            print("+ AdminUser admin/123456")

        # ---------- 门店 ----------
        store = (
            await db.execute(select(Store).where(Store.code == "store001"))
        ).scalar_one_or_none()
        if not store:
            db.add(Store(code="store001", name="测试门店·望京店", contact="010-88888888"))
            print("+ Store store001")
            await db.flush()

        # ---------- 广告组（PRD：每组10条 = 5分） ----------
        for i in range(1, 4):
            code = f"AD_GROUP_{i}"
            g = (
                await db.execute(select(AdGroup).where(AdGroup.code == code))
            ).scalar_one_or_none()
            if not g:
                db.add(
                    AdGroup(
                        code=code,
                        title=f"第{i}组广告",
                        description=f"看完10条发放5积分（第{i}组）",
                        points_per_group=5,
                        callbacks_required=10,
                        is_active=True,
                    )
                )
                print(f"+ AdGroup {code}")

        # ---------- 兑换商品 ----------
        items = [
            ("纸巾一盒", 1, 100, 50),
            ("奶茶券", 2, 50, 200),
            ("门店5折券", 2, 200, 100),
            ("VIP月卡", 3, 500, 20),
        ]
        for name, itype, cost, stock in items:
            it = (
                await db.execute(select(ExchangeItem).where(ExchangeItem.name == name))
            ).scalar_one_or_none()
            if not it:
                db.add(
                    ExchangeItem(
                        name=name,
                        description=f"{name}（{cost}积分兑换）",
                        item_type=itype,
                        points_cost=cost,
                        stock=stock,
                        is_active=True,
                    )
                )
                print(f"+ ExchangeItem {name}")

        # ---------- 每日任务 ----------
        tasks = [
            ("signin", "每日签到", 1),
            ("moments", "发朋友圈", 3),
            ("appDownload", "App下载", 25),
            ("yifenGou", "1分购", 3),
            ("study", "线上学习", 5),
            ("studyOffline", "线下学习", 20),
            ("parttime", "做兼职", 3),
        ]
        for idx, (code, title, pts) in enumerate(tasks):
            t = (
                await db.execute(select(TaskDef).where(TaskDef.code == code))
            ).scalar_one_or_none()
            if not t:
                db.add(
                    TaskDef(
                        code=code,
                        title=title,
                        description=f"完成「{title}」获得 {pts} 积分（每日一次）",
                        reward_points=pts,
                        reward_type="bucket",
                        sort_no=idx + 1,
                        is_active=True,
                    )
                )
                print(f"+ TaskDef {code}")

        await db.flush()

        # ---------- 测试用户 ----------
        # 13800000003 绑定 13800000001 为上线（验证拉新奖励）
        a = (
            await db.execute(select(User).where(User.phone == "13800000001"))
        ).scalar_one_or_none()
        if not a:
            a = User(phone="13800000001", nickname="用户A", growth_value=100, total_earned=100)
            db.add(a)
            await db.flush()
            print("+ User 13800000001 (用户A)")

        b = (
            await db.execute(select(User).where(User.phone == "13800000002"))
        ).scalar_one_or_none()
        if not b:
            b = User(phone="13800000002", nickname="用户B", growth_value=0, total_earned=0)
            db.add(b)
            await db.flush()
            print("+ User 13800000002 (用户B)")

        c = (
            await db.execute(select(User).where(User.phone == "13800000003"))
        ).scalar_one_or_none()
        if not c:
            c = User(phone="13800000003", nickname="用户C", growth_value=200, total_earned=200)
            db.add(c)
            await db.flush()
            print("+ User 13800000003 (用户C)")

        # C 的上线 = A（拉新链路）
        if c.referrer_id != a.id:
            c.referrer_id = a.id

        # 初始积分桶（A=100, B=0, C=200）
        for user, balance, days in ((a, 100, 30), (b, 0, 30), (c, 200, 60)):
            cnt = (
                await db.execute(
                    select(func.count())
                    .select_from(PointsBucket)
                    .where(PointsBucket.user_id == user.id)
                )
            ).scalar()
            if int(cnt or 0) == 0 and balance > 0:
                db.add(
                    PointsBucket(
                        user_id=user.id,
                        balance=balance,
                        source="admin",
                        source_ref="seed",
                        expire_date=datetime.utcnow() + timedelta(days=days),
                    )
                )
                print(f"+ PointsBucket user={user.phone} {balance}分 ({days}天过期)")

        await db.commit()

    print("\n✅ Seed 完成。测试账号：")
    print("   C端  13800000001 (A/100分) 13800000002 (B/0分) 13800000003 (C/200分, 上线=A)")
    print("   B端  store001")
    print("   A端  admin / 123456")
    print("   验证码 123456")


if __name__ == "__main__":
    asyncio.run(seed())