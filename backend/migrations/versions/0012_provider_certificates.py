"""服务商技能证书表 provider_certificates

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-19

服务商在「资质与实名认证」页拍照上传技能证书：
图片走已有图床（BeeIMG），本表只存 URL 与审核状态。
"""
import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "provider_certificates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("city_id", sa.String(length=10), nullable=True),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("image_url", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("reviewer_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["provider_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_provider_certificates_id", "provider_certificates", ["id"])
    op.create_index("ix_provider_certificates_provider_id", "provider_certificates", ["provider_id"])
    op.create_index("ix_provider_certificates_city_id", "provider_certificates", ["city_id"])
    op.create_index("ix_provider_certificates_status", "provider_certificates", ["status"])


def downgrade() -> None:
    op.drop_index("ix_provider_certificates_status", table_name="provider_certificates")
    op.drop_index("ix_provider_certificates_city_id", table_name="provider_certificates")
    op.drop_index("ix_provider_certificates_provider_id", table_name="provider_certificates")
    op.drop_index("ix_provider_certificates_id", table_name="provider_certificates")
    op.drop_table("provider_certificates")
