#!/usr/bin/env python3
"""
Script to check email classification results.

Usage:
    python scripts/check_classifications.py

Or via Docker:
    docker compose exec api python scripts/check_classifications.py
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, func, desc
from api.database import AsyncSessionLocal
from api.models import Email, EmailCategory, ProcessingStatus, EmailAccount


async def show_classification_stats():
    """Show overall classification statistics"""
    async with AsyncSessionLocal() as db:
        print("\n" + "=" * 80)
        print("📊 CLASSIFICATION STATISTICS")
        print("=" * 80)

        # Total emails
        total_query = select(func.count(Email.id))
        total_result = await db.execute(total_query)
        total = total_result.scalar()

        print(f"\n📧 Total Emails: {total}")

        if total == 0:
            print("\n⚠️  No emails found. Sync your email accounts first.")
            return

        # By category
        print("\n📂 By Category:")
        print("-" * 80)
        for category in EmailCategory:
            query = select(func.count(Email.id)).where(Email.category == category)
            result = await db.execute(query)
            count = result.scalar()

            if count > 0:
                percentage = (count / total) * 100
                bar = "█" * int(percentage / 2)
                print(f"  {category.value:15s} │ {count:4d} │ {percentage:5.1f}% │ {bar}")

        # By status
        print("\n⚙️  By Processing Status:")
        print("-" * 80)
        for status in ProcessingStatus:
            query = select(func.count(Email.id)).where(Email.status == status)
            result = await db.execute(query)
            count = result.scalar()

            if count > 0:
                percentage = (count / total) * 100
                status_icon = {
                    ProcessingStatus.PENDING: "⏳",
                    ProcessingStatus.PROCESSING: "🔄",
                    ProcessingStatus.COMPLETED: "✅",
                    ProcessingStatus.ERROR: "❌",
                    ProcessingStatus.QUARANTINE: "🚨"
                }.get(status, "❓")

                print(f"  {status_icon} {status.value:15s} │ {count:4d} │ {percentage:5.1f}%")


async def show_recent_classifications(limit: int = 20):
    """Show recent classified emails"""
    async with AsyncSessionLocal() as db:
        print("\n" + "=" * 80)
        print(f"📬 RECENT CLASSIFICATIONS (Last {limit})")
        print("=" * 80)

        query = select(Email).order_by(desc(Email.created_at)).limit(limit)
        result = await db.execute(query)
        emails = result.scalars().all()

        if not emails:
            print("\n⚠️  No emails found.")
            return

        for email in emails:
            # Get account info
            account_query = select(EmailAccount.email_address).where(
                EmailAccount.id == email.account_id
            )
            account_result = await db.execute(account_query)
            account_email = account_result.scalar_one_or_none() or "Unknown"

            # Format date
            date_str = email.date_received.strftime("%Y-%m-%d %H:%M")

            # Category icon
            category_icons = {
                EmailCategory.INVOICE: "💰",
                EmailCategory.RECEIPT: "🧾",
                EmailCategory.DOCUMENT: "📄",
                EmailCategory.PROFESSIONAL: "💼",
                EmailCategory.NEWSLETTER: "📰",
                EmailCategory.PROMOTION: "🎁",
                EmailCategory.SOCIAL: "👥",
                EmailCategory.NOTIFICATION: "🔔",
                EmailCategory.PERSONAL: "✉️",
                EmailCategory.SPAM: "🗑️",
                EmailCategory.UNKNOWN: "❓"
            }
            icon = category_icons.get(email.category, "❓")

            # Status icon
            status_icons = {
                ProcessingStatus.PENDING: "⏳",
                ProcessingStatus.PROCESSING: "🔄",
                ProcessingStatus.COMPLETED: "✅",
                ProcessingStatus.ERROR: "❌",
                ProcessingStatus.QUARANTINE: "🚨"
            }
            status_icon = status_icons.get(email.status, "❓")

            print(f"\n{icon} {email.category.value:12s} │ {status_icon} {email.status.value:10s}")
            print(f"   Subject: {email.subject[:60]}")
            print(f"   From: {email.sender[:50]}")
            print(f"   Account: {account_email}")
            print(f"   Date: {date_str}")

            if email.classification_confidence:
                print(f"   Confidence: {email.classification_confidence}%")

            if email.classification_reason:
                reason = email.classification_reason[:100]
                if len(email.classification_reason) > 100:
                    reason += "..."
                print(f"   Reason: {reason}")

            print("   " + "-" * 76)


async def show_by_category(category: str, limit: int = 10):
    """Show emails by specific category"""
    async with AsyncSessionLocal() as db:
        try:
            cat = EmailCategory(category)
        except ValueError:
            print(f"\n❌ Invalid category: {category}")
            print(f"   Valid categories: {', '.join([c.value for c in EmailCategory])}")
            return

        print("\n" + "=" * 80)
        print(f"📂 EMAILS IN CATEGORY: {cat.value.upper()}")
        print("=" * 80)

        query = select(Email).where(Email.category == cat).order_by(
            desc(Email.date_received)
        ).limit(limit)
        result = await db.execute(query)
        emails = result.scalars().all()

        if not emails:
            print(f"\n⚠️  No emails found in category '{cat.value}'")
            return

        print(f"\nFound {len(emails)} email(s) (showing up to {limit}):\n")

        for email in emails:
            date_str = email.date_received.strftime("%Y-%m-%d %H:%M")
            confidence = f"{email.classification_confidence}%" if email.classification_confidence else "N/A"

            print(f"• {email.subject[:60]}")
            print(f"  From: {email.sender} │ Date: {date_str} │ Confidence: {confidence}")
            if email.classification_reason:
                print(f"  Reason: {email.classification_reason[:80]}")
            print()


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Check email classification results')
    parser.add_argument('--stats', action='store_true', help='Show classification statistics')
    parser.add_argument('--recent', type=int, metavar='N', help='Show N recent classifications (default: 20)')
    parser.add_argument('--category', type=str, help='Show emails in specific category')
    parser.add_argument('--limit', type=int, default=10, help='Limit for category filter (default: 10)')

    args = parser.parse_args()

    # If no args, show stats and recent
    if not any([args.stats, args.recent is not None, args.category]):
        await show_classification_stats()
        await show_recent_classifications(20)
    else:
        if args.stats:
            await show_classification_stats()

        if args.recent is not None:
            await show_recent_classifications(args.recent)

        if args.category:
            await show_by_category(args.category, args.limit)


if __name__ == "__main__":
    asyncio.run(main())
