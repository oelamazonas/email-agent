# 📬 Email Agent AI - Guide Rapide

## 🚀 Démarrage en 3 étapes

| Étape | Commande | Description |
|-------|----------|-------------|
| **1. Démarrer** | `docker-compose up -d` | Lance tous les services |
| **2. Ajouter compte** | `docker-compose exec api python scripts/add_email_account.py` | Ajoute votre premier compte email |
| **3. Vérifier** | `docker-compose logs -f worker` | Surveille la synchronisation |

---

## 📧 Configuration compte email

### Gmail (Recommandé)

| Action | Lien / Commande |
|--------|-----------------|
| **1. Préparer Gmail** | https://myaccount.google.com/security |
| **2. Activer 2FA** | Dans "Validation en 2 étapes" |
| **3. Créer mot de passe app** | Dans "Mots de passe des applications" |
| **4. Exécuter script** | `docker-compose exec api python scripts/add_email_account.py` |
| **5. Choisir Gmail** | Option `1` |
| **6. Choisir app password** | Option `1` |

### Outlook

| Action | Détail |
|--------|--------|
| **1. Activer IMAP** | https://outlook.live.com/mail/0/options/mail/sync |
| **2. Exécuter script** | `docker-compose exec api python scripts/add_email_account.py` |
| **3. Choisir Outlook** | Option `2` |
| **4. IMAP Direct** | Option `2` |

### IMAP Générique

| Fournisseur | Serveur IMAP | Port |
|-------------|--------------|------|
| Gmail | `imap.gmail.com` | 993 |
| Outlook | `outlook.office365.com` | 993 |
| Yahoo | `imap.mail.yahoo.com` | 993 |
| iCloud | `imap.mail.me.com` | 993 |
| ProtonMail* | `127.0.0.1` | 1143 |

*Nécessite ProtonMail Bridge

---

## 🔧 Commandes essentielles

### Gestion services

| Action | Commande |
|--------|----------|
| Démarrer | `docker-compose up -d` |
| Arrêter | `docker-compose down` |
| Redémarrer | `docker-compose restart` |
| Voir statut | `docker-compose ps` |
| Voir logs | `docker-compose logs -f` |
| Logs d'un service | `docker-compose logs -f worker` |

### Gestion comptes

| Action | Commande |
|--------|----------|
| Ajouter compte | `docker-compose exec api python scripts/add_email_account.py` |
| Lister comptes | `docker-compose exec api python scripts/add_email_account.py list` |
| Mettre à jour | Même commande qu'ajouter, avec même email |

### Base de données

| Action | Commande |
|--------|----------|
| Connexion DB | `docker-compose exec db psql -U emailagent -d emailagent` |
| Backup | `docker-compose exec db pg_dump -U emailagent emailagent > backup.sql` |
| Restore | `cat backup.sql \| docker-compose exec -T db psql -U emailagent emailagent` |

### Ollama (IA)

| Action | Commande |
|--------|----------|
| Télécharger Mistral | `docker-compose exec ollama ollama pull mistral` |
| Lister modèles | `docker-compose exec ollama ollama list` |
| Tester classification | Voir section API ci-dessous |

---

## 🌐 API Endpoints

### Health & Status

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/` | GET | Info API |
| `/health` | GET | Health check |
| `/docs` | GET | Documentation interactive |

### Comptes email

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/accounts/` | GET | Liste des comptes |
| `/api/accounts/{id}` | GET | Détails d'un compte |
| `/api/accounts/{id}` | DELETE | Désactiver un compte |

### Emails

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/emails/` | GET | Liste des emails |
| `/api/emails/{id}` | GET | Détails d'un email |
| `/api/emails/?category=invoice` | GET | Filtrer par catégorie |
| `/api/emails/?limit=10` | GET | Limiter les résultats |

### Classification

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/classification/test` | POST | Tester la classification |

**Exemple classification :**

