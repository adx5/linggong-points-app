"""
models.py - SQLAlchemy ORM 数据表
覆盖 PRD v0.2.2 全部业务实体：
- 用户 / 积分分桶 / 积分流水 / 验证码
- 广告组 / 广告回调日志
- 门店 / 核销日志
- 兑换商品 / 兑换日志
- 任务定义 / 任务日志（按天重置）
- 管理员
"""
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)

from database import Base


# ---------- 用户 ----------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    nickname = Column(String(64), nullable=False, default="")
    password_hash = Column(String(255), nullable=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    growth_value = Column(BigInteger, nullable=False, default=0)
    total_earned = Column(BigInteger, nullable=False, default=0)
    total_spent = Column(BigInteger, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


# ---------- 积分分桶 (FIFO 扣减按 expire_date 升序) ----------
class PointsBucket(Base):
    __tablename__ = "points_buckets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    balance = Column(BigInteger, nullable=False, default=0)
    source = Column(String(32), nullable=False)  # ad | referral | task | admin
    source_ref = Column(String(64), nullable=True)
    expire_date = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_buckets_user_expire", "user_id", "expire_date"),
    )


# ---------- 积分流水 ----------
class PointsLedger(Base):
    __tablename__ = "points_ledger"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    delta = Column(BigInteger, nullable=False)  # 正=收入 负=支出
    balance_after = Column(BigInteger, nullable=False)
    bucket_id = Column(Integer, ForeignKey("points_buckets.id"), nullable=True)
    tx_type = Column(String(32), nullable=False)  # earn | spend | expire | adjust
    ref_type = Column(String(32), nullable=True)  # ad_group | task | referral | verify | exchange
    ref_id = Column(String(64), nullable=True)
    note = Column(String(255), nullable=True)
    created_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, index=True
    )


# ---------- 验证码 ----------
class SmsCode(Base):
    __tablename__ = "sms_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(20), nullable=False, index=True)
    code = Column(String(8), nullable=False)
    used = Column(Boolean, nullable=False, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ---------- 广告组 ----------
class AdGroup(Base):
    __tablename__ = "ad_groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False)
    title = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    points_per_group = Column(Integer, nullable=False, default=5)
    callbacks_required = Column(Integer, nullable=False, default=10)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ---------- 广告回调日志 ----------
class AdCallbackLog(Base):
    __tablename__ = "ad_callback_log"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ad_group_id = Column(Integer, ForeignKey("ad_groups.id"), nullable=False, index=True)
    ad_code = Column(String(64), nullable=False)
    status = Column(Integer, nullable=False, default=0)  # 0=pending 1=credited
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


# ---------- 门店 ----------
class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    contact = Column(String(64), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ---------- 核销日志 ----------
class VerifyLog(Base):
    __tablename__ = "verify_log"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    points_spent = Column(BigInteger, nullable=False)
    growth_delta = Column(BigInteger, nullable=False, default=0)
    verify_code = Column(String(64), nullable=True)  # 库存系统传入的核销码
    batch_no = Column(String(64), nullable=True)  # 批次号
    operator_name = Column(String(64), nullable=True)  # 操作人（门店）
    note = Column(String(255), nullable=True)
    is_first_verify = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


# ---------- 兑换商品 ----------
class ExchangeItem(Base):
    __tablename__ = "exchange_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    item_type = Column(Integer, nullable=False, default=1)  # 1实物 2团购券 3VIP卡密
    points_cost = Column(BigInteger, nullable=False)
    stock = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ---------- 兑换日志 ----------
class ExchangeLog(Base):
    __tablename__ = "exchange_log"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("exchange_items.id"), nullable=False)
    points_spent = Column(BigInteger, nullable=False)
    verify_code = Column(String(32), nullable=True)  # 提货核销码
    status = Column(Integer, nullable=False, default=1)  # 1=待核销 2=已完成
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)


# ---------- 福利任务定义 ----------
class TaskDef(Base):
    __tablename__ = "task_defs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(64), unique=True, nullable=False)
    title = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    reward_points = Column(Integer, nullable=False, default=0)
    reward_type = Column(String(32), nullable=False, default="bucket")  # bucket | growth
    sort_no = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ---------- 任务完成日志（按天重置） ----------
class TaskLog(Base):
    __tablename__ = "task_log"

    id = Column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("task_defs.id"), nullable=False)
    reward = Column(Integer, nullable=False, default=0)
    log_date = Column(Date, nullable=False, default=date.today, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_tasklog_user_date", "user_id", "log_date"),
    )

# ---------- 管理员 ----------
class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, default="admin")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ---------- 招工信息表 (注意这里不要缩进！) ----------
class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    publisher_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    salary = Column(String(50), nullable=False)
    location = Column(String(255), nullable=False)
    tags = Column(String(255), nullable=False)  # 逗号分隔，如 "日结,包餐"
    description = Column(Text, nullable=True)
    status = Column(Integer, nullable=False, default=1)  # 1=开放, 0=关闭
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


# ---------- 投递记录表 (不要缩进) ----------
class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(Integer, nullable=False, default=1)  # 1=待处理, 2=已录用, 3=已拒绝
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)