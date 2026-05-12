"""initial users and policy_explanations

Revision ID: p001_initial
Revises:
Create Date: 2026-05-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "p001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "policy_explanations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("topic", sa.String(length=32), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=True),
        sa.Column("input_digest", sa.String(length=512), nullable=True),
        sa.Column("result_json", sa.JSON(), nullable=False),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_policy_explanations_user_id_users"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_policy_explanations")),
    )
    op.create_index(
        op.f("ix_policy_explanations_user_id"),
        "policy_explanations",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_policy_explanations_user_id"), table_name="policy_explanations")
    op.drop_table("policy_explanations")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_table("users")
