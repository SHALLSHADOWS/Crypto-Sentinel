# 🎯 Crypto Sentinel - Plan de Développement Détaillé

## 📋 Vue d'ensemble
Ce document contient toutes les tâches nécessaires pour développer l'assistant IA crypto autonome. Chaque tâche est conçue pour être exécutée immédiatement par une IA sans ambiguïté.

---

## 🚀 PHASE 1 : INFRASTRUCTURE DE BASE

### [CRITIQUE] CORE-001 - Configuration de l'environnement

#### 🎯 Objectif
Configurer l'environnement de développement avec toutes les dépendances nécessaires.

#### 📋 Prérequis
- [ ] Python 3.11+ installé
- [ ] Git configuré
- [ ] Accès aux clés API (OpenAI, Alchemy, Telegram)

#### 🔧 Étapes IA Détaillées

**Étape 1 : Créer le fichier requirements.txt**
**Fichier** : `requirements.txt`
**Action** : Créer
**Code à implémenter** :
```txt
# FastAPI et serveur
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0

# Base de données
motor==3.3.2
pymongo==4.6.0

# Blockchain et Web3
web3==6.12.0
websockets==12.0

# IA et OpenAI
openai==1.3.7

# HTTP et APIs
httpx==0.25.2
aiohttp==3.9.1
requests==2.31.0

# Telegram
python-telegram-bot==20.7
telethon==1.33.1

# Twitter (optionnel)
tweepy==4.14.0

# Scheduling et tâches
APScheduler==3.10.4

# Utilitaires
python-dotenv==1.0.0
loguru==0.7.2
rich==13.7.0
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Monitoring
psutil==5.9.6
```
**Validation** : `pip install -r requirements.txt` s'exécute sans erreur

**Étape 2 : Créer le fichier .env.example**
**Fichier** : `.env.example`
**Action** : Créer
**Code à implémenter** :
```env
# === APPLICATION ===
DEBUG=False
HOST=0.0.0.0
PORT=8000
SECRET_KEY=your-secret-key-change-in-production

# === DATABASE ===
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE=crypto_sentinel

# === ETHEREUM ===
ALCHEMY_API_KEY=your-alchemy-api-key
INFURA_PROJECT_ID=your-infura-project-id
ETHEREUM_NETWORK=mainnet

# === OPENAI ===
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4-turbo-preview

# === TELEGRAM ===
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-telegram-chat-id
TELEGRAM_API_ID=your-telegram-api-id
TELEGRAM_API_HASH=your-telegram-api-hash

# === DEXTOOLS ===
DEXTOOLS_API_KEY=your-dextools-api-key

# === TWITTER (OPTIONNEL) ===
TWITTER_BEARER_TOKEN=your-twitter-bearer-token
TWITTER_API_KEY=your-twitter-api-key
TWITTER_API_SECRET=your-twitter-api-secret
ENABLE_TWITTER_MONITORING=False

# === ANALYSIS SETTINGS ===
MIN_NOTIFICATION_SCORE=7.0
MIN_LIQUIDITY_USD=10000
MAX_CONCURRENT_ANALYSES=5
```
**Validation** : Le fichier contient toutes les variables nécessaires

#### 📁 Fichiers Concernés
- `requirements.txt` - Dépendances Python
- `.env.example` - Template de configuration
- `.gitignore` - Exclusions Git

#### 🧪 Tests à Implémenter
- [ ] Test d'installation des dépendances
- [ ] Test de chargement de la configuration

---

### [CRITIQUE] CORE-002 - Modules utilitaires

#### 🎯 Objectif
Créer les modules utilitaires pour le logging, la validation et les helpers.

#### 🔧 Étapes IA Détaillées

**Étape 1 : Créer le système de logging**
**Fichier** : `app/utils/logger.py`
**Action** : Créer
**Code à implémenter** :
```python
#!/usr/bin/env python3
"""
Crypto Sentinel - Logging Utilities
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler
from rich.console import Console

def setup_logger(name: str) -> logging.Logger:
    """Configure un logger avec Rich et rotation de fichiers."""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Console handler avec Rich
    console = Console()
    console_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=True,
        markup=True
    )
    console_handler.setLevel(logging.INFO)
    
    # File handler avec rotation
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    file_handler = RotatingFileHandler(
        log_dir / "crypto_sentinel.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Formatters
    console_format = "%(message)s"
    file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    console_handler.setFormatter(logging.Formatter(console_format))
    file_handler.setFormatter(logging.Formatter(file_format))
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger
```
**Validation** : Le logger fonctionne et crée les fichiers de log

**Étape 2 : Créer les utilitaires de validation**
**Fichier** : `app/utils/validators.py`
**Action** : Créer
**Code à implémenter** :
```python
#!/usr/bin/env python3
"""
Crypto Sentinel - Validation Utilities
"""

import re
from typing import Optional
from web3 import Web3

def is_valid_ethereum_address(address: str) -> bool:
    """Valide une adresse Ethereum."""
    if not address or not isinstance(address, str):
        return False
    
    if not address.startswith('0x') or len(address) != 42:
        return False
    
    try:
        return Web3.is_address(address)
    except:
        return False

def is_valid_transaction_hash(tx_hash: str) -> bool:
    """Valide un hash de transaction."""
    if not tx_hash or not isinstance(tx_hash, str):
        return False
    
    pattern = r'^0x[a-fA-F0-9]{64}$'
    return bool(re.match(pattern, tx_hash))

def sanitize_token_name(name: str) -> Optional[str]:
    """Nettoie et valide un nom de token."""
    if not name or not isinstance(name, str):
        return None
    
    # Supprimer les caractères non-ASCII et limiter la longueur
    cleaned = re.sub(r'[^\x20-\x7E]', '', name).strip()
    
    if len(cleaned) > 50:
        cleaned = cleaned[:50]
    
    return cleaned if len(cleaned) > 0 else None

def is_suspicious_token_name(name: str) -> bool:
    """Détecte les noms de tokens suspects."""
    if not name:
        return False
    
    suspicious_patterns = [
        r'(?i)(elon|musk|tesla|spacex)',
        r'(?i)(moon|rocket|pump|gem)',
        r'(?i)(safe|baby|mini|doge)',
        r'(?i)(inu|shib|floki)',
        r'(?i)(100x|1000x|lambo)'
    ]
    
    name_lower = name.lower()
    return any(re.search(pattern, name_lower) for pattern in suspicious_patterns)
```
**Validation** : Les fonctions de validation retournent les résultats attendus

#### 📁 Fichiers Concernés
- `app/utils/__init__.py` - Module utilitaires
- `app/utils/logger.py` - Système de logging
- `app/utils/validators.py` - Fonctions de validation
- `app/utils/helpers.py` - Fonctions d'aide

---

## 🔗 PHASE 2 : SERVICES DE DONNÉES

### [HAUTE] DATA-001 - Service de scan de tokens

#### 🎯 Objectif
Créer le service de scan des tokens ERC20 pour récupérer toutes les informations nécessaires.

#### 🔧 Étapes IA Détaillées

