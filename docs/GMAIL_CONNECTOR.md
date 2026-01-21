# Gmail Connector - Documentation Technique

Documentation complète du connecteur Gmail OAuth2 pour Email Agent AI.

## 📐 Architecture

### Composants

```
shared/integrations/
├── base.py              # BaseEmailConnector (interface abstraite)
├── gmail.py             # GmailConnector (implémentation Gmail API)
└── imap.py              # ImapConnector (fallback IMAP)

shared/
├── oauth2_manager.py    # Gestion du flow OAuth2
└── security.py          # Chiffrement des credentials

worker/tasks/
└── email_sync.py        # Orchestration de la synchronisation
```

### Flow de données

```
1. User Authentication
   ┌─────────────────┐
   │ add_email_account│
   └────────┬─────────┘
            │
            ▼
   ┌─────────────────┐
   │ OAuth2Manager   │ → Interactive flow
   │ .interactive_   │ → Returns credentials
   │  auth_flow()    │
   └────────┬─────────┘
            │
            ▼
   ┌─────────────────┐
   │ encrypt_        │
   │ credentials()   │
   └────────┬─────────┘
            │
            ▼
   ┌─────────────────┐
   │ EmailAccount    │
   │ (DB storage)    │
   └─────────────────┘

2. Email Synchronization
   ┌─────────────────┐
   │ Celery Worker   │
   │ sync_account()  │
   └────────┬─────────┘
            │
            ▼
   ┌─────────────────┐
   │ decrypt_        │
   │ credentials()   │
   └────────┬─────────┘
            │
            ▼
   ┌─────────────────┐
   │ GmailConnector  │
   │ .connect()      │
   └────────┬─────────┘
            │
            ▼
   ┌─────────────────┐
   │ .fetch_emails() │ → Gmail API calls
   └────────┬─────────┘
            │
            ▼
   ┌─────────────────┐
   │ Parse & Save    │ → Email table
   └────────┬─────────┘
            │
            ▼
   ┌─────────────────┐
   │ Token refresh?  │ → Update if needed
   └─────────────────┘
```

## 🔧 Composants détaillés

### 1. BaseEmailConnector

**Fichier**: `shared/integrations/base.py`

Classe abstraite définissant l'interface commune pour tous les connecteurs.

**Méthodes abstraites:**
```python
@abstractmethod
def connect(self) -> None:
    """Établir la connexion."""

@abstractmethod
def disconnect(self) -> None:
    """Fermer la connexion."""

@abstractmethod
def fetch_emails(
    folder: str = "INBOX",
    limit: int = 50,
    since: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """Récupérer les emails."""

@abstractmethod
def move_email(message_id: str, destination_folder: str) -> bool:
    """Déplacer un email."""

@abstractmethod
def delete_email(message_id: str, permanent: bool = False) -> bool:
    """Supprimer un email."""
```

**Méthode utilitaire:**
```python
def test_connection(self) -> Dict[str, Any]:
    """Tester la connexion."""
```

### 2. GmailConnector

**Fichier**: `shared/integrations/gmail.py`

Implémentation pour Gmail API avec OAuth2.

**Scopes OAuth2:**
```python
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]
```

**Credentials format:**
```python
{
    "token": str,              # Access token
    "refresh_token": str,      # Refresh token
    "token_uri": str,          # OAuth2 endpoint
    "client_id": str,          # Google client ID
    "client_secret": str,      # Google client secret
    "scopes": List[str],       # Authorized scopes
    "expiry": str              # ISO format datetime
}
```

**Méthodes principales:**

#### `connect()`
Établit la connexion à Gmail API:
1. Build `Credentials` object depuis le dict
2. Vérifie l'expiration du token
3. Refresh automatiquement si expiré
4. Build le service Gmail API
5. Test avec `getProfile()`

#### `fetch_emails(folder, limit, since)`
Récupère les emails depuis Gmail:
1. Construit la query (labels + date filter)
2. `messages().list()` pour obtenir les IDs
3. Batch `messages().get()` pour les détails
4. Parse chaque message avec `_parse_gmail_message()`
5. Retourne la liste standardisée

