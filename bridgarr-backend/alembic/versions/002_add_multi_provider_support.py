"""add multi-provider support

Revision ID: 002
Revises:
Create Date: 2025-10-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = None  # This is the first migration
branch_labels = None
depends_on = None


def upgrade():
    # Create enum type for debrid providers
    debrid_provider_enum = postgresql.ENUM(
        'real-debrid', 'alldebrid', 'premiumize', 'debrid-link',
        name='debridprovider',
        create_type=True
    )
    debrid_provider_enum.create(op.get_bind(), checkfirst=True)

    # Add new columns
    op.add_column('users', sa.Column(
        'debrid_provider',
        sa.Enum('real-debrid', 'alldebrid', 'premiumize', 'debrid-link', name='debridprovider'),
        nullable=False,
        server_default='real-debrid'
    ))
    op.add_column('users', sa.Column('debrid_api_token', sa.String(500), nullable=True))
    op.add_column('users', sa.Column('debrid_token_expires_at', sa.DateTime(timezone=True), nullable=True))

    # Migrate existing rd_api_token data to new debrid_api_token column
    op.execute("""
        UPDATE users 
        SET debrid_api_token = rd_api_token,
            debrid_token_expires_at = rd_token_expires_at,
            debrid_provider = 'real-debrid'
        WHERE rd_api_token IS NOT NULL
    """)


def downgrade():
    # Remove new columns
    op.drop_column('users', 'debrid_token_expires_at')
    op.drop_column('users', 'debrid_api_token')
    op.drop_column('users', 'debrid_provider')

    # Drop enum type
    op.execute('DROP TYPE IF EXISTS debridprovider')