**Étape 1 : Implémenter le scanner de tokens**
**Fichier** : `app/token_scanner.py`
**Action** : Créer
**Code à implémenter** :
```python
#!/usr/bin/env python3
"""
Crypto Sentinel - Token Scanner Service
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime

from web3 import Web3
from web3.exceptions import ContractLogicError
import httpx

from app.config import settings, ERC20_ABI, STABLE_TOKENS
from app.models import TokenInfo, TokenSource
from app.utils.logger import setup_logger
from app.utils.validators import is_valid_ethereum_address, sanitize_token_name

logger = setup_logger(__name__)

class TokenScannerService:
    """Service de scan des tokens ERC20."""
    
    def __init__(self):
        self.web3 = Web3(Web3.HTTPProvider(settings.ethereum_http_url))
        self.http_client = httpx.AsyncClient(timeout=30)
        
    async def scan_token(self, contract_address: str) -> Optional[TokenInfo]:
        """Scanne un token ERC20 complet."""
        try:
            if not is_valid_ethereum_address(contract_address):
                logger.error(f"Adresse invalide: {contract_address}")
                return None
            
            logger.info(f"🔍 Scan du token: {contract_address}")
            
            # Informations de base du contrat
            basic_info = await self._get_basic_token_info(contract_address)
            if not basic_info:
                return None
            
            # Informations de marché
            market_info = await self._get_market_info(contract_address)
            
            # Informations de liquidité
            liquidity_info = await self._get_liquidity_info(contract_address)
            
            # Informations des holders
            holder_info = await self._get_holder_info(contract_address)
            
            # Créer l'objet TokenInfo
            token_info = TokenInfo(
                contract_address=contract_address,
                name=basic_info.get('name'),
                symbol=basic_info.get('symbol'),
                decimals=basic_info.get('decimals'),
                total_supply=basic_info.get('total_supply'),
                price_usd=market_info.get('price_usd'),
                market_cap_usd=market_info.get('market_cap_usd'),
                liquidity_usd=liquidity_info.get('liquidity_usd'),
                volume_24h_usd=market_info.get('volume_24h_usd'),
                price_change_24h=market_info.get('price_change_24h'),
                holder_count=holder_info.get('holder_count'),
                transaction_count=holder_info.get('transaction_count'),
                source=TokenSource.MANUAL
            )
            
            logger.info(f"✅ Token scanné: {token_info.name} ({token_info.symbol})")
            return token_info
            
        except Exception as e:
            logger.error(f"Erreur lors du scan de {contract_address}: {e}")
            return None
    
    async def _get_basic_token_info(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """Récupère les informations de base du contrat ERC20."""
        try:
            contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=ERC20_ABI
            )
            
            # Appels aux fonctions ERC20
            name = contract.functions.name().call()
            symbol = contract.functions.symbol().call()
            decimals = contract.functions.decimals().call()
            total_supply_raw = contract.functions.totalSupply().call()
            
            # Conversion de la supply
            total_supply = total_supply_raw / (10 ** decimals)
            
            return {
                'name': sanitize_token_name(name),
                'symbol': symbol.upper() if symbol else None,
                'decimals': decimals,
                'total_supply': total_supply
            }
            
        except ContractLogicError:
            logger.error(f"Contrat non-ERC20: {contract_address}")
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos de base: {e}")
            return None
```
**Validation** : Le service peut scanner un token ERC20 existant

#### 📁 Fichiers Concernés
- `app/token_scanner.py` - Service de scan principal
- `app/utils/web3_helpers.py` - Helpers Web3

---

### [HAUTE] DATA-002 - Service Dexscreener

#### 🎯 Objectif
Intégrer l'API Dexscreener pour récupérer les données de marché et détecter les nouvelles paires.

#### 🔧 Étapes IA Détaillées

**Étape 1 : Implémenter le service Dexscreener**
**Fichier** : `app/dexscanner.py`
**Action** : Créer
**Code à implémenter** :
```python
#!/usr/bin/env python3
"""
Crypto Sentinel - Dexscreener Service
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

import httpx
from app.config import settings
from app.models import TokenInfo, TokenSource
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class DexscannerService:
    """Service d'intégration avec Dexscreener API."""
    
    def __init__(self):
        self.base_url = settings.DEXSCREENER_API_URL
        self.http_client = httpx.AsyncClient(
            timeout=settings.DEXSCREENER_TIMEOUT,
            limits=httpx.Limits(max_connections=10)
        )
        self.rate_limiter = asyncio.Semaphore(5)  # 5 requêtes simultanées max
        self.last_request_time = 0
        self.min_request_interval = 60 / settings.DEXSCREENER_RATE_LIMIT
        
    async def start_monitoring(self):
        """Démarre la surveillance des nouvelles paires."""
        logger.info("🔄 Démarrage du monitoring Dexscreener...")
        
        while True:
            try:
                await self._scan_new_pairs()
                await asyncio.sleep(settings.SCAN_INTERVAL_SECONDS)
            except Exception as e:
                logger.error(f"Erreur dans le monitoring Dexscreener: {e}")
                await asyncio.sleep(60)  # Attendre 1 minute en cas d'erreur
    
    async def _scan_new_pairs(self):
        """Scanne les nouvelles paires sur Dexscreener."""
        try:
            # Récupérer les nouvelles paires Ethereum
            new_pairs = await self._get_latest_pairs('ethereum')
            
            if new_pairs:
                logger.info(f"📊 {len(new_pairs)} nouvelles paires détectées")
                
                for pair in new_pairs:
                    await self._process_new_pair(pair)
                    
        except Exception as e:
            logger.error(f"Erreur lors du scan des nouvelles paires: {e}")
    
    async def _get_latest_pairs(self, chain: str) -> List[Dict[str, Any]]:
        """Récupère les dernières paires d'une blockchain."""
        async with self.rate_limiter:
            await self._respect_rate_limit()
            
            try:
                url = f"{self.base_url}/dex/pairs/{chain}"
                response = await self.http_client.get(url)
                response.raise_for_status()
                
                data = response.json()
                pairs = data.get('pairs', [])
                
                # Filtrer les paires récentes (< 1 heure)
                recent_pairs = []
                cutoff_time = datetime.utcnow() - timedelta(hours=1)
                
                for pair in pairs:
                    created_at = pair.get('pairCreatedAt')
                    if created_at:
                        pair_time = datetime.fromtimestamp(created_at / 1000)
                        if pair_time > cutoff_time:
                            recent_pairs.append(pair)
                
                return recent_pairs
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Erreur HTTP Dexscreener: {e.response.status_code}")
                return []
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des paires: {e}")
                return []
    
    async def _process_new_pair(self, pair_data: Dict[str, Any]):
        """Traite une nouvelle paire détectée."""
        try:
            base_token = pair_data.get('baseToken', {})
            quote_token = pair_data.get('quoteToken', {})
            
            # Identifier le token principal (non-stablecoin)
            token_address = None
            if base_token.get('symbol') not in ['WETH', 'USDT', 'USDC', 'DAI']:
                token_address = base_token.get('address')
            elif quote_token.get('symbol') not in ['WETH', 'USDT', 'USDC', 'DAI']:
                token_address = quote_token.get('address')
            
            if token_address:
                # Créer les informations du token
                token_info = self._create_token_info_from_pair(pair_data, token_address)
                
                if token_info:
                    # Déclencher l'analyse
                    await self._trigger_token_analysis(token_info)
                    
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la paire: {e}")
    
    def _create_token_info_from_pair(self, pair_data: Dict[str, Any], token_address: str) -> Optional[TokenInfo]:
        """Crée un TokenInfo à partir des données de paire."""
        try:
            base_token = pair_data.get('baseToken', {})
            quote_token = pair_data.get('quoteToken', {})
            
            # Déterminer quel token correspond à l'adresse
            token_data = base_token if base_token.get('address') == token_address else quote_token
            
            if not token_data:
                return None
            
            # Extraire les informations
            price_usd = float(pair_data.get('priceUsd', 0))
            liquidity_usd = float(pair_data.get('liquidity', {}).get('usd', 0))
            volume_24h = float(pair_data.get('volume', {}).get('h24', 0))
            price_change_24h = float(pair_data.get('priceChange', {}).get('h24', 0))
            
            token_info = TokenInfo(
                contract_address=token_address,
                name=token_data.get('name'),
                symbol=token_data.get('symbol'),
                price_usd=price_usd,
                liquidity_usd=liquidity_usd,
                volume_24h_usd=volume_24h,
                price_change_24h=price_change_24h,
                source=TokenSource.DEXSCREENER
            )
            
            return token_info
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du TokenInfo: {e}")
            return None
    
    async def _trigger_token_analysis(self, token_info: TokenInfo):
        """Déclenche l'analyse d'un token détecté."""
        # Cette méthode sera connectée au système principal
        logger.info(f"🎯 Nouveau token détecté via Dexscreener: {token_info.contract_address}")
        # TODO: Intégrer avec le système d'analyse principal
    
    async def _respect_rate_limit(self):
        """Respecte les limites de taux de l'API."""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = asyncio.get_event_loop().time()
```
**Validation** : Le service peut récupérer les données de Dexscreener

---

### [MOYENNE] DATA-003 - Service de notification Telegram

#### 🎯 Objectif
Créer le service de notifications Telegram pour envoyer les alertes de tokens à potentiel.

#### 🔧 Étapes IA Détaillées

