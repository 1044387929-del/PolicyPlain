"""users: email instead of username (login identifier)

Revision ID: p002_email
Revises: p001_initial
Create Date: 2026-05-12

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "p002_email"
down_revision: Union[str, Sequence[str], None] = "p001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE users SET email = CASE
                WHEN strpos(username, '@') > 0 THEN lower(username)
                ELSE lower(username) || '@migrated.policyplain'
            END
            WHERE email IS NULL
            """
        )
    )
    op.alter_column("users", "email", existing_type=sa.String(length=255), nullable=False)
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_column("users", "username")
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)


def downgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(length=64), nullable=True))
    op.execute(sa.text("UPDATE users SET username = substring(replace(id::text, '-', '') from 1 for 32)"))
    op.alter_column("users", "username", existing_type=sa.String(length=64), nullable=False)
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_column("users", "email")
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
