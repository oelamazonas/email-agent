# Structure des Intégrations Email

Documentation de la structure et organisation des connecteurs email dans Email Agent AI.

## 📁 Structure des répertoires

```
email-agent/
├── shared/
│   └── integrations/          # ✅ NOUVEAU: Connecteurs centralisés
│       ├── __init__.py        # Exports publics
│       ├── base.py            # BaseEmailConnector (interface)
│       ├── imap.py            # ImapConnector
│       ├── gmail.py           # GmailConnector
│       └── microsoft.py       # (à venir) MicrosoftConnector
│
└── worker/
    └── connectors/            # ⚠️ DEPRECATED: Redirection pour compatibilité
        └── __init__.py        # Redirige vers shared/integrations
```

## 🎯 Rationale du changement

### Pourquoi `shared/integrations/` ?

1. **Cohérence avec CLAUDE.md**: Le guide du projet spécifie que les connecteurs doivent être dans `shared/integrations/`

2. **Séparation des responsabilités**:
   - `shared/`: Code réutilisable par tous les modules
   - `worker/`: Code spécifique aux tâches Celery
   - `api/`: Code spécifique à l'API FastAPI

3. **Réutilisabilité**:
   - Les connecteurs peuvent être utilisés par `worker/`, `api/`, et `scripts/`
   - Évite les imports circulaires
   - Facilite les tests unitaires

4. **Convention standard**:
   - `shared/` contient déjà `config.py`, `security.py`, `oauth2_manager.py`
   - Les intégrations externes suivent la même logique

## 📦 Imports

### ✅ Nouveau format (recommandé)

```python
# Import depuis shared/integrations
from shared.integrations import ImapConnector, GmailConnector, BaseEmailConnector

# Créer un connecteur
connector = ImapConnector(email, credentials)
```

### ⚠️ Ancien format (deprecated)

```python
# Import depuis worker/connectors (deprecated)
from worker.connectors import ImapConnector  # Affiche un warning

# ⚠️ Ce code fonctionne encore mais génère un DeprecationWarning
```

## 🔄 Migration automatique

### Pour le code existant

**Aucune action immédiate requise** - La compatibilité est maintenue via `worker/connectors/__init__.py`:

```python
# worker/connectors/__init__.py
import warnings
from shared.integrations import BaseEmailConnector, ImapConnector, GmailConnector

warnings.warn(
    "worker.connectors is deprecated. Use 'from shared.integrations import ...' instead.",
    DeprecationWarning,
    stacklevel=2
)
```

### Migration recommandée

**Avant:**
```python
from worker.connectors.imap import ImapConnector
from worker.connectors.gmail import GmailConnector
```

**Après:**
```python
from shared.integrations import ImapConnector, GmailConnector
```

## 📝 Fichiers mis à jour

### Code source
- ✅ `shared/integrations/__init__.py` - Nouveau module principal
- ✅ `shared/integrations/base.py` - Déplacé depuis worker/connectors
- ✅ `shared/integrations/imap.py` - Déplacé depuis worker/connectors
- ✅ `shared/integrations/gmail.py` - Déplacé depuis worker/connectors
- ✅ `worker/connectors/__init__.py` - Redirection avec warning
- ✅ `worker/tasks/email_sync.py` - Imports mis à jour

### Scripts
- ✅ `scripts/test_imap_connector.py` - Imports mis à jour
- ✅ `scripts/test_gmail_connector.py` - Imports mis à jour

### Documentation
- ✅ `docs/CONNECTOR_REFACTORING.md` - Chemins mis à jour
- ✅ `docs/GMAIL_CONNECTOR.md` - Chemins mis à jour
- ✅ `docs/INTEGRATIONS_STRUCTURE.md` - Nouveau guide

## 🧪 Vérification

### Test des imports

```bash
# Depuis le conteneur Docker
docker-compose exec api python -c "from shared.integrations import ImapConnector, GmailConnector; print('✅ Imports OK')"

# Depuis la machine locale (si environnement Python configuré)
python -m py_compile shared/integrations/*.py
```

### Test de compatibilité rétroactive

