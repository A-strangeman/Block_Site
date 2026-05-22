"""Initial schema migration applying backend/sql/schema.sql
Revision ID: 0001_initial
Revises: None
Create Date: 2026-05-22
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Apply the raw SQL schema from the repository
    sql_path = __file__.rsplit("/alembic/", 1)[0] + "/sql/schema.sql"
    try:
        with open(sql_path, "r", encoding="utf-8") as f:
            sql = f.read()
    except Exception:
        # Fallback: try windows-style path separator
        sql_path = __file__.rsplit("\\alembic\\", 1)[0] + "\\sql\\schema.sql"
        with open(sql_path, "r", encoding="utf-8") as f:
            sql = f.read()

    op.execute(sql)


def downgrade() -> None:
    # Downgrade not implemented for the initial migration.
    pass
