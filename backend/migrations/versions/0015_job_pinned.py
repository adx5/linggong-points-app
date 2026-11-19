"""岗位加热置顶：jobs.pinned_until

Revision ID: 0015
Revises: 0014
Create Date: 2026-11-20

B 端在「岗位管理」对在招岗位点「加热置顶」：
  · 按天从企业推广余额扣费（BOOST_POINTS_PER_DAY，默认 30 分/天）
  · 写入 pinned_until，C 端列表把置顶岗位排在最前
  · 重复加热则在原到期时间上顺延
"""
import sqlalchemy as sa
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("pinned_until", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "pinned_until")
