# Configuration Gmail avec OAuth2

Guide complet pour configurer l'accès Gmail via OAuth2 avec Email Agent AI.

## 🎯 Pourquoi OAuth2 ?

**Avantages OAuth2 vs Mot de passe d'application:**
- ✅ Accès complet à Gmail API (plus rapide, plus fiable)
- ✅ Opérations batch (efficacité)
- ✅ Gestion avancée des labels
- ✅ Pas besoin de 2FA/App Password
- ✅ Révocable facilement depuis Google Account
- ✅ Plus sécurisé (scopes limités)

## 📋 Pré-requis

1. Compte Google
2. Accès à [Google Cloud Console](https://console.cloud.google.com)
3. 10-15 minutes pour la configuration initiale

## 🚀 Configuration Google Cloud

### Étape 1: Créer un projet

1. Aller sur [Google Cloud Console](https://console.cloud.google.com)
2. Cliquer sur le sélecteur de projet (en haut)
3. **Nouveau projet**
4. Nom: `Email Agent AI` (ou autre)
5. **Créer**

### Étape 2: Activer Gmail API

1. Dans le menu ☰ → **APIs & Services** → **Library**
2. Rechercher **Gmail API**
3. Cliquer sur **Gmail API**
4. **Activer**

### Étape 3: Configurer l'écran de consentement OAuth

1. Menu ☰ → **APIs & Services** → **OAuth consent screen**
2. Type: **Externe** (pour usage personnel)
3. **Créer**
4. Remplir:
   - **App name**: Email Agent AI
   - **User support email**: votre email
   - **Developer contact**: votre email
5. **Enregistrer et continuer**
6. **Scopes**: Ignorer, cliquer **Enregistrer et continuer**
7. **Test users**: Ajouter votre adresse Gmail
8. **Enregistrer et continuer**

### Étape 4: Créer les credentials OAuth2

1. Menu ☰ → **APIs & Services** → **Credentials**
2. **+ Créer des identifiants** → **ID client OAuth**
3. Type d'application: **Application de bureau**
4. Nom: `Email Agent Desktop`
5. **Créer**
6. 📥 **Télécharger JSON** → Sauvegarder le fichier

**Format du fichier JSON téléchargé:**
```json
{
  "installed": {
    "client_id": "123456789-abcdef.apps.googleusercontent.com",
    "client_secret": "GOCSPX-xxxxxxxxxxxxxx",
    "redirect_uris": ["http://localhost"],
    ...
  }
}
```

## ⚙️ Configuration Email Agent AI

### Méthode 1: Variables d'environnement (.env)

Ajouter dans votre fichier `.env`:

```bash
# Gmail OAuth2
GOOGLE_CLIENT_ID=123456789-abcdef.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxx
GOOGLE_REDIRECT_URI=http://localhost:8080
```

### Méthode 2: Configuration interactive

Le script `add_email_account.py` vous demandera les credentials si non configurés.

## 📧 Ajouter un compte Gmail

### Via Docker (Recommandé)

```bash
# Démarrer les services
docker-compose up -d

# Lancer le script d'ajout
docker-compose exec api python scripts/add_email_account.py
```

**Processus interactif:**
```
📬 Email Agent AI - Ajout de compte email
===========================================================

Type de compte:
1. Gmail
2. Outlook/Microsoft
3. IMAP générique

Choisir le type [1]: 1

📧 Configuration compte Gmail
--------------------------------------------------
Vous avez deux options:
1. OAuth2 (recommandé - accès complet à l'API Gmail)
2. Mot de passe d'application (IMAP uniquement)

Choisir l'option [1]: 1

🔐 Configuration OAuth2 Gmail
--------------------------------------------------
Adresse Gmail: votre.email@gmail.com

🌐 Lancement du flow OAuth2...
Un navigateur va s'ouvrir pour autoriser l'application.

[Navigateur s'ouvre automatiquement]
[Autoriser l'accès dans Google]

✅ Authentification OAuth2 réussie!

Nom d'affichage [votre.email@gmail.com]: Mon Gmail Pro

📋 Récapitulatif:
   Type: gmail
   Email: votre.email@gmail.com
   Nom: Mon Gmail Pro

Confirmer l'ajout du compte? [Y/n]: Y

✅ Compte email ajouté avec succès!
   ID: 1
   Email: votre.email@gmail.com
   Type: gmail

🔄 La synchronisation démarrera automatiquement.
```

### Via Python directement

```bash
cd /Users/eric/Developer/I39/email-agent
python scripts/add_email_account.py
```

## 🔄 Synchronisation automatique

Une fois le compte ajouté:

1. **Celery Worker** détecte automatiquement le nouveau compte
2. **Synchronisation** démarre toutes les 5 minutes (configurable)
3. **Logs** visibles via:
   ```bash
   docker-compose logs -f worker
   ```

## 🛠️ Dépannage

### Erreur: "OAuth2 credentials not configured"

**Solution**: Vérifier que `.env` contient `GOOGLE_CLIENT_ID` et `GOOGLE_CLIENT_SECRET`

### Erreur: "Token expired"

**Solution**: Le refresh token est automatique. Si problème persiste:
```bash
# Re-authentifier le compte
docker-compose exec api python scripts/add_email_account.py
# Choisir "Mettre à jour" pour le compte existant
```

### Le navigateur ne s'ouvre pas

**Solution**: Si vous êtes sur un serveur distant:
1. Copier l'URL affichée dans le terminal
2. Ouvrir dans un navigateur local
3. Autoriser l'accès
4. Copier le code de redirection
5. Le coller dans le terminal

### Erreur: "Access blocked: This app's request is invalid"

**Solution**:
1. Vérifier que Gmail API est bien activée
2. Vérifier l'écran de consentement OAuth (statut: "En test")
3. Vérifier que votre email est dans les "Test users"

### Erreur: "invalid_grant" lors du refresh

**Solution**: Le refresh token a expiré ou a été révoqué
1. Supprimer le compte dans Email Agent
2. Révoquer l'accès sur [Google Account](https://myaccount.google.com/permissions)
3. Re-ajouter le compte avec OAuth2

## 📊 Vérification du fonctionnement

### Vérifier les logs de synchronisation

```bash
docker-compose logs -f worker | grep -i gmail
```

**Sortie attendue:**
```
worker_1  | INFO - Syncing account 1
worker_1  | INFO - Connecting to Gmail API for votre.email@gmail.com
worker_1  | INFO - Gmail API connection successful
worker_1  | INFO - Fetching emails with query: label:INBOX
worker_1  | INFO - Found 50 messages, fetching details...
worker_1  | INFO - Successfully parsed 50 emails
worker_1  | INFO - Account 1 sync completed. Saved 50 new emails.
```

### Vérifier les emails en DB

```bash
docker-compose exec db psql -U emailagent -d emailagent -c "SELECT COUNT(*) FROM emails WHERE account_id = 1;"
```

### Vérifier le token

```bash
docker-compose exec api python -c "
from api.database import AsyncSessionLocal
from api.models import EmailAccount
from shared.security import decrypt_credentials
import asyncio

async def check():
    async with AsyncSessionLocal() as db:
        account = await db.get(EmailAccount, 1)
        if account:
            creds = decrypt_credentials(account.encrypted_credentials)
            print('Token expiry:', creds.get('expiry'))
            print('Has refresh_token:', bool(creds.get('refresh_token')))

asyncio.run(check())
"
```

## 🔐 Sécurité

### Scopes demandés

L'application demande uniquement:
- `gmail.readonly`: Lecture des emails
- `gmail.modify`: Modification (déplacement, archivage, suppression)

**Pas d'accès à:**
- Envoi d'emails
- Suppression de compte
- Contacts
- Autres services Google

### Stockage des credentials

- **Chiffrement**: Fernet (AES 128-bit)
- **Clé**: `ENCRYPTION_KEY` dans `.env` (générer avec `Fernet.generate_key()`)
- **Refresh tokens**: Chiffrés en base de données
- **Access tokens**: Rechargés en mémoire, jamais loggés

### Révocation

Pour révoquer l'accès:
1. [Google Account Permissions](https://myaccount.google.com/permissions)
2. Trouver "Email Agent AI"
3. **Supprimer l'accès**

## 📚 Références

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [OAuth2 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Python Quickstart](https://developers.google.com/gmail/api/quickstart/python)

## 🆘 Support

En cas de problème:
1. Vérifier les logs: `docker-compose logs -f worker`
2. Vérifier la configuration: `cat .env | grep GOOGLE`
3. Créer une issue sur GitHub avec les logs (sans credentials!)
