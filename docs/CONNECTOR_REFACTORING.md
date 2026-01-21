# Refactoring des Connecteurs Email

Documentation de la refactorisation des connecteurs email vers une architecture unifiée basée sur `BaseEmailConnector`.

## 🎯 Objectifs de la refactorisation

### Problèmes résolus

1. **Inconsistance des interfaces**: Chaque connecteur avait sa propre signature
2. **Duplication de code**: Pas de réutilisation entre connecteurs
3. **Testabilité**: Difficile de tester uniformément
4. **Extensibilité**: Ajout de nouveaux providers compliqué
5. **Maintenance**: Changements devant être dupliqués

### Architecture finale

```
BaseEmailConnector (interface abstraite)
├── ImapConnector (IMAP générique)
├── GmailConnector (Gmail API OAuth2)
└── MicrosoftConnector (à venir - MS Graph)
```

## 📋 Changements principaux

### 1. BaseEmailConnector (nouveau)

**Fichier**: `shared/integrations/base.py`

Classe abstraite définissant l'interface commune:

```python
class BaseEmailConnector(ABC):
    def __init__(self, email_address: str, credentials: Dict[str, Any])

    @abstractmethod
    def connect(self) -> None

    @abstractmethod
    def disconnect(self) -> None

    @abstractmethod
    def fetch_emails(...) -> List[Dict[str, Any]]

    @abstractmethod
    def move_email(message_id: str, destination_folder: str) -> bool

    @abstractmethod
    def delete_email(message_id: str, permanent: bool = False) -> bool

    def test_connection(self) -> Dict[str, Any]
```

### 2. ImapConnector refactorisé

**Changements:**

#### Avant (ancien format)
```python
connector = ImapConnector(
    host="imap.gmail.com",
    email_address="user@gmail.com",
    password="password",
    ssl=True
)
```

#### Après (nouveau format)
```python
credentials = {
    "type": "imap",
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "username": "user@gmail.com",
    "password": "password",
    "use_ssl": True
}

connector = ImapConnector(
    email_address="user@gmail.com",
    credentials=credentials
)
```

**Nouvelles méthodes implémentées:**

1. **move_email()**: Déplacer un email vers un dossier
2. **delete_email()**: Supprimer un email (soft ou permanent)
3. **test_connection()**: Héritée de BaseEmailConnector

**Améliorations:**

- ✅ Héritage de BaseEmailConnector
- ✅ Format credentials unifié
- ✅ Méthodes privées (`_parse_email`, `_extract_body_and_attachments`)
- ✅ Meilleure gestion des erreurs
- ✅ Logging via `self.logger` (de BaseEmailConnector)
- ✅ Support complet IMAP UID pour opérations

### 3. GmailConnector (nouveau)

**Fichier**: `shared/integrations/gmail.py`

Implémentation complète Gmail API:

```python
credentials = {
    "token": "ya29...",
    "refresh_token": "1//0g...",
    "client_id": "...",
    "client_secret": "...",
    "scopes": [...],
    "expiry": "2025-01-21T10:00:00"
}

connector = GmailConnector(
    email_address="user@gmail.com",
    credentials=credentials
)
```

**Fonctionnalités:**
- OAuth2 avec refresh automatique
- Fetch emails avec labels Gmail
- Move/delete via labels et trash
- Parsing optimisé des messages
- Token refresh transparent

## 🔧 Migration

### Code utilisant ImapConnector

#### Ancien code
```python
from shared.integrations.imap import ImapConnector

connector = ImapConnector(
    host="imap.gmail.com",
    email_address=email,
    password=password
)
```

#### Nouveau code
```python
from shared.integrations.imap import ImapConnector

credentials = {
    "type": "imap",
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "username": email,
    "password": password,
    "use_ssl": True
}

connector = ImapConnector(
    email_address=email,
    credentials=credentials
)
```

#### Compatibilité temporaire

Pour faciliter la transition, `ImapConnectorLegacy` est disponible:

```python
from shared.integrations.imap import ImapConnectorLegacy

# Ancienne signature toujours supportée
connector = ImapConnectorLegacy(
    host="imap.gmail.com",
    email_address=email,
    password=password,
    ssl=True
)
```

⚠️ **DEPRECATED**: Cette classe sera retirée dans une future version.

### Données en DB

**Format credentials en DB:**

Les credentials sont stockés chiffrés (Fernet) en format JSON:

```python
# IMAP
{
    "type": "imap",
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "username": "user@gmail.com",
    "password": "app_password",
    "use_ssl": True
}

# Gmail OAuth2
{
    "token": "ya29...",
    "refresh_token": "1//0g...",
    "client_id": "...",
    "client_secret": "...",
    "scopes": [...],
    "expiry": "2025-01-21T10:00:00"
}
```

**Migration des comptes existants:**

Les comptes avec l'ancien format (password simple) sont automatiquement migrés lors de la synchronisation via la logique de fallback dans `email_sync.py`:

```python
def _get_connector(account):
    if account_type == AccountType.IMAP:
        credentials = decrypt_credentials(encrypted_creds)

        # Fallback pour ancien format
        if not isinstance(credentials, dict):
            credentials = {
                "type": "imap",
                "imap_server": auto_detect_host(email),
                "imap_port": 993,
                "username": email,
                "password": credentials,
                "use_ssl": True
            }

        return ImapConnector(email, credentials)
```

## 🧪 Tests

### Test unitaire IMAP

```bash
# Tester le connecteur IMAP
docker-compose exec api python scripts/test_imap_connector.py

# Lister les comptes IMAP
docker-compose exec api python scripts/test_imap_connector.py list

# Tester le format credentials
docker-compose exec api python scripts/test_imap_connector.py format
```

### Test unitaire Gmail

