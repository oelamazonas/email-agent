#!/usr/bin/env python3
"""
Script pour ajouter un compte email à Email Agent AI.

Usage:
    python scripts/add_email_account.py

Ou via Docker:
    docker-compose exec api python scripts/add_email_account.py
"""
import asyncio
import sys
import os
import json
import getpass
from pathlib import Path

# Ajouter le parent directory au path pour importer les modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from cryptography.fernet import Fernet
from passlib.context import CryptContext

from api.database import AsyncSessionLocal
from api.models import User, EmailAccount, AccountType
from shared.config import settings
from shared.security import encrypt_credentials, decrypt_credentials


# Configuration du hashing de password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Note: encrypt_credentials et decrypt_credentials sont maintenant dans shared/security.py


async def get_or_create_admin_user(db):
    """Récupère ou crée l'utilisateur admin"""
    result = await db.execute(
        select(User).where(User.email == settings.ADMIN_EMAIL)
    )
    user = result.scalar_one_or_none()

    if not user:
        print("🔧 Création de l'utilisateur admin...")
        user = User(
            email=settings.ADMIN_EMAIL,
            username="admin",
            hashed_password=pwd_context.hash(settings.ADMIN_PASSWORD),
            full_name="Administrator",
            is_admin=True,
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"✅ Utilisateur admin créé: {user.email}")
    else:
        print(f"✅ Utilisateur admin trouvé: {user.email}")

    return user


def get_imap_credentials():
    """Récupère les credentials IMAP de l'utilisateur"""
    print("\n📧 Configuration compte IMAP")
    print("-" * 50)

    email_address = input("Adresse email: ").strip()
    imap_server = input("Serveur IMAP (ex: imap.gmail.com): ").strip()
    imap_port = input("Port IMAP [993]: ").strip() or "993"

    print("\nAuthentification:")
    username = input(f"Username [{email_address}]: ").strip() or email_address
    password = getpass.getpass("Password (caché): ")

    use_ssl = input("Utiliser SSL/TLS? [Y/n]: ").strip().lower() != 'n'

    return {
        "email_address": email_address,
        "account_type": AccountType.IMAP,
        "credentials": {
            "type": "imap",
            "imap_server": imap_server,
            "imap_port": int(imap_port),
            "username": username,
            "password": password,
            "use_ssl": use_ssl
        }
    }


def get_gmail_credentials():
    """Récupère les credentials Gmail (OAuth2)"""
    print("\n📧 Configuration compte Gmail")
    print("-" * 50)
    print("Vous avez deux options:")
    print("1. OAuth2 (recommandé - accès complet à l'API Gmail)")
    print("2. Mot de passe d'application (IMAP uniquement)")
    print()

    choice = input("Choisir l'option [1]: ").strip() or "1"

    email_address = input("Adresse Gmail: ").strip()

    if choice == "1":
        # OAuth2 Flow
        print("\n🔐 Configuration OAuth2 Gmail")
        print("-" * 50)
        print("Pour utiliser OAuth2, vous devez:")
        print("1. Créer un projet sur Google Cloud Console")
        print("2. Activer Gmail API")
        print("3. Créer des credentials OAuth2")
        print()
        print("Détails: https://developers.google.com/gmail/api/quickstart/python")
        print()

        # Vérifier si les credentials OAuth2 sont dans settings
        from shared.config import settings

        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            print("❌ GOOGLE_CLIENT_ID et GOOGLE_CLIENT_SECRET non configurés dans .env")
            print()
            print("Voulez-vous les saisir maintenant? [y/N]: ")
            if input().strip().lower() != 'y':
                print("⚠️  Configuration annulée. Configurez .env puis relancez.")
                return None

            client_id = input("Google Client ID: ").strip()
            client_secret = getpass.getpass("Google Client Secret: ")
        else:
            client_id = settings.GOOGLE_CLIENT_ID
            client_secret = settings.GOOGLE_CLIENT_SECRET

        # Flow OAuth2 interactif
        print("\n🌐 Lancement du flow OAuth2...")
        print("Un navigateur va s'ouvrir pour autoriser l'application.")
        print()

        try:
            from shared.oauth2_manager import GmailOAuth2Manager

            oauth_manager = GmailOAuth2Manager(
                client_id=client_id,
                client_secret=client_secret
            )

            # Flow interactif
            credentials = oauth_manager.interactive_auth_flow()

            print("\n✅ Authentification OAuth2 réussie!")

            return {
                "email_address": email_address,
                "account_type": AccountType.GMAIL,
                "credentials": credentials
            }

        except Exception as e:
            print(f"\n❌ Erreur lors de l'authentification OAuth2: {e}")
            import traceback
            traceback.print_exc()
            return None

    elif choice == "2":
        # App Password (IMAP)
        print("\n📝 Pour créer un mot de passe d'application:")
        print("   1. Allez sur https://myaccount.google.com/security")
        print("   2. Activez la validation en 2 étapes si nécessaire")
        print("   3. Allez dans 'Mots de passe des applications'")
        print("   4. Générez un mot de passe pour 'Email Agent'")
        print()

        app_password = getpass.getpass("Mot de passe d'application (16 caractères): ")

        return {
            "email_address": email_address,
            "account_type": AccountType.IMAP,  # IMAP mode
            "credentials": {
                "type": "imap",
                "imap_server": "imap.gmail.com",
                "imap_port": 993,
                "username": email_address,
                "password": app_password,
                "use_ssl": True
            }
        }
    else:
        print("❌ Choix invalide")
        return None


