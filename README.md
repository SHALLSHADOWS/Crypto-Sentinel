# 🚀 Crypto Sentinel - Assistant IA Crypto Autonome

## 📋 Description
Crypto Sentinel est un assistant IA autonome qui surveille en temps réel le lancement de nouveaux tokens ERC20 sur Ethereum, les analyse avec une intelligence artificielle avancée (GPT-4), et envoie des notifications Telegram pour les tokens ayant un potentiel spéculatif élevé.

## ✨ Fonctionnalités Principales
- [ ] Surveillance temps réel des nouveaux contrats ERC20 via WebSocket Ethereum
- [ ] Analyse multi-sources (Dexscreener, Dextools, Telegram, Twitter)
- [ ] Évaluation IA du potentiel spéculatif avec scoring automatique (0-10)
- [ ] Notifications Telegram instantanées pour les opportunités détectées
- [ ] Base de données MongoDB pour historique et analytics
- [ ] Architecture modulaire extensible (Solana, BSC, Base)
- [ ] Déploiement Azure App Service ready

## 🛠️ Technologies Utilisées
- **Backend** : Python 3.11+, FastAPI, WebSockets
- **Base de données** : MongoDB Atlas
- **IA** : OpenAI GPT-4 / Claude
- **Blockchain** : Web3.py, Alchemy/Infura WebSocket
- **APIs** : Dexscreener, Telegram Bot API
- **Monitoring** : APScheduler, Logging
- **DevOps** : Docker, Azure App Service

## 🚀 Installation

### Prérequis
- Python 3.11+
- MongoDB (Atlas ou local)
- Redis (optionnel, pour le cache)
- Docker & Docker Compose (pour déploiement)
- Clés API requises :
  - OpenAI API Key
  - Alchemy/Infura API Key
  - Telegram Bot Token
  - Dexscreener API (optionnel)
  - Twitter API (optionnel)

### Installation Rapide avec Docker

#### 🚀 Script de Démarrage Automatique

**Linux/Mac :**
```bash
# 1. Cloner le repository
git clone <repository-url>
cd crypto-sentinel

# 2. Lancer le script de démarrage
chmod +x start.sh
./start.sh
```

**Windows (PowerShell) :**
```powershell
# 1. Cloner le repository
git clone <repository-url>
cd crypto-sentinel

# 2. Lancer le script de démarrage
.\start.ps1
```

#### 📋 Installation Manuelle

```bash
# 1. Cloner le repository
git clone <repository-url>
cd crypto-sentinel

# 2. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos clés API

# 3. Lancer avec Docker Compose
docker-compose up -d

# 4. Vérifier le statut
curl http://localhost:8000/health
```

### Installation Manuelle

```bash
# 1. Cloner et configurer
git clone <repository-url>
cd crypto-sentinel
cp .env.example .env

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer MongoDB (local)
# Installer MongoDB Community Edition
# Créer la base de données : crypto_sentinel

# 5. Lancer l'application
python -m app.main
```

### Configuration des Variables d'Environnement

Éditer le fichier `.env` :

```env
# Application
APP_NAME=Crypto Sentinel
ENVIRONMENT=development
LOG_LEVEL=INFO

# Base de données
MONGODB_URL=mongodb://localhost:27017/crypto_sentinel
REDIS_URL=redis://localhost:6379/0

# Ethereum
ALCHEMY_API_KEY=your_alchemy_key
INFURA_API_KEY=your_infura_key
ETHEREUM_NETWORK=mainnet

# Intelligence Artificielle
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4
OPENAI_MAX_TOKENS=1000

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
ENABLE_TELEGRAM_NOTIFICATIONS=true

# APIs externes (optionnel)
DEXSCREENER_API_KEY=your_dexscreener_key
TWITTER_BEARER_TOKEN=your_twitter_bearer
ENABLE_TWITTER_MONITORING=false

# Seuils d'analyse
MIN_NOTIFICATION_SCORE=7.0
MIN_LIQUIDITY_USD=10000
MAX_TOKEN_AGE_HOURS=24
```

