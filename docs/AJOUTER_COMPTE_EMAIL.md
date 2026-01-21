# 📧 Guide : Ajouter un compte email

## Méthode rapide (Recommandée)

### Via Docker (le plus simple)

```bash
docker-compose exec api python scripts/add_email_account.py
```

### Liste des comptes configurés

```bash
docker-compose exec api python scripts/add_email_account.py list
```

---

## Configuration par type de compte

### 🔵 Gmail

#### Option 1 : Mot de passe d'application (Recommandé)

**Étapes préalables :**

1. Allez sur [Google Account Security](https://myaccount.google.com/security)
2. Activez la **validation en 2 étapes** si nécessaire
3. Allez dans **Mots de passe des applications**
4. Sélectionnez "Autre (nom personnalisé)"
5. Entrez "Email Agent AI"
6. Copiez le mot de passe de 16 caractères généré

**Lors de l'exécution du script :**
- Type de compte : `1` (Gmail)
- Option : `1` (Mot de passe d'application)
- Adresse Gmail : votre email
- Mot de passe d'application : collez le mot de passe

#### Option 2 : OAuth2 (Future implémentation)

*Non encore disponible - utilisez l'option 1*

---

### 🔴 Outlook/Microsoft

#### IMAP Direct

**Prérequis :**
- Activez IMAP dans les paramètres Outlook
- Allez sur [Outlook Settings](https://outlook.live.com/mail/0/options/mail/sync)
- Activez "Let devices and apps use IMAP"

**Configuration :**
- Type de compte : `2` (Outlook)
- Option : `2` (IMAP)
- Serveur : `outlook.office365.com` (par défaut)
- Port : `993` (par défaut)
- Username : votre email complet
- Password : votre mot de passe

---

### ⚙️ IMAP Générique

Pour tout autre fournisseur email supportant IMAP.

**Informations nécessaires :**
- Serveur IMAP (ex: `imap.example.com`)
- Port IMAP (généralement `993` pour SSL/TLS)
- Username (souvent votre email complet)
- Password

**Exemples de configuration :**

| Fournisseur | Serveur IMAP | Port |
|-------------|--------------|------|
| Gmail | `imap.gmail.com` | 993 |
| Outlook | `outlook.office365.com` | 993 |
| Yahoo | `imap.mail.yahoo.com` | 993 |
| iCloud | `imap.mail.me.com` | 993 |
| ProtonMail Bridge | `127.0.0.1` | 1143 |

---

## Exemple complet d'ajout

```bash
$ docker-compose exec api python scripts/add_email_account.py

============================================================
📬 Email Agent AI - Ajout de compte email
============================================================

Type de compte:
1. Gmail
2. Outlook/Microsoft
3. IMAP générique

Choisir le type [1]: 1

📧 Configuration compte Gmail
--------------------------------------------------
⚠️  Pour Gmail, vous avez deux options:
1. Mot de passe d'application (recommandé)
2. OAuth2 (nécessite configuration Google Cloud)

Choisir l'option [1]: 1

Adresse Gmail: votre.email@gmail.com

📝 Pour créer un mot de passe d'application:
   1. Allez sur https://myaccount.google.com/security
   2. Activez la validation en 2 étapes si nécessaire
   3. Allez dans 'Mots de passe des applications'
   4. Générez un mot de passe pour 'Email Agent'

Mot de passe d'application (16 caractères): ****************

Nom d'affichage [votre.email@gmail.com]: Mon Gmail Pro

============================================================
📋 Récapitulatif:
   Type: gmail
   Email: votre.email@gmail.com
   Nom: Mon Gmail Pro
============================================================

Confirmer l'ajout du compte? [Y/n]: Y

✅ Utilisateur admin trouvé: admin@example.com
✅ Compte email ajouté avec succès!
   ID: 1
   Email: votre.email@gmail.com
   Type: gmail

🔄 La synchronisation démarrera automatiquement.
   Vous pouvez consulter les logs avec:
   docker-compose logs -f worker
```

---

## Vérification et surveillance

### Vérifier que le compte est ajouté

```bash
docker-compose exec api python scripts/add_email_account.py list
```

Sortie attendue :
```
📬 Comptes email configurés:
================================================================================
ID:   1 | ✅ Actif | gmail    | votre.email@gmail.com                    | Dernière sync: Jamais
================================================================================
```

### Surveiller la synchronisation

```bash
# Voir les logs du worker en temps réel
docker-compose logs -f worker

# Voir les logs du scheduler (déclenchement des tâches)
docker-compose logs -f scheduler
```

### Vérifier l'API

```bash
# Liste des comptes via API
curl http://localhost:8000/api/accounts/

# Détails d'un compte
curl http://localhost:8000/api/accounts/1
```

---

## Dépannage

### ❌ Erreur : "Authentication failed"

**Gmail :**
- Vérifiez que la validation en 2 étapes est activée
- Générez un nouveau mot de passe d'application
- Assurez-vous de copier les 16 caractères sans espaces

**Outlook :**
- Vérifiez que IMAP est activé dans les paramètres
- Utilisez votre mot de passe de compte complet
- Si vous utilisez 2FA, créez un mot de passe d'application

**IMAP Générique :**
- Vérifiez le serveur et le port
- Essayez avec et sans SSL
- Consultez la documentation de votre fournisseur

### ❌ Erreur : "Connection timeout"

- Vérifiez votre connexion internet
- Vérifiez que le serveur IMAP n'est pas bloqué par un firewall
- Pour ProtonMail, vérifiez que ProtonMail Bridge est lancé

### ❌ Erreur : "Account already exists"

Le script vous proposera de mettre à jour les credentials :
```
⚠️  Un compte avec l'adresse email@example.com existe déjà!
Mettre à jour les credentials? [y/N]: y
```

### 🔍 Voir les credentials (debug)

⚠️ **Attention : Les credentials sont chiffrés dans la DB**

Pour vérifier manuellement :
```python
# Se connecter à la DB
docker-compose exec db psql -U emailagent -d emailagent

# Voir les comptes
SELECT id, email_address, account_type, is_active FROM email_accounts;
```

---

## Sécurité

### 🔐 Chiffrement des credentials

- Tous les credentials sont chiffrés avec **Fernet** (cryptographie symétrique)
- La clé de chiffrement est définie dans `.env` (`ENCRYPTION_KEY`)
- ⚠️ **Ne partagez JAMAIS votre fichier `.env`**
- Les credentials ne sont **jamais** stockés en clair

### 🛡️ Bonnes pratiques

1. **Utilisez des mots de passe d'application** plutôt que vos mots de passe principaux
2. **Limitez les permissions** : Email Agent a besoin de :
   - Lecture des emails (IMAP)
   - Déplacement/marquage des emails (optionnel)
   - PAS besoin d'envoyer des emails (SMTP)
3. **Surveillez l'activité** régulièrement via les logs
4. **Sauvegardez** régulièrement votre base de données

---

## Prochaines étapes

Une fois le compte ajouté :

1. **Vérifier la synchronisation** :
   ```bash
   docker-compose logs -f worker
   ```

2. **Consulter les emails** :
   ```bash
   curl http://localhost:8000/api/emails/?limit=10
   ```

3. **Tester la classification** :
   ```bash
   curl http://localhost:8000/api/classification/test \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{
       "subject": "Facture Janvier 2025",
       "sender": "comptabilite@entreprise.com",
       "body_preview": "Veuillez trouver ci-joint votre facture..."
     }'
   ```

4. **Configurer les règles de classification** (optionnel)
   - Créer des règles personnalisées via l'API `/api/classification/rules`

---

## Support

Pour toute question :
- 📚 Consultez [CLAUDE.md](../CLAUDE.md) pour l'architecture complète
- 🐛 Ouvrez une issue sur GitHub
- 📧 Contactez le support

---

**Version** : 1.0.0
**Dernière mise à jour** : 2025-01-20
