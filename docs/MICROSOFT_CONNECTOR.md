# 🔧 Microsoft Connector - Documentation technique

> Documentation complète de l'architecture et de l'implémentation du **MicrosoftConnector** pour Email Agent AI.

---

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Architecture](#architecture)
3. [Composants](#composants)
4. [Flow de données](#flow-de-données)
5. [API Microsoft Graph](#api-microsoft-graph)
6. [Gestion des tokens](#gestion-des-tokens)
7. [Sécurité](#sécurité)
8. [Performance](#performance)
9. [Tests](#tests)

---

## 🎯 Vue d'ensemble

### Objectif

Fournir un connecteur robuste et performant pour intégrer les comptes **Microsoft 365**, **Outlook.com**, et **Office 365** via la **Microsoft Graph API** avec authentification **OAuth2**.

### Caractéristiques principales

- ✅ **OAuth2 Device Code Flow**: Authentification sécurisée sans mot de passe
- ✅ **Refresh automatique**: Tokens refresh en arrière-plan
- ✅ **Graph API v1.0**: API REST moderne et stable
- ✅ **MSAL Integration**: Utilise Microsoft Authentication Library
- ✅ **Multi-tenant**: Support des comptes personnels et professionnels
- ✅ **Error Handling**: Gestion robuste des erreurs et retry logic
- ✅ **Backward Compatible**: Fallback IMAP si OAuth2 non disponible

---

## 🏗️ Architecture

### Hiérarchie des classes

```
BaseEmailConnector (ABC)
    ↓
MicrosoftConnector
    ├── _session: requests.Session
    ├── token: str
    ├── refresh_token: str
    ├── expiry: datetime
    └── Methods:
        ├── connect()
        ├── disconnect()
        ├── fetch_emails()
        ├── move_email()
        ├── delete_email()
        └── _refresh_access_token()
```

### Fichiers du connecteur

```
shared/
├── integrations/
│   ├── base.py                 # BaseEmailConnector (abstract)
│   ├── microsoft.py            # ✅ MicrosoftConnector
│   └── __init__.py             # Exports
├── oauth2_manager.py           # ✅ MicrosoftOAuth2Manager
├── security.py                 # Encryption/Decryption
└── config.py                   # Settings (MICROSOFT_CLIENT_ID, etc.)

worker/
└── tasks/
    └── email_sync.py           # ✅ Integration dans _get_connector()

scripts/
├── add_email_account.py        # ✅ Setup interactif
└── test_microsoft_connector.py # ✅ Tests manuels
```

---

## 🧩 Composants

### 1. MicrosoftConnector

**Localisation**: `shared/integrations/microsoft.py`

#### Constructeur

```python
def __init__(self, email_address: str, credentials: Dict[str, Any]):
    """
    Initialise le connecteur Microsoft.

    Args:
        email_address: Adresse email Outlook/Office 365
        credentials: Dict avec OAuth2 credentials:
            {
                "token": str,              # Access token
                "refresh_token": str,       # Refresh token
                "client_id": str,           # Azure AD client ID
                "client_secret": str,       # Client secret (optionnel)
                "tenant_id": str,           # Tenant ID (default: 'common')
                "scopes": List[str],        # Authorized scopes
                "expiry": str               # ISO format datetime
            }
    """
```

#### Méthodes principales

##### `connect() -> None`

Établit la connexion à Microsoft Graph API.

```python
def connect(self) -> None:
    """
    1. Vérifie l'expiration du token
    2. Refresh si nécessaire
    3. Crée une session HTTP avec Authorization header
    4. Test la connexion avec GET /me

    Raises:
        ConnectionError: Si la connexion échoue
    """
```

**Exemple d'utilisation**:
```python
connector = MicrosoftConnector(email, credentials)
connector.connect()
# Session active avec token valide
```

##### `fetch_emails() -> List[Dict[str, Any]]`

Récupère les emails depuis Microsoft Graph API.

```python
def fetch_emails(
    self,
    folder: str = "INBOX",
    limit: int = 50,
    since: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Récupère les emails via GET /me/mailFolders/{folder}/messages

    Args:
        folder: Nom du dossier (INBOX, SENT, etc.)
        limit: Nombre max d'emails (max 999 par requête Graph)
        since: Date à partir de laquelle récupérer

    Returns:
        Liste de dicts avec format standard:
        [
            {
                "message_id": str,        # Internet Message-ID
                "microsoft_id": str,      # Graph ID (pour operations)
                "subject": str,
                "sender": str,
                "date_received": datetime,
                "body": str,              # Preview (premiers 2000 chars)
                "has_attachments": bool,
                "attachment_count": int,
                "attachments": []
            }
        ]
    """
```

**Query parameters utilisés**:
```python
params = {
    '$top': min(limit, 999),                          # Max per request
    '$orderby': 'receivedDateTime desc',              # Tri
    '$select': 'id,subject,from,receivedDateTime,...',# Fields
    '$filter': f'receivedDateTime ge {since_str}'     # Date filter
}
```

##### `move_email() -> bool`

Déplace un email vers un autre dossier.

```python
def move_email(self, message_id: str, destination_folder: str) -> bool:
    """
    Déplace via POST /me/messages/{id}/move

    Args:
        message_id: Microsoft Graph ID (pas Internet Message-ID)
        destination_folder: Nom du dossier de destination

    Returns:
        True si succès, False sinon
    """
```

##### `delete_email() -> bool`

Supprime un email (soft ou hard delete).

```python
def delete_email(self, message_id: str, permanent: bool = False) -> bool:
    """
    Supprime un email.

    Args:
        message_id: Microsoft Graph ID
        permanent: Si True, suppression définitive (DELETE)
                   Si False, déplace vers Deleted Items (POST /move)

    Returns:
        True si succès
    """
```

##### `_refresh_access_token() -> None`

Refresh le token OAuth2 avec MSAL.

```python
def _refresh_access_token(self) -> None:
    """
    1. Instancie MSAL app (PublicClient ou ConfidentialClient)
    2. Appelle acquire_token_by_refresh_token()
    3. Met à jour self.token, self.refresh_token, self.expiry

    Raises:
        ConnectionError: Si le refresh échoue
    """
```

**Logic**:
```python
if self.client_secret:
    app = ConfidentialClientApplication(
        self.client_id,
        authority=f"https://login.microsoftonline.com/{self.tenant_id}",
        client_credential=self.client_secret
    )
else:
    app = PublicClientApplication(
        self.client_id,
        authority=f"https://login.microsoftonline.com/{self.tenant_id}"
    )

result = app.acquire_token_by_refresh_token(
    self.refresh_token,
    scopes=self.scopes
)
```

---

### 2. MicrosoftOAuth2Manager

**Localisation**: `shared/oauth2_manager.py`

Gère le flow OAuth2 pour obtenir les credentials initiaux.

#### Méthodes principales

##### `interactive_auth_flow() -> Dict[str, Any]`

Lance le **Device Code Flow** interactif.

```python
def interactive_auth_flow(self) -> Dict[str, Any]:
    """
    Device Code Flow pour applications sans navigateur.

    Process:
        1. Initiate device flow → Obtient code + URL
        2. Affiche instructions à l'utilisateur
        3. Attend que l'utilisateur valide sur microsoft.com/devicelogin
        4. Acquire token → Obtient access + refresh token

    Returns:
        Dict avec credentials:
        {
            "token": str,
            "refresh_token": str,
            "client_id": str,
            "client_secret": str,  # Si fourni
            "tenant_id": str,
            "scopes": List[str],
            "expiry": str
        }
    """
```

**Exemple d'output**:
```
============================================================
Microsoft OAuth2 - Device Code Flow
============================================================
To sign in, use a web browser to open the page
https://microsoft.com/devicelogin and enter the code
A1B2C3D4 to authenticate.
============================================================
```

##### `refresh_access_token() -> Dict[str, Any]`

Refresh un token expiré (méthode statique).

```python
@staticmethod
def refresh_access_token(credentials: Dict[str, Any]) -> Dict[str, Any]:
    """
    Refresh le token avec MSAL.

    Args:
        credentials: Dict avec credentials actuels

    Returns:
        Dict avec nouveaux credentials
    """
```

---

### 3. Integration dans email_sync.py

**Localisation**: `worker/tasks/email_sync.py`

#### Factory Pattern

```python
def _get_connector(account: Dict[str, Any]):
    """
    Créer le connecteur approprié selon le type de compte.

    Args:
        account: Dict avec:
            - type: AccountType (IMAP, GMAIL, OUTLOOK)
            - email: str
            - encrypted_credentials: str

    Returns:
        Instance du connecteur approprié
    """
    account_type = account['type']

    if account_type == AccountType.OUTLOOK:
        # Déchiffrer les credentials OAuth2
        credentials = decrypt_credentials(account['encrypted_credentials'])

        # Vérifier si c'est OAuth2 ou IMAP
        if credentials.get('type') == 'imap':
            # Fallback IMAP
            return ImapConnector(
                email_address=account['email'],
                credentials=credentials
            )
        else:
            # OAuth2 (Graph API)
            return MicrosoftConnector(
                email_address=account['email'],
                credentials=credentials
            )
```

#### Sync Flow

```python
@shared_task(name='worker.tasks.email_sync.sync_account')
def sync_account(account_id: int):
    """
    1. Récupérer account details
    2. Créer connector via _get_connector()
    3. Fetch emails
    4. Sauvegarder en DB
    5. Update credentials si refresh (OAuth2)
    6. Cleanup
    """
    account = asyncio.run(_get_account_details(account_id))
    connector = _get_connector(account)
    emails = connector.fetch_emails(limit=50, since=account['last_sync'])
    saved_count = asyncio.run(_save_emails(account_id, emails))

    # Sauvegarder les tokens refresh
    asyncio.run(_update_credentials_if_refreshed(account_id, connector))

    connector.disconnect()
```

---

## 📊 Flow de données

### Diagramme de séquence complet

```
┌──────┐         ┌────────┐         ┌─────────┐         ┌──────────┐         ┌────┐
│ User │         │ Script │         │ Azure AD│         │  Worker  │         │ DB │
└──┬───┘         └───┬────┘         └────┬────┘         └────┬─────┘         └─┬──┘
   │                 │                   │                   │                  │
   │ add account     │                   │                   │                  │
   ├────────────────>│                   │                   │                  │
   │                 │ device flow start │                   │                  │
   │                 ├──────────────────>│                   │                  │
   │                 │  code + URL       │                   │                  │
   │                 │<──────────────────┤                   │                  │
   │<────────────────┤                   │                   │                  │
   │ Visit URL       │                   │                   │                  │
   ├─────────────────────────────────────>│                   │                  │
   │ Enter code      │                   │                   │                  │
   ├─────────────────────────────────────>│                   │                  │
   │ Login + consent │                   │                   │                  │
   ├─────────────────────────────────────>│                   │                  │
   │                 │  tokens           │                   │                  │
   │                 │<──────────────────┤                   │                  │
   │                 │ encrypt           │                   │                  │
   │                 │─┐                 │                   │                  │
   │                 │<┘                 │                   │                  │
   │                 │ INSERT account    │                   │                  │
   │                 ├──────────────────────────────────────────────────────────>│
   │                 │                   │                   │                  │
   │                 │                   │  Celery Beat (5min)                  │
   │                 │                   │                   │<─────────────────┤
   │                 │                   │                   │ SELECT account   │
   │                 │                   │                   ├─────────────────>│
   │                 │                   │                   │ credentials      │
   │                 │                   │                   │<─────────────────┤
   │                 │                   │                   │ decrypt          │
   │                 │                   │                   │─┐                │
   │                 │                   │                   │<┘                │
   │                 │                   │ GET /me/messages  │                  │
   │                 │                   │<──────────────────┤                  │
   │                 │                   │ emails            │                  │
   │                 │                   ├──────────────────>│                  │
   │                 │                   │                   │ INSERT emails    │
   │                 │                   │                   ├─────────────────>│
   │                 │                   │                   │ UPDATE last_sync │
   │                 │                   │                   ├─────────────────>│
```

---

## 🌐 API Microsoft Graph

### Endpoints utilisés

| Endpoint | Méthode | Usage |
|----------|---------|-------|
| `/me` | GET | Test connexion, obtenir profil |
| `/me/mailFolders/{folder}/messages` | GET | Lister les emails |
| `/me/messages/{id}` | GET | Obtenir détails email |
| `/me/messages/{id}/move` | POST | Déplacer email |
| `/me/messages/{id}` | DELETE | Supprimer email |
| `/me/mailFolders` | GET | Lister dossiers |

### Query Parameters

```python
# Standard query pour fetch_emails
params = {
    '$top': 50,                                      # Pagination
    '$skip': 0,                                      # Offset
    '$orderby': 'receivedDateTime desc',             # Tri
    '$select': 'id,subject,from,receivedDateTime',   # Projection
    '$filter': 'receivedDateTime ge 2025-01-01',     # Filtrage
    '$expand': 'attachments'                         # Expand relations
}
```

### Headers requis

```python
headers = {
    'Authorization': f'Bearer {access_token}',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}
```

### Format de réponse

```json
{
  "@odata.context": "https://graph.microsoft.com/v1.0/$metadata#users('...')/mailFolders('inbox')/messages",
  "@odata.count": 50,
  "value": [
    {
      "id": "AAMkAGI2...",
      "subject": "Test email",
      "from": {
        "emailAddress": {
          "name": "John Doe",
          "address": "john@example.com"
        }
      },
      "receivedDateTime": "2025-01-20T10:30:00Z",
      "bodyPreview": "This is a preview...",
      "hasAttachments": true
    }
  ]
}
```

---

## 🔐 Gestion des tokens

### Structure des tokens

```python
credentials = {
    "token": "EwBYA8l6BAAURSNgAESL4AKxR7...",     # Access token (1 hour)
    "refresh_token": "0.AXEA7Dk...",             # Refresh token (90 days)
    "client_id": "12345678-...",
    "client_secret": "xxx",                      # Optionnel
    "tenant_id": "common",
    "scopes": [
        "https://graph.microsoft.com/Mail.Read",
        "https://graph.microsoft.com/Mail.ReadWrite"
    ],
    "expiry": "2025-01-20T11:30:00"              # ISO format
}
```

### Lifecycle des tokens

```
1. Initial Auth (Device Code Flow)
   ↓
2. Access Token (valid 1 hour)
   ↓
3. Token Expiry Detection (_is_token_expired)
   ↓
4. Automatic Refresh (_refresh_access_token)
   ↓
5. Update in DB (_update_credentials_if_refreshed)
   ↓
6. Continue Operations
   ↓
   (Refresh token valid 90 days)
```

### Code de refresh

```python
def _is_token_expired(self) -> bool:
    """
    Vérifier si le token est expiré.

    Returns:
        True si expiré ou expiration dans moins de 5 minutes
    """
    if not self.expiry:
        return True

    # Buffer de 5 minutes
    buffer = timedelta(minutes=5)
    return datetime.utcnow() >= (self.expiry - buffer)
```

---

## 🔒 Sécurité

### 1. Encryption en DB

Toutes les credentials sont chiffrées avec **Fernet (AES 128-bit)**:

```python
# shared/security.py
from cryptography.fernet import Fernet

cipher = Fernet(settings.ENCRYPTION_KEY.encode())

# Encrypt
encrypted = cipher.encrypt(json.dumps(credentials).encode()).decode()

# Decrypt
decrypted = json.loads(cipher.decrypt(encrypted.encode()).decode())
```

### 2. Permissions granulaires

Scopes minimaux requis:

```python
SCOPES = [
    'https://graph.microsoft.com/Mail.Read',         # Lecture emails
    'https://graph.microsoft.com/Mail.ReadWrite',    # Modification emails
    'offline_access'                                 # Refresh token
]
```

### 3. Token rotation

- **Access token**: 1 heure → Refresh automatique
- **Refresh token**: 90 jours → Require ré-authentification si expiré

### 4. Error handling

```python
try:
    response = self._session.get(endpoint)
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        # Token invalide → Re-authenticate
        logger.error("Invalid token, re-authentication required")
    elif e.response.status_code == 429:
        # Rate limit → Retry avec backoff
        logger.warning("Rate limit exceeded, backing off")
```

---

## ⚡ Performance

### Optimisations

1. **Batch Requests**: Graph API supporte jusqu'à 20 requests par batch
2. **Pagination**: Fetch par pages de 50 emails (max 999)
3. **Select Fields**: Ne récupérer que les champs nécessaires (`$select`)
4. **Filter Server-Side**: Utiliser `$filter` plutôt que filtrer en Python
5. **Session Reuse**: `requests.Session` pour connection pooling

### Metrics

| Opération | Temps moyen |
|-----------|-------------|
| `connect()` | ~200ms |
| `fetch_emails(50)` | ~500ms |
| `move_email()` | ~150ms |
| `delete_email()` | ~100ms |
| `_refresh_access_token()` | ~300ms |

### Rate Limits

Microsoft Graph impose des limites:
- **10 000 requests / 10 minutes** par application/tenant
- **1 000 requests / minute** par mailbox

Notre stratégie:
- Sync toutes les 5 minutes (Celery Beat)
- Max 50 emails par sync
- Backoff exponentiel si 429 (Rate Limit)

---

## 🧪 Tests

### Test manuel

```bash
# Test du connecteur
python scripts/test_microsoft_connector.py

# Test OAuth2 flow
python scripts/test_microsoft_connector.py oauth
```

### Test unitaire

```python
# tests/test_integrations/test_microsoft.py

@pytest.fixture
def microsoft_connector():
    credentials = {
        "token": "fake_token",
        "refresh_token": "fake_refresh",
        "client_id": "fake_id",
        "tenant_id": "common",
        "scopes": [...],
        "expiry": (datetime.utcnow() + timedelta(hours=1)).isoformat()
    }
    return MicrosoftConnector("test@outlook.com", credentials)

def test_connect(microsoft_connector, mocker):
    mock_session = mocker.patch('requests.Session.get')
    mock_session.return_value.status_code = 200

    microsoft_connector.connect()

    assert microsoft_connector._session is not None
```

### Test d'intégration

```bash
# Sync complète d'un compte
docker-compose exec worker celery -A worker.celery_app call \
  worker.tasks.email_sync.sync_account --args='[1]'

# Vérifier les logs
docker-compose logs -f worker | grep microsoft
```

---

## 📚 Références

- **Microsoft Graph Mail API**: https://docs.microsoft.com/en-us/graph/api/resources/mail-api-overview
- **MSAL Python**: https://msal-python.readthedocs.io/
- **Device Code Flow**: https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-device-code
- **Graph API Best Practices**: https://docs.microsoft.com/en-us/graph/best-practices-concept

---

**✅ Documentation complète du MicrosoftConnector**