**Étape 1 : Implémenter le notificateur Telegram**
**Fichier** : `app/telegram_notifier.py`
**Action** : Créer
**Code à implémenter** :
```python
#!/usr/bin/env python3
"""
Crypto Sentinel - Telegram Notifier Service
"""

import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from telegram import Bot
from telegram.error import TelegramError

from app.config import settings
from app.models import TokenAnalysis, NotificationAlert, create_notification_alert
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class TelegramNotifierService:
    """Service de notifications Telegram."""
    
    def __init__(self):
        self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.notification_cooldown = timedelta(minutes=settings.NOTIFICATION_COOLDOWN_MINUTES)
        self.last_notifications = {}  # Cache des dernières notifications
        
    async def send_alert(self, analysis: TokenAnalysis) -> bool:
        """Envoie une alerte pour un token à potentiel."""
        try:
            # Vérifier le cooldown
            if not self._can_send_notification(analysis.token_info.contract_address):
                logger.info(f"⏰ Notification en cooldown pour {analysis.token_info.contract_address}")
                return False
            
            # Créer le message
            message = self._create_alert_message(analysis)
            
            # Envoyer le message
            sent_message = await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=False
            )
            
            # Marquer comme envoyé
            self._mark_notification_sent(analysis.token_info.contract_address)
            
            logger.info(f"📢 Alerte envoyée pour {analysis.token_info.contract_address}")
            return True
            
        except TelegramError as e:
            logger.error(f"Erreur Telegram: {e}")
            return False
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'alerte: {e}")
            return False
    
    def _create_alert_message(self, analysis: TokenAnalysis) -> str:
        """Crée le message d'alerte formaté."""
        token = analysis.token_info
        ai = analysis.ai_analysis
        
        # Emojis basés sur le score
        if ai.score >= 8.5:
            emoji = "🚀🔥"
        elif ai.score >= 7.5:
            emoji = "🚀"
        else:
            emoji = "⭐"
        
        # Formatage des nombres
        price = f"${token.price_usd:.8f}" if token.price_usd else "N/A"
        market_cap = self._format_number(token.market_cap_usd) if token.market_cap_usd else "N/A"
        liquidity = self._format_number(token.liquidity_usd) if token.liquidity_usd else "N/A"
        volume = self._format_number(token.volume_24h_usd) if token.volume_24h_usd else "N/A"
        
        # Âge du token
        age = token.age_hours
        age_str = f"{age:.1f}h" if age else "N/A"
        
        message = f"""{emoji} <b>NOUVEAU TOKEN DÉTECTÉ</b> {emoji}

🪙 <b>{token.name or 'Unknown'}</b> (${token.symbol or 'N/A'})
📍 <code>{token.contract_address}</code>

📊 <b>MÉTRIQUES</b>
💰 Prix: {price}
📈 Market Cap: {market_cap}
💧 Liquidité: {liquidity}
📊 Volume 24h: {volume}
⏰ Âge: {age_str}
👥 Holders: {token.holder_count or 'N/A'}

🤖 <b>ANALYSE IA</b>
⭐ Score: <b>{ai.score}/10</b>
🎯 Recommandation: <b>{ai.recommendation.value.upper()}</b>
🔮 Confiance: {ai.confidence*100:.0f}%

💡 <b>RAISONNEMENT</b>
{ai.reasoning}

⚠️ <b>RISQUES</b>
{chr(10).join([f'• {risk}' for risk in ai.risks[:3]])}

🎯 <b>OPPORTUNITÉS</b>
{chr(10).join([f'• {opp}' for opp in ai.opportunities[:3]])}

🔗 <a href="https://dexscreener.com/ethereum/{token.contract_address}">Voir sur Dexscreener</a>
🔗 <a href="https://etherscan.io/address/{token.contract_address}">Voir sur Etherscan</a>

<i>⚡ Crypto Sentinel - {datetime.utcnow().strftime('%H:%M:%S UTC')}</i>"""
        
        return message
    
    def _format_number(self, value: Optional[float]) -> str:
        """Formate un nombre pour l'affichage."""
        if value is None:
            return "N/A"
        
        if value >= 1e9:
            return f"${value/1e9:.2f}B"
        elif value >= 1e6:
            return f"${value/1e6:.2f}M"
        elif value >= 1e3:
            return f"${value/1e3:.2f}K"
        else:
            return f"${value:.2f}"
    
    def _can_send_notification(self, contract_address: str) -> bool:
        """Vérifie si une notification peut être envoyée (cooldown)."""
        last_sent = self.last_notifications.get(contract_address)
        
        if last_sent is None:
            return True
        
        return datetime.utcnow() - last_sent > self.notification_cooldown
    
    def _mark_notification_sent(self, contract_address: str):
        """Marque une notification comme envoyée."""
        self.last_notifications[contract_address] = datetime.utcnow()
        
        # Nettoyer les anciennes entrées
        cutoff = datetime.utcnow() - timedelta(hours=24)
        self.last_notifications = {
            addr: time for addr, time in self.last_notifications.items()
            if time > cutoff
        }
    
    async def send_system_status(self, status: Dict[str, Any]) -> bool:
        """Envoie un rapport de statut système."""
        try:
            message = f"""
📊 <b>CRYPTO SENTINEL - RAPPORT DE STATUT</b>

🔄 <b>ACTIVITÉ</b>
• Tokens détectés aujourd'hui: {status.get('tokens_detected_today', 0)}
• Tokens analysés: {status.get('tokens_analyzed_today', 0)}
• Notifications envoyées: {status.get('notifications_sent_today', 0)}
• Score moyen: {status.get('average_score_today', 0):.1f}/10

⚡ <b>SYSTÈME</b>
• Base de données: {'✅' if status.get('database_connected') else '❌'}
• Ethereum: {'✅' if status.get('ethereum_connected') else '❌'}
• Services actifs: {status.get('services_running', 0)}

<i>📅 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</i>
"""
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du statut: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Vérifie l'état de santé du service Telegram."""
        try:
            await self.bot.get_me()
            return True
        except Exception as e:
            logger.error(f"Health check Telegram échoué: {e}")
            return False
```
**Validation** : Le service peut envoyer des messages Telegram

---

## 🤖 PHASE 3 : SERVICES AVANCÉS

### [MOYENNE] ADVANCED-001 - Service de scraping Telegram

#### 🎯 Objectif
Créer le service de surveillance des channels Telegram pour détecter les mentions de nouveaux tokens.

#### 🔧 Étapes IA Détaillées

