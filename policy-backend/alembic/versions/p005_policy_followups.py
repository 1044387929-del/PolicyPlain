"""policy_followups for explanation Q&A rounds

Revision ID: p005_policy_followups
Revises: p004_redis_register
Create Date: 2026-05-13

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "p005_policy_followups"
down_revision: Union[str, Sequence[str], None] = "p004_redis_register"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "policy_followups",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("explanation_id", sa.String(length=36), nullable=False),
        sa.Column("turn_index", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["explanation_id"],
            ["policy_explanations.id"],
            name=op.f("fk_policy_followups_explanation_id_policy_explanations"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_policy_followups")),
        sa.UniqueConstraint(
            "explanation_id",
            "turn_index",
            name=op.f("uq_policy_followups_explanation_turn"),
        ),
    )
    op.create_index(
        op.f("ix_policy_followups_explanation_id"),
        "policy_followups",
        ["explanation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_policy_followups_explanation_id"), table_name="policy_followups")
    op.drop_table("policy_followups")
