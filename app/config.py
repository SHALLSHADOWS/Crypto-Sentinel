#!/usr/bin/env python3
"""
Crypto Sentinel - Configuration Settings

Centralise toutes les configurations de l'application avec gestion des variables
d'environnement et validation des paramètres critiques.

Author: Crypto Sentinel Team
Version: 1.0.0
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, validator
from functools import lru_cache


class Settings(BaseSettings):
    """Configuration principale de l'application."""
    
    # === APPLICATION SETTINGS ===
    APP_NAME: str = "Crypto Sentinel"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # === DATABASE SETTINGS ===
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DATABASE: str = "crypto_sentinel"
    MONGODB_COLLECTION_TOKENS: str = "tokens"
    MONGODB_COLLECTION_ANALYTICS: str = "analytics"
    MONGODB_COLLECTION_ALERTS: str = "alerts"
    
    # === ETHEREUM SETTINGS ===
    ALCHEMY_API_KEY: str = ""
    INFURA_PROJECT_ID: str = ""
    ETHEREUM_NETWORK: str = "mainnet"  # mainnet, goerli, sepolia
    WEBSOCKET_RECONNECT_DELAY: int = 5
    MAX_RECONNECT_ATTEMPTS: int = 10
    
    # === AI SETTINGS ===
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TEMPERATURE: float = 0.3
    AI_ANALYSIS_TIMEOUT: int = 30
    
    # === TELEGRAM SETTINGS ===
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    TELEGRAM_CHANNEL_USERNAME: str = ""  # Pour scraping
    TELEGRAM_API_ID: str = ""
    TELEGRAM_API_HASH: str = ""
    
    # === DEXSCREENER SETTINGS ===
    DEXSCREENER_API_URL: str = "https://api.dexscreener.com/latest"
    DEXSCREENER_RATE_LIMIT: int = 300  # Requêtes par minute
    DEXSCREENER_TIMEOUT: int = 10
    
    # === DEXTOOLS SETTINGS ===
    DEXTOOLS_API_KEY: str = ""
    DEXTOOLS_API_URL: str = "https://api.dextools.io/v1"
    DEXTOOLS_RATE_LIMIT: int = 100
    
    # === TWITTER SETTINGS ===
    TWITTER_BEARER_TOKEN: str = ""
    TWITTER_API_KEY: str = ""
    TWITTER_API_SECRET: str = ""
    TWITTER_ACCESS_TOKEN: str = ""
    TWITTER_ACCESS_TOKEN_SECRET: str = ""
    ENABLE_TWITTER_MONITORING: bool = False
    
    # === ANALYSIS SETTINGS ===
    MIN_NOTIFICATION_SCORE: float = 7.0
    MIN_LIQUIDITY_USD: float = 10000.0
    MAX_SUPPLY: float = 1e12  # 1 trillion
    MIN_HOLDERS: int = 10
    ANALYSIS_COOLDOWN_MINUTES: int = 60
    
    # === MONITORING SETTINGS ===
    SCAN_INTERVAL_SECONDS: int = 30
    CLEANUP_INTERVAL_HOURS: int = 24
    MAX_TOKENS_PER_HOUR: int = 100
    RATE_LIMIT_WINDOW_MINUTES: int = 60
    
    # === SECURITY SETTINGS ===
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # === LOGGING SETTINGS ===
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/crypto_sentinel.log"
    LOG_MAX_SIZE: int = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # === PERFORMANCE SETTINGS ===
    MAX_CONCURRENT_ANALYSES: int = 5
    CACHE_TTL_SECONDS: int = 300
    REQUEST_TIMEOUT_SECONDS: int = 30
    
    # === NOTIFICATION SETTINGS ===
    NOTIFICATION_COOLDOWN_MINUTES: int = 30
    MAX_NOTIFICATIONS_PER_HOUR: int = 20
    ENABLE_SOUND_ALERTS: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    @validator('MONGODB_URL')
    def validate_mongodb_url(cls, v):
        if not v:
            raise ValueError('MONGODB_URL is required')
        return v
    
    @validator('OPENAI_API_KEY')
    def validate_openai_key(cls, v):
        if not v:
            raise ValueError('OPENAI_API_KEY is required')
        return v
    
    @validator('TELEGRAM_BOT_TOKEN')
    def validate_telegram_token(cls, v):
        if not v:
            raise ValueError('TELEGRAM_BOT_TOKEN is required')
        return v
    
    @validator('MIN_NOTIFICATION_SCORE')
    def validate_min_score(cls, v):
        if not 0 <= v <= 10:
            raise ValueError('MIN_NOTIFICATION_SCORE must be between 0 and 10')
        return v
    
    @validator('OPENAI_TEMPERATURE')
    def validate_temperature(cls, v):
        if not 0 <= v <= 2:
            raise ValueError('OPENAI_TEMPERATURE must be between 0 and 2')
        return v
    
    @property
    def ethereum_websocket_url(self) -> str:
        """Construit l'URL WebSocket Ethereum."""
        if self.ALCHEMY_API_KEY:
            return f"wss://eth-{self.ETHEREUM_NETWORK}.g.alchemy.com/v2/{self.ALCHEMY_API_KEY}"
        elif self.INFURA_PROJECT_ID:
            return f"wss://{self.ETHEREUM_NETWORK}.infura.io/ws/v3/{self.INFURA_PROJECT_ID}"
        else:
            raise ValueError("Either ALCHEMY_API_KEY or INFURA_PROJECT_ID is required")
    
    @property
    def ethereum_http_url(self) -> str:
        """Construit l'URL HTTP Ethereum."""
        if self.ALCHEMY_API_KEY:
            return f"https://eth-{self.ETHEREUM_NETWORK}.g.alchemy.com/v2/{self.ALCHEMY_API_KEY}"
        elif self.INFURA_PROJECT_ID:
            return f"https://{self.ETHEREUM_NETWORK}.infura.io/v3/{self.INFURA_PROJECT_ID}"
        else:
            raise ValueError("Either ALCHEMY_API_KEY or INFURA_PROJECT_ID is required")
    
    @property
    def is_production(self) -> bool:
        """Vérifie si l'application est en mode production."""
        return not self.DEBUG and os.getenv('ENVIRONMENT', '').lower() == 'production'
    
    def get_ai_prompt_template(self) -> str:
        """Template de prompt pour l'analyse IA."""
        return """
Analyse ce token ERC20 et donne-lui un score de 0 à 10 pour son potentiel spéculatif.

Informations du token:
- Nom: {name}
- Symbole: {symbol}
- Adresse: {contract_address}
- Supply totale: {total_supply}
- Liquidité: {liquidity_usd} USD
- Nombre de holders: {holder_count}
- Âge: {age_hours} heures
- Volume 24h: {volume_24h} USD
- Prix: {price_usd} USD
- Variation 24h: {price_change_24h}%

Critères d'évaluation:
1. Potentiel de viralité (nom, symbole, concept)
2. Liquidité et volume
3. Distribution des tokens
4. Timing de lancement
5. Activité sur les réseaux sociaux
6. Risques potentiels

Réponds au format JSON:
{
  "score": 8.5,
  "reasoning": "Explication détaillée",
  "risks": ["Risque 1", "Risque 2"],
  "opportunities": ["Opportunité 1", "Opportunité 2"],
  "recommendation": "BUY/HOLD/AVOID",
  "confidence": 0.85
}
"""


