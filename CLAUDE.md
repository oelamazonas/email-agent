# 🤖 CLAUDE.md - Guide pour Claude Code & Assistants Anthropic

> **Audience** : Claude, Claude Code, et tous assistants IA Anthropic  
> **Objectif** : Contexte complet pour développer Email Agent AI de manière cohérente

---

## 🎯 Vision du projet

### Mission
Système de gestion d'emails intelligent, **self-hosted** et **privacy-first** qui :
- Trie automatiquement via IA (Ollama LLM local - pas de cloud)
- Support multi-comptes (Gmail, Outlook, IMAP)
- Coûte 0€/mois (Oracle Cloud Free Tier)
- Respect total de la vie privée (données 100% locales)

### Utilisateurs cibles
1. **Freelances/Consultants** : Auto-tri factures, projets
2. **Équipes/PME** : Classification support, projets
3. **Particuliers** : Inbox Zero, privacy
4. **Tech users** : Self-hosted, contrôle total

### Principes directeurs
✅ **Privacy-First** : Données locales uniquement  
✅ **Production-Ready** : Code professionnel, pas POC  
✅ **Developer-Friendly** : Code clair, bien documenté  
✅ **Extensible** : Architecture modulaire  
✅ **Gratuit** : Fonctionne sur Oracle Cloud Free Tier

---

## 🏗️ Architecture

### Stack technique

```yaml
Backend:
  Framework: FastAPI 0.109+ (async)
  ORM: SQLAlchemy 2.0+ (async)
  Queue: Celery 5.3+ + Redis
  Auth: JWT + Fernet encryption

Database:
  Primary: PostgreSQL 15 (Alpine)
  Cache: Redis 7 (Alpine)

AI/LLM:
  Runtime: Ollama (local)
  Model: Mistral 7B (default)
  Fallback: Anthropic API (optional)

Infrastructure:
  Containers: Docker + Docker Compose
  Reverse Proxy: Nginx (Alpine)
  Monitoring: Portainer

Email:
  Protocols: IMAP, Gmail API, MS Graph
  Libraries: imapclient, google-api-python-client, msal
```

### Services Docker

| Service | Port | Rôle |
|---------|------|------|
| api | 8000 | FastAPI backend |
| worker | - | Celery async workers |
| scheduler | - | Celery Beat (cron) |
| db | 5432 | PostgreSQL |
| redis | 6379 | Cache + Queue |
| ollama | 11434 | LLM local |
| nginx | 80/443 | Reverse proxy |

### Flux de données

```
1. Email Reception
   Email Account → Celery sync (poll 5min) → Parse → Save DB → Classify

2. Classification  
   Email → Check YAML rules → If uncertain → Ollama LLM → Update category → Execute action

3. User API
   HTTP Request → FastAPI → SQLAlchemy → PostgreSQL → JSON Response
```

---

## 📝 Conventions de code

### Python (PEP 8 + spécificités)

```python
# 1. Type hints OBLIGATOIRES
async def classify_email(
    email_id: int,
    force: bool = False
) -> dict[str, Any]:
    """Classify email using Ollama."""
    pass

# 2. Docstrings Google style
"""
Module pour classification d'emails.

Utilise Ollama LLM pour classification intelligente.
"""

# 3. Imports ordering
# Standard lib
import os
from datetime import datetime

# Third party
from fastapi import APIRouter
from sqlalchemy import select

# Local
from api.models import Email
from shared.config import settings

# 4. Naming
class EmailAccount:      # PascalCase classes
def sync_account():      # snake_case functions
MAX_RETRIES = 3          # UPPER_CASE constants
_helper_func()           # _private avec underscore

# 5. Async/await pour IO
async def get_email(db: AsyncSession, id: int) -> Email:
    result = await db.execute(select(Email).where(Email.id == id))
    return result.scalar_one_or_none()

# 6. Logging
import logging
logger = logging.getLogger(__name__)

logger.info("Normal operation")
logger.error("Error occurred", exc_info=True)  # Toujours exc_info=True
```

### Configuration centralisée

```python
# shared/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Configuration centralisée."""
    DATABASE_URL: str
    REDIS_URL: str
    OLLAMA_HOST: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "mistral"
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## 🎨 Patterns essentiels

### 1. Database Access

```python
from api.database import get_db

