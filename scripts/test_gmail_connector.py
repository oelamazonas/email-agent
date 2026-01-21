#!/usr/bin/env python3
"""
Script de test pour le connecteur Gmail OAuth2.

Usage:
    python scripts/test_gmail_connector.py

Ce script teste:
1. Connexion à Gmail API
2. Récupération d'emails
3. Parsing des données
4. Refresh du token

Pré-requis:
- Compte Gmail configuré dans la DB
- GOOGLE_CLIENT_ID et GOOGLE_CLIENT_SECRET dans .env
"""
import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from api.database import AsyncSessionLocal
from api.models import EmailAccount, AccountType
from shared.security import decrypt_credentials
from shared.integrations import GmailConnector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_gmail_connector():
    """Tester le connecteur Gmail."""
    print("\n" + "=" * 60)
    print("🧪 Test du connecteur Gmail OAuth2")
    print("=" * 60)

    # 1. Récupérer un compte Gmail depuis la DB
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(EmailAccount).where(
                EmailAccount.account_type == AccountType.GMAIL,
                EmailAccount.is_active == True
            ).limit(1)
        )
        account = result.scalar_one_or_none()

        if not account:
            print("\n❌ Aucun compte Gmail trouvé dans la base de données")
            print("   Utilisez: python scripts/add_email_account.py")
            return

        print(f"\n✅ Compte trouvé: {account.email_address}")
        print(f"   ID: {account.id}")
        print(f"   Type: {account.account_type.value}")

        # 2. Déchiffrer les credentials
        try:
            credentials = decrypt_credentials(account.encrypted_credentials)
            print(f"\n✅ Credentials déchiffrés")
            print(f"   Token présent: {bool(credentials.get('token'))}")
            print(f"   Refresh token présent: {bool(credentials.get('refresh_token'))}")
            print(f"   Expiry: {credentials.get('expiry', 'N/A')}")
        except Exception as e:
            print(f"\n❌ Erreur lors du déchiffrement: {e}")
            return

    # 3. Créer le connecteur
    print(f"\n📡 Création du connecteur Gmail...")
    connector = GmailConnector(
        email_address=account.email_address,
        credentials=credentials
    )

    # 4. Tester la connexion
    print(f"\n🔌 Test de connexion...")
    try:
        test_result = connector.test_connection()
        if test_result['success']:
            print(f"✅ Connexion réussie: {test_result['message']}")
        else:
            print(f"❌ Échec de connexion: {test_result['message']}")
            return
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        import traceback
        traceback.print_exc()
        return

    # 5. Récupérer des emails
    print(f"\n📥 Récupération des 10 derniers emails...")
    try:
        emails = connector.fetch_emails(folder="INBOX", limit=10)
        print(f"\n✅ {len(emails)} emails récupérés")

        if emails:
            print("\n📧 Aperçu des emails:")
            print("-" * 60)
            for i, email in enumerate(emails[:5], 1):
                print(f"{i}. Subject: {email['subject'][:50]}")
                print(f"   From: {email['sender'][:50]}")
                print(f"   Date: {email['date_received']}")
                print(f"   Attachments: {email['attachment_count']}")
                print("-" * 60)
    except Exception as e:
        print(f"❌ Erreur lors de la récupération: {e}")
        import traceback
        traceback.print_exc()
        return

    # 6. Vérifier si le token a été refresh
    refreshed_creds = connector.get_refreshed_credentials()
    if refreshed_creds and refreshed_creds.get('token') != credentials.get('token'):
        print(f"\n🔄 Token a été refresh automatiquement")
        print(f"   Nouveau token: {refreshed_creds['token'][:20]}...")
        print(f"   Nouvelle expiry: {refreshed_creds.get('expiry')}")

        # Mettre à jour en DB
        from shared.security import encrypt_credentials
        async with AsyncSessionLocal() as db:
            account = await db.get(EmailAccount, account.id)
            if account:
                account.encrypted_credentials = encrypt_credentials(refreshed_creds)
                await db.commit()
                print(f"✅ Credentials mis à jour en DB")
    else:
        print(f"\n✅ Token toujours valide, pas de refresh nécessaire")

    # 7. Cleanup
    connector.disconnect()
    print(f"\n✅ Connexion fermée")

    print("\n" + "=" * 60)
    print("✅ Test terminé avec succès!")
    print("=" * 60)


async def list_gmail_accounts():
    """Lister tous les comptes Gmail configurés."""
    print("\n📬 Comptes Gmail configurés:")
    print("=" * 80)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(EmailAccount).where(
                EmailAccount.account_type == AccountType.GMAIL
            )
        )
        accounts = result.scalars().all()

        if not accounts:
            print("Aucun compte Gmail trouvé")
        else:
            for acc in accounts:
                status = "✅ Actif" if acc.is_active else "❌ Inactif"
                last_sync = acc.last_sync.strftime("%Y-%m-%d %H:%M") if acc.last_sync else "Jamais"
                print(f"ID: {acc.id:3d} | {status} | {acc.email_address:40s} | Dernière sync: {last_sync}")

    print("=" * 80)


def main():
    """Point d'entrée."""
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        asyncio.run(list_gmail_accounts())
    else:
        asyncio.run(test_gmail_connector())


if __name__ == "__main__":
    main()
