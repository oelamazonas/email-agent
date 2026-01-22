# Scripts utilitaires Email Agent AI

Collection de scripts pour la gestion et la maintenance d'Email Agent AI.

## 📧 add_email_account.py

Script interactif pour ajouter et gérer les comptes email.

### Usage

```bash
# Ajouter un nouveau compte (interactif)
docker-compose exec api python scripts/add_email_account.py

# Lister tous les comptes configurés
docker-compose exec api python scripts/add_email_account.py list
```

### Fonctionnalités

- ✅ Support Gmail (mot de passe d'application)
- ✅ Support Outlook/Microsoft (IMAP)
- ✅ Support IMAP générique
- ✅ Chiffrement automatique des credentials (Fernet)
- ✅ Création automatique de l'utilisateur admin
- ✅ Mise à jour des credentials existants
- ✅ Interface interactive et guidée

### Types de comptes supportés

#### 1. Gmail
- **Méthode** : Mot de passe d'application
- **Prérequis** :
  - Activer la validation en 2 étapes
  - Générer un mot de passe d'application
- **URL** : https://myaccount.google.com/security

#### 2. Outlook/Microsoft
- **Méthode** : IMAP
- **Serveur** : outlook.office365.com:993
- **Prérequis** : Activer IMAP dans les paramètres

#### 3. IMAP Générique
- **Méthode** : Configuration manuelle
- **Requis** : Serveur IMAP, port, username, password

### Exemples

#### Ajouter un compte Gmail

```bash
$ docker-compose exec api python scripts/add_email_account.py

Type de compte: 1 (Gmail)
Option: 1 (Mot de passe d'application)
Adresse Gmail: votre.email@gmail.com
Mot de passe d'application: [16 caractères]
Nom d'affichage: Mon Gmail

Confirmer? Y
✅ Compte ajouté!
```

#### Lister les comptes

```bash
$ docker-compose exec api python scripts/add_email_account.py list

📬 Comptes email configurés:
================================================================================
ID:   1 | ✅ Actif | gmail    | votre.email@gmail.com    | Dernière sync: 2025-01-20 15:30
ID:   2 | ✅ Actif | imap     | pro@entreprise.com       | Dernière sync: Jamais
================================================================================
```

#### Mettre à jour un compte

```bash
$ docker-compose exec api python scripts/add_email_account.py

# Entrer le même email qu'un compte existant
⚠️  Un compte avec l'adresse email@example.com existe déjà!
Mettre à jour les credentials? [y/N]: y
✅ Compte mis à jour!
```

### Sécurité

- **Chiffrement** : Tous les credentials sont chiffrés avec Fernet
- **Clé** : Définie dans `.env` (`ENCRYPTION_KEY`)
- **Stockage** : Base de données PostgreSQL, jamais en clair
- **Validation** : Les credentials sont validés avant l'ajout

### Dépannage

#### Script non trouvé

```bash
# Rebuild le conteneur API
docker-compose build api
docker-compose up -d api
```

#### Erreur de connexion DB

```bash
# Vérifier que la DB est démarrée
docker-compose ps db

# Vérifier les logs
docker-compose logs db
```

#### Credentials invalides

Le script ne teste PAS la connexion au serveur email lors de l'ajout.
La validation se fait lors de la première synchronisation.

Vérifier les logs du worker :
```bash
docker-compose logs -f worker
```

---

## 🔑 generate_keys.py

Génère des clés de sécurité pour la configuration d'Email Agent AI.

### Usage

```bash
# Générer toutes les clés nécessaires
python scripts/generate_keys.py
```

### Fonctionnalités

- ✅ Génération de SECRET_KEY (format hexadécimal, 64 caractères)
- ✅ Génération de ENCRYPTION_KEY (format Fernet base64)
- ✅ Affichage formaté prêt pour copier dans .env
- ✅ Avertissements de sécurité intégrés

### Sortie

```
============================================================
Email Agent AI - Key Generator
============================================================

Add these to your .env file:

# JWT and session signing
SECRET_KEY=a1b2c3d4e5f6...

# Fernet encryption for credentials
ENCRYPTION_KEY=xyzABC123...==

============================================================
⚠️  WARNING: Changing ENCRYPTION_KEY will make existing
    encrypted data unreadable. Only change during setup
    or if you're resetting the database.
============================================================
```

### Sécurité

- **SECRET_KEY** : Utilisée pour signer les JWT et les sessions
- **ENCRYPTION_KEY** : Utilisée pour chiffrer les credentials email en base de données
- ⚠️ **Important** : Ne jamais committer ces clés dans Git
- ⚠️ **Important** : Changer ENCRYPTION_KEY rend les données chiffrées illisibles

---

## 📊 check_classifications.py

Affiche des statistiques et détails sur les emails classifiés.

### Usage

```bash
# Afficher tout (stats + emails récents)
docker-compose exec api python scripts/check_classifications.py

# Uniquement les statistiques
docker-compose exec api python scripts/check_classifications.py --stats

# Uniquement les N emails récents
docker-compose exec api python scripts/check_classifications.py --recent 10

# Filtrer par catégorie
docker-compose exec api python scripts/check_classifications.py --category invoice --limit 20
```

### Fonctionnalités

- 📊 Statistiques globales par catégorie
- 📈 Répartition par statut de traitement
- 📬 Liste des emails récents classifiés
- 🔍 Filtrage par catégorie spécifique
- 💯 Affichage du niveau de confiance et raisons de classification

### Catégories disponibles

- `invoice` - Factures
- `receipt` - Reçus
- `document` - Documents
- `professional` - Emails professionnels
- `newsletter` - Newsletters
- `promotion` - Promotions
- `social` - Réseaux sociaux
- `notification` - Notifications
- `personal` - Personnel
- `spam` - Spam
- `unknown` - Non classifié

### Exemples

#### Voir les statistiques

```bash
$ docker-compose exec api python scripts/check_classifications.py --stats

================================================================================
📊 CLASSIFICATION STATISTICS
================================================================================

📧 Total Emails: 1,234

📂 By Category:
--------------------------------------------------------------------------------
  invoice         │  123 │  10.0% │ █████
  receipt         │   89 │   7.2% │ ███
  document        │  234 │  19.0% │ █████████
  professional    │  456 │  37.0% │ ██████████████████
  ...
```

#### Voir les emails récents

```bash
$ docker-compose exec api python scripts/check_classifications.py --recent 5

================================================================================
📬 RECENT CLASSIFICATIONS (Last 5)
================================================================================

💰 invoice       │ ✅ completed
   Subject: Facture Amazon - Janvier 2025
   From: invoice@amazon.com
   Account: mon.email@gmail.com
   Date: 2025-01-22 14:30
   Confidence: 95%
   Reason: Contains invoice number and payment details
   ----------------------------------------------------------------------------
```

#### Filtrer par catégorie

```bash
$ docker-compose exec api python scripts/check_classifications.py --category invoice --limit 10

================================================================================
📂 EMAILS IN CATEGORY: INVOICE
================================================================================

Found 10 email(s) (showing up to 10):

• Facture Amazon - Janvier 2025
  From: invoice@amazon.com │ Date: 2025-01-22 14:30 │ Confidence: 95%
  Reason: Contains invoice number and payment details
```

---

## 🧪 test_rules.py

Teste le chargement et l'application des règles de classification.

### Usage

```bash
# Tester les règles
docker-compose exec api python scripts/test_rules.py
```

### Fonctionnalités

- ✅ Vérification du chargement des règles depuis `rules/global_rules.yaml`
- 📋 Affichage du résumé des règles par catégorie
- 🧪 Test avec un email d'exemple
- 🎯 Détection de la règle correspondante

### Sortie

```
================================================================================
🔧 CLASSIFICATION RULES TEST
================================================================================

📂 Loading rules from: /app/rules
   Rules file: /app/rules/global_rules.yaml

✅ Loaded 15 rules

--------------------------------------------------------------------------------
📋 RULES SUMMARY
--------------------------------------------------------------------------------

📂 invoice (5 rules)
   [100] Invoice Detection
        → Folder: Finances/Invoices
   [ 90] Billing Emails
        → Folder: Finances/Bills

📂 promotion (3 rules)
   [ 80] Marketing Campaigns
        → Auto-delete: Yes
   ...

================================================================================
🧪 TEST WITH SAMPLE EMAIL
================================================================================

📧 Sample Email:
   Subject: Your Invoice #12345
   From: billing@company.com
   Has attachments: True

✅ Matched Rule: Invoice Detection
   Priority: 100
   Category: invoice
   Target Folder: Finances/Invoices
```

### Cas d'usage

- Vérifier que les règles se chargent correctement
- Déboguer les règles de classification
- Tester de nouvelles règles avant déploiement
- Comprendre quelle règle s'applique à un type d'email

---

## 🔄 À venir

### backup_database.sh
Script pour sauvegarder la base de données PostgreSQL.

### restore_database.sh
Script pour restaurer une sauvegarde.

### migrate_accounts.py
Migration de comptes depuis d'autres systèmes.

### health_check.py
Vérifier l'état de santé du système.

---

## 📚 Documentation

- [Guide complet : Ajouter un compte](../docs/ADD_EMAIL_ACCOUNT.md)
- [Démarrage rapide](../docs/QUICK_START.md)
- [Architecture complète](../CLAUDE.md)

---

**Version** : 1.0.0