@router.get("/emails/{email_id}")
async def get_email(
    email_id: int,
    db: AsyncSession = Depends(get_db)  # Dependency injection
):
    result = await db.execute(select(Email).where(Email.id == email_id))
    email = result.scalar_one_or_none()
    if not email:
        raise HTTPException(status_code=404)
    return email
```

### 2. Celery Tasks

```python
from celery import shared_task

@shared_task(
    name='worker.tasks.email_sync.sync_account',
    bind=True,
    max_retries=3
)
def sync_account(self, account_id: int):
    """Sync emails from account."""
    try:
        logger.info(f"Syncing account {account_id}")
        
        # Import inside to avoid circular imports
        from api.database import get_db_context
        
        async with get_db_context() as db:
            # Your sync logic
            pass
            
        return {'status': 'success'}
    except Exception as exc:
        logger.error(f"Sync failed: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
```

### 3. Pydantic Models

```python
from pydantic import BaseModel, EmailStr, Field

# Request (input validation)
class EmailAccountCreate(BaseModel):
    """Model for creating account."""
    email_address: EmailStr
    account_type: str = Field(..., pattern="^(gmail|outlook|imap)$")
    display_name: str | None = None

# Response (output)
class EmailAccountResponse(BaseModel):
    """Model for responses."""
    id: int
    email_address: str
    is_active: bool
    
    class Config:
        from_attributes = True  # SQLAlchemy conversion
```

### 4. Error Handling

```python
# Custom exceptions
class EmailAgentException(Exception):
    """Base exception."""
    pass

class EmailNotFoundError(EmailAgentException):
    """Email not found."""
    pass

# Endpoint with proper handling
@router.post("/classify/{email_id}")
async def classify(email_id: int, db: AsyncSession = Depends(get_db)):
    try:
        email = await get_email(db, email_id)
        if not email:
            raise HTTPException(status_code=404, detail="Email not found")
        
        result = await classifier.classify(email)
        return result
        
    except ClassificationError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected: {e}", exc_info=True)
        raise HTTPException(status_code=500)
```

### 5. Ollama Integration

```python
class OllamaClassifier:
    """Email classifier using Ollama."""
    
    async def classify(self, email_data: dict) -> dict:
        """
        Classify email.
        
        Returns:
            {'category': str, 'confidence': int, 'reason': str}
        """
        # 1. Build prompt
        prompt = f"""Classify this email.

Email:
Subject: {email_data['subject']}
From: {email_data['sender']}

Respond ONLY with JSON:
{{"category": "invoice|receipt|...", "confidence": 0-100, "reason": "..."}}"""
        
        # 2. Call Ollama
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.1}
                }
            )
            result = response.json()
        
        # 3. Parse JSON response
        return self._parse(result['response'])
```

---

## 🗄️ Structure DB

### Modèles principaux

```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    email_accounts = relationship("EmailAccount")

class EmailAccount(Base):
    __tablename__ = "email_accounts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    account_type = Column(Enum(AccountType))  # gmail|outlook|imap
    email_address = Column(String(255), unique=True)
    encrypted_credentials = Column(Text)  # Fernet encrypted
    last_sync = Column(DateTime)
    emails = relationship("Email")

