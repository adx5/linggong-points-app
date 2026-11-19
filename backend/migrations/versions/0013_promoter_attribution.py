"""推广归属：job_applications.promoter_id

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-19

闭环链路：
  推广人分享岗位（?promoter=xx）→ 求职者投递时带上 promoter → 落库到投递记录
  → 工单结单（C 端确认完工 / 系统超时结单）→ 给推广人发积分

积分发放走 point_transactions，ref_no = promo_{application_id}，
配合 uq_biz_ref 唯一约束保证「一单只奖励一次」。
"""
import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_applications", sa.Column("promoter_id", sa.Integer(), nullable=True))
    op.create_index("ix_job_applications_promoter_id", "job_applications", ["promoter_id"])


def downgrade() -> None:
    op.drop_index("ix_job_applications_promoter_id", table_name="job_applications")
    op.drop_column("job_applications", "promoter_id")
