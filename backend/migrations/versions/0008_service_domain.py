"""同城服务业务域：类目 / 师傅档案 / 服务订单扩展 / 服务评价

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-19

P5 同城服务页、P6b 服务详情、P6c 评价列表依赖的数据结构。
`service_orders` 原为早期遗留的空表（只有 id/city_id/provider_id/status），
这里就地扩列，不新建表，避免又留一张僵尸表。
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---------- 服务类目 ----------
    op.create_table(
        "service_categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("city_id", sa.String(length=10), nullable=True),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("icon", sa.String(length=20), nullable=True),
        sa.Column("sort_no", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_service_categories_id", "service_categories", ["id"])
    op.create_index("ix_service_categories_city_id", "service_categories", ["city_id"])
    op.create_index("ix_service_categories_status", "service_categories", ["status"])

    # ---------- 师傅/服务商档案 ----------
    op.create_table(
        "provider_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("city_id", sa.String(length=10), nullable=True),
        sa.Column("display_name", sa.String(length=50), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("avatar", sa.String(length=255), nullable=True),
        sa.Column("intro", sa.Text(), nullable=True),
        sa.Column("district", sa.String(length=50), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("orders_done", sa.Integer(), nullable=True),
        sa.Column("verify_status", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_provider_profiles_id", "provider_profiles", ["id"])
    op.create_index("ix_provider_profiles_user_id", "provider_profiles", ["user_id"], unique=True)
    op.create_index("ix_provider_profiles_city_id", "provider_profiles", ["city_id"])
    op.create_index("ix_provider_profiles_category_id", "provider_profiles", ["category_id"])
    op.create_index("ix_provider_profiles_district", "provider_profiles", ["district"])

    # ---------- 服务评价 ----------
    op.create_table(
        "service_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("city_id", sa.String(length=10), nullable=True),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=True),
        sa.Column("customer_name", sa.String(length=50), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("images", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["service_orders.id"]),
        sa.ForeignKeyConstraint(["provider_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_service_reviews_id", "service_reviews", ["id"])
    op.create_index("ix_service_reviews_city_id", "service_reviews", ["city_id"])
    op.create_index("ix_service_reviews_order_id", "service_reviews", ["order_id"])
    op.create_index("ix_service_reviews_provider_id", "service_reviews", ["provider_id"])
    op.create_index("ix_service_reviews_customer_id", "service_reviews", ["customer_id"])

    # ---------- 扩展 service_orders ----------
    op.add_column("service_orders", sa.Column("customer_id", sa.Integer(), nullable=True))
    op.add_column("service_orders", sa.Column("category_id", sa.Integer(), nullable=True))
    op.add_column("service_orders", sa.Column("title", sa.String(length=100), nullable=True))
    op.add_column("service_orders", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("service_orders", sa.Column("price", sa.Float(), nullable=True))
    op.add_column("service_orders", sa.Column("address", sa.String(length=255), nullable=True))
    op.add_column("service_orders", sa.Column("contact_phone", sa.String(length=20), nullable=True))
    op.add_column("service_orders", sa.Column("scheduled_at", sa.String(length=50), nullable=True))
    op.add_column("service_orders", sa.Column("updated_at", sa.DateTime(), nullable=True))

    op.create_foreign_key(
        "fk_service_orders_customer_id", "service_orders", "users", ["customer_id"], ["id"]
    )
    op.create_index("ix_service_orders_customer_id", "service_orders", ["customer_id"])
    op.create_index("ix_service_orders_category_id", "service_orders", ["category_id"])
    op.create_index("ix_service_orders_provider_id", "service_orders", ["provider_id"])
    op.create_index("ix_service_orders_status", "service_orders", ["status"])


def downgrade() -> None:
    op.drop_index("ix_service_orders_status", table_name="service_orders")
    op.drop_index("ix_service_orders_provider_id", table_name="service_orders")
    op.drop_index("ix_service_orders_category_id", table_name="service_orders")
    op.drop_index("ix_service_orders_customer_id", table_name="service_orders")
    op.drop_constraint("fk_service_orders_customer_id", "service_orders", type_="foreignkey")

    for col in ("updated_at", "scheduled_at", "contact_phone", "address", "price",
                "description", "title", "category_id", "customer_id"):
        op.drop_column("service_orders", col)

    op.drop_index("ix_service_reviews_customer_id", table_name="service_reviews")
    op.drop_index("ix_service_reviews_provider_id", table_name="service_reviews")
    op.drop_index("ix_service_reviews_order_id", table_name="service_reviews")
    op.drop_index("ix_service_reviews_city_id", table_name="service_reviews")
    op.drop_index("ix_service_reviews_id", table_name="service_reviews")
    op.drop_table("service_reviews")

    op.drop_index("ix_provider_profiles_district", table_name="provider_profiles")
    op.drop_index("ix_provider_profiles_category_id", table_name="provider_profiles")
    op.drop_index("ix_provider_profiles_city_id", table_name="provider_profiles")
    op.drop_index("ix_provider_profiles_user_id", table_name="provider_profiles")
    op.drop_index("ix_provider_profiles_id", table_name="provider_profiles")
    op.drop_table("provider_profiles")

    op.drop_index("ix_service_categories_status", table_name="service_categories")
    op.drop_index("ix_service_categories_city_id", table_name="service_categories")
    op.drop_index("ix_service_categories_id", table_name="service_categories")
    op.drop_table("service_categories")
