# backend/models.py (数据库表结构：全量完整版)
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, CheckConstraint, \
    UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from database import Base


class City(Base):
    __tablename__ = "cities"
    id = Column(String(10), primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    status = Column(String(20), default="active")


class GlobalConfig(Base):
    __tablename__ = "global_configs"
    key = Column(String(50), primary_key=True, index=True)
    value = Column(String(255), nullable=False)
    description = Column(String(255), default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, index=True)
    nickname = Column(String(50), default="新用户")
    total_points = Column(Integer, default=0)
    city_id = Column(String(10), index=True, nullable=True)
    token_version = Column(Integer, default=0, nullable=False)
    # 与库中实际约束保持一致（DB 为 NOT NULL），避免 Alembic 持续报漂移
    role = Column(String(20), default="worker", index=True, nullable=False)
    available_roles = Column(String(100), default="worker")
    resume_data = Column(JSONB, default={})

    # 🚨 实名认证字段
    real_name = Column(String(50), nullable=True)
    id_card = Column(String(100), nullable=True)
    verify_status = Column(String(20), default="unverified")  # unverified / pending / verified

    created_at = Column(DateTime, default=datetime.utcnow)


class CooperationEntity(Base):
    __tablename__ = "cooperation_entities"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    city_id = Column(String(10), index=True, nullable=True)
    file_no = Column(String(50), unique=True, index=True)
    type = Column(String(20), index=True)
    name = Column(String(100), index=True)
    status = Column(String(20), default="pending")
    reject_reason = Column(String(255), default="")
    credit_score = Column(Integer, default=100)
    deposit_amount = Column(Float, default=0.0)
    # 推广积分余额（B 端充值，按单扣减；平台不代收 C 端资金，规避二清）
    promotion_balance = Column(Float, default=0.0)
    bank_account = Column(String(100), default="")
    ext_info = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)


class EntityCertificate(Base):
    __tablename__ = "entity_certificates"
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey("cooperation_entities.id"))
    city_id = Column(String(10), index=True, nullable=True)
    cert_type = Column(String(50))
    cert_no = Column(String(100), default="")
    image_url = Column(String(255), default="")
    expire_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="normal")
    created_at = Column(DateTime, default=datetime.utcnow)


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    merchant_id = Column(Integer, ForeignKey("users.id"))
    city_id = Column(String(10), index=True, nullable=True)
    title = Column(String(100))
    salary = Column(String(50))
    location = Column(String(255))
    job_type = Column(String(20), default="long_term")
    filter_tag = Column(String(50), default="")
    tags = Column(String(255))
    description = Column(Text, default="")
    requirement = Column(Text, default="")
    # 企业上传的岗位封面（图床 URL），为空时前端用占位图兜底
    cover_image = Column(String(255), default="")
    # 企业注册地所在区/镇，用于「附近」粗粒度筛选（大范围）
    district = Column(String(50), default="", index=True)
    publish_status = Column(String(20), default="draft", index=True)
    risk_score = Column(Integer, default=0)
    risk_points = Column(Text, default="")
    # 风控判定结果：unchecked / pass / review(转人工) / blocked(拦截)
    risk_status = Column(String(20), default="unchecked", index=True)
    risk_checked_at = Column(DateTime, nullable=True)
    # 本岗位每成功推广一单奖励的积分（发布时由 B 端设定，结算时从企业推广余额扣减）
    promotion_points = Column(Integer, default=0)
    # 加热置顶到期时间（>现在 表示置顶中）；加热消耗企业推广余额
    pinned_until = Column(DateTime, nullable=True)
    # 最近一次「刷新」时间：C 端排序用（越新越靠前）
    refreshed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class JobApplication(Base):
    __tablename__ = "job_applications"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    worker_id = Column(Integer, ForeignKey("users.id"))
    city_id = Column(String(10), index=True, nullable=True)
    business_city_id = Column(String(10), index=True, nullable=True)
    # 推广归属：这条投递是谁推广来的（结单后给推广人发积分）
    promoter_id = Column(Integer, index=True, nullable=True)
    status = Column(Integer, default=1)
    reject_reason = Column(String(255), default="")
    settled_points = Column(Integer, default=0)
    evidence_photo = Column(String(255), default="")
    invite_time = Column(DateTime, nullable=True)
    interview_confirm_time = Column(DateTime, nullable=True)
    hired_time = Column(DateTime, nullable=True)
    finish_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 🚨 防重复投递：原实现仅靠应用层查重，并发下会产生重复记录
    __table_args__ = (
        UniqueConstraint('job_id', 'worker_id', name='uq_job_worker'),
    )


