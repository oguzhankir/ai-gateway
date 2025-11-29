"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable TimescaleDB extension
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('username', sa.String(255), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_users_username', 'users', ['username'])

    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('key_hash', sa.String(255), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'])
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('ix_api_keys_is_active', 'api_keys', ['is_active'])

    # Create request_logs table
    # Note: Primary key includes request_timestamp for TimescaleDB hypertable compatibility
    op.create_table(
        'request_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_timestamp', sa.DateTime(), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('messages', postgresql.JSONB(), nullable=True),
        sa.Column('max_tokens', sa.Integer(), nullable=True),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('completion', sa.Text(), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('completion_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('total_tokens', sa.Integer(), nullable=False, default=0),
        sa.Column('cost_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('cache_hit', sa.Boolean(), nullable=False, default=False),
        sa.Column('pii_detected', sa.Boolean(), nullable=False, default=False),
        sa.Column('pii_entities', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='completed'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('guardrail_violations', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id', 'request_timestamp'),  # Composite PK for TimescaleDB
    )
    # Create basic indexes first (without unique constraints)
    op.create_index('ix_request_logs_user_id', 'request_logs', ['user_id'])
    op.create_index('ix_request_logs_provider', 'request_logs', ['provider'])
    op.create_index('ix_request_logs_created_at', 'request_logs', ['created_at'])

    # Convert request_logs to hypertable (TimescaleDB)
    # Note: Primary key includes partitioning column (id, request_timestamp)
    op.execute("SELECT create_hypertable('request_logs', 'request_timestamp', if_not_exists => TRUE);")

    # Create indexes on partitioning column after hypertable creation
    op.create_index('ix_request_logs_request_timestamp', 'request_logs', ['request_timestamp'])
    op.create_index('idx_user_timestamp', 'request_logs', ['user_id', 'request_timestamp'])
    op.create_index('idx_provider_timestamp', 'request_logs', ['provider', 'request_timestamp'])
    # Note: Cannot create unique index on id alone in TimescaleDB hypertable
    # Primary key (id, request_timestamp) ensures uniqueness
    # Foreign keys to request_logs.id are handled at application level

    # Create budgets table
    op.create_table(
        'budgets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column('limit', sa.Float(), nullable=False),
        sa.Column('period', sa.String(20), nullable=False),
        sa.Column('current_spend', sa.Float(), nullable=False, default=0.0),
        sa.Column('reset_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('ix_budgets_user_id', 'budgets', ['user_id'])

    # Create webhooks table
    op.create_table(
        'webhooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('events', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('secret', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('ix_webhooks_user_id', 'webhooks', ['user_id'])
    op.create_index('ix_webhooks_is_active', 'webhooks', ['is_active'])

    # Create guardrail_logs table
    op.create_table(
        'guardrail_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('request_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rule_name', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        # Note: request_id foreign key removed due to composite primary key in request_logs
        # Application should handle referential integrity
    )
    op.create_index('ix_guardrail_logs_user_id', 'guardrail_logs', ['user_id'])
    op.create_index('ix_guardrail_logs_request_id', 'guardrail_logs', ['request_id'])
    op.create_index('ix_guardrail_logs_rule_name', 'guardrail_logs', ['rule_name'])
    op.create_index('ix_guardrail_logs_timestamp', 'guardrail_logs', ['timestamp'])


def downgrade() -> None:
    op.drop_table('guardrail_logs')
    op.drop_table('webhooks')
    op.drop_table('budgets')
    op.execute("SELECT drop_hypertable('request_logs', if_exists => TRUE);")
    op.drop_table('request_logs')
    op.drop_table('api_keys')
    op.drop_table('users')
    op.execute("DROP EXTENSION IF EXISTS timescaledb;")

