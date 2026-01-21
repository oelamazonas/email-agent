"""
Classification rules module.

Handles loading and matching of email classification rules from YAML files.
"""
from worker.rules.rules_parser import RulesParser, ClassificationRule, rules_parser

__all__ = ['RulesParser', 'ClassificationRule', 'rules_parser']
