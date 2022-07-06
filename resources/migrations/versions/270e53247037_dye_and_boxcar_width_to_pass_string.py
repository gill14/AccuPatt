"""dye and boxcar_width to pass_string

Revision ID: 270e53247037
Revises: 7444c2307883
Create Date: 2022-07-06 09:27:40.310271

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '270e53247037'
down_revision = '7444c2307883'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("pass_string", sa.Column("dye", sa.String))
    op.add_column("pass_string", sa.Column("boxcar_width", sa.Integer))
    # Migrate
    conn = op.get_bind()
    conn.execute(
        """UPDATE pass_string SET dye = ?, boxcar_width = ?""",
        ("Rhodamine WT", 0)
    )


def downgrade():
    pass
