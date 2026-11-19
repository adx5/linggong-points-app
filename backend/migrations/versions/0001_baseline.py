"""baseline: 按当前 models.py 创建全部表

Revision ID: 0001
Revises:
Create Date: 2026-11-19

⚠️ 说明（基线策略）
本项目的既有表结构是历史上由 `Base.metadata.create_all` 建出来的，没有版本记录。
为了让 Alembic 能接管，这条基线以「当前 models.py 为准」建全量表，用于全新环境从零搭建。

已经存在表结构的环境（Staging / 生产）**不要执行 upgrade**，而是直接打标：
    alembic stamp 0001
之后再按 0002、0003… 正常升级。

这条基线的已知代价：它引用的是"当前"的 models.py，如果将来 models 继续演进，
从零重放基线得到的是新结构，而不是当时的结构。这是接管既有库的常见折中；
若后续需要严格可重放，可把本文件替换为显式 op.create_table 快照。
"""
from alembic import op

from database import Base
import models  # noqa: F401  确保 metadata 完整

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
