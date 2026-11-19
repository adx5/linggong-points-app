"""岗位风控字段：risk_status / risk_checked_at

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-19

配合 services/risk_rules.py（风控第一层：确定性规则）：
  risk_status: unchecked / pass / review(转人工) / blocked(拦截)
  risk_score : 0~100（由 0~1 的规则分换算，复用既有列）
  risk_points: 规则命中的可解释依据（JSON 文本）
"""
import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("risk_status", sa.String(length=20), nullable=True))
    op.add_column("jobs", sa.Column("risk_checked_at", sa.DateTime(), nullable=True))
    op.create_index("ix_jobs_risk_status", "jobs", ["risk_status"])

    # 历史岗位统一标记为 unchecked（上架闸门只拦 blocked，不会误伤存量）
    op.execute("UPDATE jobs SET risk_status = 'unchecked' WHERE risk_status IS NULL")


def downgrade() -> None:
    op.drop_index("ix_jobs_risk_status", table_name="jobs")
    op.drop_column("jobs", "risk_checked_at")
    op.drop_column("jobs", "risk_status")
