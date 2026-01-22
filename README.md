# 📧 Email Agent AI - Gestionnaire intelligent d'inbox

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![Oracle Cloud](https://img.shields.io/badge/oracle%20cloud-free%20tier-red.svg)](https://www.oracle.com/cloud/free/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

Agent AI pour trier, classifier et archiver automatiquement vos emails avec support multi-comptes.

## 🎯 Fonctionnalités

- ✅ Classification automatique des emails (factures, documents, promotions, etc.)
- 🗂️ Archivage intelligent avec structure personnalisable
- 🔄 Support multi-comptes (Gmail, Outlook, IMAP)
- 🤖 LLM local (Ollama) pour analyse contextuelle
- 📊 Dashboard de monitoring
- 🔒 Sécurité : credentials chiffrés, mode suggestion avant suppression
- 🆓 **Déployable gratuitement sur Oracle Cloud**

## 🏗️ Architecture

```
┌─────────────────┐
│  Email Accounts │
│  (IMAP/Gmail)   │
└────────┬────────┘
         │
    ┌────▼─────┐
    │  Worker  │──────┐
    │ (Celery) │      │
    └────┬─────┘      │
         │            │
    ┌────▼─────┐  ┌──▼──────┐
    │   API    │  │  Ollama │
    │(FastAPI) │  │  (LLM)  │
    └────┬─────┘  └─────────┘
         │
    ┌────▼─────┐
    │PostgreSQL│
    │  Redis   │
    └──────────┘
```

## 🚀 Déploiement rapide sur Oracle Cloud

### Prérequis

1. **Compte Oracle Cloud** (gratuit) : https://www.oracle.com/cloud/free/
2. **Instance VM.Standard.A1.Flex** (ARM, 4 OCPU, 24 GB RAM - inclus dans free tier)

### Étape 1 : Créer l'instance Oracle Cloud

1. Connectez-vous à Oracle Cloud Console
2. Menu → Compute → Instances
3. Créer une instance :
   - **Image** : Ubuntu 22.04 (ARM)
   - **Shape** : VM.Standard.A1.Flex (4 OCPU, 24 GB RAM)
   - **Networking** : Créer un nouveau VCN ou utiliser existant
   - **Add SSH keys** : Générer ou importer votre clé SSH
   - **Boot volume** : 100 GB (gratuit jusqu'à 200 GB)

4. Configurer les règles de sécurité :
   - Aller dans VCN → Security Lists → Default Security List
   - Ajouter Ingress Rules :
     - Port 80 (HTTP)
     - Port 443 (HTTPS)
     - Port 9000 (Portainer - optionnel)

### Étape 2 : Connexion et installation

```bash
# Connexion SSH (remplacer <IP> par l'IP publique de votre instance)
ssh ubuntu@<IP>

# Une fois connecté, cloner le repo
git clone https://github.com/VOTRE-USERNAME/email-agent.git
cd email-agent

# Lancer le script d'installation automatique
chmod +x scripts/setup-oracle.sh
sudo ./scripts/setup-oracle.sh
```

### Étape 3 : Configuration

```bash
# Copier et éditer le fichier de configuration
cp .env.example .env
nano .env
```

Générer les clés de sécurité :
```bash
# Méthode recommandée : utiliser le script de génération
python3 scripts/generate_keys.py

# Le script génère automatiquement :
# - SECRET_KEY (format hexadécimal pour JWT signing)
# - ENCRYPTION_KEY (format Fernet base64 pour chiffrement)
```

Configurer au minimum dans `.env` :
```env
SECRET_KEY=votre_clé_secrète_hex_ici
ENCRYPTION_KEY=votre_clé_fernet_base64_ici

# Configuration email (exemple Gmail)
# Les comptes seront ajoutés via l'interface web
```

### Étape 4 : Démarrage

```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier que tout fonctionne
docker-compose ps

# Voir les logs
docker-compose logs -f
```

### Étape 5 : Premier accès

1. **Dashboard** : http://<IP_INSTANCE>
2. **Portainer** : http://<IP_INSTANCE>:9000 (pour gérer Docker)

**Credentials par défaut :**
- Username : `admin`
- Password : `changeme` (à changer immédiatement !)

## 📁 Structure du projet

```
email-agent/
├── api/                    # FastAPI backend
│   ├── main.py
│   ├── routers/
│   ├── models/
│   └── services/
├── worker/                 # Celery workers
│   ├── tasks.py
│   └── classifiers/
├── scripts/               # Scripts de déploiement
│   ├── setup-oracle.sh
│   └── backup.sh
├── docker/                # Dockerfiles
├── config/                # Configuration Nginx, etc.
├── tests/
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 🔧 Configuration avancée

### Ajouter un compte email

Via l'interface web ou CLI :

```bash
# Via CLI
docker-compose exec api python -m scripts.add_account \
  --type gmail \
  --email votre.email@gmail.com \
  --credentials credentials.json
```

### Personnaliser les règles de classification

Éditer `config/classification-rules.yaml` :

```yaml
rules:
  - name: "Factures"
    conditions:
      - attachment_name_contains: ["facture", "invoice", "reçu"]
      - body_contains: ["TVA", "montant", "€"]
    action: "archive"
    folder: "Finances/Factures"
    priority: high
```

### Changer le modèle LLM

Par défaut : Mistral 7B (2.5 GB)

Pour utiliser un modèle plus léger :
```bash
docker-compose exec ollama ollama pull phi3:mini
# Puis modifier OLLAMA_MODEL=phi3:mini dans .env
```

## 📊 Monitoring

### Portainer (Interface Docker)
- URL : http://<IP>:9000
- Gérer containers, volumes, réseaux
- Voir logs en temps réel

### Métriques et statistiques
```bash
# Voir les statistiques de classification
docker-compose exec api python scripts/check_classifications.py

# Voir uniquement les stats globales
docker-compose exec api python scripts/check_classifications.py --stats

# Voir les 20 emails récents
docker-compose exec api python scripts/check_classifications.py --recent 20

# Filtrer par catégorie
docker-compose exec api python scripts/check_classifications.py --category invoice

# Tester les règles de classification
docker-compose exec api python scripts/test_rules.py
```

## 🔐 Sécurité

### SSL/HTTPS (Recommandé)

```bash
# Installer Certbot
sudo apt install certbot python3-certbot-nginx

# Obtenir un certificat (nécessite un nom de domaine)
sudo certbot --nginx -d votre-domaine.com

# Renouvellement automatique déjà configuré
```

### Backups automatiques

Le script de backup est configuré pour s'exécuter quotidiennement :

```bash
# Backup manuel
./scripts/backup.sh

# Restaurer un backup
./scripts/restore.sh backup-20250120.tar.gz
```

Backups stockés dans `/var/backups/email-agent/`

## 🐛 Troubleshooting

### Les emails ne sont pas traités

```bash
# Vérifier les workers
docker-compose logs worker

# Redémarrer le worker
docker-compose restart worker
```

### Ollama trop lent / Out of memory

```bash
# Utiliser un modèle plus petit
docker-compose exec ollama ollama pull phi3:mini

# Ou limiter la RAM allouée à Ollama (docker-compose.yml)
deploy:
  resources:
    limits:
      memory: 8G
```

### Problèmes de connexion IMAP

```bash
# Tester la connexion
docker-compose exec api python -m scripts.test_connection \
  --account votre.email@gmail.com
```

## 📈 Performance

Sur Oracle Cloud Free Tier (4 OCPU ARM, 24 GB RAM) :
- **Emails/heure** : ~500-1000 (selon complexité)
- **Latence moyenne** : 1-3 secondes par email
- **RAM utilisée** : ~12-16 GB (Ollama + services)
- **Stockage** : ~15 GB après 3 mois (avec 10k emails)

## 🛠️ Développement local

```bash
# Cloner le repo
git clone https://github.com/VOTRE-USERNAME/email-agent.git
cd email-agent

# Créer environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer dépendances
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Lancer en mode dev
docker-compose -f docker-compose.dev.yml up
```

Tests :
```bash
pytest tests/
```

## 📝 Roadmap

- [ ] Support Microsoft Graph API (Outlook/Office 365)
- [ ] Fine-tuning du modèle LLM sur vos emails
- [ ] Application mobile (notifications)
- [ ] Intégration Zapier/n8n
- [ ] Support POP3
- [ ] Multi-langue (actuellement FR/EN)

## 🤝 Contribution

Les contributions sont les bienvenues ! Voir [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 License

MIT License - Voir [LICENSE](LICENSE)

## 💬 Support

- 🐛 Issues : https://github.com/VOTRE-USERNAME/email-agent/issues
- 📧 Email : votre.email@example.com
- 💬 Discord : [Lien vers serveur Discord]

---

Made with ❤️ by Eric | Powered by Oracle Cloud Free Tier
