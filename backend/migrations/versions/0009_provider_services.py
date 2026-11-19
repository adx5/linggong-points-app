"""服务商服务项目表 provider_services（一键直发的产物）

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-19

B 端「服务管理」tab 与「一键直发 Step1-5」依赖：
服务商把自己能提供的服务（保洁/维修/搬家…）上架成条目，C 端才能看到并下单。
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "provider_services",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("city_id", sa.String(length=10), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("price_unit", sa.String(length=20), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("images", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["provider_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_provider_services_id", "provider_services", ["id"])
    op.create_index("ix_provider_services_provider_id", "provider_services", ["provider_id"])
    op.create_index("ix_provider_services_city_id", "provider_services", ["city_id"])
    op.create_index("ix_provider_services_category_id", "provider_services", ["category_id"])
    op.create_index("ix_provider_services_status", "provider_services", ["status"])


def downgrade() -> None:
    op.drop_index("ix_provider_services_status", table_name="provider_services")
    op.drop_index("ix_provider_services_category_id", table_name="provider_services")
    op.drop_index("ix_provider_services_city_id", table_name="provider_services")
    op.drop_index("ix_provider_services_provider_id", table_name="provider_services")
    op.drop_index("ix_provider_services_id", table_name="provider_services")
    op.drop_table("provider_services")