#### `_parse_gmail_message(message)`
Parse un message Gmail API:
1. Extrait headers (Subject, From, Date, Message-ID)
2. Parse date (parsedate_to_datetime)
3. Extrait body (text/plain prioritaire, sinon HTML)
4. Liste attachments (filename, type, size)
5. Retourne dict standardisé

#### `move_email(message_id, destination_folder)`
Déplace un email (gestion des labels):
```python
body = {
    'addLabelIds': [destination_folder],
    'removeLabelIds': ['INBOX']
}
messages().modify(userId='me', id=message_id, body=body)
```

#### `delete_email(message_id, permanent)`
Supprime un email:
- `permanent=False`: `messages().trash()`
- `permanent=True`: `messages().delete()`

#### `get_refreshed_credentials()`
Retourne les credentials actuels (pour mise à jour DB si refresh).

**Méthodes privées:**

- `_build_credentials()`: Credentials dict → google.oauth2.credentials.Credentials
- `_refresh_token_if_needed()`: Auto-refresh si expiré
- `_fetch_message_details(message_id)`: Fetch un message spécifique
- `_extract_body(payload)`: Extraction récursive du corps (multipart)
- `_extract_attachments_info(payload)`: Liste des attachments

### 3. GmailOAuth2Manager

**Fichier**: `shared/oauth2_manager.py`

Gère le flow d'authentification OAuth2.

**Méthodes:**

#### `get_authorization_url()`
Génère l'URL d'autorisation Google:
```python
flow = InstalledAppFlow.from_client_config(client_config, scopes)
auth_url, _ = flow.authorization_url(
    access_type='offline',
    prompt='consent'
)
return auth_url
```

#### `exchange_code_for_token(authorization_code)`
Échange le code d'autorisation contre un token:
```python
flow.fetch_token(code=authorization_code)
creds = flow.credentials
return _credentials_to_dict(creds)
```

#### `interactive_auth_flow()`
Flow interactif complet (local server):
```python
flow.run_local_server(
    port=8080,
    access_type='offline',
    prompt='consent'
)
```

Lance un serveur local sur port 8080, ouvre le navigateur, attend le callback.

#### `refresh_access_token(credentials)`
Refresh un token expiré:
```python
creds = Credentials(**credentials)
creds.refresh(Request())
return _credentials_to_dict(creds)
```

### 4. Security Module

**Fichier**: `shared/security.py`

Gestion du chiffrement des credentials.

**Fonctions:**

```python
def encrypt_credentials(credentials: Dict[str, Any]) -> str:
    """Chiffre un dict en string base64."""
    f = Fernet(settings.ENCRYPTION_KEY)
    json_str = json.dumps(credentials)
    return f.encrypt(json_str.encode()).decode()

def decrypt_credentials(encrypted: str) -> Dict[str, Any]:
    """Déchiffre un string base64 en dict."""
    f = Fernet(settings.ENCRYPTION_KEY)
    decrypted = f.decrypt(encrypted.encode()).decode()
    return json.loads(decrypted)
```

**Algorithme**: Fernet (AES 128-bit CBC + HMAC)

### 5. Email Sync Task

**Fichier**: `worker/tasks/email_sync.py`

Orchestration de la synchronisation.

**Fonctions principales:**

#### `sync_account(account_id)`
Synchronise un compte:
1. Récupère les détails du compte (async)
2. Crée le connecteur approprié via `_get_connector()`
3. Fetch emails avec `connector.fetch_emails()`
4. Sauvegarde en DB avec `_save_emails()`
5. Update credentials si refresh avec `_update_credentials_if_refreshed()`
6. Cleanup

#### `_get_connector(account)`
Factory pattern pour créer le bon connecteur:
```python
if account_type == AccountType.GMAIL:
    credentials = decrypt_credentials(encrypted_creds)
    return GmailConnector(email_address, credentials)
elif account_type == AccountType.IMAP:
    password = decrypt_password(encrypted_creds)
    return ImapConnector(host, email_address, password)
```

#### `_update_credentials_if_refreshed(account_id, connector)`
Met à jour les credentials en DB si refresh:
```python
new_creds = connector.get_refreshed_credentials()
if new_creds:
    encrypted = encrypt_credentials(new_creds)
    account.encrypted_credentials = encrypted
    await db.commit()
```