class ApplicationLog(Base):
    __tablename__ = "application_logs"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("job_applications.id"))
    city_id = Column(String(10), index=True, nullable=True)
    operator_type = Column(String(20))
    action = Column(String(50))
    detail = Column(Text, default="")
    evidence_photo = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    merchant_id = Column(Integer, ForeignKey("users.id"))
    worker_id = Column(Integer, ForeignKey("users.id"))
    city_id = Column(String(10), index=True, nullable=True)
    interview_time = Column(String(100))
    interview_address = Column(String(255))
    method = Column(String(20), default="线下")
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("job_applications.id"))
    merchant_id = Column(Integer, ForeignKey("users.id"))
    worker_id = Column(Integer, ForeignKey("users.id"))
    city_id = Column(String(10), index=True, nullable=True)
    rating = Column(Integer, default=5)
    comment = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    city_id = Column(String(10), index=True, nullable=True)
    title = Column(String(100))
    content = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    operator_id = Column(Integer, index=True)
    city_id = Column(String(10), index=True, nullable=True)
    action = Column(String(50))
    target_type = Column(String(20))
    target_id = Column(Integer)
    detail = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class PointTransaction(Base):
    __tablename__ = "point_transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    city_id = Column(String(10), index=True, nullable=True)
    amount = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    biz_type = Column(String(50), nullable=False)
    ref_no = Column(String(100), nullable=False)
    original_transaction_id = Column(Integer, ForeignKey("point_transactions.id"), nullable=True)
    status = Column(String(20), default="success")
    order_id = Column(String(100), nullable=True)
    reviewer_id = Column(Integer, nullable=True)
    operator_id = Column(Integer, nullable=True)
    remark = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        UniqueConstraint('biz_type', 'ref_no', name='uq_biz_ref'),
    )


class ServiceOrder(Base):
    """同城服务订单（P5/P6 服务商业务域）

    原表只有 id/city_id/provider_id/status，这里扩展为完整订单：
    customer_id = 下单用户（C 端），provider_id = 接单服务商（users.id）
    """
    __tablename__ = "service_orders"
    id = Column(Integer, primary_key=True)
    city_id = Column(String(10), index=True, nullable=True)
    customer_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    provider_id = Column(Integer, ForeignKey("users.id"), index=True)
    category_id = Column(Integer, index=True, nullable=True)
    title = Column(String(100), default="")
    description = Column(Text, default="")
    price = Column(Float, default=0.0)
    address = Column(String(255), default="")
    contact_phone = Column(String(20), default="")
    scheduled_at = Column(String(50), default="")
    status = Column(String(20), default="pending", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ServiceCategory(Base):
    """同城服务类目（家政保洁、维修安装…）"""
    __tablename__ = "service_categories"
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(String(10), index=True, nullable=True)
    name = Column(String(50), nullable=False)
    icon = Column(String(20), default="")
    sort_no = Column(Integer, default=0)
    status = Column(String(20), default="active", index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProviderProfile(Base):
    """服务商/师傅档案（服务商端专属）"""
    __tablename__ = "provider_profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True, nullable=False)
    city_id = Column(String(10), index=True, nullable=True)
    display_name = Column(String(50), default="")
    category_id = Column(Integer, index=True, nullable=True)
    avatar = Column(String(255), default="")
    intro = Column(Text, default="")
    district = Column(String(50), default="", index=True)
    rating = Column(Float, default=5.0)
    orders_done = Column(Integer, default=0)
    verify_status = Column(String(20), default="unverified")
    created_at = Column(DateTime, default=datetime.utcnow)


class ProviderCertificate(Base):
    """服务商技能证书（走图床上传，平台审核）"""
    __tablename__ = "provider_certificates"
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    city_id = Column(String(10), index=True, nullable=True)
    title = Column(String(100), nullable=False)
    image_url = Column(String(255), nullable=False)
    status = Column(String(20), default="pending", index=True)  # pending / verified / rejected
    reviewer_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class JobPromotion(Base):
    """岗位推广记录：服务商/经纪人把岗位分享出去帮平台招工

    同一推广人对同一岗位只记一次（唯一键），用于后续结算推广激励。
    """
    __tablename__ = "job_promotions"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), index=True, nullable=False)
    promoter_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    city_id = Column(String(10), index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        UniqueConstraint('job_id', 'promoter_id', name='uq_job_promoter'),
    )


