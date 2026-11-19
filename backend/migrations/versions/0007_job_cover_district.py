"""岗位：封面图 + 所在区镇（支撑 C 端图文卡与「附近」）

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-19

· cover_image：企业上传到图床的封面 URL，C 端首页/列表图文卡使用
· district   ：企业注册地所在区/镇，用于「附近」按大范围（区镇）筛选
"""
import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("cover_image", sa.String(length=255), nullable=True))
    op.add_column("jobs", sa.Column("district", sa.String(length=50), nullable=True))
    op.create_index("ix_jobs_district", "jobs", ["district"])


def downgrade() -> None:
    op.drop_index("ix_jobs_district", table_name="jobs")
    op.drop_column("jobs", "district")
    op.drop_column("jobs", "cover_image")
