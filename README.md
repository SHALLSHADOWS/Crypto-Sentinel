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

## 📦 Installation

### Prérequis
- Python 3.11+
- MongoDB Atlas account
- Alchemy/Infura API key
- OpenAI API key
- Telegram Bot Token
- Git

### Étapes d'installation
1. **Cloner le repository**
   ```bash
   git clone <repository-url>
   cd crypto-sentinel
   ```

2. **Créer l'environnement virtuel**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **Installer les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurer l'environnement**
   ```bash
   cp .env.example .env
   # Éditer .env avec vos clés API
   ```

5. **Lancer l'application**
   ```bash
   python app/main.py
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