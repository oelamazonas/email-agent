# 📚 Email Agent AI - Index Documentation

Guide de navigation pour toute la documentation du projet.

---

## 📂 Structure de la documentation

```
docs/
├── guides/           → Guides d'utilisation pour les utilisateurs
└── tech_doc/         → Documentation technique pour les développeurs
    ├── notes/        → Notes de développement et résumés de sessions
    └── *.md          → Documentation technique principale
```

---

## 🚀 Démarrage Rapide

| Document | Description | Quand l'utiliser |
|----------|-------------|------------------|
| [docs/guides/QUICK_START.md](docs/guides/QUICK_START.md) | Démarrage en 5 minutes | Première installation locale |
| [docs/guides/GMAIL_EXAMPLE.md](docs/guides/GMAIL_EXAMPLE.md) | Tutorial Gmail pas-à-pas | Premier ajout de compte Gmail |
| [docs/guides/ORACLE_CLOUD_QUICKSTART.md](docs/guides/ORACLE_CLOUD_QUICKSTART.md) | Guide Oracle Cloud | Déploiement sur Oracle Cloud |

---

## 📖 Guides d'Utilisation

**Localisation** : `docs/guides/`

### Démarrage & Installation
| Document | Description | Niveau |
|----------|-------------|--------|
| [QUICK_START.md](docs/guides/QUICK_START.md) | Guide de démarrage général | 🟢 Débutant |
| [QUICK_START_PHASE2.md](docs/guides/QUICK_START_PHASE2.md) | Démarrage avec actions Phase 2 | 🟢 Débutant |
| [ORACLE_CLOUD_QUICKSTART.md](docs/guides/ORACLE_CLOUD_QUICKSTART.md) | Démarrage Oracle Cloud | 🟡 Intermédiaire |

### Configuration des Comptes Email
| Document | Description | Niveau |
|----------|-------------|--------|
| [ADD_EMAIL_ACCOUNT.md](docs/guides/ADD_EMAIL_ACCOUNT.md) | Guide général tous fournisseurs | 🟢 Débutant |
| [GMAIL_EXAMPLE.md](docs/guides/GMAIL_EXAMPLE.md) | Tutorial Gmail complet | 🟢 Débutant |
| [GMAIL_SETUP.md](docs/guides/GMAIL_SETUP.md) | Configuration Gmail OAuth2 | 🟡 Intermédiaire |
| [MICROSOFT_SETUP.md](docs/guides/MICROSOFT_SETUP.md) | Configuration Microsoft OAuth2 | 🟡 Intermédiaire |

### Déploiement Oracle Cloud
| Document | Description | Niveau |
|----------|-------------|--------|
| [ORACLE_ARM_QUICK_REF.md](docs/guides/ORACLE_ARM_QUICK_REF.md) | Référence rapide Oracle | 🟡 Intermédiaire |
| [ORACLE_ARM_SETUP_SUMMARY.md](docs/guides/ORACLE_ARM_SETUP_SUMMARY.md) | Résumé configuration Oracle | 🟡 Intermédiaire |

---

## 🔧 Documentation Technique

**Localisation** : `docs/tech_doc/`

### Architecture & Développement
| Document | Description | Niveau |
|----------|-------------|--------|
| [CLAUDE.md](docs/tech_doc/CLAUDE.md) | **Guide développeur complet** | 🔴 Avancé |
| [AGENT.md](docs/tech_doc/AGENT.md) | Guide pour agents IA | 🔴 Avancé |
| [CHECKLIST.md](docs/tech_doc/CHECKLIST.md) | Checklist développement | 🟡 Intermédiaire |

