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

## 🔄 À venir

### backup_database.sh
Script pour sauvegarder la base de données PostgreSQL.

### restore_database.sh
Script pour restaurer une sauvegarde.

### migrate_accounts.py
Migration de comptes depuis d'autres systèmes.

### test_classification.py
Tester la classification sur des exemples.

### health_check.py
Vérifier l'état de santé du système.

---

## 📚 Documentation

- [Guide complet : Ajouter un compte](../docs/AJOUTER_COMPTE_EMAIL.md)
- [Démarrage rapide](../docs/QUICK_START.md)
- [Architecture complète](../CLAUDE.md)

---

**Version** : 1.0.0