def get_outlook_credentials():
    """Récupère les credentials Outlook/Microsoft"""
    print("\n📧 Configuration compte Outlook/Microsoft")
    print("-" * 50)
    print("Vous avez deux options:")
    print("1. OAuth2 (recommandé - accès complet à Microsoft Graph API)")
    print("2. IMAP direct (si activé sur votre compte)")
    print()

    choice = input("Choisir l'option [1]: ").strip() or "1"

    email_address = input("Adresse email Outlook/Office 365: ").strip()

    if choice == "1":
        # OAuth2 Flow
        print("\n🔐 Configuration OAuth2 Microsoft")
        print("-" * 50)
        print("Pour utiliser OAuth2, vous devez:")
        print("1. Créer une application sur Azure AD (portal.azure.com)")
        print("2. Configurer les permissions Microsoft Graph (Mail.Read, Mail.ReadWrite)")
        print("3. Créer un client ID et (optionnel) client secret")
        print()
        print("Détails: https://docs.microsoft.com/en-us/graph/auth-v2-user")
        print()

        # Vérifier si les credentials OAuth2 sont dans settings
        from shared.config import settings

        if not settings.MICROSOFT_CLIENT_ID:
            print("❌ MICROSOFT_CLIENT_ID non configuré dans .env")
            print()
            print("Voulez-vous le saisir maintenant? [y/N]: ")
            if input().strip().lower() != 'y':
                print("⚠️  Configuration annulée. Configurez .env puis relancez.")
                return None

            client_id = input("Microsoft Client ID: ").strip()
            client_secret = getpass.getpass("Microsoft Client Secret (optionnel, Enter pour ignorer): ").strip() or None
            tenant_id = input("Tenant ID [common]: ").strip() or "common"
        else:
            client_id = settings.MICROSOFT_CLIENT_ID
            client_secret = getattr(settings, 'MICROSOFT_CLIENT_SECRET', None)
            tenant_id = getattr(settings, 'MICROSOFT_TENANT_ID', 'common')

        # Flow OAuth2 interactif
        print("\n🌐 Lancement du flow OAuth2 Microsoft...")
        print("Vous allez recevoir un code à entrer sur https://microsoft.com/devicelogin")
        print()

        try:
            from shared.oauth2_manager import MicrosoftOAuth2Manager

            oauth_manager = MicrosoftOAuth2Manager(
                client_id=client_id,
                client_secret=client_secret,
                tenant_id=tenant_id
            )

            # Flow interactif (device code)
            credentials = oauth_manager.interactive_auth_flow()

            print("\n✅ Authentification OAuth2 réussie!")

            return {
                "email_address": email_address,
                "account_type": AccountType.OUTLOOK,
                "credentials": credentials
            }

        except Exception as e:
            print(f"\n❌ Erreur lors de l'authentification OAuth2: {e}")
            import traceback
            traceback.print_exc()
            return None

    elif choice == "2":
        # IMAP direct
        print("\n📝 Pour utiliser IMAP avec Outlook/Office 365:")
        print("   1. Assurez-vous que IMAP est activé dans les paramètres Outlook")
        print("   2. Utilisez votre mot de passe de compte Microsoft")
        print("   3. Si 2FA est activé, vous devrez peut-être créer un mot de passe d'application")
        print()

        username = input(f"Username [{email_address}]: ").strip() or email_address
        password = getpass.getpass("Password: ")

        return {
            "email_address": email_address,
            "account_type": AccountType.OUTLOOK,
            "credentials": {
                "type": "imap",
                "imap_server": "outlook.office365.com",
                "imap_port": 993,
                "username": username,
                "password": password,
                "use_ssl": True
            }
        }
    else:
        print("❌ Choix invalide")
        return None