class ProviderService(Base):
    __tablename__ = "provider_services"
    id = Column(Integer, primary_key=True, index=True)
    provider_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    city_id = Column(String(10), index=True, nullable=True)
    category_id = Column(Integer, index=True, nullable=True)
    title = Column(String(100), nullable=False)
    price = Column(Float, default=0.0)
    price_unit = Column(String(20), default="次")
    description = Column(Text, default="")
    images = Column(JSONB, default=[])
    # 一键直发采集的结构化信息：sub_items / experience / has_store / advantages / card_style
    meta = Column(JSONB, default={})
    status = Column(String(20), default="active", index=True)  # active / off
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ServiceReview(Base):
    __tablename__ = "service_reviews"
    id = Column(Integer, primary_key=True, index=True)
    city_id = Column(String(10), index=True, nullable=True)
    order_id = Column(Integer, ForeignKey("service_orders.id"), index=True, nullable=True)
    provider_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=True)
    customer_name = Column(String(50), default="匿名用户")
    rating = Column(Integer, default=5)
    content = Column(Text, default="")
    images = Column(JSONB, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    city_id = Column(String(10), index=True, nullable=True)
    reporter_id = Column(Integer)
    target_id = Column(Integer)
    reason = Column(Text)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class Blacklist(Base):
    __tablename__ = "blacklists"
    id = Column(Integer, primary_key=True)
    city_id = Column(String(10), index=True, nullable=True)
    entity_id = Column(Integer)
    reason = Column(Text)
    reviewer_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ExchangeOrder(Base):
    __tablename__ = "exchange_orders"
    id = Column(Integer, primary_key=True)
    city_id = Column(String(10), index=True, nullable=True)
    user_id = Column(Integer)
    item_id = Column(Integer)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class VerificationCode(Base):
    __tablename__ = "verification_codes"
    id = Column(Integer, primary_key=True)
    city_id = Column(String(10), index=True, nullable=True)
    order_id = Column(Integer)
    code = Column(String(50))
    status = Column(String(20), default="unused")
    created_at = Column(DateTime, default=datetime.utcnow)


class Withdrawal(Base):
    __tablename__ = "withdrawals"
    id = Column(Integer, primary_key=True)
    city_id = Column(String(10), index=True, nullable=True)
    user_id = Column(Integer)
    amount = Column(Float)
    status = Column(String(20), default="pending")
    reviewer_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProfitSharingBill(Base):
    __tablename__ = "profit_sharing_bills"
    id = Column(Integer, primary_key=True)
    city_id = Column(String(10), index=True, nullable=True)
    bill_no = Column(String(100), unique=True)
    amount = Column(Float)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class TempAuthorization(Base):
    __tablename__ = "temp_authorizations"
    id = Column(Integer, primary_key=True)
    city_id = Column(String(10), index=True, nullable=True)
    operator_id = Column(Integer)
    target_id = Column(Integer)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class ExportLog(Base):
    __tablename__ = "export_logs"
    id = Column(Integer, primary_key=True)
    city_id = Column(String(10), index=True, nullable=True)
    operator_id = Column(Integer)
    file_type = Column(String(50))
    watermark_text = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class HighRiskApproval(Base):
    __tablename__ = "high_risk_approvals"
    id = Column(Integer, primary_key=True)
    city_id = Column(String(10), index=True, nullable=True)
    operator_id = Column(Integer, nullable=False)
    reviewer_id = Column(Integer, nullable=True)
    action_type = Column(String(50))
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        CheckConstraint('operator_id != reviewer_id OR reviewer_id IS NULL', name='check_operator_not_reviewer'),
    )


class Verification(Base):
    """实名/人脸核验记录

    一次认证尝试一条记录：
      · 提交身份信息（姓名+身份证+证件照）→ status=pending, provider=info
      · 人脸活体核验 → status=verified / rejected / manual_review, provider=mock|tencent|alipay
    人工兜底审核后由管理员改写 status 并记录 reviewer_id / reviewed_at。
    """
    __tablename__ = "verifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    city_id = Column(String(10), index=True, nullable=True)
    scene = Column(String(20), default="register", index=True)   # register / first_order / high_risk
    provider = Column(String(20), default="info")                 # info / mock / tencent / alipay
    biz_no = Column(String(64), unique=True, index=True)
    status = Column(String(20), default="pending", index=True)    # pending/verified/rejected/manual_review
    liveness_score = Column(Float, nullable=True)
    similarity_score = Column(Float, nullable=True)
    raw_result = Column(JSONB, default={})
    reject_reason = Column(String(255), default="")
    reviewer_id = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)