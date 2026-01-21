import asyncio
import os
import sys
import logging

# Add root to path
sys.path.append(os.getcwd())

from shared.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from api.database import get_db_context
from api.models import EmailAccount, AccountType, User
from worker.tasks.email_sync import sync_account
from shared.security import encrypt_password

async def create_or_get_test_account(email, password):
    async with get_db_context() as db:
        # 1. Get or create user
        result = await db.execute(
            "SELECT id FROM users WHERE email = :email", 
            {"email": "test@example.com"}
        )
        user_id = result.scalar()
        
        if not user_id:
            logger.info("Creating test user")
            # Create simple user
            from api.models import User
            user = User(
                email="test@example.com", 
                hashed_password="hash", 
                username="tester"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            user_id = user.id
            
        # 2. Create IMAP account
        stmt = "SELECT id FROM email_accounts WHERE email_address = :email"
        result = await db.execute(stmt, {"email": email})
        account_id = result.scalar()
        
        if account_id:
            logger.info(f"Account {email} exists (id={account_id})")
            # Update password just in case
            stmt = "UPDATE email_accounts SET encrypted_credentials = :creds WHERE id = :id"
            await db.execute(stmt, {"creds": encrypt_password(password), "id": account_id})
            await db.commit()
        else:
            logger.info(f"Creating account for {email}")
            account = EmailAccount(
                user_id=user_id,
                account_type=AccountType.IMAP,
                email_address=email,
                encrypted_credentials=encrypt_password(password),
                is_active=True,
                sync_enabled=True,
                display_name="Test Account"
            )
            db.add(account)
            await db.commit()
            await db.refresh(account)
            account_id = account.id
            
        return account_id

def main():
    print("=== IMAP Sync Test ===")
    email = os.environ.get("TEST_EMAIL")
    password = os.environ.get("TEST_PASSWORD")
    
    if not email or not password:
        print("Please set TEST_EMAIL and TEST_PASSWORD env vars")
        return

    print(f"Testing with {email}...")
    
    # 1. Setup DB entry
    try:
        account_id = asyncio.run(create_or_get_test_account(email, password))
        print(f"Account ID: {account_id}")
    except Exception as e:
        print(f"Error setting up account: {e}")
        return

    # 2. Run sync task
    print("Running sync task...")
    try:
        result = sync_account(account_id)
        print("Sync Result:", result)
    except Exception as e:
        print(f"Sync failed: {e}")

if __name__ == "__main__":
    main()