```bash
# Tester le connecteur Gmail
docker-compose exec api python scripts/test_gmail_connector.py

# Lister les comptes Gmail
docker-compose exec api python scripts/test_gmail_connector.py list
```

### Test d'intégration

```bash
# Forcer une sync complète
docker-compose exec worker celery -A worker.celery_app call \
  worker.tasks.email_sync.sync_account --args='[1]'

# Vérifier les logs
docker-compose logs -f worker | grep -i "connector\|sync"
```

## 📊 Comparaison des connecteurs

| Feature | ImapConnector | GmailConnector |
|---------|---------------|----------------|
| **Protocole** | IMAP | Gmail API |
| **Auth** | Password/App Password | OAuth2 |
| **Vitesse** | ~8-12s/50 emails | ~2-3s/50 emails |
| **Labels** | Limité | Support natif |
| **Batch ops** | Non | Oui |
| **Rate limits** | Variable serveur | 1B req/jour |
| **Token refresh** | N/A | Automatique |
| **Move** | COPY + DELETE | Label modification |
| **Delete** | Mark DELETED + EXPUNGE | trash() ou delete() |

## 🔐 Sécurité

### Stockage credentials

Tous les connecteurs utilisent le même système:

```python
from shared.security import encrypt_credentials, decrypt_credentials

# Chiffrement avant stockage DB
encrypted = encrypt_credentials(credentials_dict)
account.encrypted_credentials = encrypted

# Déchiffrement pour usage
credentials = decrypt_credentials(account.encrypted_credentials)
connector = ConnectorClass(email, credentials)
```

**Algorithme**: Fernet (AES 128-bit CBC + HMAC)

### Bonnes pratiques

1. **Jamais logger les credentials**: Utiliser `self.logger` qui filtre automatiquement
2. **Scopes minimaux**: OAuth2 avec permissions strictes
3. **Token rotation**: Gmail refresh automatique tous les ~60 min
4. **Chiffrement fort**: ENCRYPTION_KEY dans `.env` avec `Fernet.generate_key()`

## 🚀 Ajouter un nouveau connecteur

### Template

```python
from .base import BaseEmailConnector
from typing import Dict, Any, List, Optional
from datetime import datetime

class MyProviderConnector(BaseEmailConnector):
    """Connecteur pour MyProvider."""

    def __init__(self, email_address: str, credentials: Dict[str, Any]):
        super().__init__(email_address, credentials)

        # Extract provider-specific config
        self.api_key = credentials.get('api_key')
        self.endpoint = credentials.get('endpoint')

    def connect(self) -> None:
        """Établir connexion."""
        # Implement connection logic
        pass

    def disconnect(self) -> None:
        """Fermer connexion."""
        pass

    def fetch_emails(
        self,
        folder: str = "INBOX",
        limit: int = 50,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Fetch emails."""
        # Return standardized format
        return [
            {
                "message_id": str,
                "subject": str,
                "sender": str,
                "date_received": datetime,
                "body": str,
                "has_attachments": bool,
                "attachment_count": int,
                "attachments": List[Dict]
            }
        ]

    def move_email(self, message_id: str, destination_folder: str) -> bool:
        """Move email."""
        pass

    def delete_email(self, message_id: str, permanent: bool = False) -> bool:
        """Delete email."""
        pass
```

### Enregistrement

1. Ajouter dans `shared/integrations/__init__.py`:
```python
from .my_provider import MyProviderConnector

__all__ = [..., "MyProviderConnector"]
```

2. Ajouter dans `api/models.py`:
```python
class AccountType(str, enum.Enum):
    ...
    MYPROVIDER = "myprovider"
```

3. Ajouter dans `email_sync.py`:
```python
def _get_connector(account):
    ...
    elif account_type == AccountType.MYPROVIDER:
        credentials = decrypt_credentials(encrypted_creds)
        return MyProviderConnector(email, credentials)
```

## 📚 Références

- **Base Connector**: `shared/integrations/base.py`
- **IMAP Connector**: `shared/integrations/imap.py`
- **Gmail Connector**: `shared/integrations/gmail.py`
- **Sync Task**: `worker/tasks/email_sync.py`
- **Security**: `shared/security.py`

## ❓ FAQ

### Q: Mon ancien code IMAP ne fonctionne plus

**R**: Utilisez `ImapConnectorLegacy` temporairement ou migrez vers le nouveau format avec credentials dict.

### Q: Comment migrer mes comptes existants?

**R**: Aucune action nécessaire. La migration est automatique lors de la prochaine synchronisation.

### Q: Puis-je encore utiliser l'ancien format?

**R**: Oui via `ImapConnectorLegacy`, mais c'est DEPRECATED. Migrez dès que possible.

### Q: Quelle est la différence entre IMAP Gmail et Gmail API?

**R**: Gmail API est plus rapide, plus fiable, et offre plus de fonctionnalités. Préférez OAuth2 quand possible.

### Q: Comment tester mon connecteur?

**R**: Créez un script de test dans `scripts/test_my_connector.py` basé sur les exemples IMAP/Gmail.

## 🔄 Roadmap

### Court terme (Q1 2025)
- ✅ BaseEmailConnector (fait)
- ✅ ImapConnector refactorisé (fait)
- ✅ GmailConnector OAuth2 (fait)
- ⏳ MicrosoftConnector OAuth2 (en cours)

### Moyen terme (Q2 2025)
- ⏳ Webhook support (Gmail push notifications)
- ⏳ Batch operations optimization
- ⏳ Attachment download/storage
- ⏳ Advanced filtering

### Long terme (Q3-Q4 2025)
- ⏳ CalDAV/CardDAV support
- ⏳ Custom provider plugins
- ⏳ Multi-protocol unified inbox
