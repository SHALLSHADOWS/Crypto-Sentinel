#!/usr/bin/env python3
"""
Crypto Sentinel - Helper Utilities

Fonctions d'aide générales pour le projet Crypto Sentinel.
"""

import asyncio
import hashlib
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from decimal import Decimal
import re

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def format_number(value: Union[int, float, Decimal], decimals: int = 2) -> str:
    """Formate un nombre avec des séparateurs de milliers."""
    if value is None:
        return "N/A"
    
    try:
        if isinstance(value, (int, float)):
            if value >= 1_000_000_000:
                return f"{value / 1_000_000_000:.{decimals}f}B"
            elif value >= 1_000_000:
                return f"{value / 1_000_000:.{decimals}f}M"
            elif value >= 1_000:
                return f"{value / 1_000:.{decimals}f}K"
            else:
                return f"{value:.{decimals}f}"
        return str(value)
    except (ValueError, TypeError):
        return "N/A"


def format_percentage(value: Union[int, float], decimals: int = 2) -> str:
    """Formate un pourcentage avec le symbole %."""
    if value is None:
        return "N/A"
    
    try:
        formatted = f"{float(value):.{decimals}f}%"
        if value > 0:
            return f"+{formatted}"
        return formatted
    except (ValueError, TypeError):
        return "N/A"


def format_usd(value: Union[int, float, Decimal], decimals: int = 2) -> str:
    """Formate une valeur en USD."""
    if value is None:
        return "$N/A"
    
    try:
        formatted_number = format_number(value, decimals)
        return f"${formatted_number}"
    except (ValueError, TypeError):
        return "$N/A"


def calculate_age_hours(timestamp: Union[int, float, datetime]) -> float:
    """Calcule l'âge en heures depuis un timestamp."""
    try:
        if isinstance(timestamp, datetime):
            target_time = timestamp
        else:
            target_time = datetime.fromtimestamp(float(timestamp))
        
        age_delta = datetime.utcnow() - target_time
        return age_delta.total_seconds() / 3600
    except (ValueError, TypeError, OSError):
        return 0.0


def format_age(hours: float) -> str:
    """Formate un âge en heures en format lisible."""
    if hours < 1:
        minutes = int(hours * 60)
        return f"{minutes}m"
    elif hours < 24:
        return f"{hours:.1f}h"
    else:
        days = int(hours / 24)
        remaining_hours = int(hours % 24)
        if remaining_hours > 0:
            return f"{days}d {remaining_hours}h"
        return f"{days}d"


def truncate_address(address: str, start_chars: int = 6, end_chars: int = 4) -> str:
    """Tronque une adresse Ethereum pour l'affichage."""
    if not address or len(address) < start_chars + end_chars:
        return address
    
    return f"{address[:start_chars]}...{address[-end_chars:]}"


def generate_cache_key(*args: Any) -> str:
    """Génère une clé de cache à partir d'arguments."""
    key_string = "|".join(str(arg) for arg in args)
    return hashlib.md5(key_string.encode()).hexdigest()


def safe_divide(numerator: Union[int, float], denominator: Union[int, float], default: float = 0.0) -> float:
    """Division sécurisée qui évite la division par zéro."""
    try:
        if denominator == 0:
            return default
        return float(numerator) / float(denominator)
    except (ValueError, TypeError, ZeroDivisionError):
        return default


def extract_contract_addresses(text: str) -> List[str]:
    """Extrait les adresses de contrat Ethereum d'un texte."""
    if not text:
        return []
    
    # Pattern pour les adresses Ethereum
    pattern = r'0x[a-fA-F0-9]{40}'
    addresses = re.findall(pattern, text)
    
    # Filtrer les doublons et valider
    unique_addresses = []
    for addr in addresses:
        if addr not in unique_addresses:
            unique_addresses.append(addr)
    
    return unique_addresses


def is_stablecoin(symbol: str) -> bool:
    """Vérifie si un token est un stablecoin connu."""
    if not symbol:
        return False
    
    stablecoins = {
        'USDT', 'USDC', 'DAI', 'BUSD', 'TUSD', 'USDP', 'GUSD', 'SUSD',
        'FRAX', 'LUSD', 'MIM', 'USTC', 'USDD', 'USDN', 'HUSD'
    }
    
    return symbol.upper() in stablecoins


def is_wrapped_token(symbol: str) -> bool:
    """Vérifie si un token est un token wrappé connu."""
    if not symbol:
        return False
    
    wrapped_tokens = {
        'WETH', 'WBTC', 'WBNB', 'WMATIC', 'WAVAX', 'WFTM', 'WONE'
    }
    
    return symbol.upper() in wrapped_tokens


def calculate_market_cap(price: float, total_supply: float) -> float:
    """Calcule la capitalisation de marché."""
    try:
        return float(price) * float(total_supply)
    except (ValueError, TypeError):
        return 0.0


def calculate_liquidity_ratio(liquidity: float, market_cap: float) -> float:
    """Calcule le ratio liquidité/market cap."""
    return safe_divide(liquidity, market_cap, 0.0)


def is_recent_token(creation_timestamp: Union[int, float, datetime], max_age_hours: float = 24.0) -> bool:
    """Vérifie si un token est récent (créé dans les X heures)."""
    age_hours = calculate_age_hours(creation_timestamp)
    return age_hours <= max_age_hours


def sanitize_string(text: str, max_length: int = 100) -> str:
    """Nettoie et limite la longueur d'une chaîne."""
    if not text:
        return ""
    
    # Supprimer les caractères de contrôle et limiter la longueur
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', str(text)).strip()
    
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + "..."
    
    return cleaned


def batch_list(items: List[Any], batch_size: int) -> List[List[Any]]:
    """Divise une liste en lots de taille donnée."""
    if not items or batch_size <= 0:
        return []
    
    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i:i + batch_size])
    
    return batches


async def retry_async(func, max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Retry une fonction async avec backoff exponentiel."""
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = delay * (backoff ** attempt)
                logger.warning(f"Tentative {attempt + 1} échouée, retry dans {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"Toutes les tentatives échouées: {e}")
    
    raise last_exception


def get_emoji_for_score(score: float) -> str:
    """Retourne un emoji basé sur le score d'analyse."""
    if score >= 9.0:
        return "🚀"  # Excellent
    elif score >= 8.0:
        return "🔥"  # Très bon
    elif score >= 7.0:
        return "⭐"  # Bon
    elif score >= 6.0:
        return "👍"  # Correct
    elif score >= 5.0:
        return "⚠️"   # Moyen
    else:
        return "❌"  # Mauvais


def get_emoji_for_change(change_percent: float) -> str:
    """Retourne un emoji basé sur le changement de prix."""
    if change_percent > 20:
        return "🚀"
    elif change_percent > 10:
        return "📈"
    elif change_percent > 0:
        return "🟢"
    elif change_percent > -10:
        return "🔴"
    else:
        return "💥"


def create_progress_bar(current: int, total: int, width: int = 20) -> str:
    """Crée une barre de progression textuelle."""
    if total <= 0:
        return "[" + "?" * width + "]"
    
    progress = min(current / total, 1.0)
    filled = int(progress * width)
    bar = "█" * filled + "░" * (width - filled)
    percentage = int(progress * 100)
    
    return f"[{bar}] {percentage}%"