# backend/models.py (数据库表结构：全量业务表、角色池与全局配置)
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, CheckConstraint, UniqueConstraint
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
    role = Column(String(20), default="worker", index=True) # 当前激活角色
    available_roles = Column(String(100), default="worker") # 拥有的角色池
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
    publish_status = Column(String(20), default="draft", index=True)
    risk_score = Column(Integer, default=0)
    risk_points = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

class JobApplication(Base):
    __tablename__ = "job_applications"
    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    worker_id = Column(Integer, ForeignKey("users.id"))
    city_id = Column(String(10), index=True, nullable=True)
    business_city_id = Column(String(10), index=True, nullable=True)
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
    __tablename__ = "service_orders"
    id = Column(Integer, primary_key=True)
    city_id = Column(String(10), index=True, nullable=True)
    provider_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(20), default="pending")
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