## 🔐 Sécurité

### Token Storage

**Stockage:**
- Credentials chiffrés avec Fernet (AES 128-bit)
- Clé de chiffrement: `ENCRYPTION_KEY` dans `.env`
- Base64 encoding pour storage en DB

**Token Lifecycle:**
1. **Initial auth**: OAuth2 flow → credentials (access + refresh token)
2. **Chiffrement**: `encrypt_credentials()` → DB storage
3. **Usage**: `decrypt_credentials()` → Credentials object
4. **Refresh**: Auto si expiré → `encrypt_credentials()` → DB update

### Scopes minimaux

```python
SCOPES = [
    'gmail.readonly',   # Lecture seule
    'gmail.modify'      # Modification (labels, trash)
]
```

**Pas d'accès à:**
- `gmail.send` - Envoi d'emails
- `gmail.compose` - Création de brouillons
- Autres services Google (Drive, Calendar, etc.)

### Best Practices

1. **Rotation de clés**: Générer une nouvelle `ENCRYPTION_KEY` régulièrement
2. **Revocation**: Permettre aux users de révoquer l'accès
3. **Scopes minimum**: Ne demander que les permissions nécessaires
4. **Token refresh**: Automatique, transparent pour l'utilisateur
5. **Error handling**: Logs sans exposer les tokens

## 📊 Performance

### Gmail API vs IMAP

| Opération | Gmail API | IMAP |
|-----------|-----------|------|
| Fetch 50 emails | ~2-3s | ~8-12s |
| Parse attachments | Inclus | Extra fetches |
| Batch operations | Oui | Non |
| Rate limits | 1B req/day | Serveur-dependent |

### Optimisations

1. **Batch fetching**: Un seul appel API pour metadata + body
2. **Incremental sync**: `since` parameter pour fetch delta seulement
3. **Caching**: Credentials en mémoire pendant la sync
4. **Parallel**: Celery permet sync multi-comptes en parallèle

### Rate Limits

**Gmail API:**
- 1 billion quota units/day (par projet)
- 250 quota units/user/second
- Fetch message: 5 units
- List messages: 5 units

**Mitigation:**
- Incremental sync (pas de full re-fetch)
- Limit paramètre (max 50 par sync)
- Intervalle de sync configurable (5 min default)

## 🧪 Testing

### Test unitaire du connecteur

```bash
# Avec un compte Gmail configuré
docker-compose exec api python scripts/test_gmail_connector.py

# Lister les comptes Gmail
docker-compose exec api python scripts/test_gmail_connector.py list
```

### Test manuel

```python
from shared.integrations.gmail import GmailConnector

credentials = {
    "token": "...",
    "refresh_token": "...",
    "client_id": "...",
    "client_secret": "...",
    # ...
}

connector = GmailConnector("user@gmail.com", credentials)
connector.connect()

emails = connector.fetch_emails(limit=10)
for email in emails:
    print(email['subject'])

connector.disconnect()
```

### Test d'intégration

```bash
# Ajouter un compte
docker-compose exec api python scripts/add_email_account.py

# Forcer une sync immédiate
docker-compose exec worker celery -A worker.celery_app call worker.tasks.email_sync.sync_account --args='[1]'

# Vérifier les logs
docker-compose logs -f worker
```

## 🐛 Debugging

### Logs détaillés

```python
import logging
logging.getLogger('worker.connectors.gmail').setLevel(logging.DEBUG)
```

### Vérifier le token

```python
from shared.oauth2_manager import GmailOAuth2Manager

credentials = {...}
refreshed = GmailOAuth2Manager.refresh_access_token(credentials)
print(refreshed['expiry'])
```

### Test de connexion

```python
connector = GmailConnector(email, credentials)
result = connector.test_connection()
print(result)
```

## 📚 Références

- [Gmail API Reference](https://developers.google.com/gmail/api/reference/rest)
- [OAuth2 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Google Auth Library](https://google-auth.readthedocs.io/)
- [Fernet Encryption](https://cryptography.io/en/latest/fernet/)