class Email(Base):
    __tablename__ = "emails"
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("email_accounts.id"))
    message_id = Column(String(500), unique=True, index=True)
    subject = Column(String(500))
    sender = Column(String(255), index=True)
    date_received = Column(DateTime, index=True)
    category = Column(Enum(EmailCategory), index=True)
    classification_confidence = Column(Integer)
    status = Column(Enum(ProcessingStatus), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Index recommandés

```sql
CREATE INDEX idx_emails_account_date ON emails(account_id, date_received DESC);
CREATE INDEX idx_emails_category ON emails(category, status);
```

---

## 🔒 Sécurité

### 1. Credentials Encryption

```python
from cryptography.fernet import Fernet
import json

def encrypt_credentials(creds: dict) -> str:
    """Encrypt avec Fernet."""
    cipher = Fernet(settings.ENCRYPTION_KEY.encode())
    return cipher.encrypt(json.dumps(creds).encode()).decode()

def decrypt_credentials(encrypted: str) -> dict:
    """Decrypt credentials."""
    cipher = Fernet(settings.ENCRYPTION_KEY.encode())
    return json.loads(cipher.decrypt(encrypted.encode()).decode())
```

### 2. JWT Auth

```python
from jose import jwt
from datetime import datetime, timedelta

def create_token(user_id: int) -> str:
    """Create JWT token."""
    expire = datetime.utcnow() + timedelta(minutes=settings.TOKEN_EXPIRE)
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        settings.SECRET_KEY,
        algorithm="HS256"
    )
```

---

## 🗺️ Roadmap & TODOs

### ✅ Phase 1: Core Connectors (COMPLÉTÉE - 2026-01-20)

**Status**: Tous les connecteurs sont implémentés et fonctionnels!

**Localisation**: `shared/integrations/`

**Connecteurs disponibles**:

1. **✅ IMAP Connector** (`shared/integrations/imap.py`)
   - Connect SSL
   - Authenticate
   - Fetch since last_sync
   - Parse MIME
   - Handle attachments
   - Move/delete emails
   - Documentation: `docs/CONNECTOR_REFACTORING.md`

2. **✅ Gmail Connector** (`shared/integrations/gmail.py`)
   - OAuth2 flow (GmailOAuth2Manager)
   - Token refresh automatique
   - Fetch via Gmail API
   - Batch operations
   - Move/delete emails
   - Documentation: `docs/GMAIL_SETUP.md`, `docs/GMAIL_CONNECTOR.md`

3. **✅ Microsoft Connector** (`shared/integrations/microsoft.py`)
   - OAuth2 MSAL (MicrosoftOAuth2Manager)
   - Microsoft Graph API
   - Fetch messages
   - Move/delete emails
   - Documentation: `docs/MICROSOFT_SETUP.md`, `docs/MICROSOFT_CONNECTOR.md`

**Structure commune**:
- Tous héritent de `BaseEmailConnector` (`shared/integrations/base.py`)
- Credentials chiffrées en DB (Fernet)
- Refresh automatique des tokens OAuth2
- Intégration dans `worker/tasks/email_sync.py`
- Scripts de test disponibles: `scripts/test_*_connector.py`

### ✅ Phase 2: Actions (COMPLÉTÉE - 2026-01-21)

**Status**: Tous les composants d'actions sont implémentés et testés!

**Localisation**: `worker/actions/` et `worker/rules/`

**Composants implémentés**:

1. **✅ Classification Rules System** (`worker/rules/rules_parser.py`)
   - YAML-based rules engine
   - Priority-based rule matching
   - Multiple condition types (sender, subject, body, attachments)
   - Default rules: `rules/global_rules.yaml`
   - Documentation: `docs/PHASE_2_ACTIONS.md`

2. **✅ Email Actions Module** (`worker/actions/email_actions.py`)
   - `apply_classification_action()` - Apply actions based on classification
   - `bulk_move_emails()` - Batch move operation with error handling
   - `apply_label()` - Gmail label support
   - `bulk_classify_pending_emails()` - Process pending emails
   - Full action logging to ProcessingLog table

3. **✅ Celery Integration** (`worker/tasks/email_classification.py`)
   - `classify_pending_emails` - Scheduled task (every 10 min)
   - `classify_single_email` - On-demand classification
   - Auto-trigger after email sync

4. **✅ Action Logging**
   - All actions logged to `processing_logs` table
   - Tracks success/failure, details, timestamps
   - Full audit trail for compliance

5. **✅ Test Suite**
   - `tests/test_email_actions.py` - 8 comprehensive tests
   - `tests/test_rules_parser.py` - 11 rule parsing tests
   - All tests passing ✅

**Workflow**:
```
Email Sync → Rules Check → LLM (if needed) → Actions → Logging
     ↓            ↓              ↓              ↓         ↓
  Phase 1    Phase 2        Phase 2        Phase 2   Phase 2
```

**Documentation**: Voir `docs/PHASE_2_ACTIONS.md` pour détails complets

### Phase 3: Advanced (PRIORITÉ MOYENNE)

```python
# 1. OCR pour factures
class InvoiceExtractor:
    """
    TODO:
    - OCR PDF
    - Extract montant, date, IBAN
    - Store structured data
    """

# 2. Fine-tuning
class ModelFineTuner:
    """
    TODO:
    - Collect corrections
    - Build dataset
    - Fine-tune Ollama
    """

# 3. Adaptive scheduling
class AdaptiveScheduler:
    """
    TODO:
    - Analyze patterns
    - Adjust sync frequency
    - Per-account schedule
    """
```

### Phase 4: UI (PRIORITÉ MOYENNE)

```
frontend/ (React + TypeScript)
├── Dashboard.tsx
├── EmailList.tsx  
├── AccountSetup.tsx
└── Rules.tsx
```

---

## 🧪 Tests

### Structure

```
tests/
├── test_api/
│   ├── test_auth.py
│   ├── test_accounts.py
│   └── test_emails.py
├── test_workers/
│   └── test_classification.py
└── test_integration/
    └── test_full_flow.py
```

### Exemple

```python
@pytest.mark.asyncio
async def test_classify_invoice(client: AsyncClient):
    response = await client.post("/api/classification/test", json={
        "subject": "Facture Jan 2025",
        "sender": "compta@entreprise.be",
        "body_preview": "Montant: 1250€"
    })
    
    assert response.status_code == 200
    assert response.json()["category"] == "invoice"
    assert response.json()["confidence"] >= 80
```

---

## 📌 Checklist pour Claude

Quand tu codes pour ce projet, TOUJOURS :

✅ **Async/await** pour toutes opérations IO  
✅ **Type hints** partout  
✅ **Docstrings** Google style  
✅ **Logging** approprié (info/error avec exc_info)  
✅ **Error handling** robuste (try/except, jamais silent fail)  
✅ **Tests** pytest pour nouvelles features  
✅ **Sécurité** : Credentials chiffrés, validation input  
✅ **Performance** : Index DB, caching, batch operations  

### Template nouveau module

```python
"""
Module description.

This module handles X for Email Agent AI.
"""
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Constants
CONSTANT_NAME = "value"

# Your code here

class YourClass:
    """Class description."""
    
    def __init__(self):
        pass
    
    async def method(self, param: str) -> dict[str, Any]:
        """
        Method description.
        
        Args:
            param: Parameter description
            
        Returns:
            Dict with results
        """
        pass
```

### Workflow développement

```bash
# 1. Créer branche
git checkout -b feature/gmail-oauth

# 2. Coder + Tester
docker-compose -f docker-compose.dev.yml up
pytest tests/

# 3. Commit
git commit -m "feat: Add Gmail OAuth2"

# 4. Push + PR
git push origin feature/gmail-oauth
```

### Migrations DB

```bash
# Modifier api/models.py
# Puis:
docker-compose exec api alembic revision --autogenerate -m "Description"
docker-compose exec api alembic upgrade head
```

---

## 🎯 Rappels finaux

### Philosophie du code
- **Clarté > Cleverness** : Code simple et lisible
- **Safety > Speed** : Sécurité avant performance
- **Docs > Assumptions** : Documenter plutôt que supposer

### Ressources
- **README.md** : Vue d'ensemble
- **api/models.py** : Schéma DB
- **worker/classifiers/ollama_classifier.py** : Classification
- **shared/config.py** : Configuration

### Questions fréquentes

**Q: Où ajouter un nouveau endpoint ?**  
A: `api/routers/` + importer dans `api/main.py`

**Q: Comment ajouter une tâche Celery ?**  
A: `worker/tasks/` avec `@shared_task` + importer dans `worker/celery_app.py`

**Q: Comment tester localement ?**  
A: `docker-compose -f docker-compose.dev.yml up`

**Q: Où sont les credentials ?**  
A: `.env` (jamais committés), chiffrés en DB avec Fernet

---

**Ce guide est ta référence principale. Consulte-le AVANT de développer.** 🚀

**Version**: 1.2.0 | **Dernière mise à jour**: 2026-01-21 | **Phase 1 & 2: ✅ COMPLÉTÉES**
