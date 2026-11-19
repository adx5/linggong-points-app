"""实名认证记录表 verifications

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-19

一次认证尝试一条记录：
  · provider=info   提交身份信息（姓名 + 身份证 + 证件照）
  · provider=mock/tencent/alipay  人脸活体核验
status: pending / verified / rejected / manual_review
人工兜底复核后由管理员改写 status，并记录 reviewer_id / reviewed_at。
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "verifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("city_id", sa.String(length=10), nullable=True),
        sa.Column("scene", sa.String(length=20), nullable=True),
        sa.Column("provider", sa.String(length=20), nullable=True),
        sa.Column("biz_no", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("liveness_score", sa.Float(), nullable=True),
        sa.Column("similarity_score", sa.Float(), nullable=True),
        sa.Column("raw_result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reject_reason", sa.String(length=255), nullable=True),
        sa.Column("reviewer_id", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_verifications_id", "verifications", ["id"])
    op.create_index("ix_verifications_user_id", "verifications", ["user_id"])
    op.create_index("ix_verifications_city_id", "verifications", ["city_id"])
    op.create_index("ix_verifications_scene", "verifications", ["scene"])
    op.create_index("ix_verifications_status", "verifications", ["status"])
    op.create_index("ix_verifications_biz_no", "verifications", ["biz_no"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_verifications_biz_no", table_name="verifications")
    op.drop_index("ix_verifications_status", table_name="verifications")
    op.drop_index("ix_verifications_scene", table_name="verifications")
    op.drop_index("ix_verifications_city_id", table_name="verifications")
    op.drop_index("ix_verifications_user_id", table_name="verifications")
    op.drop_index("ix_verifications_id", table_name="verifications")
    op.drop_table("verifications")
