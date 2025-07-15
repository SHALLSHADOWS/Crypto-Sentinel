#!/usr/bin/env python3
"""
Crypto Sentinel - Dexscreener Service

Service d'intégration avec l'API Dexscreener pour détecter les nouvelles paires
et récupérer les données de marché en temps réel.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

import httpx
from app.config import settings
from app.models import TokenInfo, TokenSource
from app.utils.logger import setup_logger
from app.utils.helpers import format_usd, format_percentage, calculate_age_hours

logger = setup_logger(__name__)


class DexscannerService:
    """Service d'intégration avec Dexscreener API."""
    
    def __init__(self):
        self.base_url = "https://api.dexscreener.com/latest"
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_connections=10)
        )
        self.rate_limiter = asyncio.Semaphore(5)  # 5 requêtes simultanées max
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 seconde entre les requêtes
        self.processed_pairs = set()  # Cache des paires déjà traitées
        
    async def start_monitoring(self):
        """Démarre la surveillance des nouvelles paires."""
        logger.info("🔄 Démarrage du monitoring Dexscreener...")
        
        while True:
            try:
                await self._scan_new_pairs()
                await asyncio.sleep(60)  # Scan toutes les minutes
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
                    pair_address = pair.get('pairAddress')
                    if pair_address and pair_address not in self.processed_pairs:
                        created_at = pair.get('pairCreatedAt')
                        if created_at:
                            pair_time = datetime.fromtimestamp(created_at / 1000)
                            if pair_time > cutoff_time:
                                recent_pairs.append(pair)
                                self.processed_pairs.add(pair_address)
                
                return recent_pairs
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Erreur HTTP Dexscreener: {e.response.status_code}")
                return []
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des paires: {e}")
                return []
    
    async def get_token_data(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """Récupère les données d'un token spécifique."""
        async with self.rate_limiter:
            await self._respect_rate_limit()
            
            try:
                url = f"{self.base_url}/dex/tokens/{contract_address}"
                response = await self.http_client.get(url)
                response.raise_for_status()
                
                data = response.json()
                return data
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.warning(f"Token non trouvé sur Dexscreener: {contract_address}")
                else:
                    logger.error(f"Erreur HTTP Dexscreener: {e.response.status_code}")
                return None
            except Exception as e:
                logger.error(f"Erreur lors de la récupération du token: {e}")
                return None
    
    async def get_pair_data(self, pair_address: str) -> Optional[Dict[str, Any]]:
        """Récupère les données d'une paire spécifique."""
        async with self.rate_limiter:
            await self._respect_rate_limit()
            
            try:
                url = f"{self.base_url}/dex/pairs/ethereum/{pair_address}"
                response = await self.http_client.get(url)
                response.raise_for_status()
                
                data = response.json()
                return data.get('pair')
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.warning(f"Paire non trouvée sur Dexscreener: {pair_address}")
                else:
                    logger.error(f"Erreur HTTP Dexscreener: {e.response.status_code}")
                return None
            except Exception as e:
                logger.error(f"Erreur lors de la récupération de la paire: {e}")
                return None
    
    async def _process_new_pair(self, pair_data: Dict[str, Any]):
        """Traite une nouvelle paire détectée."""
        try:
            base_token = pair_data.get('baseToken', {})
            quote_token = pair_data.get('quoteToken', {})
            
            # Identifier le token principal (non-stablecoin/WETH)
            token_address = None
            token_data = None
            
            stable_symbols = {'WETH', 'USDT', 'USDC', 'DAI', 'BUSD'}
            
            if base_token.get('symbol') not in stable_symbols:
                token_address = base_token.get('address')
                token_data = base_token
            elif quote_token.get('symbol') not in stable_symbols:
                token_address = quote_token.get('address')
                token_data = quote_token
            
            if token_address and token_data:
                # Créer les informations du token
                token_info = self._create_token_info_from_pair(pair_data, token_address, token_data)
                
                if token_info and self._is_interesting_token(token_info, pair_data):
                    # Déclencher l'analyse
                    await self._trigger_token_analysis(token_info)
                    
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la paire: {e}")
    
    def _create_token_info_from_pair(self, pair_data: Dict[str, Any], token_address: str, token_data: Dict[str, Any]) -> Optional[TokenInfo]:
        """Crée un TokenInfo à partir des données de paire."""
        try:
            # Extraire les informations
            price_usd = float(pair_data.get('priceUsd', 0))
            liquidity_usd = float(pair_data.get('liquidity', {}).get('usd', 0))
            volume_24h = float(pair_data.get('volume', {}).get('h24', 0))
            price_change_24h = float(pair_data.get('priceChange', {}).get('h24', 0))
            
            # Calculer l'âge du token
            created_at = pair_data.get('pairCreatedAt')
            age_hours = 0
            if created_at:
                age_hours = calculate_age_hours(created_at / 1000)
            
            token_info = TokenInfo(
                contract_address=token_address,
                name=token_data.get('name'),
                symbol=token_data.get('symbol'),
                price_usd=price_usd,
                liquidity_usd=liquidity_usd,
                volume_24h_usd=volume_24h,
                price_change_24h=price_change_24h,
                age_hours=age_hours,
                source=TokenSource.DEXSCREENER,
                dex_pair_address=pair_data.get('pairAddress'),
                dex_name=pair_data.get('dexId', 'unknown')
            )
            
            return token_info
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du TokenInfo: {e}")
            return None
    
    def _is_interesting_token(self, token_info: TokenInfo, pair_data: Dict[str, Any]) -> bool:
        """Détermine si un token est intéressant pour l'analyse."""
        try:
            # Critères de filtrage
            min_liquidity = 10000  # $10K minimum
            max_age_hours = 24  # Maximum 24h
            min_volume = 1000  # $1K minimum de volume
            
            # Vérifier la liquidité
            if token_info.liquidity_usd < min_liquidity:
                logger.debug(f"Token {token_info.contract_address} ignoré: liquidité trop faible ({format_usd(token_info.liquidity_usd)})")
                return False
            
            # Vérifier l'âge
            if token_info.age_hours > max_age_hours:
                logger.debug(f"Token {token_info.contract_address} ignoré: trop ancien ({token_info.age_hours:.1f}h)")
                return False
            
            # Vérifier le volume
            if token_info.volume_24h_usd < min_volume:
                logger.debug(f"Token {token_info.contract_address} ignoré: volume trop faible ({format_usd(token_info.volume_24h_usd)})")
                return False
            
            # Vérifier que ce n'est pas un token suspect
            if self._is_suspicious_token(token_info):
                logger.debug(f"Token {token_info.contract_address} ignoré: suspect")
                return False
            
            logger.info(f"✅ Token intéressant détecté: {token_info.symbol} - Liquidité: {format_usd(token_info.liquidity_usd)}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du token: {e}")
            return False
    
    def _is_suspicious_token(self, token_info: TokenInfo) -> bool:
        """Détecte les tokens suspects."""
        if not token_info.name or not token_info.symbol:
            return True
        
        # Patterns suspects dans le nom/symbole
        suspicious_patterns = [
            r'(?i)(elon|musk|tesla|spacex)',
            r'(?i)(moon|rocket|pump|gem)',
            r'(?i)(safe|baby|mini)',
            r'(?i)(100x|1000x|lambo)',
            r'(?i)(inu|shib|floki|doge)',
            r'(?i)(test|fake|scam)'
        ]
        
        text_to_check = f"{token_info.name} {token_info.symbol}".lower()
        
        for pattern in suspicious_patterns:
            if re.search(pattern, text_to_check):
                return True
        
        return False
    
    async def _trigger_token_analysis(self, token_info: TokenInfo):
        """Déclenche l'analyse d'un token détecté."""
        logger.info(f"🎯 Nouveau token détecté via Dexscreener: {token_info.contract_address}")
        logger.info(f"   Nom: {token_info.name} ({token_info.symbol})")
        logger.info(f"   Prix: {format_usd(token_info.price_usd)}")
        logger.info(f"   Liquidité: {format_usd(token_info.liquidity_usd)}")
        logger.info(f"   Volume 24h: {format_usd(token_info.volume_24h_usd)}")
        logger.info(f"   Change 24h: {format_percentage(token_info.price_change_24h)}")
        logger.info(f"   Âge: {token_info.age_hours:.1f}h")
        
        # TODO: Intégrer avec le système d'analyse principal
        # Cette méthode sera connectée au TokenAnalysisOrchestrator
    
    async def _respect_rate_limit(self):
        """Respecte les limites de taux de l'API."""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = asyncio.get_event_loop().time()
    
    async def close(self):
        """Ferme les connexions HTTP."""
        await self.http_client.aclose()
        logger.info("🔌 Connexions Dexscreener fermées")


# Import nécessaire pour les patterns regex
import re