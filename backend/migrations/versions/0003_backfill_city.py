"""数据回填：users / cooperation_entities / jobs / point_transactions 的 city_id

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-19

背景：单城改造后，历史数据存在 city_id 为空的情况——
  · 用户空城市 → 发岗 city_id 为空 → C 端列表永远查不到
  · 积分流水空城市 → 按城市对账失真
策略：用户/企业先补默认城市（取自 global_configs，不硬编码），
      岗位与流水再按所属用户城市精确回填。
全部语句幂等（只处理 NULL 行）。
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        UPDATE users
        SET city_id = (SELECT value FROM global_configs WHERE key = 'DEFAULT_CITY_ID')
        WHERE city_id IS NULL
          AND EXISTS (SELECT 1 FROM global_configs WHERE key = 'DEFAULT_CITY_ID')
    """)

    op.execute("""
        UPDATE cooperation_entities
        SET city_id = (SELECT value FROM global_configs WHERE key = 'DEFAULT_CITY_ID')
        WHERE city_id IS NULL
          AND EXISTS (SELECT 1 FROM global_configs WHERE key = 'DEFAULT_CITY_ID')
    """)

    op.execute("""
        UPDATE jobs j
        SET city_id = u.city_id
        FROM users u
        WHERE j.merchant_id = u.id
          AND j.city_id IS NULL
          AND u.city_id IS NOT NULL
    """)

    op.execute("""
        UPDATE point_transactions pt
        SET city_id = u.city_id
        FROM users u
        WHERE pt.user_id = u.id
          AND pt.city_id IS NULL
          AND u.city_id IS NOT NULL
    """)


def downgrade() -> None:
    # 数据回填不可逆（无法区分原始 NULL 与回填值），故不提供回滚
    pass
