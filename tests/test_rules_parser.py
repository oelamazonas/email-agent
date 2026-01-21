"""
Tests for classification rules parser.
"""
import pytest
import tempfile
import yaml
from pathlib import Path

from api.models import EmailCategory
from worker.rules import RulesParser, ClassificationRule


@pytest.fixture
def temp_rules_dir():
    """Create a temporary directory for test rules."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_rules_yaml():
    """Sample YAML rules for testing."""
    return """
rules:
  - name: "Invoice by subject"
    priority: 100
    conditions:
      subject_contains: "facture|invoice"
    category: INVOICE
    folder: "Finance/Invoices"

  - name: "LinkedIn notification"
    priority: 60
    conditions:
      sender_contains: "@linkedin.com"
    category: SOCIAL
    folder: "Social/LinkedIn"

  - name: "Spam with attachment"
    priority: 10
    conditions:
      subject_contains: "viagra|casino"
      has_attachments: true
    category: SPAM
    auto_delete: true
"""


def test_classification_rule_matches_simple():
    """Test simple rule matching."""
    rule = ClassificationRule(
        name="Test invoice",
        conditions={"subject_contains": "invoice"},
        category=EmailCategory.INVOICE,
        priority=100
    )

    # Should match
    assert rule.matches({
        'subject': 'Invoice #123',
        'sender': 'billing@company.com',
        'body_preview': 'Payment due',
        'has_attachments': True
    })

    # Should not match
    assert not rule.matches({
        'subject': 'Receipt #456',
        'sender': 'billing@company.com',
        'body_preview': 'Payment received',
        'has_attachments': False
    })


def test_classification_rule_matches_multiple_conditions():
    """Test rule with multiple conditions (AND logic)."""
    rule = ClassificationRule(
        name="Spam with attachment",
        conditions={
            "subject_contains": "casino",
            "has_attachments": True
        },
        category=EmailCategory.SPAM,
        priority=10
    )

    # Both conditions match
    assert rule.matches({
        'subject': 'Win at casino now!',
        'sender': 'spam@example.com',
        'body_preview': 'Click here',
        'has_attachments': True
    })

    # Only one condition matches - should not match
    assert not rule.matches({
        'subject': 'Win at casino now!',
        'sender': 'spam@example.com',
        'body_preview': 'Click here',
        'has_attachments': False
    })


def test_classification_rule_matches_or_pattern():
    """Test rule with OR pattern (pipe-separated)."""
    rule = ClassificationRule(
        name="Invoice multi-lang",
        conditions={"subject_contains": "invoice|facture|factuur"},
        category=EmailCategory.INVOICE,
        priority=100
    )

    # Match first pattern
    assert rule.matches({
        'subject': 'Invoice #123',
        'sender': 'billing@company.com',
        'body_preview': '',
        'has_attachments': False
    })

    # Match second pattern
    assert rule.matches({
        'subject': 'Facture #456',
        'sender': 'billing@company.com',
        'body_preview': '',
        'has_attachments': False
    })

    # Match third pattern
    assert rule.matches({
        'subject': 'Factuur #789',
        'sender': 'billing@company.com',
        'body_preview': '',
        'has_attachments': False
    })

    # No match
    assert not rule.matches({
        'subject': 'Receipt #999',
        'sender': 'billing@company.com',
        'body_preview': '',
        'has_attachments': False
    })


def test_classification_rule_sender_conditions():
    """Test sender-based conditions."""
    rule = ClassificationRule(
        name="LinkedIn",
        conditions={"sender_contains": "@linkedin.com"},
        category=EmailCategory.SOCIAL,
        priority=60
    )

    # Match
    assert rule.matches({
        'subject': 'New connection request',
        'sender': 'notifications@linkedin.com',
        'body_preview': 'John wants to connect',
        'has_attachments': False
    })

    # No match
    assert not rule.matches({
        'subject': 'New connection request',
        'sender': 'notifications@facebook.com',
        'body_preview': 'Friend request',
        'has_attachments': False
    })


def test_classification_rule_attachment_name():
    """Test attachment name condition."""
    rule = ClassificationRule(
        name="Invoice by attachment",
        conditions={"attachment_name_contains": "invoice"},
        category=EmailCategory.INVOICE,
        priority=100
    )

    # Match
    assert rule.matches({
        'subject': 'Document attached',
        'sender': 'billing@company.com',
        'body_preview': 'See attached',
        'has_attachments': True,
        'attachment_names': ['invoice_2025_01.pdf', 'terms.pdf']
    })

    # No match - no invoice attachment
    assert not rule.matches({
        'subject': 'Document attached',
        'sender': 'billing@company.com',
        'body_preview': 'See attached',
        'has_attachments': True,
        'attachment_names': ['report.pdf', 'terms.pdf']
    })

    # No match - no attachments
    assert not rule.matches({
        'subject': 'Document attached',
        'sender': 'billing@company.com',
        'body_preview': 'See attached',
        'has_attachments': False,
        'attachment_names': []
    })


def test_rules_parser_load_rules(temp_rules_dir, sample_rules_yaml):
    """Test loading rules from YAML file."""
    # Write sample rules to file
    rules_file = Path(temp_rules_dir) / "global_rules.yaml"
    with open(rules_file, 'w') as f:
        f.write(sample_rules_yaml)

    # Load rules
    parser = RulesParser(rules_dir=temp_rules_dir)
    parser.load_rules()

    # Verify rules loaded
    assert len(parser.rules) == 3

    # Verify sorting by priority (descending)
    assert parser.rules[0].priority == 100
    assert parser.rules[1].priority == 60
    assert parser.rules[2].priority == 10

    # Verify rule details
    invoice_rule = parser.rules[0]
    assert invoice_rule.name == "Invoice by subject"
    assert invoice_rule.category == EmailCategory.INVOICE
    assert invoice_rule.folder == "Finance/Invoices"
    assert not invoice_rule.auto_delete


def test_rules_parser_find_matching_rule(temp_rules_dir, sample_rules_yaml):
    """Test finding matching rule for email."""
    # Setup
    rules_file = Path(temp_rules_dir) / "global_rules.yaml"
    with open(rules_file, 'w') as f:
        f.write(sample_rules_yaml)

    parser = RulesParser(rules_dir=temp_rules_dir)
    parser.load_rules()

    # Test invoice match
    email_data = {
        'subject': 'Invoice #123',
        'sender': 'billing@company.com',
        'body_preview': 'Payment due',
        'has_attachments': True
    }

    rule = parser.find_matching_rule(email_data)
    assert rule is not None
    assert rule.name == "Invoice by subject"
    assert rule.category == EmailCategory.INVOICE

    # Test LinkedIn match
    email_data = {
        'subject': 'New connection',
        'sender': 'notifications@linkedin.com',
        'body_preview': 'John wants to connect',
        'has_attachments': False
    }

    rule = parser.find_matching_rule(email_data)
    assert rule is not None
    assert rule.name == "LinkedIn notification"
    assert rule.category == EmailCategory.SOCIAL

    # Test no match
    email_data = {
        'subject': 'Regular email',
        'sender': 'friend@example.com',
        'body_preview': 'How are you?',
        'has_attachments': False
    }

    rule = parser.find_matching_rule(email_data)
    assert rule is None


def test_rules_parser_priority_order(temp_rules_dir):
    """Test that higher priority rules match first."""
    # Create rules with overlapping conditions but different priorities
    rules_yaml = """