### Connecteurs & Intégrations
| Document | Description | Niveau |
|----------|-------------|--------|
| [CONNECTOR_REFACTORING.md](docs/tech_doc/CONNECTOR_REFACTORING.md) | Architecture des connecteurs | 🔴 Avancé |
| [GMAIL_CONNECTOR.md](docs/tech_doc/GMAIL_CONNECTOR.md) | Connecteur Gmail détaillé | 🔴 Avancé |
| [MICROSOFT_CONNECTOR.md](docs/tech_doc/MICROSOFT_CONNECTOR.md) | Connecteur Microsoft détaillé | 🔴 Avancé |
| [INTEGRATIONS_STRUCTURE.md](docs/tech_doc/INTEGRATIONS_STRUCTURE.md) | Structure des intégrations | 🔴 Avancé |

### Phases de Développement
| Document | Description | Niveau |
|----------|-------------|--------|
| [PHASE_2_ACTIONS.md](docs/tech_doc/PHASE_2_ACTIONS.md) | Système d'actions email | 🔴 Avancé |
| [BATCH_PROCESSING_PLAN.md](docs/tech_doc/BATCH_PROCESSING_PLAN.md) | Plan traitement batch | 🔴 Avancé |

### Déploiement & Infrastructure
| Document | Description | Niveau |
|----------|-------------|--------|
| [DEPLOY_ORACLE_ARM.md](docs/tech_doc/DEPLOY_ORACLE_ARM.md) | Guide complet déploiement Oracle | 🔴 Avancé |
| [GITHUB_SETUP.md](docs/tech_doc/GITHUB_SETUP.md) | Configuration GitHub | 🟡 Intermédiaire |

### Notes de Développement
**Localisation** : `docs/tech_doc/notes/`

| Document | Description | Niveau |
|----------|-------------|--------|
| [MIGRATION_SUMMARY.md](docs/tech_doc/notes/MIGRATION_SUMMARY.md) | Notes de migration | 🟡 Intermédiaire |
| [MICROSOFT_IMPLEMENTATION_SUMMARY.md](docs/tech_doc/notes/MICROSOFT_IMPLEMENTATION_SUMMARY.md) | Notes implémentation Microsoft | 🟡 Intermédiaire |
| [PHASE2_COMPLETION_SUMMARY.md](docs/tech_doc/notes/PHASE2_COMPLETION_SUMMARY.md) | Notes achèvement Phase 2 | 🟡 Intermédiaire |

---

## 📄 Documents à la Racine

### Essentiels
| Document | Description |
|----------|-------------|
| [README.md](README.md) | Vue d'ensemble du projet |
| [CHANGELOG.md](CHANGELOG.md) | Historique des versions |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Guide de contribution |

