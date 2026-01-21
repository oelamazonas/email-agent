# 📧 Exemple complet : Ajouter un compte Gmail

Guide pas-à-pas avec captures d'écran textuelles pour ajouter votre premier compte Gmail.

---

## 🎯 Objectif

À la fin de ce guide, vous aurez :
- ✅ Un mot de passe d'application Gmail configuré
- ✅ Votre compte Gmail ajouté à Email Agent AI
- ✅ La synchronisation automatique en cours
- ✅ Vos emails classifiés par IA

⏱️ **Temps estimé** : 5 minutes

---

## Étape 1 : Préparer Gmail (2 minutes)

### 1.1 Ouvrir la page de sécurité Google

1. Allez sur : https://myaccount.google.com/security
2. Connectez-vous avec votre compte Gmail

### 1.2 Activer la validation en 2 étapes (si pas déjà fait)

```
Page Google Security
└─ "Comment vous connecter à Google"
   └─ "Validation en 2 étapes"
      └─ Cliquez sur "Activer"
      └─ Suivez les instructions (SMS, app Google Authenticator, etc.)
```

### 1.3 Créer un mot de passe d'application

```
Page Google Security
└─ "Comment vous connecter à Google"
   └─ "Mots de passe des applications"
      └─ Sélectionnez "Autre (nom personnalisé)"
      └─ Tapez : "Email Agent AI"
      └─ Cliquez "Générer"

      📋 Résultat : Mot de passe de 16 caractères
      Exemple : abcd efgh ijkl mnop

      ⚠️ COPIEZ-LE MAINTENANT (affiché une seule fois)
```

**Exemple de mot de passe généré :**
```
xxxx xxxx xxxx xxxx
```

✅ **Checkpoint 1** : Vous avez un mot de passe de 16 caractères copié

---

## Étape 2 : Ajouter le compte dans Email Agent AI (2 minutes)

### 2.1 Démarrer les services (si pas déjà fait)

```bash
cd /chemin/vers/email-agent
docker-compose up -d
```

**Sortie attendue :**
```
✔ Container email-agent-db      Running
✔ Container email-agent-redis   Running
✔ Container email-agent-ollama  Running
✔ Container email-agent-api     Started
✔ Container email-agent-worker  Started
✔ Container email-agent-scheduler Started
```

### 2.2 Lancer le script d'ajout de compte

```bash
docker-compose exec api python scripts/add_email_account.py
```

### 2.3 Suivre le guide interactif

#### Écran 1 : Type de compte

```
============================================================
📬 Email Agent AI - Ajout de compte email
============================================================

Type de compte:
1. Gmail
2. Outlook/Microsoft
3. IMAP générique

Choisir le type [1]:
```

👉 **Tapez : `1`** (ou juste Entrée pour Gmail par défaut)

---

#### Écran 2 : Configuration Gmail

```
📧 Configuration compte Gmail
--------------------------------------------------
⚠️  Pour Gmail, vous avez deux options:
1. Mot de passe d'application (recommandé)
2. OAuth2 (nécessite configuration Google Cloud)

Choisir l'option [1]:
```

👉 **Tapez : `1`** (ou juste Entrée)

---

#### Écran 3 : Adresse email

```
Adresse Gmail:
```

👉 **Tapez votre adresse Gmail complète**
```
votre.email@gmail.com
```

---

#### Écran 4 : Mot de passe d'application

```
📝 Pour créer un mot de passe d'application:
   1. Allez sur https://myaccount.google.com/security
   2. Activez la validation en 2 étapes si nécessaire
   3. Allez dans 'Mots de passe des applications'
   4. Générez un mot de passe pour 'Email Agent'

Mot de passe d'application (16 caractères):
```

👉 **Collez le mot de passe** (les espaces seront ignorés)
```
xxxx xxxx xxxx xxxx
```

⚠️ **Le mot de passe est caché** (normal)

---

#### Écran 5 : Nom d'affichage

```
Nom d'affichage [votre.email@gmail.com]:
```

👉 **Options :**
- Entrée pour garder l'email comme nom
- Ou tapez un nom : `Mon Gmail Pro`

---

#### Écran 6 : Confirmation

```
============================================================
📋 Récapitulatif:
   Type: gmail
   Email: votre.email@gmail.com
   Nom: Mon Gmail Pro
============================================================

Confirmer l'ajout du compte? [Y/n]:
```

👉 **Tapez : `Y`** (ou juste Entrée)

---

#### Écran 7 : Succès !

```
🔧 Création de l'utilisateur admin...
✅ Utilisateur admin créé: admin@example.com

✅ Compte email ajouté avec succès!
   ID: 1
   Email: votre.email@gmail.com
   Type: gmail

🔄 La synchronisation démarrera automatiquement.
   Vous pouvez consulter les logs avec:
   docker-compose logs -f worker
```

✅ **Checkpoint 2** : Compte ajouté avec succès !

---

## Étape 3 : Vérifier que ça fonctionne (1 minute)

### 3.1 Vérifier le compte ajouté

```bash
docker-compose exec api python scripts/add_email_account.py list
```