**Étape 1 : Implémenter le scraper Telegram**
**Fichier** : `app/telegram_scraper.py`
**Action** : Créer
**Code à implémenter** :
```python
#!/usr/bin/env python3
"""
Crypto Sentinel - Telegram Scraper Service
"""

import asyncio
import re
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

from app.config import settings
from app.models import TokenInfo, TokenSource
from app.utils.logger import setup_logger
from app.utils.validators import is_valid_ethereum_address

logger = setup_logger(__name__)

class TelegramScraperService:
    """Service de scraping des channels Telegram."""
    
    def __init__(self):
        self.client = TelegramClient(
            'crypto_sentinel_session',
            settings.TELEGRAM_API_ID,
            settings.TELEGRAM_API_HASH
        )
        
        # Channels à surveiller
        self.monitored_channels = [
            '@uniswapgemsnew',
            '@dextoolstrending',
            '@newpairbot',
            '@tokenlaunches'
        ]
        
        # Patterns pour détecter les adresses de contrats
        self.contract_patterns = [
            r'0x[a-fA-F0-9]{40}',  # Adresse Ethereum standard
            r'Contract[:\s]*0x[a-fA-F0-9]{40}',  # "Contract: 0x..."
            r'CA[:\s]*0x[a-fA-F0-9]{40}',  # "CA: 0x..."
        ]
        
        self.processed_messages = set()  # Cache des messages traités
        
    async def start_monitoring(self):
        """Démarre la surveillance des channels Telegram."""
        try:
            logger.info("🔄 Démarrage du monitoring Telegram...")
            
            await self.client.start()
            
            # Vérifier l'authentification
            if not await self.client.is_user_authorized():
                logger.error("❌ Client Telegram non autorisé")
                return
            
            # S'abonner aux nouveaux messages
            @self.client.on(events.NewMessage(chats=self.monitored_channels))
            async def handle_new_message(event):
                await self._process_message(event)
            
            logger.info(f"✅ Surveillance active sur {len(self.monitored_channels)} channels")
            
            # Maintenir la connexion
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"Erreur dans le monitoring Telegram: {e}")
    
    async def _process_message(self, event):
        """Traite un nouveau message Telegram."""
        try:
            message = event.message
            
            # Éviter les doublons
            if message.id in self.processed_messages:
                return
            
            self.processed_messages.add(message.id)
            
            # Nettoyer le cache (garder seulement les 1000 derniers)
            if len(self.processed_messages) > 1000:
                self.processed_messages = set(list(self.processed_messages)[-1000:])
            
            # Extraire les adresses de contrats
            contract_addresses = self._extract_contract_addresses(message.text or "")
            
            if contract_addresses:
                logger.info(f"📱 {len(contract_addresses)} contrat(s) détecté(s) sur Telegram")
                
                for address in contract_addresses:
                    await self._handle_detected_contract(address, message)
                    
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message Telegram: {e}")
    
    def _extract_contract_addresses(self, text: str) -> List[str]:
        """Extrait les adresses de contrats d'un texte."""
        addresses = []
        
        for pattern in self.contract_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            
            for match in matches:
                # Nettoyer l'adresse (enlever les préfixes)
                clean_address = re.search(r'0x[a-fA-F0-9]{40}', match)
                if clean_address:
                    address = clean_address.group(0)
                    
                    if is_valid_ethereum_address(address) and address not in addresses:
                        addresses.append(address)
        
        return addresses
    
    async def _handle_detected_contract(self, contract_address: str, message):
        """Traite un contrat détecté."""
        try:
            logger.info(f"🎯 Nouveau contrat détecté via Telegram: {contract_address}")
            
            # Créer les informations de base
            token_info = TokenInfo(
                contract_address=contract_address,
                source=TokenSource.TELEGRAM,
                detected_at=datetime.utcnow()
            )
            
            # Extraire des informations supplémentaires du message
            self._enrich_token_info_from_message(token_info, message.text or "")
            
            # Déclencher l'analyse
            await self._trigger_token_analysis(token_info)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du contrat {contract_address}: {e}")
    
    def _enrich_token_info_from_message(self, token_info: TokenInfo, text: str):
        """Enrichit les informations du token à partir du message."""
        try:
            # Rechercher le nom du token
            name_patterns = [
                r'Name[:\s]*([^\n\r]{1,50})',
                r'Token[:\s]*([^\n\r]{1,50})',
                r'\$([A-Z]{2,10})\s',
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match and not token_info.name:
                    token_info.name = match.group(1).strip()
                    break
            
            # Rechercher le symbole
            symbol_patterns = [
                r'Symbol[:\s]*\$?([A-Z]{2,10})',
                r'Ticker[:\s]*\$?([A-Z]{2,10})',
                r'\$([A-Z]{2,10})\b',
            ]
            
            for pattern in symbol_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match and not token_info.symbol:
                    token_info.symbol = match.group(1).strip()
                    break
            
        except Exception as e:
            logger.error(f"Erreur lors de l'enrichissement: {e}")
    
    async def _trigger_token_analysis(self, token_info: TokenInfo):
        """Déclenche l'analyse d'un token détecté."""
        # Cette méthode sera connectée au système principal
        logger.info(f"🎯 Nouveau token détecté via Telegram: {token_info.contract_address}")
        # TODO: Intégrer avec le système d'analyse principal
    
    async def health_check(self) -> bool:
        """Vérifie l'état de santé du service."""
        try:
            if not self.client.is_connected():
                return False
            
            # Test simple
            await self.client.get_me()
            return True
            
        except Exception as e:
            logger.error(f"Health check Telegram scraper échoué: {e}")
            return False
```
**Validation** : Le service peut se connecter et surveiller les channels Telegram

---

### [BASSE] ADVANCED-002 - Service de monitoring Twitter

#### 🎯 Objectif
Créer le service optionnel de surveillance Twitter pour détecter les mentions de tokens.

#### 🔧 Étapes IA Détaillées

**Étape 1 : Implémenter le moniteur Twitter**
**Fichier** : `app/twitter_monitor.py`
**Action** : Créer
**Code à implémenter** :
```python
#!/usr/bin/env python3
"""
Crypto Sentinel - Twitter Monitor Service (Optionnel)
"""

import asyncio
import re
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

import tweepy

from app.config import settings
from app.models import TokenInfo, TokenSource
from app.utils.logger import setup_logger
from app.utils.validators import is_valid_ethereum_address

logger = setup_logger(__name__)

class TwitterMonitorService:
    """Service de surveillance Twitter (optionnel)."""
    
    def __init__(self):
        if not settings.ENABLE_TWITTER_MONITORING:
            logger.info("📱 Monitoring Twitter désactivé")
            return
        
        # Configuration de l'API Twitter
        auth = tweepy.OAuthHandler(
            settings.TWITTER_API_KEY,
            settings.TWITTER_API_SECRET
        )
        auth.set_access_token(
            settings.TWITTER_ACCESS_TOKEN,
            settings.TWITTER_ACCESS_TOKEN_SECRET
        )
        
        self.api = tweepy.API(auth, wait_on_rate_limit=True)
        
        # Mots-clés à surveiller
        self.keywords = [
            'new token',
            'just launched',
            'contract address',
            '$ETH token',
            'new gem',
            '0x',  # Adresses Ethereum
        ]
        
        self.processed_tweets = set()
        
    async def start_monitoring(self):
        """Démarre la surveillance Twitter."""
        if not settings.ENABLE_TWITTER_MONITORING:
            return
        
        try:
            logger.info("🔄 Démarrage du monitoring Twitter...")
            
            # Créer un stream listener
            stream_listener = TwitterStreamListener(self)
            stream = tweepy.Stream(auth=self.api.auth, listener=stream_listener)
            
            # Démarrer le stream avec les mots-clés
            stream.filter(track=self.keywords, is_async=True)
            
            logger.info(f"✅ Surveillance Twitter active avec {len(self.keywords)} mots-clés")
            
        except Exception as e:
            logger.error(f"Erreur dans le monitoring Twitter: {e}")
    
    async def process_tweet(self, tweet_data: Dict[str, Any]):
        """Traite un tweet détecté."""
        try:
            tweet_id = tweet_data.get('id')
            
            if tweet_id in self.processed_tweets:
                return
            
            self.processed_tweets.add(tweet_id)
            
            # Nettoyer le cache
            if len(self.processed_tweets) > 1000:
                self.processed_tweets = set(list(self.processed_tweets)[-1000:])
            
            text = tweet_data.get('text', '')
            
            # Extraire les adresses de contrats
            contract_addresses = self._extract_contract_addresses(text)
            
            if contract_addresses:
                logger.info(f"🐦 {len(contract_addresses)} contrat(s) détecté(s) sur Twitter")
                
                for address in contract_addresses:
                    await self._handle_detected_contract(address, tweet_data)
                    
        except Exception as e:
            logger.error(f"Erreur lors du traitement du tweet: {e}")
    
    def _extract_contract_addresses(self, text: str) -> List[str]:
        """Extrait les adresses de contrats d'un tweet."""
        addresses = []
        
        # Pattern pour les adresses Ethereum
        pattern = r'0x[a-fA-F0-9]{40}'
        matches = re.findall(pattern, text)
        
        for match in matches:
            if is_valid_ethereum_address(match) and match not in addresses:
                addresses.append(match)
        
        return addresses
    
    async def _handle_detected_contract(self, contract_address: str, tweet_data: Dict[str, Any]):
        """Traite un contrat détecté sur Twitter."""
        try:
            logger.info(f"🎯 Nouveau contrat détecté via Twitter: {contract_address}")
            
            # Créer les informations de base
            token_info = TokenInfo(
                contract_address=contract_address,
                source=TokenSource.TWITTER,
                detected_at=datetime.utcnow()
            )
            
            # Déclencher l'analyse
            await self._trigger_token_analysis(token_info)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du contrat Twitter {contract_address}: {e}")
    
    async def _trigger_token_analysis(self, token_info: TokenInfo):
        """Déclenche l'analyse d'un token détecté."""
        # Cette méthode sera connectée au système principal
        logger.info(f"🎯 Nouveau token détecté via Twitter: {token_info.contract_address}")
        # TODO: Intégrer avec le système d'analyse principal
    
    async def health_check(self) -> bool:
        """Vérifie l'état de santé du service."""
        if not settings.ENABLE_TWITTER_MONITORING:
            return True  # Service désactivé = OK
        
        try:
            # Test simple de l'API
            self.api.verify_credentials()
            return True
        except Exception as e:
            logger.error(f"Health check Twitter échoué: {e}")
            return False


class TwitterStreamListener(tweepy.StreamListener):
    """Listener pour le stream Twitter."""
    
    def __init__(self, monitor_service):
        super().__init__()
        self.monitor_service = monitor_service
    
    def on_status(self, status):
        """Appelé quand un nouveau tweet est reçu."""
        try:
            tweet_data = {
                'id': status.id,
                'text': status.text,
                'user': status.user.screen_name,
                'created_at': status.created_at
            }
            
            # Traiter le tweet de manière asynchrone
            asyncio.create_task(self.monitor_service.process_tweet(tweet_data))
            
        except Exception as e:
            logger.error(f"Erreur dans le stream listener: {e}")
        
        return True
    
    def on_error(self, status_code):
        """Appelé en cas d'erreur."""
        logger.error(f"Erreur Twitter stream: {status_code}")
        
        if status_code == 420:
            # Rate limit - arrêter le stream
            return False
        
        return True
```
**Validation** : Le service peut surveiller Twitter (si activé)