```bash
# Vérifier que l'ancien import fonctionne (avec warning)
docker-compose exec api python -c "
import warnings
warnings.simplefilter('always')
from worker.connectors import ImapConnector
print('✅ Compatibilité OK')
"
```

### Test de synchronisation

```bash
# Forcer une sync pour vérifier que tout fonctionne
docker-compose exec worker celery -A worker.celery_app call \
  worker.tasks.email_sync.sync_account --args='[1]'

# Vérifier les logs
docker-compose logs -f worker | grep -i "connector\|sync"
```

## 📊 Hiérarchie des modules

```
shared/integrations/
│
├── base.py                    # Interface abstraite
│   └── BaseEmailConnector
│       ├── __init__(email, credentials)
│       ├── connect() [abstract]
│       ├── disconnect() [abstract]
│       ├── fetch_emails() [abstract]
│       ├── move_email() [abstract]
│       ├── delete_email() [abstract]
│       └── test_connection() [implémenté]
│
├── imap.py                    # Implémentation IMAP
│   └── ImapConnector(BaseEmailConnector)
│       ├── Tous les méthodes abstraites implémentées
│       └── ImapConnectorLegacy (deprecated)
│
└── gmail.py                   # Implémentation Gmail API
    └── GmailConnector(BaseEmailConnector)
        ├── Tous les méthodes abstraites implémentées
        └── OAuth2 avec refresh automatique
```

## 🔮 Future

### Prochains connecteurs

```python
# shared/integrations/microsoft.py
class MicrosoftConnector(BaseEmailConnector):
    """Microsoft Graph API avec OAuth2."""
    pass

# shared/integrations/exchange.py
class ExchangeConnector(BaseEmailConnector):
    """Exchange Web Services (EWS)."""
    pass

# shared/integrations/caldav.py
class CalDAVConnector(BaseEmailConnector):
    """CalDAV/CardDAV."""
    pass
```

### Structure finale attendue

```
shared/integrations/
├── __init__.py
├── base.py                    # BaseEmailConnector
├── imap.py                    # ImapConnector
├── gmail.py                   # GmailConnector
├── microsoft.py               # MicrosoftConnector (Q1 2025)
├── exchange.py                # ExchangeConnector (Q2 2025)
└── caldav.py                  # CalDAVConnector (Q3 2025)
```

## ✅ Checklist de migration

Pour migrer votre code:

- [ ] Remplacer `from worker.connectors import ...` par `from shared.integrations import ...`
- [ ] Vérifier que les imports fonctionnent (pas de ModuleNotFoundError)
- [ ] Tester la synchronisation avec vos comptes configurés
- [ ] Mettre à jour votre documentation locale si applicable
- [ ] Supprimer les imports deprecated quand tous les warnings sont résolus

## 📚 Références

- **Structure principale**: `shared/integrations/__init__.py`
- **Interface de base**: `shared/integrations/base.py`
- **IMAP**: `shared/integrations/imap.py`
- **Gmail**: `shared/integrations/gmail.py`
- **Synchronisation**: `worker/tasks/email_sync.py`
- **Tests**: `scripts/test_*_connector.py`

## ⚠️ Notes importantes

1. **Ne pas supprimer `worker/connectors/`** pour l'instant - il assure la compatibilité
2. **Warnings sont normaux** - ils encouragent la migration vers le nouveau chemin
3. **Tous les tests passent** - la compatibilité est garantie
4. **Migration progressive** - pas besoin de tout migrer d'un coup

## 🆘 Dépannage

### Erreur: `ModuleNotFoundError: No module named 'shared.integrations'`

**Solution**: Vérifier que vous êtes dans l'environnement Docker ou que votre PYTHONPATH inclut le répertoire racine:

```bash
export PYTHONPATH=/Users/eric/Developer/I39/email-agent:$PYTHONPATH
```

### Warning: `DeprecationWarning: worker.connectors is deprecated`

**Solution**: C'est normal - remplacez l'import par:

```python
from shared.integrations import ImapConnector, GmailConnector
```

### Tests échouent après migration

**Solution**: Vérifier les imports dans vos tests et scripts:

```bash
grep -r "from worker.connectors" . --exclude-dir=docs
# Remplacer tous par "from shared.integrations"
```
