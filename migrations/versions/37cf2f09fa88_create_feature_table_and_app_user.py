"""create feature table and app user

Revision ID: 37cf2f09fa88
Revises: 
Create Date: 2026-06-07 14:20:20.781530

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import os


# revision identifiers, used by Alembic.
revision: str = '37cf2f09fa88'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create feature table
    op.create_table(
        'feature',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('zone', sa.String(), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('price', sa.Float(), nullable=True),
        sa.Column('quantity', sa.Float(), nullable=True),
        sa.Column('fdir', sa.Float(), nullable=True),
        sa.Column('ssrd', sa.Float(), nullable=True),
        sa.Column('temperature_2m', sa.Float(), nullable=True),
        sa.Column('wind_u_10m', sa.Float(), nullable=True),
        sa.Column('wind_v_10m', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('zone', 'timestamp', name='uq_feature_zone_timestamp')
    )

    # Create app user
    app_db_user = os.environ["APP_DB_USER"]
    app_db_password = os.environ["APP_DB_PASSWORD"]
    db_name = os.environ["DB_NAME"]

    op.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{app_db_user}') THEN
                CREATE USER {app_db_user} WITH PASSWORD '{app_db_password}';
                GRANT CONNECT ON DATABASE {db_name} TO {app_db_user};
                GRANT USAGE, CREATE ON SCHEMA public TO {app_db_user};
                GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO {app_db_user};
                GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {app_db_user};
                ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE ON TABLES TO {app_db_user};
                ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO {app_db_user};
            END IF;
        END
        $$;
    """)


def downgrade() -> None:
    op.drop_table('feature')