---

## ⚙️ PHASE 4 : ORCHESTRATION ET DÉPLOIEMENT

### [CRITIQUE] DEPLOY-001 - Scheduler et orchestration

#### 🎯 Objectif
Créer le système de scheduling pour orchestrer toutes les tâches périodiques.

#### 🔧 Étapes IA Détaillées

**Étape 1 : Implémenter le scheduler**
**Fichier** : `app/scheduler.py`
**Action** : Créer
**Code à implémenter** :
```python
#!/usr/bin/env python3
"""
Crypto Sentinel - Scheduler Service
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class SchedulerService:
    """Service de scheduling pour les tâches périodiques."""
    
    def __init__(self, services: Dict[str, Any]):
        self.services = services
        self.scheduler = AsyncIOScheduler()
        self.start_time = datetime.utcnow()
        
    def start(self):
        """Démarre le scheduler avec toutes les tâches."""
        try:
            logger.info("⏰ Démarrage du scheduler...")
            
            # Tâches de maintenance
            self._schedule_maintenance_tasks()
            
            # Tâches de monitoring
            self._schedule_monitoring_tasks()
            
            # Tâches de reporting
            self._schedule_reporting_tasks()
            
            # Démarrer le scheduler
            self.scheduler.start()
            
            logger.info("✅ Scheduler démarré avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du scheduler: {e}")
    
    def stop(self):
        """Arrête le scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("🛑 Scheduler arrêté")
    
    def _schedule_maintenance_tasks(self):
        """Programme les tâches de maintenance."""
        # Nettoyage de la base de données (quotidien à 2h)
        self.scheduler.add_job(
            self._cleanup_database,
            CronTrigger(hour=2, minute=0),
            id='cleanup_database',
            name='Nettoyage base de données'
        )
        
        # Nettoyage des caches (toutes les 6 heures)
        self.scheduler.add_job(
            self._cleanup_caches,
            IntervalTrigger(hours=6),
            id='cleanup_caches',
            name='Nettoyage des caches'
        )
        
        # Sauvegarde des analytics (quotidien à 23h)
        self.scheduler.add_job(
            self._save_daily_analytics,
            CronTrigger(hour=23, minute=0),
            id='save_analytics',
            name='Sauvegarde analytics'
        )
    
    def _schedule_monitoring_tasks(self):
        """Programme les tâches de monitoring."""
        # Health check général (toutes les 5 minutes)
        self.scheduler.add_job(
            self._system_health_check,
            IntervalTrigger(minutes=5),
            id='health_check',
            name='Vérification santé système'
        )
        
        # Traitement des analyses en attente (toutes les 30 secondes)
        self.scheduler.add_job(
            self._process_pending_analyses,
            IntervalTrigger(seconds=30),
            id='process_pending',
            name='Traitement analyses en attente'
        )
        
        # Vérification des notifications non envoyées (toutes les minutes)
        self.scheduler.add_job(
            self._check_pending_notifications,
            IntervalTrigger(minutes=1),
            id='check_notifications',
            name='Vérification notifications'
        )
    
    def _schedule_reporting_tasks(self):
        """Programme les tâches de reporting."""
        # Rapport quotidien (tous les jours à 8h)
        self.scheduler.add_job(
            self._send_daily_report,
            CronTrigger(hour=8, minute=0),
            id='daily_report',
            name='Rapport quotidien'
        )
        
        # Rapport de statut (toutes les 4 heures)
        self.scheduler.add_job(
            self._send_status_report,
            IntervalTrigger(hours=4),
            id='status_report',
            name='Rapport de statut'
        )
    
    async def _cleanup_database(self):
        """Nettoie la base de données."""
        try:
            logger.info("🧹 Début du nettoyage de la base de données...")
            
            if 'db' in self.services:
                cleanup_stats = await self.services['db'].cleanup_old_data()
                logger.info(f"✅ Nettoyage terminé: {cleanup_stats}")
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage DB: {e}")
    
    async def _cleanup_caches(self):
        """Nettoie les caches des services."""
        try:
            logger.info("🧹 Nettoyage des caches...")
            
            # Nettoyer le cache GPT
            if 'gpt_analyzer' in self.services:
                analyzer = self.services['gpt_analyzer']
                if hasattr(analyzer, '_cleanup_cache'):
                    analyzer._cleanup_cache()
            
            logger.info("✅ Caches nettoyés")
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des caches: {e}")
    
    async def _save_daily_analytics(self):
        """Sauvegarde les analytics quotidiennes."""
        try:
            logger.info("📊 Sauvegarde des analytics quotidiennes...")
            
            if 'db' in self.services:
                stats = await self.services['db'].get_system_stats()
                # TODO: Créer et sauvegarder l'objet AnalyticsData
                logger.info("✅ Analytics sauvegardées")
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des analytics: {e}")
    
    async def _system_health_check(self):
        """Vérifie la santé du système."""
        try:
            issues = []
            
            # Vérifier la base de données
            if 'db' in self.services:
                if not await self.services['db'].health_check():
                    issues.append("Base de données déconnectée")
            
            # Vérifier Ethereum WebSocket
            if 'eth_listener' in self.services:
                if not self.services['eth_listener'].is_connected():
                    issues.append("WebSocket Ethereum déconnecté")
            
            # Vérifier GPT
            if 'gpt_analyzer' in self.services:
                if not await self.services['gpt_analyzer'].health_check():
                    issues.append("Service GPT indisponible")
            
            # Vérifier Telegram
            if 'telegram_notifier' in self.services:
                if not await self.services['telegram_notifier'].health_check():
                    issues.append("Service Telegram indisponible")
            
            if issues:
                logger.warning(f"⚠️ Problèmes détectés: {', '.join(issues)}")
                # TODO: Envoyer une alerte
            
        except Exception as e:
            logger.error(f"Erreur lors du health check: {e}")
    
    async def _process_pending_analyses(self):
        """Traite les analyses en attente."""
        try:
            if 'db' not in self.services or 'gpt_analyzer' not in self.services:
                return
            
            # Récupérer les analyses en attente
            pending = await self.services['db'].get_pending_analyses(limit=5)
            
            if pending:
                logger.info(f"🔄 Traitement de {len(pending)} analyses en attente")
                
                for analysis in pending:
                    # Traiter l'analyse
                    await self.services['gpt_analyzer'].analyze_token(analysis)
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement des analyses en attente: {e}")
    
    async def _check_pending_notifications(self):
        """Vérifie les notifications en attente."""
        try:
            if 'db' not in self.services or 'telegram_notifier' not in self.services:
                return
            
            # Récupérer les notifications en attente
            pending_notifications = await self.services['db'].get_pending_notifications()
            
            if pending_notifications:
                logger.info(f"📢 {len(pending_notifications)} notification(s) en attente")
                
                for notification in pending_notifications:
                    success = await self.services['telegram_notifier'].send_alert(notification)
                    if success:
                        await self.services['db'].mark_notification_sent(notification.id)
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des notifications: {e}")
    
    async def _send_daily_report(self):
        """Envoie le rapport quotidien."""
        try:
            logger.info("📊 Génération du rapport quotidien...")
            
            if 'db' in self.services and 'telegram_notifier' in self.services:
                stats = await self.services['db'].get_daily_stats()
                await self.services['telegram_notifier'].send_system_status(stats)
                logger.info("✅ Rapport quotidien envoyé")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du rapport quotidien: {e}")
    
    async def _send_status_report(self):
        """Envoie le rapport de statut."""
        try:
            if 'telegram_notifier' in self.services:
                uptime = datetime.utcnow() - self.start_time
                status = {
                    'uptime_hours': uptime.total_seconds() / 3600,
                    'services_running': len(self.services),
                    'database_connected': 'db' in self.services,
                    'ethereum_connected': 'eth_listener' in self.services
                }
                
                await self.services['telegram_notifier'].send_system_status(status)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du rapport de statut: {e}")
```
**Validation** : Le scheduler fonctionne et exécute les tâches programmées

