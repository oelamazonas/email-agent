#!/usr/bin/env python3
"""
Test classification rules loading.

Usage:
    python scripts/test_rules.py

Or via Docker:
    docker compose exec api python scripts/test_rules.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from worker.rules import rules_parser


def main():
    """Test rules loading"""
    print("\n" + "=" * 80)
    print("🔧 CLASSIFICATION RULES TEST")
    print("=" * 80)

    # Test loading rules
    print(f"\n📂 Loading rules from: {rules_parser.rules_dir}")
    print(f"   Rules file: {rules_parser.rules_dir}/global_rules.yaml")

    # Show loaded rules
    rules = rules_parser.rules
    print(f"\n✅ Loaded {len(rules)} rules")

    if rules:
        print("\n" + "-" * 80)
        print("📋 RULES SUMMARY")
        print("-" * 80)

        # Group by category
        by_category = {}
        for rule in rules:
            cat = rule.category.value
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(rule)

        for category in sorted(by_category.keys()):
            rules_in_cat = by_category[category]
            print(f"\n📂 {category} ({len(rules_in_cat)} rules)")
            for rule in sorted(rules_in_cat, key=lambda r: r.priority, reverse=True):
                print(f"   [{rule.priority:3d}] {rule.name}")
                if rule.target_folder:
                    print(f"        → Folder: {rule.target_folder}")
                if rule.auto_delete:
                    print(f"        → Auto-delete: Yes")

        # Test a sample email
        print("\n" + "=" * 80)
        print("🧪 TEST WITH SAMPLE EMAIL")
        print("=" * 80)

        test_email = {
            "subject": "Your Invoice #12345",
            "sender": "billing@company.com",
            "body_preview": "Please find attached your invoice for this month",
            "has_attachments": True,
            "attachment_names": ["invoice_january.pdf"]
        }

        print("\n📧 Sample Email:")
        print(f"   Subject: {test_email['subject']}")
        print(f"   From: {test_email['sender']}")
        print(f"   Has attachments: {test_email['has_attachments']}")

        matched_rule = rules_parser.find_matching_rule(test_email)

        if matched_rule:
            print(f"\n✅ Matched Rule: {matched_rule.name}")
            print(f"   Priority: {matched_rule.priority}")
            print(f"   Category: {matched_rule.category.value}")
            if matched_rule.target_folder:
                print(f"   Target Folder: {matched_rule.target_folder}")
            if matched_rule.auto_delete:
                print(f"   Auto-delete: Yes")
        else:
            print("\n❌ No rule matched (would use LLM classification)")

    else:
        print("\n⚠️  No rules loaded!")
        print("   Check that rules/global_rules.yaml exists")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
