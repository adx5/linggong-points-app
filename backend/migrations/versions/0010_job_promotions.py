"""岗位推广记录表 job_promotions

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-19

服务商 / 经纪人把岗位分享出去帮平台招工（B 端「招聘大厅」的「立即推广」），
记录推广人与岗位的对应关系，后续可据此结算推广激励。
同一推广人对同一岗位只记一次。
"""
import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_promotions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("promoter_id", sa.Integer(), nullable=False),
        sa.Column("city_id", sa.String(length=10), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.ForeignKeyConstraint(["promoter_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "promoter_id", name="uq_job_promoter"),
    )
    op.create_index("ix_job_promotions_id", "job_promotions", ["id"])
    op.create_index("ix_job_promotions_job_id", "job_promotions", ["job_id"])
    op.create_index("ix_job_promotions_promoter_id", "job_promotions", ["promoter_id"])
    op.create_index("ix_job_promotions_city_id", "job_promotions", ["city_id"])


def downgrade() -> None:
    op.drop_index("ix_job_promotions_city_id", table_name="job_promotions")
    op.drop_index("ix_job_promotions_promoter_id", table_name="job_promotions")
    op.drop_index("ix_job_promotions_job_id", table_name="job_promotions")
    op.drop_index("ix_job_promotions_id", table_name="job_promotions")
    op.drop_table("job_promotions")
