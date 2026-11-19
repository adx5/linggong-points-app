"""收敛 schema：补齐 models 声明但库中缺失的索引/约束/外键

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-19

背景
----
`alembic check` 暴露出历史遗留的严重漂移——根因是应用一直用
`Base.metadata.create_all` 建表：它**只建缺失的表，从不给已存在的表补索引/约束**。
于是 models.py 里写了大量 `index=True` / `UniqueConstraint`，库里从来没有过。

本迁移把库补齐到 models.py 声明的状态（含数据去重），使 `alembic check` 归零。

关键修复
--------
`point_transactions` 的 `uq_biz_ref`(biz_type, ref_no) 一直不存在，
导致定时任务「靠唯一键冲突做幂等」的逻辑形同虚设，
`ad_reward/fallback_6` 已实际发生 3 次重复发放。
"""
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---------------------------------------------------------------
    # 0. 先清理重复流水，否则 uq_biz_ref 加不上。
    #    规则：同一 (biz_type, ref_no) 只保留 id 最小的一条。
    # ---------------------------------------------------------------
    op.execute("""
        DELETE FROM point_transactions a
        USING point_transactions b
        WHERE a.biz_type = b.biz_type
          AND a.ref_no = b.ref_no
          AND a.id > b.id
    """)

    # ---------------------------------------------------------------
    # 1. 补齐 models 声明但库中缺失的普通索引
    # ---------------------------------------------------------------
    op.create_index("ix_application_logs_city_id", "application_logs", ["city_id"])
    op.create_index("ix_application_logs_id", "application_logs", ["id"])
    op.create_index("ix_audit_logs_city_id", "audit_logs", ["city_id"])

    op.create_index("ix_cooperation_entities_city_id", "cooperation_entities", ["city_id"])
    op.create_index("ix_cooperation_entities_id", "cooperation_entities", ["id"])
    op.create_index("ix_cooperation_entities_name", "cooperation_entities", ["name"])
    op.create_index("ix_cooperation_entities_type", "cooperation_entities", ["type"])

    op.create_index("ix_entity_certificates_city_id", "entity_certificates", ["city_id"])
    op.create_index("ix_interviews_city_id", "interviews", ["city_id"])
    op.create_index("ix_job_applications_business_city_id", "job_applications", ["business_city_id"])

    op.create_index("ix_notifications_city_id", "notifications", ["city_id"])
    op.create_index("ix_notifications_id", "notifications", ["id"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    op.create_index("ix_reviews_city_id", "reviews", ["city_id"])
    op.create_index("ix_reviews_id", "reviews", ["id"])
    op.create_index("ix_users_role", "users", ["role"])

    # ---------------------------------------------------------------
    # 2. file_no：库里是唯一约束，模型声明的是「唯一索引」，统一为后者
    # ---------------------------------------------------------------
    op.drop_constraint("cooperation_entities_file_no_key", "cooperation_entities", type_="unique")
    op.create_index("ix_cooperation_entities_file_no", "cooperation_entities", ["file_no"], unique=True)

    # ---------------------------------------------------------------
    # 3. point_transactions：补唯一约束（幂等键），移除多余的单列索引
    # ---------------------------------------------------------------
    op.drop_index("ix_point_transactions_biz_type", table_name="point_transactions")
    op.create_unique_constraint("uq_biz_ref", "point_transactions", ["biz_type", "ref_no"])

    # ---------------------------------------------------------------
    # 4. entity_certificates：补外键（库中从未创建过该外键）
    # ---------------------------------------------------------------
    op.create_foreign_key(
        "fk_entity_certificates_entity_id",
        "entity_certificates", "cooperation_entities",
        ["entity_id"], ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_entity_certificates_entity_id", "entity_certificates", type_="foreignkey")

    op.drop_constraint("uq_biz_ref", "point_transactions", type_="unique")
    op.create_index("ix_point_transactions_biz_type", "point_transactions", ["biz_type"])

    op.drop_index("ix_cooperation_entities_file_no", table_name="cooperation_entities")
    op.create_unique_constraint(
        "cooperation_entities_file_no_key", "cooperation_entities", ["file_no"]
    )

    for name, table in [
        ("ix_users_role", "users"),
        ("ix_reviews_id", "reviews"),
        ("ix_reviews_city_id", "reviews"),
        ("ix_notifications_user_id", "notifications"),
        ("ix_notifications_id", "notifications"),
        ("ix_notifications_city_id", "notifications"),
        ("ix_job_applications_business_city_id", "job_applications"),
        ("ix_interviews_city_id", "interviews"),
        ("ix_entity_certificates_city_id", "entity_certificates"),
        ("ix_cooperation_entities_type", "cooperation_entities"),
        ("ix_cooperation_entities_name", "cooperation_entities"),
        ("ix_cooperation_entities_id", "cooperation_entities"),
        ("ix_cooperation_entities_city_id", "cooperation_entities"),
        ("ix_audit_logs_city_id", "audit_logs"),
        ("ix_application_logs_id", "application_logs"),
        ("ix_application_logs_city_id", "application_logs"),
    ]:
        op.drop_index(name, table_name=table)