## 🏗️ Architecture

```
Crypto Sentinel Architecture

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Core Engine   │    │   Notifications │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ Ethereum WS     │───▶│ Token Scanner   │───▶│ Telegram Bot    │
│ Dexscreener API │───▶│ GPT Analyzer    │───▶│ Alert System    │
│ Dextools        │───▶│ Risk Assessor   │───▶│ Dashboard       │
│ Telegram Scraper│───▶│ Score Engine    │    │                 │
│ Twitter Monitor │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   MongoDB       │
                       │   Database      │
                       └─────────────────┘
```

## 🤖 Guide pour IDE IA (Cursor/Copilot)

### Configuration recommandée
- Utiliser le fichier `tasks.md` comme référence principale pour le développement
- Activer les suggestions contextuelles pour Python et FastAPI
- Configurer les snippets personnalisés pour les patterns crypto

### Commandes IA utiles
- `@workspace` : Analyser l'ensemble du projet crypto-sentinel
- `@terminal` : Exécuter les commandes de test et déploiement
- `@docs` : Consulter la documentation technique

### Patterns de développement
- Suivre les conventions PEP 8 pour Python
- Utiliser les type hints pour toutes les fonctions
- Implémenter des tests unitaires pour chaque module
- Documenter les fonctions avec des docstrings détaillées

## 📚 Documentation
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - Architecture détaillée du système
- [API.md](docs/API.md) - Documentation des endpoints FastAPI
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Guide de déploiement Azure
- [SECURITY.md](docs/SECURITY.md) - Bonnes pratiques de sécurité

## 📊 Utilisation

### Démarrage Rapide

1. **Lancer l'application**
   ```bash
   # Avec Docker
   docker-compose up -d
   
   # Ou manuellement
   python -m app.main
   ```

2. **Vérifier le fonctionnement**
   ```bash
   # Santé de l'application
   curl http://localhost:8000/health
   
   # Statistiques système
   curl http://localhost:8000/stats
   ```

3. **Accéder aux interfaces**
   - **API Documentation** : http://localhost:8000/docs
   - **Health Check** : http://localhost:8000/health
   - **Monitoring** : http://localhost:3000 (Grafana, si activé)

### API Endpoints

#### Endpoints Principaux

```http
# Page d'accueil
GET /

# Santé de l'application
GET /health
Response: {
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "database": "connected",
    "websocket": "active",
    "gpt_analyzer": "ready"
  }
}

# Statistiques système
GET /stats
Response: {
  "tokens_analyzed_today": 156,
  "high_score_tokens": 12,
  "notifications_sent": 8,
  "uptime_hours": 24.5,
  "gpt_tokens_used": 45000,
  "estimated_cost_usd": 2.25
}
```

#### Endpoints d'Analyse

```http
# Récupérer les analyses récentes
GET /api/analyses/recent?limit=10
Response: [
  {
    "id": "507f1f77bcf86cd799439011",
    "token_info": {
      "contract_address": "0x...",
      "name": "NewToken",
      "symbol": "NEW",
      "total_supply": 1000000,
      "decimals": 18,
      "created_at": "2024-01-15T10:00:00Z"
    },
    "ai_analysis": {
      "overall_score": 8.5,
      "recommendation": "BUY",
      "confidence": 0.85,
      "reasoning": "Token shows strong fundamentals..."
    },
    "analyzed_at": "2024-01-15T10:05:00Z"
  }
]

# Récupérer les analyses avec score élevé
GET /api/analyses/high-score?min_score=7.0&limit=5

# Récupérer une analyse spécifique
GET /api/analyses/{analysis_id}
```

### Notifications Telegram

#### Configuration du Bot

