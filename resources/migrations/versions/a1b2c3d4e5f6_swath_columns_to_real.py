"""swath columns to real

Revision ID: a1b2c3d4e5f6
Revises: 270e53247037
Create Date: 2026-06-05 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '270e53247037'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("series_string") as batch_op:
        batch_op.alter_column("swath_adjusted", type_=sa.Float)
    with op.batch_alter_table("series_spray_card") as batch_op:
        batch_op.alter_column("swath_adjusted", type_=sa.Float)
    with op.batch_alter_table("spray_system") as batch_op:
        batch_op.alter_column("swath", type_=sa.Float)


def downgrade():
    pass
