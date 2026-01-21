"""
Classification rules parser from YAML configuration.

This module handles loading and parsing of email classification rules
from YAML files, supporting both user-specific and global rules.
"""
import yaml
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from api.models import EmailCategory

logger = logging.getLogger(__name__)


class ClassificationRule:
    """Represents a single classification rule."""

    def __init__(
        self,
        name: str,
        conditions: Dict[str, Any],
        category: EmailCategory,
        folder: Optional[str] = None,
        auto_delete: bool = False,
        priority: int = 0
    ):
        """
        Initialize a classification rule.

        Args:
            name: Rule name for identification
            conditions: Dict of conditions to match
            category: Target EmailCategory
            folder: Optional folder to move email to
            auto_delete: Whether to auto-delete matched emails
            priority: Rule priority (higher = more important)
        """
        self.name = name
        self.conditions = conditions
        self.category = category
        self.folder = folder
        self.auto_delete = auto_delete
        self.priority = priority

    def matches(self, email_data: Dict[str, Any]) -> bool:
        """
        Check if email matches this rule's conditions.

        Args:
            email_data: Dict with email fields (subject, sender, body_preview, etc.)

        Returns:
            True if all conditions match, False otherwise
        """
        try:
            # Extract email fields
            subject = (email_data.get('subject') or '').lower()
            sender = (email_data.get('sender') or '').lower()
            body = (email_data.get('body_preview') or '').lower()
            has_attachments = email_data.get('has_attachments', False)

            # Check each condition
            for condition_type, condition_value in self.conditions.items():
                if condition_type == 'sender_contains':
                    if not self._check_contains(sender, condition_value):
                        return False

                elif condition_type == 'sender_equals':
                    if sender != condition_value.lower():
                        return False

                elif condition_type == 'subject_contains':
                    if not self._check_contains(subject, condition_value):
                        return False

                elif condition_type == 'subject_equals':
                    if subject != condition_value.lower():
                        return False

                elif condition_type == 'body_contains':
                    if not self._check_contains(body, condition_value):
                        return False

                elif condition_type == 'has_attachments':
                    if has_attachments != condition_value:
                        return False

                elif condition_type == 'attachment_name_contains':
                    attachment_names = email_data.get('attachment_names', [])
                    if not any(condition_value.lower() in name.lower() for name in attachment_names):
                        return False

                else:
                    logger.warning(f"Unknown condition type: {condition_type}")

            # All conditions matched
            return True

        except Exception as e:
            logger.error(f"Error checking rule '{self.name}': {e}", exc_info=True)
            return False

    def _check_contains(self, text: str, pattern: str) -> bool:
        """
        Check if text contains pattern (case-insensitive).

        Supports multiple patterns separated by '|' (OR logic).
        """
        if '|' in pattern:
            # Multiple patterns - match any
            patterns = [p.strip().lower() for p in pattern.split('|')]
            return any(p in text for p in patterns)
        else:
            # Single pattern
            return pattern.lower() in text


class RulesParser:
    """Parser for classification rules from YAML files."""

    def __init__(self, rules_dir: str = "/app/rules"):
        """
        Initialize rules parser.

        Args:
            rules_dir: Directory containing YAML rule files
        """
        self.rules_dir = Path(rules_dir)
        self.rules: List[ClassificationRule] = []
        self.last_loaded: Optional[datetime] = None

    def load_rules(self, force_reload: bool = False) -> None:
        """
        Load all rules from YAML files.

        Args:
            force_reload: If True, reload even if already loaded
        """
        if not force_reload and self.rules and self.last_loaded:
            logger.debug("Rules already loaded, skipping")
            return

        logger.info(f"Loading classification rules from {self.rules_dir}")

        try:
            # Ensure rules directory exists
            self.rules_dir.mkdir(parents=True, exist_ok=True)

            # Clear existing rules
            self.rules = []

            # Load global rules
            global_rules_file = self.rules_dir / "global_rules.yaml"
            if global_rules_file.exists():
                self._load_rules_file(global_rules_file)
            else:
                logger.warning(f"Global rules file not found: {global_rules_file}")

            # Sort rules by priority (descending)
            self.rules.sort(key=lambda r: r.priority, reverse=True)

            self.last_loaded = datetime.utcnow()
            logger.info(f"Loaded {len(self.rules)} classification rules")

        except Exception as e:
            logger.error(f"Error loading rules: {e}", exc_info=True)

    def _load_rules_file(self, file_path: Path) -> None:
        """
        Load rules from a single YAML file.

        Args:
            file_path: Path to YAML file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)

            if not data or 'rules' not in data:
                logger.warning(f"No rules found in {file_path}")
                return

            for rule_data in data['rules']:
                rule = self._parse_rule(rule_data)
                if rule:
                    self.rules.append(rule)
                    logger.debug(f"Loaded rule: {rule.name}")

        except Exception as e:
            logger.error(f"Error loading rules file {file_path}: {e}", exc_info=True)

    def _parse_rule(self, rule_data: Dict[str, Any]) -> Optional[ClassificationRule]:
        """
        Parse a single rule from YAML data.

        Args:
            rule_data: Dict with rule configuration

        Returns:
            ClassificationRule or None if invalid
        """
        try:
            name = rule_data.get('name')
            if not name:
                logger.error("Rule missing 'name' field")
                return None

            conditions = rule_data.get('conditions', {})
            if not conditions:
                logger.error(f"Rule '{name}' has no conditions")
                return None

            category_str = rule_data.get('category', 'unknown').upper()
            try:
                category = EmailCategory[category_str]
            except KeyError:
                logger.error(f"Invalid category '{category_str}' in rule '{name}'")
                return None

            folder = rule_data.get('folder')
            auto_delete = rule_data.get('auto_delete', False)
            priority = rule_data.get('priority', 0)

            return ClassificationRule(
                name=name,
                conditions=conditions,
                category=category,
                folder=folder,
                auto_delete=auto_delete,
                priority=priority
            )

        except Exception as e:
            logger.error(f"Error parsing rule: {e}", exc_info=True)
            return None

    def find_matching_rule(self, email_data: Dict[str, Any]) -> Optional[ClassificationRule]:
        """
        Find first rule that matches the email.

        Rules are checked in priority order (highest first).

        Args:
            email_data: Dict with email fields

        Returns:
            Matching ClassificationRule or None
        """
        if not self.rules:
            self.load_rules()

        for rule in self.rules:
            if rule.matches(email_data):
                logger.info(f"Email matched rule: {rule.name}")
                return rule

        return None

    def get_category_for_email(self, email_data: Dict[str, Any]) -> Optional[EmailCategory]:
        """
        Get category for email based on rules.

        Args:
            email_data: Dict with email fields

        Returns:
            EmailCategory if matched, None otherwise
        """
        rule = self.find_matching_rule(email_data)
        return rule.category if rule else None


# Global instance
rules_parser = RulesParser()