@lru_cache()
def get_settings() -> Settings:
    """Récupère les paramètres de configuration (avec cache)."""
    return Settings()


# Instance globale des paramètres
settings = get_settings()


# === CONSTANTES ===
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    }
]

UNISWAP_V2_FACTORY_ADDRESS = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
UNISWAP_V3_FACTORY_ADDRESS = "0x1F98431c8aD98523631AE4a59f267346ea31F984"

# Adresses de tokens stables pour calculs de liquidité
STABLE_TOKENS = {
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "USDC": "0xA0b86a33E6441b8435b662303c0f218C8c7c6b07",
    "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
}

# Patterns suspects pour détection de scams
SUSPICIOUS_PATTERNS = [
    r"(?i)(elon|musk|tesla|spacex)",
    r"(?i)(moon|rocket|pump|gem)",
    r"(?i)(safe|baby|mini|doge)",
    r"(?i)(inu|shib|floki)",
    r"(?i)(100x|1000x|moon)"
]

# Sources de données prioritaires
DATA_SOURCES = {
    "ethereum_websocket": {"priority": 1, "enabled": True},
    "dexscreener": {"priority": 2, "enabled": True},
    "dextools": {"priority": 3, "enabled": True},
    "telegram": {"priority": 4, "enabled": True},
    "twitter": {"priority": 5, "enabled": False}
}