"""岗位刷新时间：jobs.refreshed_at

Revision ID: 0016
Revises: 0015
Create Date: 2026-11-20

B 端「岗位管理」的「刷新」按钮：
  · 把 refreshed_at 置为当前时间
  · C 端列表排序改为：置顶优先 → 最近刷新/发布时间倒序
"""
import sqlalchemy as sa
from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("refreshed_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("jobs", "refreshed_at")
