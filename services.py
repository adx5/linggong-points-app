"""
services.py - 核心业务逻辑（PRD v0.2.2）
1. FIFO 积分分桶扣减：严格按 expire_date 升序，FOR UPDATE 行锁 + 事务
2. 广告按组结算：同组 status=0 累计达 callbacks_required 时发放 points_per_group
3. 门店核销：FIFO 扣减 + growth_value 累加 + verify_log
4. 拉新绑定：下线首次核销给上线发 100 积分
"""
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import PointsBucket, PointsLedger, User, VerifyLog

# ---------- 等级规则（PRD v0.2.2） ----------
LEVELS: List[Tuple[int, str, int]] = [
    (1, "青铜", 0),
    (2, "白银", 100),
    (3, "黄金", 500),
    (4, "铂金", 2000),
    (5, "钻石", 5000),
]


def member_level(growth_value: int) -> Tuple[int, str]:
    """按成长值返回 (level, level_name)"""
    lv, name = LEVELS[0][0], LEVELS[0][1]
    for l, n, need in LEVELS:
        if growth_value >= need:
            lv, name = l, n
    return lv, name


def now() -> datetime:
    return datetime.utcnow()


# ---------- 积分查询 ----------
async def available_points(db: AsyncSession, user_id: int) -> int:
    """未过期分桶余额合计"""
    r = await db.execute(
        select(func.coalesce(func.sum(PointsBucket.balance), 0)).where(
            PointsBucket.user_id == user_id,
            PointsBucket.balance > 0,
            PointsBucket.expire_date > now(),
        )
    )
    return int(r.scalar() or 0)


async def get_active_buckets(
    db: AsyncSession, user_id: int, lock: bool = False
) -> List[PointsBucket]:
    """按 expire_date 升序取未过期分桶；lock=True 时加 FOR UPDATE 行锁"""
    stmt = (
        select(PointsBucket)
        .where(
            PointsBucket.user_id == user_id,
            PointsBucket.balance > 0,
            PointsBucket.expire_date > now(),
        )
        .order_by(PointsBucket.expire_date.asc(), PointsBucket.id.asc())
    )
    if lock:
        stmt = stmt.with_for_update()
    r = await db.execute(stmt)
    return list(r.scalars().all())


# ---------- 发放积分 ----------
async def grant_points(
    db: AsyncSession,
    user: User,
    points: int,
    source: str,
    source_ref: Optional[str] = None,
    tx_type: str = "earn",
    ref_type: Optional[str] = None,
    ref_id: Optional[str] = None,
    note: Optional[str] = None,
    valid_days: int = 365,
) -> PointsBucket:
    """写入新分桶 + 流水 + 累加 total_earned（由调用方 commit）"""
    bucket = PointsBucket(
        user_id=user.id,
        balance=points,
        source=source,
        source_ref=source_ref,
        expire_date=now() + timedelta(days=valid_days),
    )
    db.add(bucket)
    await db.flush()

    user.total_earned = (user.total_earned or 0) + points
    balance = await available_points(db, user.id)
    db.add(
        PointsLedger(
            user_id=user.id,
            delta=points,
            balance_after=balance,
            bucket_id=bucket.id,
            tx_type=tx_type,
            ref_type=ref_type,
            ref_id=str(ref_id) if ref_id is not None else None,
            note=note,
        )
    )
    await db.flush()
    return bucket


# ---------- FIFO 扣减 ----------
class InsufficientPoints(Exception):
    def __init__(self, missing: int):
        super().__init__(f"积分不足，还差 {missing} 分")
        self.missing = missing


async def spend_points_fifo(
    db: AsyncSession,
    user_id: int,
    points: int,
    ref_type: Optional[str] = None,
    ref_id: Optional[str] = None,
    note: Optional[str] = None,
) -> int:
    """
    严格 FIFO 扣减：按 expire_date 升序逐桶扣，FOR UPDATE 保证并发安全。
    返回扣减后的可用余额。积分不足时抛 InsufficientPoints（调用方需 rollback）。
    流水在调用方 commit 后由 balance_after 统一回填。
    """
    remaining = points
    buckets = await get_active_buckets(db, user_id, lock=True)
    for b in buckets:
        if remaining <= 0:
            break
        take = min(int(b.balance), remaining)
        b.balance = int(b.balance) - take
        remaining -= take
        db.add(
            PointsLedger(
                user_id=user_id,
                delta=-take,
                balance_after=0,  # 稍后统一回填
                bucket_id=b.id,
                tx_type="spend",
                ref_type=ref_type,
                ref_id=str(ref_id) if ref_id is not None else None,
                note=note,
            )
        )
        await db.flush()

    if remaining > 0:
        raise InsufficientPoints(remaining)

    balance = await available_points(db, user_id)
    # 回填本笔流水的 balance_after
    r = await db.execute(
        select(PointsLedger)
        .where(
            PointsLedger.user_id == user_id,
            PointsLedger.tx_type == "spend",
            PointsLedger.balance_after == 0,
        )
        .order_by(PointsLedger.id.desc())
        .limit(50)
    )
    for row in r.scalars().all():
        row.balance_after = balance
    await db.flush()
    return balance


# ---------- 首次核销判定 ----------
async def is_first_verify(db: AsyncSession, user_id: int) -> bool:
    cnt = (
        await db.execute(
            select(func.count()).select_from(VerifyLog).where(VerifyLog.user_id == user_id)
        )
    ).scalar()
    return int(cnt or 0) == 0


# ---------- 拉新奖励 ----------
async def reward_referrer(
    db: AsyncSession, downline: User, amount: int = 100
) -> bool:
    """下线首次核销 → 给上线发 100 积分。成功返回 True"""
    if not downline.referrer_id:
        return False
    ref_user = await db.get(User, downline.referrer_id)
    if not ref_user or not ref_user.is_active:
        return False
    await grant_points(
        db,
        ref_user,
        amount,
        source="referral",
        source_ref=f"ref:{downline.id}",
        tx_type="earn",
        ref_type="referral",
        ref_id=downline.id,
        note=f"下线 {downline.phone} 首次核销奖励",
    )
    return True


def today_str() -> date:
    return date.today()