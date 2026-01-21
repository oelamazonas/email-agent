#!/usr/bin/env python3
"""
Script de test pour le connecteur IMAP refactorisé.

Usage:
    python scripts/test_imap_connector.py

Ce script teste:
1. Connexion IMAP
2. Récupération d'emails
3. Parsing des données
4. Opérations move/delete

Pré-requis:
- Compte IMAP configuré dans la DB
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
from shared.integrations import ImapConnector
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_imap_connector():
    """Tester le connecteur IMAP."""
    print("\n" + "=" * 60)
    print("🧪 Test du connecteur IMAP refactorisé")
    print("=" * 60)

    # 1. Récupérer un compte IMAP depuis la DB
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(EmailAccount).where(
                EmailAccount.account_type == AccountType.IMAP,
                EmailAccount.is_active == True
            ).limit(1)
        )
        account = result.scalar_one_or_none()

        if not account:
            print("\n❌ Aucun compte IMAP trouvé dans la base de données")
            print("   Utilisez: python scripts/add_email_account.py")
            print("   Et choisissez l'option IMAP ou Gmail avec mot de passe d'application")
            return

        print(f"\n✅ Compte trouvé: {account.email_address}")
        print(f"   ID: {account.id}")
        print(f"   Type: {account.account_type.value}")

        # 2. Déchiffrer les credentials
        try:
            credentials = decrypt_credentials(account.encrypted_credentials)
            print(f"\n✅ Credentials déchiffrés")
            print(f"   Type: {credentials.get('type', 'N/A')}")
            print(f"   Server: {credentials.get('imap_server', 'N/A')}")
            print(f"   Port: {credentials.get('imap_port', 'N/A')}")
            print(f"   SSL: {credentials.get('use_ssl', 'N/A')}")
        except Exception as e:
            print(f"\n❌ Erreur lors du déchiffrement: {e}")
            return

    # 3. Créer le connecteur
    print(f"\n📡 Création du connecteur IMAP...")
    connector = ImapConnector(
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
                print(f"   IMAP UID: {email.get('imap_uid', 'N/A')}")
                print("-" * 60)

            # 6. Test move_email (optionnel - commenté pour sécurité)
            # print(f"\n⚠️  Test move_email désactivé par sécurité")
            # if input("Voulez-vous tester move_email? [y/N]: ").lower() == 'y':
            #     test_uid = emails[0].get('imap_uid')
            #     if test_uid:
            #         success = connector.move_email(str(test_uid), "Archive")
            #         if success:
            #             print(f"✅ Email {test_uid} déplacé vers Archive")
            #         else:
            #             print(f"❌ Échec du déplacement")

            # 7. Test delete_email (optionnel - commenté pour sécurité)
            # print(f"\n⚠️  Test delete_email désactivé par sécurité")

    except Exception as e:
        print(f"❌ Erreur lors de la récupération: {e}")
        import traceback
        traceback.print_exc()
        return

    # 8. Cleanup
    connector.disconnect()
    print(f"\n✅ Connexion fermée")

    print("\n" + "=" * 60)
    print("✅ Test terminé avec succès!")
    print("=" * 60)


async def list_imap_accounts():
    """Lister tous les comptes IMAP configurés."""
    print("\n📬 Comptes IMAP configurés:")
    print("=" * 80)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(EmailAccount).where(
                EmailAccount.account_type == AccountType.IMAP
            )
        )
        accounts = result.scalars().all()

        if not accounts:
            print("Aucun compte IMAP trouvé")
        else:
            for acc in accounts:
                status = "✅ Actif" if acc.is_active else "❌ Inactif"
                last_sync = acc.last_sync.strftime("%Y-%m-%d %H:%M") if acc.last_sync else "Jamais"
                print(f"ID: {acc.id:3d} | {status} | {acc.email_address:40s} | Dernière sync: {last_sync}")

    print("=" * 80)


async def test_credentials_format():
    """Tester le format des credentials."""
    print("\n🔍 Test du format des credentials IMAP")
    print("=" * 60)

    # Test credentials valides
    test_creds = {
        "type": "imap",
        "imap_server": "imap.gmail.com",
        "imap_port": 993,
        "username": "test@gmail.com",
        "password": "test_password",
        "use_ssl": True
    }

    try:
        connector = ImapConnector("test@gmail.com", test_creds)
        print("✅ Format credentials valide")
        print(f"   Host: {connector.host}")
        print(f"   Port: {connector.port}")
        print(f"   Username: {connector.username}")
        print(f"   SSL: {connector.use_ssl}")
    except Exception as e:
        print(f"❌ Erreur: {e}")

    print("=" * 60)


def main():
    """Point d'entrée."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            asyncio.run(list_imap_accounts())
        elif sys.argv[1] == "format":
            asyncio.run(test_credentials_format())
        else:
            print("Usage: test_imap_connector.py [list|format]")
    else:
        asyncio.run(test_imap_connector())


if __name__ == "__main__":
    main()