```bash
curl -X POST http://localhost:8000/api/classification/test \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Facture Jan 2025",
    "sender": "compta@entreprise.com",
    "body_preview": "Votre facture du mois..."
  }'
```

**Réponse attendue :**

```json
{
  "category": "invoice",
  "confidence": 95,
  "reason": "Email contient facture et informations comptables"
}
```

---

## 📊 Catégories de classification

| Catégorie | Description | Exemples |
|-----------|-------------|----------|
| `invoice` | Factures | Factures fournisseurs, clients |
| `receipt` | Reçus | Confirmations d'achat, tickets |
| `document` | Documents | PDF, contrats partagés |
| `professional` | Email pro important | Réunions, projets |
| `newsletter` | Newsletters | Bulletins d'info |
| `promotion` | Promotions | Offres commerciales |
| `social` | Réseaux sociaux | Notifications Facebook, LinkedIn |
| `notification` | Notifications | Alertes systèmes |
| `personal` | Personnel | Emails personnels |
| `spam` | Spam | Indésirables |
| `unknown` | Non classifié | Pas encore analysé |

---

## 🔍 Dépannage rapide

| Problème | Solution |
|----------|----------|
| **Container crashe** | `docker-compose logs [service]` pour voir l'erreur |
| **Sync ne marche pas** | Vérifier `docker-compose logs worker` |
| **DB inaccessible** | `docker-compose restart db` |
| **Rebuild nécessaire** | `docker-compose down && docker-compose build --no-cache && docker-compose up -d` |
| **Credentials invalides** | Re-exécuter script d'ajout avec même email, choisir "Mettre à jour" |
| **Port 8000 occupé** | Changer port dans docker-compose.yml ou arrêter service conflit |
| **Ollama lent** | Normal au 1er lancement, modèle se charge en mémoire |

---

## 📂 Structure des fichiers

```
email-agent/
├── api/              # API FastAPI
├── worker/           # Celery workers
├── shared/           # Code partagé
├── scripts/          # Scripts utilitaires
│   └── add_email_account.py  # ⭐ Script principal
├── docs/             # Documentation
│   ├── QUICK_START.md
│   └── AJOUTER_COMPTE_EMAIL.md
├── docker/           # Dockerfiles
├── config/           # Configuration nginx
├── .env              # Variables d'environnement (SECRET)
├── docker-compose.yml
└── CLAUDE.md         # Guide développeur complet
```

---

## 🎯 Checklist de démarrage

- [ ] Docker et Docker Compose installés
- [ ] Fichier `.env` configuré (copier depuis `.env.example`)
- [ ] `docker-compose up -d` exécuté
- [ ] Tous les services sont `Up` (check avec `docker-compose ps`)
- [ ] Compte email ajouté avec script
- [ ] Ollama Mistral téléchargé (`docker-compose exec ollama ollama pull mistral`)
- [ ] Première synchronisation visible dans logs worker
- [ ] API accessible sur http://localhost:8000/docs

---

## 🔗 Liens utiles

| Service | URL | Description |
|---------|-----|-------------|
| **API Docs** | http://localhost:8000/docs | Documentation interactive Swagger |
| **API Health** | http://localhost:8000/health | Vérification santé |
| **Portainer** | http://localhost:9000 | Interface gestion Docker |
| **Gmail Security** | https://myaccount.google.com/security | Configuration Gmail |
| **Outlook IMAP** | https://outlook.live.com/mail/0/options/mail/sync | Configuration Outlook |

---

## 📞 Support

**Documentation complète :**
- 📘 `CLAUDE.md` - Architecture & développement
- 📧 `docs/AJOUTER_COMPTE_EMAIL.md` - Guide complet comptes email
- 🚀 `docs/QUICK_START.md` - Démarrage détaillé
- 🔧 `scripts/README.md` - Scripts utilitaires

**Logs et debug :**
```bash
# Tous les logs
docker-compose logs -f

# Service spécifique
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f db
```

---

**Version** : 1.0.0
**Dernière mise à jour** : 2025-01-20

**Bon tri automatique ! 📬✨**