---

### [CRITIQUE] DEPLOY-002 - Orchestrateur principal

#### 🎯 Objectif
Créer l'orchestrateur principal qui coordonne tous les services.

#### 🔧 Étapes IA Détaillées

**Étape 1 : Créer l'orchestrateur**
**Fichier** : `app/orchestrator.py`
**Action** : Créer
**Code à implémenter** :
```python
#!/usr/bin/env python3
"""
Crypto Sentinel - Main Orchestrator
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from app.config import settings
from app.db import DatabaseManager
from app.websocket_listener import EthereumWebSocketListener
from app.token_scanner import TokenScannerService
from app.gpt_analyzer import GPTAnalyzerService
from app.telegram_notifier import TelegramNotifierService
from app.dexscanner import DexscannerService
from app.telegram_scraper import TelegramScraperService
from app.twitter_monitor import TwitterMonitorService
from app.scheduler import SchedulerService
from app.models import TokenAnalysis, create_token_analysis
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class CryptoSentinelOrchestrator:
    """Orchestrateur principal du système Crypto Sentinel."""
    
    def __init__(self):
        self.services = {}
        self.running = False
        self.start_time = None
        
    async def initialize(self):
        """Initialise tous les services."""
        try:
            logger.info("🚀 Initialisation de Crypto Sentinel...")
            
            # Base de données
            logger.info("📊 Initialisation de la base de données...")
            self.services['db'] = DatabaseManager()
            await self.services['db'].connect()
            await self.services['db'].create_indexes()
            
            # Services d'analyse
            logger.info("🤖 Initialisation des services d'analyse...")
            self.services['token_scanner'] = TokenScannerService()
            self.services['gpt_analyzer'] = GPTAnalyzerService()
            
            # Services de notification
            logger.info("📢 Initialisation des services de notification...")
            self.services['telegram_notifier'] = TelegramNotifierService()
            
            # Services de données
            logger.info("🔗 Initialisation des services de données...")
            self.services['dexscanner'] = DexscannerService()
            self.services['telegram_scraper'] = TelegramScraperService()
            
            if settings.ENABLE_TWITTER_MONITORING:
                self.services['twitter_monitor'] = TwitterMonitorService()
            
            # WebSocket Ethereum (en dernier)
            logger.info("⛓️ Initialisation du WebSocket Ethereum...")
            self.services['eth_listener'] = EthereumWebSocketListener(
                token_scanner=self.services['token_scanner'],
                gpt_analyzer=self.services['gpt_analyzer'],
                notifier=self.services['telegram_notifier'],
                db=self.services['db']
            )
            
            # Scheduler
            logger.info("⏰ Initialisation du scheduler...")
            self.services['scheduler'] = SchedulerService(self.services)
            
            logger.info("✅ Tous les services initialisés")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'initialisation: {e}")
            raise
    
    async def start(self):
        """Démarre tous les services."""
        try:
            if self.running:
                logger.warning("⚠️ Le système est déjà en cours d'exécution")
                return
            
            logger.info("🚀 Démarrage de Crypto Sentinel...")
            self.start_time = datetime.utcnow()
            self.running = True
            
            # Démarrer les services en arrière-plan
            tasks = []
            
            # WebSocket Ethereum
            if 'eth_listener' in self.services:
                tasks.append(asyncio.create_task(
                    self.services['eth_listener'].start_listening()
                ))
            
            # Dexscanner
            if 'dexscanner' in self.services:
                tasks.append(asyncio.create_task(
                    self.services['dexscanner'].start_monitoring()
                ))
            
            # Telegram Scraper
            if 'telegram_scraper' in self.services:
                tasks.append(asyncio.create_task(
                    self.services['telegram_scraper'].start_monitoring()
                ))
            
            # Twitter Monitor
            if 'twitter_monitor' in self.services:
                tasks.append(asyncio.create_task(
                    self.services['twitter_monitor'].start_monitoring()
                ))
            
            # Scheduler
            if 'scheduler' in self.services:
                self.services['scheduler'].start()
            
            logger.info(f"✅ {len(tasks)} services démarrés en arrière-plan")
            
            # Attendre que tous les services se terminent
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du démarrage: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Arrête tous les services."""
        try:
            if not self.running:
                return
            
            logger.info("🛑 Arrêt de Crypto Sentinel...")
            self.running = False
            
            # Arrêter le scheduler
            if 'scheduler' in self.services:
                self.services['scheduler'].stop()
            
            # Arrêter les autres services
            if 'eth_listener' in self.services:
                await self.services['eth_listener'].stop()
            
            # Fermer la base de données
            if 'db' in self.services:
                await self.services['db'].disconnect()
            
            logger.info("✅ Tous les services arrêtés")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt: {e}")
    
    async def analyze_token_manually(self, contract_address: str) -> Optional[TokenAnalysis]:
        """Analyse manuellement un token."""
        try:
            logger.info(f"🔍 Analyse manuelle du token: {contract_address}")
            
            # Scanner le token
            token_info = await self.services['token_scanner'].scan_token(contract_address)
            if not token_info:
                logger.error(f"❌ Impossible de scanner le token: {contract_address}")
                return None
            
            # Analyser avec GPT
            ai_analysis = await self.services['gpt_analyzer'].analyze_token(token_info)
            if not ai_analysis:
                logger.error(f"❌ Impossible d'analyser le token avec GPT: {contract_address}")
                return None
            
            # Créer l'analyse complète
            analysis = create_token_analysis(token_info, ai_analysis)
            
            # Sauvegarder
            await self.services['db'].save_token_analysis(analysis)
            
            # Envoyer notification si score élevé
            if analysis.should_notify:
                await self.services['telegram_notifier'].send_alert(analysis)
            
            logger.info(f"✅ Analyse terminée - Score: {ai_analysis.score}/10")
            return analysis
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse manuelle: {e}")
            return None
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Récupère le statut du système."""
        try:
            status = {
                'running': self.running,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'services': {},
                'database': {},
                'statistics': {}
            }
            
            # Statut des services
            for service_name, service in self.services.items():
                if hasattr(service, 'health_check'):
                    try:
                        status['services'][service_name] = await service.health_check()
                    except:
                        status['services'][service_name] = False
                else:
                    status['services'][service_name] = True
            
            # Statut de la base de données
            if 'db' in self.services:
                status['database'] = await self.services['db'].get_system_stats()
            
            # Statistiques
            if 'gpt_analyzer' in self.services:
                status['statistics']['gpt'] = self.services['gpt_analyzer'].get_stats()
            
            return status
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut: {e}")
            return {'error': str(e)}
```
**Validation** : L'orchestrateur peut démarrer et coordonner tous les services

---

## 🧪 PHASE 5 : TESTS ET VALIDATION

### [HAUTE] TEST-001 - Tests unitaires

#### 🎯 Objectif
Créer une suite de tests unitaires pour valider le fonctionnement des composants.

#### 🔧 Étapes IA Détaillées

