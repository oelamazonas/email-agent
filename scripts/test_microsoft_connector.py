#!/usr/bin/env python3
"""
Script de test pour le MicrosoftConnector.

Usage:
    python scripts/test_microsoft_connector.py

Teste la connexion et la récupération d'emails via Microsoft Graph API.
"""
import sys
import os
import json
from pathlib import Path
from datetime import datetime, timedelta

# Ajouter le parent directory au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.integrations.microsoft import MicrosoftConnector


def test_microsoft_connector():
    """Test du MicrosoftConnector avec des credentials OAuth2."""
    print("\n" + "=" * 80)
    print("🧪 Test MicrosoftConnector - Microsoft Graph API")
    print("=" * 80)

    # 1. Charger les credentials depuis un fichier JSON
    creds_path = Path(__file__).parent / "microsoft_credentials.json"

    if not creds_path.exists():
        print(f"\n❌ Fichier de credentials non trouvé: {creds_path}")
        print("\n💡 Pour créer ce fichier:")
        print("   1. Lancez: python scripts/add_email_account.py")
        print("   2. Choisissez 'Outlook/Microsoft' puis 'OAuth2'")
        print("   3. Complétez le flow OAuth2")
        print("   4. Ou créez manuellement un fichier microsoft_credentials.json avec:")
        print("""
{
    "email_address": "your-email@outlook.com",
    "credentials": {
        "token": "your_access_token",
        "refresh_token": "your_refresh_token",
        "client_id": "your_client_id",
        "client_secret": "your_client_secret",
        "tenant_id": "common",
        "scopes": ["https://graph.microsoft.com/Mail.Read"],
        "expiry": "2025-01-21T12:00:00"
    }
}
""")
        return

    with open(creds_path, 'r') as f:
        config = json.load(f)

    email_address = config["email_address"]
    credentials = config["credentials"]

    print(f"\n📧 Email: {email_address}")
    print(f"🔑 Client ID: {credentials.get('client_id', 'N/A')[:20]}...")
    print(f"🎫 Tenant: {credentials.get('tenant_id', 'N/A')}")

    # 2. Créer le connecteur
    print("\n🔨 Création du MicrosoftConnector...")
    connector = MicrosoftConnector(
        email_address=email_address,
        credentials=credentials
    )

    # 3. Test connexion
    print("\n🔌 Test de connexion...")
    try:
        connector.connect()
        print("✅ Connexion réussie!")
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        import traceback
        traceback.print_exc()
        return

    # 4. Test récupération d'emails
    print("\n📬 Récupération des 10 derniers emails...")
    try:
        emails = connector.fetch_emails(
            folder="INBOX",
            limit=10,
            since=datetime.utcnow() - timedelta(days=7)
        )

        print(f"✅ {len(emails)} emails récupérés")

        if emails:
            print("\n📋 Aperçu des emails:")
            print("-" * 80)
            for i, email in enumerate(emails[:5], 1):
                subject = email.get('subject', 'No Subject')[:50]
                sender = email.get('sender', 'Unknown')
                date = email.get('date_received', 'Unknown date')

                print(f"{i}. [{date}] {sender}")
                print(f"   📌 {subject}")
                if email.get('has_attachments'):
                    print(f"   📎 {email.get('attachment_count', 0)} attachments")
                print()

            if len(emails) > 5:
                print(f"   ... et {len(emails) - 5} autres emails")
        else:
            print("\n📭 Aucun email trouvé dans la période")

    except Exception as e:
        print(f"❌ Erreur lors de la récupération: {e}")
        import traceback
        traceback.print_exc()

    # 5. Test refresh credentials
    print("\n🔄 Vérification du refresh des credentials...")
    try:
        refreshed_creds = connector.get_refreshed_credentials()
        if refreshed_creds:
            print("✅ Credentials disponibles")

            # Sauvegarder si refreshed
            if refreshed_creds['token'] != credentials['token']:
                print("🔄 Token a été refresh, sauvegarde des nouveaux credentials...")
                config['credentials'] = refreshed_creds
                with open(creds_path, 'w') as f:
                    json.dump(config, f, indent=2)
                print("✅ Nouveaux credentials sauvegardés")
        else:
            print("⚠️  Pas de credentials refreshed")
    except Exception as e:
        print(f"⚠️  Erreur refresh: {e}")

    # 6. Cleanup
    print("\n🧹 Nettoyage...")
    connector.disconnect()
    print("✅ Déconnecté")

    # 7. Résumé
    print("\n" + "=" * 80)
    print("✅ Tests MicrosoftConnector terminés!")
    print("=" * 80)
    print("\n💡 Prochaines étapes:")
    print("   - Le connecteur est fonctionnel")
    print("   - Vous pouvez ajouter ce compte via: python scripts/add_email_account.py")
    print("   - Les emails seront synchronisés automatiquement toutes les 5 minutes")
    print()


def test_oauth_manager():
    """Test du MicrosoftOAuth2Manager pour obtenir de nouveaux tokens."""
    print("\n" + "=" * 80)
    print("🧪 Test MicrosoftOAuth2Manager - Device Code Flow")
    print("=" * 80)

    from shared.oauth2_manager import MicrosoftOAuth2Manager
    from shared.config import settings

    if not settings.MICROSOFT_CLIENT_ID:
        print("\n❌ MICROSOFT_CLIENT_ID non configuré dans .env")
        print("\n💡 Ajoutez dans votre fichier .env:")
        print("   MICROSOFT_CLIENT_ID=your_client_id")
        print("   MICROSOFT_CLIENT_SECRET=your_client_secret  # optionnel")
        print("   MICROSOFT_TENANT_ID=common  # ou votre tenant ID")
        return

    print(f"\n🔑 Client ID: {settings.MICROSOFT_CLIENT_ID[:20]}...")
    print(f"🎫 Tenant: {getattr(settings, 'MICROSOFT_TENANT_ID', 'common')}")

    print("\n🚀 Lancement du flow OAuth2 (Device Code)...")
    print("Suivez les instructions qui vont s'afficher.")
    print()

    try:
        oauth_manager = MicrosoftOAuth2Manager(
            client_id=settings.MICROSOFT_CLIENT_ID,
            client_secret=getattr(settings, 'MICROSOFT_CLIENT_SECRET', None),
            tenant_id=getattr(settings, 'MICROSOFT_TENANT_ID', 'common')
        )

        # Device code flow
        credentials = oauth_manager.interactive_auth_flow()

        print("\n✅ Authentification réussie!")
        print("\n📋 Credentials obtenues:")
        print(f"   Token: {credentials['token'][:30]}...")
        print(f"   Refresh token: {credentials.get('refresh_token', 'N/A')[:30]}...")
        print(f"   Expiry: {credentials.get('expiry', 'N/A')}")

        # Sauvegarder pour les tests
        email_address = input("\n📧 Adresse email du compte: ").strip()

        config = {
            "email_address": email_address,
            "credentials": credentials
        }

        creds_path = Path(__file__).parent / "microsoft_credentials.json"
        with open(creds_path, 'w') as f:
            json.dump(config, f, indent=2)

        print(f"\n✅ Credentials sauvegardées dans: {creds_path}")
        print("\n💡 Vous pouvez maintenant lancer:")
        print("   python scripts/test_microsoft_connector.py")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Point d'entrée principal."""
    if len(sys.argv) > 1 and sys.argv[1] == "oauth":
        test_oauth_manager()
    else:
        test_microsoft_connector()


if __name__ == "__main__":
    main()
