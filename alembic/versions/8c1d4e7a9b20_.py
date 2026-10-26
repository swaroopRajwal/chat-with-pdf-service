"""add chats.title

Revision ID: 8c1d4e7a9b20
Revises: f574c8ce1cb0
Create Date: 2026-10-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c1d4e7a9b20'
down_revision: Union[str, Sequence[str], None] = 'f574c8ce1cb0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('chats', sa.Column('title', sa.String(), nullable=True))

    # Backfill from each chat's first message, same rules as app.utils.make_chat_title
    op.execute(
        r"""
        UPDATE chats SET title = COALESCE((
            SELECT CASE
                WHEN char_length(c.t) > 60 THEN rtrim(left(c.t, 60)) || '…'
                ELSE c.t
            END
            FROM (
                SELECT NULLIF(btrim(regexp_replace(m.content, '\s+', ' ', 'g')), '') AS t
                FROM messages m
                WHERE m.chat_id = chats.id
                ORDER BY m."order" ASC
                LIMIT 1
            ) c
        ), 'Untitled chat')
        """
    )

    op.alter_column('chats', 'title', nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('chats', 'title')
