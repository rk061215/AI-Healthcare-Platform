"""add_appointments_duration_minutes

Revision ID: 535719eb642f
Revises: 0006
Create Date: 2026-08-14 00:58:58.600461

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '535719eb642f'
down_revision: Union[str, None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('appointments', sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='30'))

def downgrade() -> None:
    op.drop_column('appointments', 'duration_minutes')
