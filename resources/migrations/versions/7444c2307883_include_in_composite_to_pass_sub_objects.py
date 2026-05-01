"""include_in_composite to pass_sub objects

Revision ID: 7444c2307883
Revises: 9d008286ca08
Create Date: 2022-06-10 14:52:55.227163

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '7444c2307883'
down_revision = '9d008286ca08'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("pass_string", sa.Column("include_in_composite", sa.Integer))
    op.add_column("pass_spray_card", sa.Column("include_in_composite", sa.Integer))
     # Migrate
    conn = op.get_bind()
    result = conn.execute(
        text("SELECT id, string_include_in_composite, cards_include_in_composite FROM passes")
    )
    passes = result.fetchall()
    for row in passes:
        conn.execute(
            text("UPDATE pass_string SET include_in_composite = :inc WHERE pass_id = :pid"),
            {"inc": row[1], "pid": row[0]},
        )
        conn.execute(
            text("UPDATE pass_spray_card SET include_in_composite = :inc WHERE pass_id = :pid"),
            {"inc": row[2], "pid": row[0]},
        )
    op.drop_column(table_name="passes", column_name="string_include_in_composite")
    op.drop_column(table_name="passes", column_name="cards_include_in_composite")


def downgrade():
    pass