**Étape 1 : Tests des modèles**
**Fichier** : `tests/test_models.py`
**Action** : Créer
**Code à implémenter** :
```python
#!/usr/bin/env python3
"""
Tests pour les modèles Pydantic
"""

import pytest
from datetime import datetime
from app.models import (
    TokenInfo, AIAnalysis, TokenAnalysis, 
    RiskLevel, Recommendation, TokenSource,
    create_token_analysis
)

class TestTokenInfo:
    """Tests pour le modèle TokenInfo."""
    
    def test_valid_token_info(self):
        """Test création d'un TokenInfo valide."""
        token = TokenInfo(
            contract_address="0x1234567890123456789012345678901234567890",
            name="Test Token",
            symbol="TEST",
            decimals=18,
            total_supply=1000000.0,
            price_usd=0.001,
            source=TokenSource.MANUAL
        )
        
        assert token.contract_address == "0x1234567890123456789012345678901234567890"
        assert token.name == "Test Token"
        assert token.symbol == "TEST"
        assert token.is_new_token is True  # Par défaut
    
    def test_invalid_contract_address(self):
        """Test validation d'adresse de contrat invalide."""
        with pytest.raises(ValueError):
            TokenInfo(
                contract_address="invalid_address",
                name="Test Token",
                source=TokenSource.MANUAL
            )
    
    def test_age_calculation(self):
        """Test calcul de l'âge du token."""
        # Token créé il y a 2 heures
        past_time = datetime.utcnow().replace(hour=datetime.utcnow().hour - 2)
        
        token = TokenInfo(
            contract_address="0x1234567890123456789012345678901234567890",
            detected_at=past_time,
            source=TokenSource.MANUAL
        )
        
        assert token.age_hours is not None
        assert 1.5 <= token.age_hours <= 2.5  # Environ 2 heures

class TestAIAnalysis:
    """Tests pour le modèle AIAnalysis."""
    
    def test_valid_ai_analysis(self):
        """Test création d'une AIAnalysis valide."""
        analysis = AIAnalysis(
            score=8.5,
            confidence=0.9,
            recommendation=Recommendation.BUY,
            reasoning="Token prometteur avec bonne liquidité",
            risks=["Volatilité élevée"],
            opportunities=["Potentiel de croissance"]
        )
        
        assert analysis.score == 8.5
        assert analysis.risk_level == RiskLevel.HIGH  # Score > 8
        assert analysis.has_high_potential is True  # Score >= 7.5
    
    def test_score_validation(self):
        """Test validation du score (0-10)."""
        with pytest.raises(ValueError):
            AIAnalysis(
                score=11.0,  # Score invalide
                confidence=0.9,
                recommendation=Recommendation.BUY,
                reasoning="Test"
            )

class TestTokenAnalysis:
    """Tests pour le modèle TokenAnalysis."""
    
    def test_notification_logic(self):
        """Test logique de notification."""
        token_info = TokenInfo(
            contract_address="0x1234567890123456789012345678901234567890",
            liquidity_usd=50000.0,  # Au-dessus du minimum
            source=TokenSource.MANUAL
        )
        
        ai_analysis = AIAnalysis(
            score=8.0,  # Au-dessus du seuil
            confidence=0.8,
            recommendation=Recommendation.BUY,
            reasoning="Test"
        )
        
        analysis = create_token_analysis(token_info, ai_analysis)
        
        assert analysis.should_notify is True
        assert analysis.ai_score == 8.0

@pytest.fixture
def sample_token_info():
    """Fixture pour un TokenInfo de test."""
    return TokenInfo(
        contract_address="0x1234567890123456789012345678901234567890",
        name="Sample Token",
        symbol="SAMPLE",
        decimals=18,
        total_supply=1000000.0,
        price_usd=0.001,
        liquidity_usd=25000.0,
        source=TokenSource.MANUAL
    )

@pytest.fixture
def sample_ai_analysis():
    """Fixture pour une AIAnalysis de test."""
    return AIAnalysis(
        score=7.5,
        confidence=0.85,
        recommendation=Recommendation.HOLD,
        reasoning="Token avec potentiel modéré",
        risks=["Liquidité limitée", "Équipe anonyme"],
        opportunities=["Niche intéressante", "Communauté active"]
    )
```
**Validation** : Tous les tests passent avec `pytest tests/test_models.py`

---

### [HAUTE] TEST-002 - Tests d'intégration

#### 🎯 Objectif
Créer des tests d'intégration pour valider l'interaction entre les services.

#### 🔧 Étapes IA Détaillées

**Étape 1 : Tests de la base de données**
**Fichier** : `tests/test_database.py`
**Action** : Créer
**Code à implémenter** :
```python
#!/usr/bin/env python3
"""
Tests d'intégration pour la base de données
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from app.db import DatabaseManager
from app.models import (
    TokenInfo, AIAnalysis, TokenAnalysis,
    TokenSource, Recommendation, create_token_analysis
)
from app.config import settings

@pytest.fixture
async def db_manager():
    """Fixture pour le gestionnaire de base de données."""
    # Utiliser une base de données de test
    test_settings = settings.copy()
    test_settings.MONGODB_DATABASE = "crypto_sentinel_test"
    
    db = DatabaseManager()
    await db.connect()
    
    # Nettoyer avant les tests
    await db.db.tokens.delete_many({})
    await db.db.analytics.delete_many({})
    await db.db.alerts.delete_many({})
    
    yield db
    
    # Nettoyer après les tests
    await db.db.tokens.delete_many({})
    await db.db.analytics.delete_many({})
    await db.db.alerts.delete_many({})
    await db.disconnect()

@pytest.mark.asyncio
class TestDatabaseOperations:
    """Tests des opérations de base de données."""
    
    async def test_save_and_retrieve_token_analysis(self, db_manager):
        """Test sauvegarde et récupération d'analyse."""
        # Créer une analyse de test
        token_info = TokenInfo(
            contract_address="0x1234567890123456789012345678901234567890",
            name="Test Token",
            symbol="TEST",
            source=TokenSource.MANUAL
        )
        
        ai_analysis = AIAnalysis(
            score=8.0,
            confidence=0.9,
            recommendation=Recommendation.BUY,
            reasoning="Test analysis"
        )
        
        analysis = create_token_analysis(token_info, ai_analysis)
        
        # Sauvegarder
        saved_id = await db_manager.save_token_analysis(analysis)
        assert saved_id is not None
        
        # Récupérer
        retrieved = await db_manager.get_token_analysis(token_info.contract_address)
        assert retrieved is not None
        assert retrieved.token_info.contract_address == token_info.contract_address
        assert retrieved.ai_analysis.score == 8.0
    
    async def test_get_recent_tokens(self, db_manager):
        """Test récupération des tokens récents."""
        # Créer plusieurs analyses
        for i in range(5):
            token_info = TokenInfo(
                contract_address=f"0x{str(i).zfill(40)}",
                name=f"Token {i}",
                symbol=f"TOK{i}",
                source=TokenSource.MANUAL
            )
            
            ai_analysis = AIAnalysis(
                score=float(5 + i),
                confidence=0.8,
                recommendation=Recommendation.HOLD,
                reasoning=f"Analysis {i}"
            )
            
            analysis = create_token_analysis(token_info, ai_analysis)
            await db_manager.save_token_analysis(analysis)
        
        # Récupérer les tokens récents
        recent = await db_manager.get_recent_tokens(limit=3)
        assert len(recent) == 3
        
        # Vérifier l'ordre (plus récents en premier)
        scores = [t.ai_analysis.score for t in recent]
        assert scores == [9.0, 8.0, 7.0]  # Ordre décroissant par date
    
    async def test_get_high_score_tokens(self, db_manager):
        """Test récupération des tokens à score élevé."""
        # Créer des analyses avec différents scores
        scores = [6.0, 8.5, 7.0, 9.2, 5.5]
        
        for i, score in enumerate(scores):
            token_info = TokenInfo(
                contract_address=f"0x{str(i).zfill(40)}",
                name=f"Token {i}",
                source=TokenSource.MANUAL
            )
            
            ai_analysis = AIAnalysis(
                score=score,
                confidence=0.8,
                recommendation=Recommendation.HOLD,
                reasoning=f"Analysis {i}"
            )
            
            analysis = create_token_analysis(token_info, ai_analysis)
            await db_manager.save_token_analysis(analysis)
        
        # Récupérer les tokens à score élevé (>= 8.0)
        high_score = await db_manager.get_high_score_tokens(min_score=8.0)
        assert len(high_score) == 2  # Scores 8.5 et 9.2
        
        # Vérifier l'ordre (scores décroissants)
        retrieved_scores = [t.ai_analysis.score for t in high_score]
        assert retrieved_scores == [9.2, 8.5]
    
    async def test_cleanup_old_data(self, db_manager):
        """Test nettoyage des anciennes données."""
        # Créer des analyses anciennes et récentes
        old_date = datetime.utcnow() - timedelta(days=8)
        recent_date = datetime.utcnow() - timedelta(hours=1)
        
        # Analyse ancienne
        old_token = TokenInfo(
            contract_address="0x" + "1" * 40,
            name="Old Token",
            source=TokenSource.MANUAL,
            detected_at=old_date
        )
        
        old_ai = AIAnalysis(
            score=7.0,
            confidence=0.8,
            recommendation=Recommendation.HOLD,
            reasoning="Old analysis"
        )
        
        old_analysis = create_token_analysis(old_token, old_ai)
        old_analysis.created_at = old_date
        await db_manager.save_token_analysis(old_analysis)
        
        # Analyse récente
        recent_token = TokenInfo(
            contract_address="0x" + "2" * 40,
            name="Recent Token",
            source=TokenSource.MANUAL,
            detected_at=recent_date
        )
        
        recent_ai = AIAnalysis(
            score=8.0,
            confidence=0.9,
            recommendation=Recommendation.BUY,
            reasoning="Recent analysis"
        )
        
        recent_analysis = create_token_analysis(recent_token, recent_ai)
        recent_analysis.created_at = recent_date
        await db_manager.save_token_analysis(recent_analysis)
        
        # Vérifier qu'on a 2 analyses
        all_tokens = await db_manager.get_recent_tokens(limit=10)
        assert len(all_tokens) == 2
        
        # Nettoyer les données anciennes (> 7 jours)
        cleanup_stats = await db_manager.cleanup_old_data(days=7)
        assert cleanup_stats['tokens_deleted'] == 1
        
        # Vérifier qu'il ne reste que l'analyse récente
        remaining_tokens = await db_manager.get_recent_tokens(limit=10)
        assert len(remaining_tokens) == 1
        assert remaining_tokens[0].token_info.name == "Recent Token"
```
**Validation** : Tous les tests d'intégration passent