**Sortie attendue :**
```
📬 Comptes email configurés:
================================================================================
ID:   1 | ✅ Actif | gmail    | votre.email@gmail.com    | Dernière sync: Jamais
================================================================================
```

### 3.2 Surveiller la synchronisation

```bash
docker-compose logs -f worker
```

**Sortie attendue (premiers logs) :**
```
worker_1  | [INFO] Starting email sync for account 1 (votre.email@gmail.com)
worker_1  | [INFO] Connected to IMAP server: imap.gmail.com:993
worker_1  | [INFO] Fetching emails since last sync...
worker_1  | [INFO] Found 42 new emails
worker_1  | [INFO] Processing email 1/42: "Facture Amazon"
worker_1  | [INFO] Classified as: invoice (confidence: 95%)
worker_1  | [INFO] Processing email 2/42: "Newsletter Medium"
worker_1  | [INFO] Classified as: newsletter (confidence: 88%)
...
```

**Arrêter les logs** : `Ctrl+C`

### 3.3 Vérifier via l'API

```bash
# Lister les comptes
curl http://localhost:8000/api/accounts/
```

**Résultat attendu :**
```json
[
  {
    "id": 1,
    "account_type": "gmail",
    "email_address": "votre.email@gmail.com",
    "display_name": "Mon Gmail Pro",
    "is_active": true,
    "last_sync": "2025-01-20T15:30:00",
    "total_emails_processed": 42
  }
]
```

```bash
# Voir les premiers emails
curl http://localhost:8000/api/emails/?limit=5
```

✅ **Checkpoint 3** : La synchronisation fonctionne !

---

## 🎉 C'est terminé !

Votre compte Gmail est maintenant :
- ✅ Configuré et actif
- ✅ En cours de synchronisation automatique (toutes les 5 minutes)
- ✅ Les emails sont classifiés par IA avec Ollama Mistral
- ✅ Accessible via l'API REST

---

## 🔄 Que se passe-t-il maintenant ?

### Synchronisation automatique

- **Fréquence** : Toutes les 5 minutes (configurable dans `.env`)
- **Service** : Celery Beat scheduler
- **Worker** : Celery worker traite les tâches

### Classification automatique

Pour chaque email synchronisé :

1. **Règles YAML** : Vérification des règles prédéfinies (expéditeur, mots-clés)
2. **IA Ollama** : Si incertain, classification avec Mistral LLM
3. **Catégorie** : Attribution d'une catégorie (invoice, newsletter, etc.)
4. **Confiance** : Score de confiance 0-100%
5. **Action** : Optionnellement, déplacement/archivage automatique

### Prochaines étapes recommandées

1. **Télécharger Mistral** (si pas déjà fait) :
   ```bash
   docker-compose exec ollama ollama pull mistral
   ```

2. **Tester la classification** :
   ```bash
   curl -X POST http://localhost:8000/api/classification/test \
     -H "Content-Type: application/json" \
     -d '{
       "subject": "Facture Amazon Janvier",
       "sender": "invoice@amazon.com",
       "body_preview": "Votre facture est disponible..."
     }'
   ```

3. **Créer des règles personnalisées** :
   - Via l'API `/api/classification/rules`
   - Définir vos propres critères de classification

4. **Ajouter d'autres comptes** (optionnel) :
   ```bash
   docker-compose exec api python scripts/add_email_account.py
   ```

---

## 🛠️ Dépannage

### ❌ Erreur : "Authentication failed"

**Cause** : Mot de passe d'application invalide

**Solution** :
1. Générez un nouveau mot de passe d'application
2. Re-exécutez le script avec le même email
3. Choisissez "Mettre à jour les credentials"

### ❌ Emails ne se synchronisent pas

**Vérifications** :

```bash
# 1. Vérifier le worker
docker-compose ps worker
# Doit être "Up"

# 2. Vérifier les logs
docker-compose logs worker --tail 50

# 3. Vérifier Redis
docker-compose exec redis redis-cli ping
# Doit répondre : PONG

# 4. Vérifier le scheduler
docker-compose logs scheduler --tail 20
```

### ❌ Classification ne fonctionne pas

**Cause** : Ollama Mistral pas téléchargé

**Solution** :
```bash
# Télécharger le modèle
docker-compose exec ollama ollama pull mistral

# Vérifier
docker-compose exec ollama ollama list
```

---

## 📚 Documentation complète

- 📘 [Guide développeur complet](CLAUDE.md)
- 📧 [Guide détaillé comptes email](docs/AJOUTER_COMPTE_EMAIL.md)
- 🚀 [Démarrage rapide](docs/QUICK_START.md)
- 📊 [Guide de référence](GUIDE_RAPIDE.md)

---

## 🎯 Checklist finale

- [ ] Mot de passe d'application Gmail généré
- [ ] Compte ajouté dans Email Agent AI
- [ ] Synchronisation démarrée (visible dans logs)
- [ ] API répond correctement
- [ ] Ollama Mistral téléchargé
- [ ] Premier email classifié

**Si tous les points sont cochés : Bravo ! 🎉**

Vous pouvez maintenant profiter de votre inbox triée automatiquement !

---

**Version** : 1.0.0
**Testé avec** : Gmail, Docker 24.0+, Email Agent AI 1.0.0
