"""推广计费：企业推广余额 + 岗位推广积分

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-19

模式（避免二清）：
  · B 端先充值「推广积分余额」（线下对公转账，后台记账，平台不做资金代收代付）
  · 发布岗位时设定「每单推广积分」（日结/长期可不同）
  · C 端结单时：从企业余额扣减 N 分 → 给推广人发 N 分
  · 企业余额不足则不发放，并通知企业补足
"""
import sqlalchemy as sa
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cooperation_entities",
                  sa.Column("promotion_balance", sa.Float(), nullable=True))
    op.add_column("jobs",
                  sa.Column("promotion_points", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "promotion_points")
    op.drop_column("cooperation_entities", "promotion_balance")
