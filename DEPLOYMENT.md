# 🚀 Guide de Déploiement - Crypto Sentinel

Ce guide détaille les différentes méthodes de déploiement de Crypto Sentinel en production.

## 📋 Table des Matières

1. [Prérequis](#prérequis)
2. [Déploiement avec Docker](#déploiement-avec-docker)
3. [Déploiement sur Azure](#déploiement-sur-azure)
4. [Déploiement sur AWS](#déploiement-sur-aws)
5. [Déploiement sur VPS](#déploiement-sur-vps)
6. [Configuration de Production](#configuration-de-production)
7. [Monitoring et Maintenance](#monitoring-et-maintenance)
8. [Sécurité](#sécurité)
9. [Troubleshooting](#troubleshooting)

## 🔧 Prérequis

### Ressources Minimales
- **CPU** : 2 vCPUs
- **RAM** : 4 GB
- **Stockage** : 20 GB SSD
- **Bande passante** : 100 Mbps

### Ressources Recommandées
- **CPU** : 4 vCPUs
- **RAM** : 8 GB
- **Stockage** : 50 GB SSD
- **Bande passante** : 1 Gbps

### Services Externes Requis
- **MongoDB Atlas** (ou instance MongoDB)
- **Redis Cloud** (optionnel, pour le cache)
- **Clés API** :
  - OpenAI API Key
  - Alchemy/Infura API Key
  - Telegram Bot Token

## 🐳 Déploiement avec Docker

### 1. Préparation

```bash
# Cloner le repository
git clone <repository-url>
cd crypto-sentinel

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos vraies valeurs
```

### 2. Déploiement Simple

```bash
# Construire et lancer
docker-compose up -d

# Vérifier le statut
docker-compose ps
docker-compose logs -f crypto-sentinel
```

### 3. Déploiement avec Monitoring

```bash
# Lancer avec Prometheus et Grafana
docker-compose --profile monitoring up -d

# Accéder aux interfaces
# Application: http://localhost:8000
# Grafana: http://localhost:3000 (admin/cryptosentinel2024)
# Prometheus: http://localhost:9090
```

### 4. Déploiement Production avec Nginx

```bash
# Créer le certificat SSL
mkdir -p nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/crypto-sentinel.key \
  -out nginx/ssl/crypto-sentinel.crt

# Lancer avec reverse proxy
docker-compose --profile production up -d
```

## ☁️ Déploiement sur Azure

### 1. Azure Container Instances (ACI)

```bash
# Créer un groupe de ressources
az group create --name crypto-sentinel-rg --location eastus

# Créer un registre de conteneurs
az acr create --resource-group crypto-sentinel-rg \
  --name cryptosentinelacr --sku Basic

# Construire et pousser l'image
az acr build --registry cryptosentinelacr \
  --image crypto-sentinel:latest .

# Déployer sur ACI
az container create \
  --resource-group crypto-sentinel-rg \
  --name crypto-sentinel-app \
  --image cryptosentinelacr.azurecr.io/crypto-sentinel:latest \
  --cpu 2 --memory 4 \
  --ports 8000 \
  --environment-variables \
    MONGODB_URL="$MONGODB_URL" \
    OPENAI_API_KEY="$OPENAI_API_KEY" \
    ALCHEMY_API_KEY="$ALCHEMY_API_KEY" \
    TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
```

### 2. Azure App Service

```bash
# Créer un plan App Service
az appservice plan create \
  --name crypto-sentinel-plan \
  --resource-group crypto-sentinel-rg \
  --sku B2 --is-linux

# Créer l'application web
az webapp create \
  --resource-group crypto-sentinel-rg \
  --plan crypto-sentinel-plan \
  --name crypto-sentinel-app \
  --deployment-container-image-name cryptosentinelacr.azurecr.io/crypto-sentinel:latest

# Configurer les variables d'environnement
az webapp config appsettings set \
  --resource-group crypto-sentinel-rg \
  --name crypto-sentinel-app \
  --settings \
    MONGODB_URL="$MONGODB_URL" \
    OPENAI_API_KEY="$OPENAI_API_KEY" \
    ALCHEMY_API_KEY="$ALCHEMY_API_KEY" \
    TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
```

## 🌐 Déploiement sur AWS

### 1. AWS ECS (Elastic Container Service)

```bash
# Créer un cluster ECS
aws ecs create-cluster --cluster-name crypto-sentinel-cluster

# Créer un repository ECR
aws ecr create-repository --repository-name crypto-sentinel

# Construire et pousser l'image
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker build -t crypto-sentinel .
docker tag crypto-sentinel:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/crypto-sentinel:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/crypto-sentinel:latest
```

### 2. Task Definition ECS

```json
{
  "family": "crypto-sentinel-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "crypto-sentinel",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/crypto-sentinel:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "MONGODB_URL", "value": "${MONGODB_URL}"},
        {"name": "OPENAI_API_KEY", "value": "${OPENAI_API_KEY}"},
        {"name": "ALCHEMY_API_KEY", "value": "${ALCHEMY_API_KEY}"},
        {"name": "TELEGRAM_BOT_TOKEN", "value": "${TELEGRAM_BOT_TOKEN}"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/crypto-sentinel",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

## 🖥️ Déploiement sur VPS

### 1. Préparation du Serveur (Ubuntu 22.04)

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation de Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Installation de Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Installation d'outils utiles
sudo apt install -y git htop curl wget nginx certbot python3-certbot-nginx
```

### 2. Configuration SSL avec Let's Encrypt

```bash
# Obtenir un certificat SSL
sudo certbot --nginx -d your-domain.com

# Configuration Nginx
sudo nano /etc/nginx/sites-available/crypto-sentinel
```

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

### 3. Déploiement de l'Application

```bash
# Cloner le projet
git clone <repository-url> /opt/crypto-sentinel
cd /opt/crypto-sentinel

# Configuration
cp .env.example .env
# Éditer .env avec vos valeurs

# Lancer l'application
docker-compose up -d

# Activer Nginx
sudo ln -s /etc/nginx/sites-available/crypto-sentinel /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## ⚙️ Configuration de Production

### Variables d'Environnement Critiques

```env
# Production settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING

# Sécurité
SECRET_KEY=<générer-une-clé-forte-aléatoire>
CORS_ORIGINS=https://your-domain.com

# Performance
MAX_CONCURRENT_ANALYSES=10
MAX_QUEUE_SIZE=500
CACHE_TTL_SECONDS=1800

# Limites de coût
MAX_DAILY_GPT_COST_USD=100.0
GPT_RATE_LIMIT_PER_MINUTE=30
```

### Optimisations de Performance

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  crypto-sentinel:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

## 📊 Monitoring et Maintenance

### 1. Logs et Monitoring

```bash
# Suivre les logs
docker-compose logs -f --tail=100 crypto-sentinel

# Métriques système
docker stats
htop

# Espace disque
df -h
docker system df
```

### 2. Sauvegarde Automatique

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups/crypto-sentinel"

# Créer le répertoire de sauvegarde
mkdir -p $BACKUP_DIR

# Sauvegarder MongoDB
docker exec crypto-sentinel-mongodb mongodump --out /tmp/backup_$DATE
docker cp crypto-sentinel-mongodb:/tmp/backup_$DATE $BACKUP_DIR/

# Sauvegarder les logs
tar -czf $BACKUP_DIR/logs_$DATE.tar.gz logs/

# Nettoyer les anciennes sauvegardes (garder 7 jours)
find $BACKUP_DIR -name "*" -mtime +7 -delete

echo "Sauvegarde terminée: $BACKUP_DIR/backup_$DATE"
```

### 3. Crontab pour Maintenance

```bash
# Éditer crontab
crontab -e

# Ajouter ces lignes
# Sauvegarde quotidienne à 2h du matin
0 2 * * * /opt/crypto-sentinel/scripts/backup.sh

# Nettoyage Docker hebdomadaire
0 3 * * 0 docker system prune -f

# Redémarrage hebdomadaire
0 4 * * 0 cd /opt/crypto-sentinel && docker-compose restart

# Vérification de santé toutes les 5 minutes
*/5 * * * * curl -f http://localhost:8000/health || echo "Health check failed" | mail -s "Crypto Sentinel Alert" admin@yourcompany.com
```

## 🔒 Sécurité

### 1. Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 2. Fail2Ban

```bash
# Installation
sudo apt install fail2ban

# Configuration
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
port = http,https
logpath = /var/log/nginx/error.log
```

### 3. Secrets Management

```bash
# Utiliser Docker Secrets en production
echo "your_openai_api_key" | docker secret create openai_api_key -
echo "your_telegram_bot_token" | docker secret create telegram_bot_token -
```

## 🔧 Troubleshooting

### Problèmes Courants

#### 1. Application ne démarre pas

```bash
# Vérifier les logs
docker-compose logs crypto-sentinel

# Vérifier la configuration
docker-compose config

# Vérifier les variables d'environnement
docker-compose exec crypto-sentinel env | grep -E "MONGODB|OPENAI|TELEGRAM"
```

#### 2. Problèmes de connexion MongoDB

```bash
# Tester la connexion
docker-compose exec crypto-sentinel python -c "
import pymongo
client = pymongo.MongoClient('mongodb://mongodb:27017')
print(client.admin.command('ping'))
"
```

#### 3. Problèmes de WebSocket

```bash
# Vérifier les connexions réseau
netstat -tulpn | grep :8000

# Tester WebSocket
wscat -c ws://localhost:8000/ws
```

#### 4. Problèmes de performance

```bash
# Surveiller les ressources
docker stats crypto-sentinel-app

# Analyser les logs de performance
grep "slow" logs/crypto_sentinel.log

# Vérifier l'utilisation de la base de données
docker exec crypto-sentinel-mongodb mongo --eval "db.stats()"
```

### Commandes de Diagnostic

```bash
# Script de diagnostic complet
#!/bin/bash
echo "=== Crypto Sentinel Diagnostic ==="
echo "Date: $(date)"
echo

echo "=== Docker Status ==="
docker-compose ps
echo

echo "=== Application Health ==="
curl -s http://localhost:8000/health | jq .
echo

echo "=== System Resources ==="
free -h
df -h
echo

echo "=== Recent Logs ==="
docker-compose logs --tail=20 crypto-sentinel
echo

echo "=== Network Connectivity ==="
ping -c 3 8.8.8.8
echo

echo "=== Database Status ==="
docker exec crypto-sentinel-mongodb mongo --eval "db.adminCommand('ping')"
```

## 📞 Support

Pour obtenir de l'aide :

1. **Documentation** : Consultez le [README.md](README.md)
2. **Issues** : Créez une issue sur GitHub
3. **Logs** : Incluez toujours les logs pertinents
4. **Configuration** : Vérifiez votre fichier `.env`

---

**Note** : Ce guide couvre les déploiements les plus courants. Pour des configurations spécifiques ou des environnements complexes, consultez la documentation officielle des plateformes utilisées.