### Gouvernance & Sécurité
| Document | Description |
|----------|-------------|
| [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Code de conduite |
| [SECURITY.md](SECURITY.md) | Politique de sécurité |
| [AUTHORS.md](AUTHORS.md) | Liste des auteurs |

---

## 🎯 Parcours par cas d'usage

### Je veux déployer en production sur Oracle Cloud

**Parcours recommandé :**
1. 📖 [ORACLE_ARM_QUICK_REF.md](docs/guides/ORACLE_ARM_QUICK_REF.md) - Lire en 5 min
2. 🚀 [scripts/deploy-oracle-arm.sh](scripts/deploy-oracle-arm.sh) - Exécuter
3. 📧 [GMAIL_EXAMPLE.md](docs/guides/GMAIL_EXAMPLE.md) - Ajouter premier compte
4. 📊 [ORACLE_ARM_SETUP_SUMMARY.md](docs/guides/ORACLE_ARM_SETUP_SUMMARY.md) - Référence technique
5. 🔧 [DEPLOY_ORACLE_ARM.md](docs/tech_doc/DEPLOY_ORACLE_ARM.md) - Guide technique complet

**Temps total : 30-40 minutes**

### Je veux développer localement

**Parcours recommandé :**
1. [README.md](README.md) - Vue d'ensemble
2. [docs/guides/QUICK_START.md](docs/guides/QUICK_START.md) - Installation
3. [docs/tech_doc/CLAUDE.md](docs/tech_doc/CLAUDE.md) - Architecture détaillée
4. [docs/tech_doc/CONNECTOR_REFACTORING.md](docs/tech_doc/CONNECTOR_REFACTORING.md) - Connecteurs

### Je veux ajouter un compte email

**Parcours recommandé :**
1. [docs/guides/GMAIL_EXAMPLE.md](docs/guides/GMAIL_EXAMPLE.md) - Si Gmail
2. [docs/guides/ADD_EMAIL_ACCOUNT.md](docs/guides/ADD_EMAIL_ACCOUNT.md) - Si autre fournisseur
3. [scripts/README.md](scripts/README.md) - Utilisation scripts

### Je veux comprendre l'architecture technique

**Parcours recommandé :**
1. [docs/tech_doc/CLAUDE.md](docs/tech_doc/CLAUDE.md) - Architecture globale
2. [docs/tech_doc/CONNECTOR_REFACTORING.md](docs/tech_doc/CONNECTOR_REFACTORING.md) - Connecteurs
3. [docs/tech_doc/PHASE_2_ACTIONS.md](docs/tech_doc/PHASE_2_ACTIONS.md) - Système d'actions

---

## 🔍 Recherche par mot-clé

### Gmail
- [docs/guides/GMAIL_EXAMPLE.md](docs/guides/GMAIL_EXAMPLE.md) - Tutorial complet
- [docs/guides/GMAIL_SETUP.md](docs/guides/GMAIL_SETUP.md) - OAuth2
- [docs/tech_doc/GMAIL_CONNECTOR.md](docs/tech_doc/GMAIL_CONNECTOR.md) - Connecteur technique
- [docs/guides/ADD_EMAIL_ACCOUNT.md](docs/guides/ADD_EMAIL_ACCOUNT.md) - Section Gmail

### Microsoft / Outlook
- [docs/guides/MICROSOFT_SETUP.md](docs/guides/MICROSOFT_SETUP.md) - OAuth2
- [docs/tech_doc/MICROSOFT_CONNECTOR.md](docs/tech_doc/MICROSOFT_CONNECTOR.md) - Connecteur technique
- [docs/tech_doc/notes/MICROSOFT_IMPLEMENTATION_SUMMARY.md](docs/tech_doc/notes/MICROSOFT_IMPLEMENTATION_SUMMARY.md) - Résumé

### Oracle Cloud / ARM
- [docs/guides/ORACLE_ARM_QUICK_REF.md](docs/guides/ORACLE_ARM_QUICK_REF.md) - Référence rapide
- [docs/guides/ORACLE_ARM_SETUP_SUMMARY.md](docs/guides/ORACLE_ARM_SETUP_SUMMARY.md) - Résumé config
- [docs/guides/ORACLE_CLOUD_QUICKSTART.md](docs/guides/ORACLE_CLOUD_QUICKSTART.md) - Guide démarrage
- [docs/tech_doc/DEPLOY_ORACLE_ARM.md](docs/tech_doc/DEPLOY_ORACLE_ARM.md) - Guide technique complet
- [docker-compose.oracle-arm.yml](docker-compose.oracle-arm.yml) - Configuration
- [.env.oracle-arm](.env.oracle-arm) - Variables

### Docker / Déploiement
- [docker-compose.yml](docker-compose.yml) - Local
- [docker-compose.oracle-arm.yml](docker-compose.oracle-arm.yml) - Oracle ARM
- [docker-compose.dev.yml](docker-compose.dev.yml) - Développement
- [scripts/deploy-oracle-arm.sh](scripts/deploy-oracle-arm.sh) - Script auto

### Architecture / Développement
- [docs/tech_doc/CLAUDE.md](docs/tech_doc/CLAUDE.md) - Guide complet
- [docs/tech_doc/CONNECTOR_REFACTORING.md](docs/tech_doc/CONNECTOR_REFACTORING.md) - Architecture connecteurs
- [docs/tech_doc/INTEGRATIONS_STRUCTURE.md](docs/tech_doc/INTEGRATIONS_STRUCTURE.md) - Structure intégrations
- [docs/tech_doc/BATCH_PROCESSING_PLAN.md](docs/tech_doc/BATCH_PROCESSING_PLAN.md) - Traitement batch

### Sécurité
- [.env.oracle-arm](.env.oracle-arm) - Configuration sécurisée
- [docs/tech_doc/DEPLOY_ORACLE_ARM.md](docs/tech_doc/DEPLOY_ORACLE_ARM.md) - Section sécurité
- [docs/tech_doc/CLAUDE.md](docs/tech_doc/CLAUDE.md) - Chiffrement credentials
- [SECURITY.md](SECURITY.md) - Politique de sécurité

### Tests
- [tests/](tests/) - Tests unitaires
- [scripts/test_*_connector.py](scripts/) - Tests connecteurs
- [docs/tech_doc/PHASE_2_ACTIONS.md](docs/tech_doc/PHASE_2_ACTIONS.md) - Tests actions

### Scripts Utilitaires
- [scripts/README.md](scripts/README.md) - Documentation complète des scripts
- [scripts/generate_keys.py](scripts/generate_keys.py) - Générer les clés de sécurité
- [scripts/add_email_account.py](scripts/add_email_account.py) - Ajouter/gérer des comptes email
- [scripts/check_classifications.py](scripts/check_classifications.py) - Statistiques de classification
- [scripts/test_rules.py](scripts/test_rules.py) - Tester les règles de classification

---

## 📊 Architecture & Composants

### Architecture globale

| Document | Niveau | Description |
|----------|--------|-------------|
| [docs/tech_doc/CLAUDE.md](docs/tech_doc/CLAUDE.md) | ⭐⭐⭐ | Architecture complète |
| [README.md](README.md) | ⭐ | Vue d'ensemble simple |
| [docs/guides/ORACLE_ARM_SETUP_SUMMARY.md](docs/guides/ORACLE_ARM_SETUP_SUMMARY.md) | ⭐⭐ | Architecture déployée |

### Composants

| Composant | Documentation | Code |
|-----------|---------------|------|
| **API** | [docs/tech_doc/CLAUDE.md](docs/tech_doc/CLAUDE.md) | [api/](api/) |
| **Workers** | [docs/tech_doc/CLAUDE.md](docs/tech_doc/CLAUDE.md) | [worker/](worker/) |
| **Connecteurs** | [docs/tech_doc/CONNECTOR_REFACTORING.md](docs/tech_doc/CONNECTOR_REFACTORING.md) | [shared/integrations/](shared/integrations/) |
| **Actions** | [docs/tech_doc/PHASE_2_ACTIONS.md](docs/tech_doc/PHASE_2_ACTIONS.md) | [worker/actions/](worker/actions/) |
| **Base de données** | [docs/tech_doc/CLAUDE.md](docs/tech_doc/CLAUDE.md) | [api/models.py](api/models.py) |

---

## 🆕 Nouveautés

### Dernières mises à jour (2026-01-21)

**Réorganisation Documentation :**
- Structure claire : `docs/guides/` + `docs/tech_doc/`
- Séparation guides utilisateur / documentation technique
- Index mis à jour avec nouvelle structure

**Phase 1 ✅ COMPLÉTÉE :**
- Connecteurs IMAP, Gmail, Microsoft implémentés
- OAuth2 flows complets
- Tests validés

**Phase 2 ✅ COMPLÉTÉE :**
- Système de règles YAML
- Actions automatiques (move, label, etc.)
- Intégration Celery
- Logging complet

**Oracle ARM Optimization :**
- Configuration complète pour 24GB ARM
- Scripts de déploiement automatique
- Documentation dédiée
- Optimisations PostgreSQL/Ollama

---

## 🎓 Niveau de difficulté

### Guides d'utilisation
| Document | Niveau | Temps lecture |
|----------|--------|---------------|
| [docs/guides/QUICK_START.md](docs/guides/QUICK_START.md) | 🟢 Débutant | 5 min |
| [docs/guides/GMAIL_EXAMPLE.md](docs/guides/GMAIL_EXAMPLE.md) | 🟢 Débutant | 10 min |
| [docs/guides/ORACLE_ARM_QUICK_REF.md](docs/guides/ORACLE_ARM_QUICK_REF.md) | 🟡 Intermédiaire | 5 min |
| [docs/guides/GMAIL_SETUP.md](docs/guides/GMAIL_SETUP.md) | 🟡 Intermédiaire | 15 min |

### Documentation technique
| Document | Niveau | Temps lecture |
|----------|--------|---------------|
| [docs/tech_doc/CLAUDE.md](docs/tech_doc/CLAUDE.md) | 🔴 Avancé | 60 min |
| [docs/tech_doc/CONNECTOR_REFACTORING.md](docs/tech_doc/CONNECTOR_REFACTORING.md) | 🔴 Avancé | 30 min |
| [docs/tech_doc/DEPLOY_ORACLE_ARM.md](docs/tech_doc/DEPLOY_ORACLE_ARM.md) | 🔴 Avancé | 30 min |
| [docs/tech_doc/PHASE_2_ACTIONS.md](docs/tech_doc/PHASE_2_ACTIONS.md) | 🔴 Avancé | 20 min |

---

## 📞 Support

### Par type de problème

| Problème | Document |
|----------|----------|
| **Installation** | [docs/guides/QUICK_START.md](docs/guides/QUICK_START.md), [docs/tech_doc/DEPLOY_ORACLE_ARM.md](docs/tech_doc/DEPLOY_ORACLE_ARM.md) |
| **Compte email** | [docs/guides/GMAIL_EXAMPLE.md](docs/guides/GMAIL_EXAMPLE.md), [docs/guides/ADD_EMAIL_ACCOUNT.md](docs/guides/ADD_EMAIL_ACCOUNT.md) |
| **Performance** | [docs/guides/ORACLE_ARM_SETUP_SUMMARY.md](docs/guides/ORACLE_ARM_SETUP_SUMMARY.md) |
| **Développement** | [docs/tech_doc/CLAUDE.md](docs/tech_doc/CLAUDE.md) |

---

## ✅ Checklist documentation

**Pour utilisateurs :**
- [ ] J'ai lu [docs/guides/QUICK_START.md](docs/guides/QUICK_START.md)
- [ ] J'ai suivi [docs/guides/GMAIL_EXAMPLE.md](docs/guides/GMAIL_EXAMPLE.md)
- [ ] J'ai configuré avec [docs/tech_doc/DEPLOY_ORACLE_ARM.md](docs/tech_doc/DEPLOY_ORACLE_ARM.md) (si Oracle)

**Pour développeurs :**
- [ ] J'ai lu [docs/tech_doc/CLAUDE.md](docs/tech_doc/CLAUDE.md)
- [ ] J'ai compris [docs/tech_doc/CONNECTOR_REFACTORING.md](docs/tech_doc/CONNECTOR_REFACTORING.md)
- [ ] J'ai consulté [docs/tech_doc/PHASE_2_ACTIONS.md](docs/tech_doc/PHASE_2_ACTIONS.md)

**Pour déploiement Oracle :**
- [ ] J'ai lu [docs/guides/ORACLE_ARM_QUICK_REF.md](docs/guides/ORACLE_ARM_QUICK_REF.md)
- [ ] J'ai suivi [docs/tech_doc/DEPLOY_ORACLE_ARM.md](docs/tech_doc/DEPLOY_ORACLE_ARM.md)
- [ ] J'ai configuré [.env.oracle-arm](.env.oracle-arm)
- [ ] J'ai exécuté [scripts/deploy-oracle-arm.sh](scripts/deploy-oracle-arm.sh)

---

**Documentation maintenant organisée de manière claire et structurée ! 📚**

**Version** : 2.0.0
**Dernière mise à jour** : 2026-01-21
**Structure** : docs/guides/ + docs/tech_doc/
