"""Initial schema

Revision ID: 001
Revises:
Create Date: 2025-01-20

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
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column('is_admin', sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column('preferences', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create email_accounts table
    op.create_table(
        'email_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('account_type', sa.Enum('GMAIL', 'OUTLOOK', 'IMAP', name='accounttype'), nullable=False),
        sa.Column('email_address', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('encrypted_credentials', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column('last_sync', sa.DateTime(), nullable=True),
        sa.Column('sync_enabled', sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column('total_emails_processed', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_accounts_email_address'), 'email_accounts', ['email_address'], unique=True)

    # Create emails table
    op.create_table(
        'emails',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.String(length=500), nullable=True),
        sa.Column('thread_id', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.String(length=500), nullable=True),
        sa.Column('sender', sa.String(length=255), nullable=True),
        sa.Column('recipients', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('date_received', sa.DateTime(), nullable=True),
        sa.Column('category', sa.Enum('INVOICE', 'RECEIPT', 'DOCUMENT', 'PROFESSIONAL', 'NEWSLETTER',
                                      'PROMOTION', 'SOCIAL', 'NOTIFICATION', 'PERSONAL', 'SPAM', 'UNKNOWN',
                                      name='emailcategory'), nullable=True, server_default='UNKNOWN'),
        sa.Column('classification_confidence', sa.Integer(), nullable=True),
        sa.Column('classification_reason', sa.Text(), nullable=True),
        sa.Column('has_attachments', sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column('attachment_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('attachment_types', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('body_preview', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'CLASSIFIED', 'ARCHIVED', 'DELETED', 'ERROR',
                                    name='processingstatus'), nullable=True, server_default='PENDING'),
        sa.Column('archived_folder', sa.String(length=255), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['account_id'], ['email_accounts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_emails_message_id'), 'emails', ['message_id'], unique=True)
    op.create_index(op.f('ix_emails_sender'), 'emails', ['sender'], unique=False)
    op.create_index(op.f('ix_emails_date_received'), 'emails', ['date_received'], unique=False)
    op.create_index(op.f('ix_emails_category'), 'emails', ['category'], unique=False)
    op.create_index(op.f('ix_emails_status'), 'emails', ['status'], unique=False)
    op.create_index(op.f('ix_emails_created_at'), 'emails', ['created_at'], unique=False)
    # Composite index for common query pattern
    op.create_index('ix_emails_account_date', 'emails', ['account_id', 'date_received'])

    # Create email_attachments table
    op.create_table(
        'email_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=True),
        sa.Column('content_type', sa.String(length=100), nullable=True),
        sa.Column('size_bytes', sa.Integer(), nullable=True),
        sa.Column('is_invoice', sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column('is_receipt', sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('storage_path', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['email_id'], ['emails.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create classification_rules table
    op.create_table(
        'classification_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column('conditions', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('target_category', sa.Enum('INVOICE', 'RECEIPT', 'DOCUMENT', 'PROFESSIONAL', 'NEWSLETTER',
                                             'PROMOTION', 'SOCIAL', 'NOTIFICATION', 'PERSONAL', 'SPAM', 'UNKNOWN',
                                             name='emailcategory'), nullable=False),
        sa.Column('target_folder', sa.String(length=255), nullable=True),
        sa.Column('auto_delete', sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column('match_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create processing_logs table
    op.create_table(
        'processing_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email_id', sa.Integer(), nullable=True),
        sa.Column('level', sa.String(length=20), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('component', sa.String(length=100), nullable=True),
        sa.Column('processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['email_id'], ['emails.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_processing_logs_created_at'), 'processing_logs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_processing_logs_created_at'), table_name='processing_logs')
    op.drop_table('processing_logs')
    op.drop_table('classification_rules')
    op.drop_table('email_attachments')
    op.drop_index('ix_emails_account_date', table_name='emails')
    op.drop_index(op.f('ix_emails_created_at'), table_name='emails')
    op.drop_index(op.f('ix_emails_status'), table_name='emails')
    op.drop_index(op.f('ix_emails_category'), table_name='emails')
    op.drop_index(op.f('ix_emails_date_received'), table_name='emails')
    op.drop_index(op.f('ix_emails_sender'), table_name='emails')
    op.drop_index(op.f('ix_emails_message_id'), table_name='emails')
    op.drop_table('emails')
    op.drop_index(op.f('ix_email_accounts_email_address'), table_name='email_accounts')
    op.drop_table('email_accounts')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    # Drop enums
    sa.Enum(name='accounttype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='emailcategory').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='processingstatus').drop(op.get_bind(), checkfirst=True)
