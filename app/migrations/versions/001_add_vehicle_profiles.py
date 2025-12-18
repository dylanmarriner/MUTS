"""Add vehicle profiles table

Revision ID: 001_add_vehicle_profiles
Revises: None
Create Date: 2025-01-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_vehicle_profiles'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create vehicle_profiles table
    op.create_table('vehicle_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('vin', sa.String(length=17), nullable=False),
        sa.Column('plate', sa.String(length=20), nullable=False),
        sa.Column('engine_number', sa.String(length=50), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('make', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=50), nullable=False),
        sa.Column('submodel', sa.String(length=100), nullable=False),
        sa.Column('body', sa.String(length=50), nullable=False),
        sa.Column('displacement', sa.Integer(), nullable=True),
        sa.Column('fuel_type', sa.String(length=20), nullable=True),
        sa.Column('colour', sa.String(length=30), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('constants_preset_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['constants_preset_id'], ['vehicle_constants_presets.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['vin'], ['vehicles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('vin')
    )
    
    # Create indexes
    op.create_index('ix_vehicle_profiles_user_id', 'vehicle_profiles', ['user_id'])
    op.create_index('ix_vehicle_profiles_vin', 'vehicle_profiles', ['vin'], unique=True)


def downgrade():
    # Drop indexes
    op.drop_index('ix_vehicle_profiles_vin', table_name='vehicle_profiles')
    op.drop_index('ix_vehicle_profiles_user_id', table_name='vehicle_profiles')
    
    # Drop table
    op.drop_table('vehicle_profiles')