async def add_email_account():
    """Fonction principale pour ajouter un compte email"""
    print("\n" + "=" * 60)
    print("📬 Email Agent AI - Ajout de compte email")
    print("=" * 60)

    # Choisir le type de compte
    print("\nType de compte:")
    print("1. Gmail")
    print("2. Outlook/Microsoft")
    print("3. IMAP générique")
    print()

    account_type_choice = input("Choisir le type [1]: ").strip() or "1"

    # Récupérer les credentials selon le type
    if account_type_choice == "1":
        config = get_gmail_credentials()
    elif account_type_choice == "2":
        config = get_outlook_credentials()
    elif account_type_choice == "3":
        config = get_imap_credentials()
    else:
        print("❌ Choix invalide")
        return

    if not config:
        print("❌ Configuration annulée")
        return

    email_address = config["email_address"]
    credentials = config["credentials"]
    account_type = config.get("account_type", AccountType.IMAP)  # Default to IMAP

    # Demander le nom d'affichage
    display_name = input(f"\nNom d'affichage [{email_address}]: ").strip() or email_address

    # Confirmation
    print("\n" + "=" * 60)
    print("📋 Récapitulatif:")
    print(f"   Type: {account_type.value}")
    print(f"   Email: {email_address}")
    print(f"   Nom: {display_name}")
    print("=" * 60)

    confirm = input("\nConfirmer l'ajout du compte? [Y/n]: ").strip().lower()
    if confirm == 'n':
        print("❌ Annulé")
        return

    # Ajouter le compte à la base de données
    async with AsyncSessionLocal() as db:
        try:
            # Vérifier si le compte existe déjà
            result = await db.execute(
                select(EmailAccount).where(EmailAccount.email_address == email_address)
            )
            existing = result.scalar_one_or_none()

            if existing:
                print(f"\n⚠️  Un compte avec l'adresse {email_address} existe déjà!")
                update = input("Mettre à jour les credentials? [y/N]: ").strip().lower()

                if update == 'y':
                    existing.encrypted_credentials = encrypt_credentials(credentials)
                    existing.display_name = display_name
                    existing.is_active = True
                    await db.commit()
                    print(f"✅ Compte {email_address} mis à jour!")
                else:
                    print("❌ Annulé")
                return

            # Récupérer ou créer l'utilisateur admin
            user = await get_or_create_admin_user(db)

            # Chiffrer les credentials
            encrypted_creds = encrypt_credentials(credentials)

            # Créer le compte email
            new_account = EmailAccount(
                user_id=user.id,
                account_type=account_type,
                email_address=email_address,
                display_name=display_name,
                encrypted_credentials=encrypted_creds,
                is_active=True,
                sync_enabled=True
            )

            db.add(new_account)
            await db.commit()
            await db.refresh(new_account)

            print(f"\n✅ Compte email ajouté avec succès!")
            print(f"   ID: {new_account.id}")
            print(f"   Email: {new_account.email_address}")
            print(f"   Type: {new_account.account_type.value}")
            print(f"\n🔄 La synchronisation démarrera automatiquement.")
            print(f"   Vous pouvez consulter les logs avec:")
            print(f"   docker-compose logs -f worker")

        except Exception as e:
            print(f"\n❌ Erreur lors de l'ajout du compte: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()


async def list_accounts():
    """Liste tous les comptes configurés"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(EmailAccount))
        accounts = result.scalars().all()

        if not accounts:
            print("\n📭 Aucun compte email configuré")
            return

        print("\n📬 Comptes email configurés:")
        print("=" * 80)
        for acc in accounts:
            status = "✅ Actif" if acc.is_active else "❌ Inactif"
            last_sync = acc.last_sync.strftime("%Y-%m-%d %H:%M") if acc.last_sync else "Jamais"
            print(f"ID: {acc.id:3d} | {status} | {acc.account_type.value:8s} | {acc.email_address:40s} | Dernière sync: {last_sync}")
        print("=" * 80)


def main():
    """Point d'entrée principal"""
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        asyncio.run(list_accounts())
    else:
        asyncio.run(add_email_account())


if __name__ == "__main__":
    main()
