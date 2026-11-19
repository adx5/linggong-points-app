"""服务项目扩展字段 meta（一键直发采集的结构化信息）

Revision ID: 0011
Revises: 0010
Create Date: 2026-11-19

一键直发 5 步采集到的信息需要落库：
  sub_items   具体服务项（多选）
  experience  从业经验
  has_store   是否有实体门店
  advantages  服务优势标签（最多 3 个）
  card_style  选用的名片方案（A/B）
用 JSONB 存，避免为这类可变结构频繁改表。
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "provider_services",
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("provider_services", "meta")
