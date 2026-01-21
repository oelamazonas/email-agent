# 🚀 Démarrage Rapide - Email Agent AI

Guide pour démarrer avec Email Agent AI en 5 minutes.

---

## Prérequis

- Docker & Docker Compose installés
- Fichier `.env` configuré (copier depuis `.env.example`)

---

## Étape 1 : Démarrer les services

```bash
# Démarrer tous les conteneurs
docker-compose up -d

# Vérifier que tout fonctionne
docker-compose ps
```

Tous les services doivent être `Up` ou `Up (healthy)`.

---

## Étape 2 : Ajouter votre premier compte email

### Gmail (Recommandé pour commencer)

**Préparez votre mot de passe d'application :**
1. Allez sur https://myaccount.google.com/security
2. Activez la validation en 2 étapes
3. Créez un mot de passe d'application pour "Email Agent"

**Exécutez le script :**
```bash
docker-compose exec api python scripts/add_email_account.py
```

**Suivez le guide interactif :**
- Type : `1` (Gmail)
- Option : `1` (Mot de passe d'application)
- Entrez votre email Gmail
- Collez le mot de passe d'application
- Confirmez

✅ Votre compte est ajouté et la synchronisation démarre automatiquement!

---

## Étape 3 : Vérifier la synchronisation

```bash
# Voir les logs en temps réel
docker-compose logs -f worker

# Dans un autre terminal, vérifier les comptes
docker-compose exec api python scripts/add_email_account.py list
```

---

## Étape 4 : Tester l'API

### Lister les comptes
```bash
curl http://localhost:8000/api/accounts/
```

### Voir les emails synchronisés
```bash
curl http://localhost:8000/api/emails/?limit=10
```

### Tester la classification
```bash
curl -X POST http://localhost:8000/api/classification/test \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "Facture Amazon - Janvier 2025",
    "sender": "invoice@amazon.com",
    "body_preview": "Votre facture du mois de janvier est disponible..."
  }'
```

---

## Étape 5 : Accéder aux interfaces

- **API Documentation** : http://localhost:8000/docs
- **Portainer (gestion Docker)** : http://localhost:9000
- **API Health Check** : http://localhost:8000/health

---

## Configuration Ollama (Classification IA)

Le modèle Mistral est nécessaire pour la classification intelligente.

```bash
# Télécharger le modèle Mistral (une seule fois)
docker-compose exec ollama ollama pull mistral

# Vérifier que le modèle est prêt
docker-compose exec ollama ollama list
```

⏱️ Le téléchargement peut prendre 5-10 minutes selon votre connexion.

---

## Commandes utiles

### Gestion des conteneurs
```bash
# Démarrer
docker-compose up -d

# Arrêter
docker-compose down

# Redémarrer un service
docker-compose restart worker

# Voir tous les logs
docker-compose logs -f

# Voir les logs d'un service spécifique
docker-compose logs -f api
```

### Base de données
```bash
# Se connecter à PostgreSQL
docker-compose exec db psql -U emailagent -d emailagent

# Backup de la base
docker-compose exec db pg_dump -U emailagent emailagent > backup.sql

# Restore
cat backup.sql | docker-compose exec -T db psql -U emailagent emailagent
```

### Gestion des emails
```bash
# Lister les comptes
docker-compose exec api python scripts/add_email_account.py list

# Ajouter un compte
docker-compose exec api python scripts/add_email_account.py

# Déclencher une synchronisation manuelle (à implémenter)
# curl -X POST http://localhost:8000/api/accounts/1/sync
```

---

## Dépannage rapide

### Les conteneurs ne démarrent pas
```bash
# Voir les erreurs
docker-compose logs

# Rebuild complet
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### La synchronisation ne fonctionne pas
```bash
# Vérifier les logs du worker
docker-compose logs worker

# Vérifier que Redis fonctionne
docker-compose exec redis redis-cli ping
# Doit répondre : PONG

# Vérifier Celery
docker-compose exec worker celery -A worker.celery_app inspect active
```

### Problèmes de credentials
```bash
# Lister les comptes
docker-compose exec api python scripts/add_email_account.py list

# Mettre à jour un compte existant
docker-compose exec api python scripts/add_email_account.py
# Choisir le même email, il proposera de mettre à jour
```

### Base de données
```bash
# Vérifier la connexion
docker-compose exec db pg_isready -U emailagent

# Voir les tables
docker-compose exec db psql -U emailagent -d emailagent -c "\dt"

# Compter les emails
docker-compose exec db psql -U emailagent -d emailagent -c "SELECT COUNT(*) FROM emails;"
```

---

## Prochaines étapes

1. **Configurer les règles de classification** pour automatiser le tri
2. **Ajouter d'autres comptes email** si nécessaire
3. **Personnaliser les catégories** selon vos besoins
4. **Configurer les actions automatiques** (archivage, suppression)
5. **Mettre en place un frontend** (React - à venir)

---

## Documentation complète

- 📘 [Architecture et développement](../CLAUDE.md)
- 📧 [Guide détaillé : Ajouter un compte email](AJOUTER_COMPTE_EMAIL.md)
- 🔧 [Configuration avancée](../README.md)

---

## Support

**Problèmes courants** : Voir section Dépannage ci-dessus

**Questions** :
- Issues GitHub
- Documentation dans `CLAUDE.md`
- Logs détaillés : `docker-compose logs -f`

---

**Version** : 1.0.0
**Dernière mise à jour** : 2025-01-20

Bon tri automatique ! 📬✨
