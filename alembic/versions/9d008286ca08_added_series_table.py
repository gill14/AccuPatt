"""Added adj sw to string and card tables

Revision ID: 9d008286ca08
Revises: 
Create Date: 2022-05-25 15:36:16.428039

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9d008286ca08'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("series_string", sa.Column("swath_adjusted", sa.Integer))
    op.add_column("series_spray_card", sa.Column("swath_adjusted", sa.Integer))
    # Migrate
    conn = op.get_bind()
    result = conn.execute(
       '''SELECT swath_adjusted FROM spray_system'''
    )
    swath_adjusted, = result.fetchone()
    print(swath_adjusted)
    conn.execute(
        """UPDATE series_string SET swath_adjusted=?""",
        (swath_adjusted)
    )
    conn.execute(
        """UPDATE series_spray_card SET swath_adjusted=?""",
        (swath_adjusted)
    )
    op.drop_column(table_name="spray_system", column_name="swath_adjusted")

def downgrade():
    pass
