"""drop register_email_codes (codes moved to Redis)

Revision ID: p004_redis_register
Revises: p003_register_codes
Create Date: 2026-05-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "p004_redis_register"
down_revision: Union[str, Sequence[str], None] = "p003_register_codes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index(op.f("ix_register_email_codes_email"), table_name="register_email_codes")
    op.drop_table("register_email_codes")


def downgrade() -> None:
    op.create_table(
        "register_email_codes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("code_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_register_email_codes")),
    )
    op.create_index(
        op.f("ix_register_email_codes_email"),
        "register_email_codes",
        ["email"],
        unique=True,
    )
