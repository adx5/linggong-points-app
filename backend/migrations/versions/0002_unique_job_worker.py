"""防重复投递：job_applications(job_id, worker_id) 唯一约束

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-19

原实现仅靠应用层 SELECT 查重，并尝试捕获一个永远不会触发的 duplicate key，
并发请求下会产生重复投递。这里落成数据库级约束。
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_job_worker", "job_applications", ["job_id", "worker_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_job_worker", "job_applications", type_="unique")