---

## 📚 PHASE 6 : DOCUMENTATION ET FINALISATION

### [MOYENNE] DOC-001 - Documentation technique

#### 🎯 Objectif
Créer la documentation technique complète du projet.

#### 🔧 Étapes IA Détaillées

**Étape 1 : Documentation de l'architecture**
**Fichier** : `docs/ARCHITECTURE.md`
**Action** : Créer
**Code à implémenter** :
```markdown
# 🏗️ Architecture de Crypto Sentinel

## Vue d'ensemble

Crypto Sentinel est un système distribué de surveillance et d'analyse de tokens ERC20 en temps réel. L'architecture suit les principes de Clean Architecture et de séparation des responsabilités.

## Diagramme d'architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CRYPTO SENTINEL                          │
├─────────────────────────────────────────────────────────────────┤
│                     COUCHE PRÉSENTATION                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   FastAPI   │  │  Telegram   │  │   Health    │            │
│  │   Routes    │  │ Notifications│  │   Checks    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
├─────────────────────────────────────────────────────────────────┤
│                     COUCHE MÉTIER                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │    Token    │  │     GPT     │  │ Orchestrator│            │
│  │   Scanner   │  │  Analyzer   │  │             │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
├─────────────────────────────────────────────────────────────────┤
│                  COUCHE INFRASTRUCTURE                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   MongoDB   │  │  Ethereum   │  │  External   │            │
│  │  Database   │  │  WebSocket  │  │    APIs     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

## Composants principaux

### 1. Services de données

#### EthereumWebSocketListener
- **Rôle** : Écoute en temps réel les nouveaux contrats déployés
- **Technologies** : Web3.py, WebSockets
- **Déclencheurs** : Nouveaux blocs, transactions de création de contrats

#### DexscannerService
- **Rôle** : Surveillance des nouvelles paires sur les DEX
- **Source** : API Dexscreener
- **Fréquence** : Toutes les 60 secondes

#### TelegramScraperService
- **Rôle** : Surveillance des channels Telegram crypto
- **Technologies** : Telethon
- **Channels surveillés** : @uniswapgemsnew, @dextoolstrending, etc.

### 2. Services d'analyse

#### TokenScannerService
- **Rôle** : Récupération des métadonnées des tokens ERC20
- **Fonctions** : Nom, symbole, supply, liquidité, holders
- **Validation** : Vérification de la conformité ERC20

#### GPTAnalyzerService
- **Rôle** : Analyse IA du potentiel des tokens
- **Modèle** : GPT-4 Turbo
- **Sortie** : Score 0-10, recommandation, risques, opportunités

### 3. Services de notification

#### TelegramNotifierService
- **Rôle** : Envoi d'alertes pour les tokens à potentiel
- **Seuil** : Score ≥ 7.0 et liquidité ≥ $10,000
- **Format** : Messages HTML enrichis avec liens

### 4. Orchestration

#### CryptoSentinelOrchestrator
- **Rôle** : Coordination de tous les services
- **Gestion** : Démarrage, arrêt, monitoring de santé
- **Récupération** : Gestion des erreurs et redémarrages

#### SchedulerService
- **Rôle** : Tâches périodiques et maintenance
- **Tâches** : Nettoyage DB, rapports, health checks
- **Technologie** : APScheduler

## Flux de données

### 1. Détection de nouveau token

```
Ethereum Block → WebSocket → Contract Detection → ERC20 Validation
                                    ↓
Dexscreener API → New Pair Detection → Token Extraction
                                    ↓
Telegram Channels → Message Parsing → Address Extraction
                                    ↓
                            Token Scanner Service
```

### 2. Analyse et notification

```
Token Info → GPT Analyzer → AI Analysis → Score Evaluation
                                              ↓
                                    Notification Decision
                                              ↓
                                    Telegram Alert + DB Save
```

## Patterns architecturaux

### Repository Pattern
- `DatabaseManager` : Abstraction de la couche de données
- Interface unifiée pour toutes les opérations CRUD
- Facilite les tests et le changement de base de données

### Observer Pattern
- Services émettent des événements lors de détections
- Orchestrateur coordonne les réactions
- Découplage entre détection et traitement

### Strategy Pattern
- Différentes sources de données (WebSocket, API, Scraping)
- Analyseurs modulaires (GPT, règles métier)
- Notificateurs multiples (Telegram, email, webhook)

## Gestion des erreurs

### Niveaux de récupération
1. **Service** : Retry automatique avec backoff exponentiel
2. **Orchestrateur** : Redémarrage des services défaillants
3. **Système** : Alertes critiques et mode dégradé

### Monitoring
- Health checks toutes les 5 minutes
- Métriques de performance en temps réel
- Logs structurés avec niveaux appropriés

## Sécurité

### Gestion des secrets
- Variables d'environnement pour toutes les clés API
- Rotation automatique recommandée
- Chiffrement des données sensibles en base

### Rate limiting
- Respect des limites des APIs externes
- Semaphores pour contrôler la concurrence
- Circuit breakers pour éviter les surcharges

## Performance

### Optimisations
- Cache en mémoire pour les analyses récentes
- Indexation MongoDB optimisée
- Traitement asynchrone avec asyncio
- Pool de connexions pour les APIs

### Scalabilité
- Architecture modulaire permettant la distribution
- Services stateless pour faciliter l'horizontal scaling
- Base de données NoSQL pour la flexibilité
```
**Validation** : La documentation est complète et précise

---

## ✅ CHECKLIST FINALE

### Phase 1 - Infrastructure ✅
- [ ] Configuration environnement (requirements.txt, .env.example)
- [ ] Système de logging avec Rich
- [ ] Utilitaires de validation
- [ ] Modèles Pydantic complets
- [ ] Gestionnaire de base de données MongoDB

### Phase 2 - Services de données ✅
- [ ] Service de scan des tokens ERC20
- [ ] Intégration API Dexscreener
- [ ] Service de notifications Telegram
- [ ] WebSocket listener Ethereum
- [ ] Analyseur GPT-4

### Phase 3 - Services avancés ✅
- [ ] Scraper Telegram avec Telethon
- [ ] Moniteur Twitter (optionnel)
- [ ] Système de cache et optimisations

### Phase 4 - Orchestration ✅
- [ ] Scheduler pour tâches périodiques
- [ ] Orchestrateur principal
- [ ] Gestion des erreurs et récupération
- [ ] Health checks et monitoring

### Phase 5 - Tests ✅
- [ ] Tests unitaires des modèles
- [ ] Tests d'intégration base de données
- [ ] Tests des services critiques
- [ ] Tests de bout en bout

### Phase 6 - Documentation ✅
- [ ] README.md complet
- [ ] Documentation architecture
- [ ] Guide de déploiement
- [ ] Documentation API

### Déploiement Azure ✅
- [ ] Configuration Docker
- [ ] Variables d'environnement Azure
- [ ] Monitoring et logs
- [ ] Sauvegarde base de données

---

## 🎯 PROCHAINES ÉTAPES

1. **Développement** : Suivre les tâches dans l'ordre de priorité
2. **Tests** : Exécuter les tests à chaque étape
3. **Déploiement** : Configurer l'environnement Azure
4. **Monitoring** : Surveiller les performances en production
5. **Optimisation** : Ajuster les paramètres selon les résultats

---

*Ce document est un guide complet pour développer Crypto Sentinel avec une IA. Chaque tâche est conçue pour être exécutée immédiatement sans ambiguïté.*