rules:
  - name: "Generic invoice"
    priority: 50
    conditions:
      subject_contains: "invoice"
    category: INVOICE
    folder: "Archive"

  - name: "Specific invoice"
    priority: 100
    conditions:
      subject_contains: "invoice"
      sender_contains: "important@"
    category: INVOICE
    folder: "Important"
"""

    rules_file = Path(temp_rules_dir) / "global_rules.yaml"
    with open(rules_file, 'w') as f:
        f.write(rules_yaml)

    parser = RulesParser(rules_dir=temp_rules_dir)
    parser.load_rules()

    # Email matches both rules
    email_data = {
        'subject': 'Invoice #123',
        'sender': 'important@company.com',
        'body_preview': 'Urgent payment',
        'has_attachments': False
    }

    # Should match higher priority rule first
    rule = parser.find_matching_rule(email_data)
    assert rule.name == "Specific invoice"
    assert rule.folder == "Important"


def test_rules_parser_invalid_category(temp_rules_dir):
    """Test handling of invalid category in rules."""
    rules_yaml = """
rules:
  - name: "Bad category"
    priority: 50
    conditions:
      subject_contains: "test"
    category: INVALID_CATEGORY
"""

    rules_file = Path(temp_rules_dir) / "global_rules.yaml"
    with open(rules_file, 'w') as f:
        f.write(rules_yaml)

    parser = RulesParser(rules_dir=temp_rules_dir)
    parser.load_rules()

    # Rule should be skipped
    assert len(parser.rules) == 0


def test_rules_parser_missing_conditions(temp_rules_dir):
    """Test handling of rules without conditions."""
    rules_yaml = """
rules:
  - name: "No conditions"
    priority: 50
    category: SPAM
"""

    rules_file = Path(temp_rules_dir) / "global_rules.yaml"
    with open(rules_file, 'w') as f:
        f.write(rules_yaml)

    parser = RulesParser(rules_dir=temp_rules_dir)
    parser.load_rules()

    # Rule should be skipped
    assert len(parser.rules) == 0


def test_get_category_for_email(temp_rules_dir, sample_rules_yaml):
    """Test getting category directly from email data."""
    rules_file = Path(temp_rules_dir) / "global_rules.yaml"
    with open(rules_file, 'w') as f:
        f.write(sample_rules_yaml)

    parser = RulesParser(rules_dir=temp_rules_dir)
    parser.load_rules()

    # Test match
    email_data = {
        'subject': 'Invoice #123',
        'sender': 'billing@company.com',
        'body_preview': 'Payment due',
        'has_attachments': True
    }

    category = parser.get_category_for_email(email_data)
    assert category == EmailCategory.INVOICE

    # Test no match
    email_data = {
        'subject': 'Regular email',
        'sender': 'friend@example.com',
        'body_preview': 'How are you?',
        'has_attachments': False
    }

    category = parser.get_category_for_email(email_data)
    assert category is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
