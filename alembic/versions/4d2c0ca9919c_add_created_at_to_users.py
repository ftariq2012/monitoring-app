"""add created_at to users

Revision ID: 4d2c0ca9919c
Revises: 883dc6540d51
Create Date: 2026-10-09 16:06:22.272137

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4d2c0ca9919c'
down_revision: Union[str, Sequence[str], None] = '883dc6540d51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "created_at")
