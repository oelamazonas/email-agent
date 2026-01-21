"""
Tests for email actions module.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from api.models import Email, EmailAccount, EmailCategory, ProcessingStatus, AccountType
from worker.actions import (
    apply_classification_action,
    bulk_move_emails,
    apply_label,
    bulk_classify_pending_emails
)


@pytest.fixture
def mock_email():
    """Create a mock email for testing."""
    return Email(
        id=1,
        account_id=1,
        message_id="test@example.com",
        subject="Test Invoice",
        sender="sender@example.com",
        date_received=datetime.utcnow(),
        body_preview="This is a test invoice for 100€",
        has_attachments=True,
        status=ProcessingStatus.PENDING,
        category=EmailCategory.UNKNOWN
    )


@pytest.fixture
def mock_account():
    """Create a mock email account for testing."""
    return EmailAccount(
        id=1,
        user_id=1,
        account_type=AccountType.IMAP,
        email_address="test@example.com",
        encrypted_credentials="encrypted_test_credentials",
        is_active=True
    )


@pytest.mark.asyncio
async def test_apply_classification_action_with_rule_match(mock_email, mock_account):
    """Test applying classification action when rule matches."""
    with patch('worker.actions.email_actions.get_db_context') as mock_db, \
         patch('worker.actions.email_actions.rules_parser') as mock_rules, \
         patch('worker.actions.email_actions._get_connector_for_account') as mock_connector:

        # Setup mocks
        mock_db_session = AsyncMock()
        mock_db_session.get = AsyncMock(side_effect=lambda model, id: mock_email if model == Email else mock_account)
        mock_db_session.commit = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db.__aexit__ = AsyncMock()

        # Mock rule match
        mock_rule = Mock()
        mock_rule.name = "Invoice by subject"
        mock_rule.category = EmailCategory.INVOICE
        mock_rule.folder = "Finance/Invoices"
        mock_rule.auto_delete = False
        mock_rules.find_matching_rule.return_value = mock_rule

        # Mock connector
        mock_conn = Mock()
        mock_conn.connect = Mock()
        mock_conn.disconnect = Mock()
        mock_conn.move_email = Mock(return_value=True)
        mock_connector.return_value = mock_conn

        # Execute
        result = await apply_classification_action(
            email_id=1,
            category=EmailCategory.INVOICE,
            confidence=95,
            rule_matched="Invoice by subject"
        )

        # Assertions
        assert result['status'] == 'success'
        assert 'moved_to:Finance/Invoices' in result['actions_taken']
        mock_conn.move_email.assert_called_once()


@pytest.mark.asyncio
async def test_apply_classification_action_auto_delete_spam(mock_email, mock_account):
    """Test auto-deletion of spam emails."""
    mock_email.category = EmailCategory.SPAM

    with patch('worker.actions.email_actions.get_db_context') as mock_db, \
         patch('worker.actions.email_actions.rules_parser') as mock_rules, \
         patch('worker.actions.email_actions._get_connector_for_account') as mock_connector:

        # Setup mocks
        mock_db_session = AsyncMock()
        mock_db_session.get = AsyncMock(side_effect=lambda model, id: mock_email if model == Email else mock_account)
        mock_db_session.commit = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db.__aexit__ = AsyncMock()

        # Mock rule with auto_delete
        mock_rule = Mock()
        mock_rule.name = "Obvious spam"
        mock_rule.category = EmailCategory.SPAM
        mock_rule.folder = None
        mock_rule.auto_delete = True
        mock_rules.find_matching_rule.return_value = mock_rule

        # Mock connector
        mock_conn = Mock()
        mock_conn.connect = Mock()
        mock_conn.disconnect = Mock()
        mock_conn.delete_email = Mock(return_value=True)
        mock_connector.return_value = mock_conn

        # Execute
        result = await apply_classification_action(
            email_id=1,
            category=EmailCategory.SPAM,
            confidence=99,
            rule_matched="Obvious spam"
        )

        # Assertions
        assert result['status'] == 'success'
        assert 'deleted' in result['actions_taken']
        mock_conn.delete_email.assert_called_once()


@pytest.mark.asyncio
async def test_bulk_move_emails_success():
    """Test successful bulk move of emails."""
    email_ids = [1, 2, 3]
    target_folder = "Archive"

    with patch('worker.actions.email_actions.get_db_context') as mock_db, \
         patch('worker.actions.email_actions._get_connector_for_account') as mock_connector:

        # Setup mock emails and account
        mock_emails = []
        for i in email_ids:
            email = Mock()
            email.id = i
            email.message_id = f"msg_{i}"
            email.account_id = 1
            mock_emails.append(email)

        mock_account = Mock()
        mock_account.id = 1
        mock_account.account_type = AccountType.IMAP

        # Setup DB mock
        mock_db_session = AsyncMock()
        call_count = [0]

        def get_side_effect(model, id):
            if model == Email:
                return mock_emails[call_count[0]]
            else:
                return mock_account

        mock_db_session.get = AsyncMock(side_effect=get_side_effect)
        mock_db_session.commit = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db.__aexit__ = AsyncMock()

        # Mock connector
        mock_conn = Mock()
        mock_conn.connect = Mock()
        mock_conn.disconnect = Mock()
        mock_conn.move_email = Mock(return_value=True)
        mock_connector.return_value = mock_conn

        # Execute
        result = await bulk_move_emails(email_ids, target_folder)

        # Assertions
        assert result['status'] == 'success'
        assert len(result['succeeded']) == 3
        assert len(result['failed']) == 0
        assert result['total'] == 3


@pytest.mark.asyncio
async def test_bulk_move_emails_partial_failure():
    """Test bulk move with some failures."""
    email_ids = [1, 2, 3]
    target_folder = "Archive"

    with patch('worker.actions.email_actions.get_db_context') as mock_db, \
         patch('worker.actions.email_actions._get_connector_for_account') as mock_connector:

        # Setup mock emails
        mock_emails = []
        for i in email_ids:
            email = Mock()
            email.id = i
            email.message_id = f"msg_{i}"
            email.account_id = 1
            mock_emails.append(email)

        mock_account = Mock()
        mock_account.id = 1

        call_count = [0]

        def get_side_effect(model, id):
            result = mock_emails[call_count[0]] if model == Email else mock_account
            call_count[0] += 1
            return result

        mock_db_session = AsyncMock()
        mock_db_session.get = AsyncMock(side_effect=get_side_effect)
        mock_db_session.commit = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db.__aexit__ = AsyncMock()

        # Mock connector - fails on second email
        mock_conn = Mock()
        mock_conn.connect = Mock()
        mock_conn.disconnect = Mock()
        move_count = [0]

        def move_side_effect(*args):
            move_count[0] += 1
            return move_count[0] != 2  # Fail on second call

        mock_conn.move_email = Mock(side_effect=move_side_effect)
        mock_connector.return_value = mock_conn

        # Execute
        result = await bulk_move_emails(email_ids, target_folder)

        # Assertions
        assert result['status'] == 'partial'
        assert len(result['succeeded']) == 2
        assert len(result['failed']) == 1
        assert result['total'] == 3


@pytest.mark.asyncio
async def test_apply_label_gmail_only():
    """Test that labels only work for Gmail accounts."""
    mock_email = Mock()
    mock_email.id = 1
    mock_email.account_id = 1

    # Test with non-Gmail account
    mock_account = Mock()
    mock_account.id = 1
    mock_account.account_type = AccountType.IMAP

    with patch('worker.actions.email_actions.get_db_context') as mock_db:
        mock_db_session = AsyncMock()
        mock_db_session.get = AsyncMock(side_effect=lambda model, id: mock_email if model == Email else mock_account)
        mock_db.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db.__aexit__ = AsyncMock()

        # Execute
        result = await apply_label(email_id=1, label="Important")

        # Should fail for non-Gmail
        assert result['status'] == 'error'
        assert 'only supported for Gmail' in result['error']


@pytest.mark.asyncio
async def test_apply_label_gmail_success():
    """Test successful label application for Gmail."""
    mock_email = Mock()
    mock_email.id = 1
    mock_email.account_id = 1
    mock_email.message_id = "gmail_msg_123"

    mock_account = Mock()
    mock_account.id = 1
    mock_account.account_type = AccountType.GMAIL

    with patch('worker.actions.email_actions.get_db_context') as mock_db, \
         patch('worker.actions.email_actions._get_connector_for_account') as mock_connector:

        # Setup DB mock
        mock_db_session = AsyncMock()
        mock_db_session.get = AsyncMock(side_effect=lambda model, id: mock_email if model == Email else mock_account)
        mock_db_session.commit = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db.__aexit__ = AsyncMock()

        # Mock Gmail connector with apply_label method
        mock_conn = Mock()
        mock_conn.connect = Mock()
        mock_conn.disconnect = Mock()
        mock_conn.apply_label = Mock(return_value=True)
        mock_connector.return_value = mock_conn

        # Execute
        result = await apply_label(email_id=1, label="Important")

        # Assertions
        assert result['status'] == 'success'
        assert result['label'] == 'Important'
        mock_conn.apply_label.assert_called_once_with("gmail_msg_123", "Important")


def test_get_default_folder_for_category():
    """Test default folder mapping for categories."""
    from worker.actions.email_actions import _get_default_folder_for_category

    assert _get_default_folder_for_category(EmailCategory.INVOICE) == "Finance/Invoices"
    assert _get_default_folder_for_category(EmailCategory.RECEIPT) == "Finance/Receipts"
    assert _get_default_folder_for_category(EmailCategory.NEWSLETTER) == "Newsletters"
    assert _get_default_folder_for_category(EmailCategory.PROMOTION) == "Promotions"
    assert _get_default_folder_for_category(EmailCategory.PROFESSIONAL) is None
    assert _get_default_folder_for_category(EmailCategory.SPAM) is None


@pytest.mark.asyncio
async def test_bulk_classify_pending_emails():
    """Test bulk classification of pending emails."""
    with patch('worker.actions.email_actions.get_db_context') as mock_db, \
         patch('worker.actions.email_actions.rules_parser') as mock_rules, \
         patch('worker.actions.email_actions.classifier') as mock_classifier, \
         patch('worker.actions.email_actions.apply_classification_action') as mock_apply:

        # Setup mock emails
        mock_email1 = Mock(spec=Email)
        mock_email1.id = 1
        mock_email1.subject = "Invoice #123"
        mock_email1.sender = "billing@company.com"
        mock_email1.body_preview = "Invoice for services"
        mock_email1.has_attachments = True

        mock_email2 = Mock(spec=Email)
        mock_email2.id = 2
        mock_email2.subject = "Newsletter"
        mock_email2.sender = "news@company.com"
        mock_email2.body_preview = "Weekly newsletter"
        mock_email2.has_attachments = False

        # Setup DB mock
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_email1, mock_email2]

        mock_db_session = AsyncMock()
        mock_db_session.execute = AsyncMock(return_value=mock_result)
        mock_db_session.commit = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db_session)
        mock_db.__aexit__ = AsyncMock()

        # Mock rule matching - first email matches rule
        mock_rule = Mock()
        mock_rule.name = "Invoice by subject"
        mock_rule.category = EmailCategory.INVOICE

        mock_rules.find_matching_rule.side_effect = [mock_rule, None]

        # Mock LLM classification for second email
        mock_classifier.classify_email = AsyncMock(return_value={
            'category': EmailCategory.NEWSLETTER,
            'confidence': 85,
            'reason': 'Newsletter pattern detected'
        })

        # Mock action application
        mock_apply.return_value = {'status': 'success'}

        # Execute
        result = await bulk_classify_pending_emails(limit=100)

        # Assertions
        assert result['status'] == 'success'
        assert result['processed'] == 2
        assert result['classified'] == 2
        assert result['errors'] == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
