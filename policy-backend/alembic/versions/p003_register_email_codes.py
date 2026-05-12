"""register_email_codes for signup verification

Revision ID: p003_register_codes
Revises: p002_email
Create Date: 2026-05-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "p003_register_codes"
down_revision: Union[str, Sequence[str], None] = "p002_email"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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


def downgrade() -> None:
    op.drop_index(op.f("ix_register_email_codes_email"), table_name="register_email_codes")
    op.drop_table("register_email_codes")