1. **Créer un bot Telegram**
   - Contacter @BotFather sur Telegram
   - Créer un nouveau bot : `/newbot`
   - Récupérer le token

2. **Configurer le chat**
   ```bash
   # Trouver votre chat ID
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates"
   ```

3. **Format des notifications**
   ```
   🚀 NOUVEAU TOKEN DÉTECTÉ
   
   📊 Score: 8.5/10 ⭐
   💎 Token: NewToken (NEW)
   📍 Contrat: 0x1234...5678
   💰 Liquidité: $45,000
   
   🤖 Analyse IA:
   Token shows strong fundamentals with innovative use case...
   
   ⚠️ Risques: Medium
   🎯 Recommandation: BUY
   🔗 Dexscreener: https://dexscreener.com/ethereum/0x1234...5678
   ```

### Monitoring et Logs

#### Logs de l'Application

```bash
# Suivre les logs en temps réel
docker-compose logs -f crypto-sentinel

# Logs spécifiques
tail -f logs/crypto_sentinel.log
tail -f logs/websocket.log
tail -f logs/gpt_analyzer.log
```

#### Métriques Importantes

- **Tokens détectés/heure** : Nombre de nouveaux tokens identifiés
- **Analyses réussies** : Pourcentage d'analyses GPT complétées
- **Notifications envoyées** : Nombre d'alertes Telegram
- **Coût GPT** : Estimation des coûts OpenAI
- **Uptime services** : Disponibilité des composants

### Commandes Utiles

```bash
# Développement
python -m pytest tests/                    # Exécuter les tests
python -m pytest tests/ -v --cov=app      # Tests avec couverture
black app/ tests/                          # Formatter le code
mypy app/                                  # Vérification des types

# Production
docker-compose up -d                       # Lancer en arrière-plan
docker-compose down                         # Arrêter les services
docker-compose logs -f crypto-sentinel     # Suivre les logs
docker-compose restart crypto-sentinel     # Redémarrer l'app

# Maintenance
docker system prune                        # Nettoyer Docker
docker-compose pull                         # Mettre à jour les images
```

## 🧪 Tests
```bash
# Tests unitaires
pytest tests/unit/

# Tests d'intégration
pytest tests/integration/

# Tests avec couverture
pytest --cov=app tests/

# Tests de performance
pytest tests/performance/
```

## 🚀 Déploiement

### Développement local
```bash
python app/main.py
```

### Production Azure App Service
```bash
# Build Docker image
docker build -t crypto-sentinel .

# Deploy to Azure
az webapp create --resource-group crypto-rg --plan crypto-plan --name crypto-sentinel
```

## 📊 Monitoring et Analytics
- Dashboard temps réel des tokens détectés
- Métriques de performance des sources de données
- Historique des scores IA et résultats
- Alertes système et monitoring uptime

## ⚠️ Limitations et Considérations
- **Rate Limits** : Respect des limites API (Etherscan, OpenAI, Telegram)
- **Coûts** : Surveillance des coûts OpenAI et infrastructure Azure
- **Latence** : Optimisation pour détection la plus rapide possible
- **Fiabilité** : Gestion des erreurs et reconnexions automatiques

## 🔐 Sécurité
- Chiffrement des clés API dans Azure Key Vault
- Validation stricte des données d'entrée
- Logging sécurisé sans exposition de secrets
- Authentification Telegram sécurisée

## 🤝 Contribution
1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit les changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

## 📈 Roadmap
- [ ] Support Solana et BSC
- [ ] Interface web dashboard
- [ ] Machine Learning pour améliorer les prédictions
- [ ] API publique pour développeurs
- [ ] Mobile app pour notifications

## 📄 Licence
MIT License - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 🆘 Support
Pour toute question ou problème :
- Créer une issue GitHub
- Consulter la documentation dans `/docs`
- Vérifier les logs dans `/logs`

---

**⚡ Crypto Sentinel - Détectez les opportunités crypto avant tout le monde !**