"""add column for users

Revision ID: 3f0e93b9529d
Revises: 1d2e644c8fd2
Create Date: 2026-11-07 00:01:04.086497

"""
import datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '3f0e93b9529d'
down_revision: Union[str, Sequence[str], None] = '1d2e644c8fd2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

JST = datetime.timezone(datetime.timedelta(hours=9))
jst_now = datetime.datetime.now(JST).replace(tzinfo=None)

def upgrade() -> None:
    """Upgrade schema."""
    # usersテーブルに対してバッチモードを適用
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True, default=jst_now))
        batch_op.create_unique_constraint('uq_users_email', ['email'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_constraint('uq_users_email', type_='unique')
        batch_op.drop_column('updated_at')
