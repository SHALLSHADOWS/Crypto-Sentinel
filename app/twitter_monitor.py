#!/usr/bin/env python3
"""
Crypto Sentinel - Twitter Monitor Service

Service de surveillance Twitter pour détecter les mentions de nouveaux tokens ERC20
et extraire les adresses de contrats depuis les tweets.

Author: Crypto Sentinel Team
Version: 1.0.0
"""

import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Set
import json

try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    TWEEPY_AVAILABLE = False

from app.config import settings
from app.models import TokenInfo, TokenSource
from app.utils.logger import setup_logger
from app.utils.validators import is_valid_ethereum_address
from app.utils.helpers import sanitize_text

logger = setup_logger(__name__)


class TwitterMonitorService:
    """Service de surveillance Twitter pour les nouveaux tokens."""
    
    def __init__(self):
        self.client: Optional[tweepy.Client] = None
        self.stream: Optional[tweepy.StreamingClient] = None
        self.is_running = False
        self.processed_tweets: Set[str] = set()
        
        # Statistiques
        self.tweets_processed = 0
        self.contracts_found = 0
        self.tokens_triggered = 0
        self.start_time = None
        
        # Patterns de détection
        self.contract_patterns = [
            r'0x[a-fA-F0-9]{40}',  # Adresse Ethereum standard
            r'Contract[:\s]*0x[a-fA-F0-9]{40}',  # "Contract: 0x..."
            r'CA[:\s]*0x[a-fA-F0-9]{40}',  # "CA: 0x..."
            r'Token[:\s]*0x[a-fA-F0-9]{40}',  # "Token: 0x..."
        ]
        
        # Mots-clés de surveillance
        self.search_keywords = [
            'new token launch',
            'fresh token',
            'stealth launch',
            'fair launch',
            'token presale',
            'new gem',
            'moonshot token',
            'early token',
            'degen play',
            'new ERC20',
            'contract address',
            'CA:',
            '0x' # Pour capturer les adresses directement
        ]
        
        # Comptes influents à surveiller
        self.monitored_accounts = [
            '@cryptogemhunters',
            '@degengemhunters',
            '@earlygemhunters',
            '@moonshotalerts',
            '@cryptosignals',
            '@dexgemhunters',
            '@cryptowhales',
            '@altcoindaily'
        ]
        
        if not TWEEPY_AVAILABLE:
            logger.warning("🐦 Tweepy non installé - Monitoring Twitter désactivé")
            return
        
        # Initialisation du client Twitter
        if self._has_twitter_credentials():
            try:
                self.client = tweepy.Client(
                    bearer_token=settings.TWITTER_BEARER_TOKEN,
                    consumer_key=settings.TWITTER_API_KEY,
                    consumer_secret=settings.TWITTER_API_SECRET,
                    access_token=settings.TWITTER_ACCESS_TOKEN,
                    access_token_secret=settings.TWITTER_ACCESS_TOKEN_SECRET,
                    wait_on_rate_limit=True
                )
                
                self.stream = tweepy.StreamingClient(
                    bearer_token=settings.TWITTER_BEARER_TOKEN,
                    wait_on_rate_limit=True
                )
                
                # Configuration des callbacks du stream
                self.stream.on_tweet = self._on_tweet
                self.stream.on_error = self._on_error
                
            except Exception as e:
                logger.error(f"❌ Erreur lors de l'initialisation du client Twitter: {e}")
        else:
            logger.warning("⚠️ Credentials Twitter non configurés - Monitoring désactivé")
    
    def _has_twitter_credentials(self) -> bool:
        """Vérifie si les credentials Twitter sont configurés."""
        return all([
            settings.TWITTER_BEARER_TOKEN,
            settings.TWITTER_API_KEY,
            settings.TWITTER_API_SECRET,
            settings.TWITTER_ACCESS_TOKEN,
            settings.TWITTER_ACCESS_TOKEN_SECRET
        ])
    
    async def start_monitoring(self):
        """Démarre la surveillance Twitter."""
        if not TWEEPY_AVAILABLE or not self.client or not settings.ENABLE_TWITTER_MONITORING:
            logger.warning("⚠️ Monitoring Twitter non disponible ou désactivé")
            return
        
        if self.is_running:
            logger.warning("⚠️ Monitoring Twitter déjà en cours")
            return
        
        try:
            logger.info("🐦 Démarrage du monitoring Twitter...")
            
            self.is_running = True
            self.start_time = datetime.utcnow()
            
            # Configuration des règles de filtrage
            await self._setup_stream_rules()
            
            # Démarrage du stream en arrière-plan
            asyncio.create_task(self._run_stream())
            
            # Démarrage de la recherche périodique
            asyncio.create_task(self._run_periodic_search())
            
            logger.info("✅ Monitoring Twitter démarré")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du démarrage du monitoring Twitter: {e}")
            self.is_running = False
    
    async def stop_monitoring(self):
        """Arrête la surveillance Twitter."""
        self.is_running = False
        if self.stream:
            self.stream.disconnect()
        logger.info("🛑 Monitoring Twitter arrêté")
    
    async def _setup_stream_rules(self):
        """Configure les règles de filtrage du stream Twitter."""
        try:
            # Supprimer les anciennes règles
            existing_rules = self.stream.get_rules()
            if existing_rules.data:
                rule_ids = [rule.id for rule in existing_rules.data]
                self.stream.delete_rules(rule_ids)
            
            # Créer de nouvelles règles
            rules = []
            
            # Règles pour les mots-clés
            for keyword in self.search_keywords[:5]:  # Limiter à 5 pour éviter les limites
                rules.append(tweepy.StreamRule(f'"{keyword}" lang:en'))
            
            # Règles pour les comptes surveillés
            for account in self.monitored_accounts[:3]:  # Limiter à 3
                rules.append(tweepy.StreamRule(f'from:{account.replace("@", "")}'))
            
            # Ajouter les règles
            if rules:
                self.stream.add_rules(rules)
                logger.info(f"🐦 {len(rules)} règles de filtrage configurées")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la configuration des règles: {e}")
    
    async def _run_stream(self):
        """Exécute le stream Twitter en arrière-plan."""
        try:
            while self.is_running:
                try:
                    # Démarrer le stream
                    self.stream.filter(
                        tweet_fields=['created_at', 'author_id', 'public_metrics', 'context_annotations'],
                        user_fields=['username', 'verified', 'public_metrics'],
                        expansions=['author_id']
                    )
                except Exception as e:
                    logger.error(f"❌ Erreur dans le stream Twitter: {e}")
                    if self.is_running:
                        await asyncio.sleep(60)  # Attendre avant de reconnecter
        
        except Exception as e:
            logger.error(f"❌ Erreur fatale dans le stream Twitter: {e}")
    
    async def _run_periodic_search(self):
        """Exécute des recherches périodiques pour compléter le stream."""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Toutes les 5 minutes
                
                if self.is_running:
                    await self._perform_search()
                    
            except Exception as e:
                logger.error(f"❌ Erreur dans la recherche périodique: {e}")
                await asyncio.sleep(60)
    
    async def _perform_search(self):
        """Effectue une recherche Twitter pour les nouveaux tokens."""
        try:
            # Rechercher les tweets récents
            query = ' OR '.join([f'"{keyword}"' for keyword in self.search_keywords[:3]])
            query += ' -is:retweet lang:en'
            
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=10,
                tweet_fields=['created_at', 'author_id', 'public_metrics'],
                user_fields=['username', 'verified'],
                expansions=['author_id']
            )
            
            if tweets.data:
                for tweet in tweets.data:
                    await self._process_tweet(tweet, tweets.includes.get('users', []))
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche Twitter: {e}")
    
    def _on_tweet(self, tweet):
        """Callback pour les nouveaux tweets du stream."""
        try:
            asyncio.create_task(self._process_tweet(tweet))
        except Exception as e:
            logger.error(f"❌ Erreur dans le callback tweet: {e}")
    
    def _on_error(self, status_code):
        """Callback pour les erreurs du stream."""
        logger.error(f"❌ Erreur Twitter Stream: {status_code}")
        return True  # Continuer le stream
    
    async def _process_tweet(self, tweet, users=None):
        """Traite un tweet pour extraire les adresses de contrats."""
        try:
            # Éviter de traiter le même tweet plusieurs fois
            if tweet.id in self.processed_tweets:
                return
            
            self.processed_tweets.add(tweet.id)
            self.tweets_processed += 1
            
            # Extraire le texte du tweet
            tweet_text = tweet.text or ""
            if not tweet_text:
                return
            
            # Nettoyer le texte
            clean_text = sanitize_text(tweet_text)
            
            # Vérifier si le tweet contient des mots-clés d'intérêt
            if not self._contains_crypto_keywords(clean_text.lower()):
                return
            
            logger.debug(f"🐦 Tweet d'intérêt détecté: {clean_text[:100]}...")
            
            # Extraire les adresses de contrats
            contract_addresses = self._extract_contract_addresses(clean_text)
            
            if contract_addresses:
                logger.info(f"🐦 {len(contract_addresses)} contrat(s) trouvé(s) dans le tweet")
                self.contracts_found += len(contract_addresses)
                
                # Traiter chaque adresse trouvée
                for address in contract_addresses:
                    await self._process_contract_address(address, tweet, clean_text, users)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement du tweet: {e}")
    
    def _contains_crypto_keywords(self, text: str) -> bool:
        """Vérifie si le texte contient des mots-clés crypto."""
        crypto_keywords = [
            'token', 'contract', 'launch', 'gem', 'moonshot', 'degen',
            'presale', 'fair launch', 'stealth', 'early', 'new', 'fresh'
        ]
        return any(keyword in text for keyword in crypto_keywords)
    
    def _extract_contract_addresses(self, text: str) -> List[str]:
        """Extrait les adresses de contrats du texte."""
        addresses = set()
        
        for pattern in self.contract_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Extraire seulement l'adresse si le pattern contient du texte supplémentaire
                address_match = re.search(r'0x[a-fA-F0-9]{40}', match)
                if address_match:
                    address = address_match.group(0).lower()
                    if is_valid_ethereum_address(address):
                        addresses.add(address)
        
        return list(addresses)
    
    async def _process_contract_address(self, address: str, tweet, tweet_text: str, users=None):
        """Traite une adresse de contrat trouvée."""
        try:
            # Créer les informations de base du token
            token_info = TokenInfo(
                contract_address=address,
                source=TokenSource.TWITTER,
                detected_at=datetime.utcnow()
            )
            
            # Ajouter des métadonnées du tweet
            author_info = {}
            if users:
                author = next((u for u in users if u.id == tweet.author_id), None)
                if author:
                    author_info = {
                        'username': author.username,
                        'verified': getattr(author, 'verified', False),
                        'followers': getattr(author.public_metrics, 'followers_count', 0) if hasattr(author, 'public_metrics') else 0
                    }
            
            metadata = {
                'tweet_id': tweet.id,
                'tweet_text': tweet_text[:500],  # Limiter la taille
                'created_at': tweet.created_at,
                'author_id': tweet.author_id,
                'author_info': author_info,
                'retweet_count': getattr(tweet.public_metrics, 'retweet_count', 0) if hasattr(tweet, 'public_metrics') else 0,
                'like_count': getattr(tweet.public_metrics, 'like_count', 0) if hasattr(tweet, 'public_metrics') else 0
            }
            
            logger.info(f"🐦 Token détecté via Twitter: {address}")
            
            # Déclencher l'analyse du token
            await self._trigger_token_analysis(token_info, metadata)
            
            self.tokens_triggered += 1
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement de l'adresse {address}: {e}")
    
    async def _trigger_token_analysis(self, token_info: TokenInfo, metadata: Dict[str, Any]):
        """Déclenche l'analyse d'un token détecté."""
        try:
            # Ici, on devrait déclencher l'analyse via le système principal
            # Pour l'instant, on log l'information
            logger.info(f"🔍 Analyse déclenchée pour {token_info.contract_address}")
            
            # TODO: Intégrer avec le système principal d'analyse
            # await token_scanner.scan_token(token_info)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du déclenchement d'analyse: {e}")
    
    async def health_check(self) -> bool:
        """Vérifie l'état de santé du service."""
        try:
            if not TWEEPY_AVAILABLE or not self.client:
                return False
            
            # Tester une requête simple
            me = self.client.get_me()
            return me is not None and self.is_running
            
        except Exception:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du service."""
        uptime = 0
        if self.start_time:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            'is_running': self.is_running,
            'uptime_seconds': uptime,
            'tweets_processed': self.tweets_processed,
            'contracts_found': self.contracts_found,
            'tokens_triggered': self.tokens_triggered,
            'processed_tweets_count': len(self.processed_tweets),
            'tweepy_available': TWEEPY_AVAILABLE,
            'monitoring_enabled': settings.ENABLE_TWITTER_MONITORING
        }
    
    def clear_processed_tweets(self):
        """Vide le cache des tweets traités."""
        self.processed_tweets.clear()
        logger.info("🐦 Cache des tweets traités vidé")
    
    async def search_user_tweets(self, username: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Recherche les tweets récents d'un utilisateur spécifique."""
        try:
            if not self.client:
                return []
            
            user = self.client.get_user(username=username.replace('@', ''))
            if not user.data:
                return []
            
            tweets = self.client.get_users_tweets(
                id=user.data.id,
                max_results=max_results,
                tweet_fields=['created_at', 'public_metrics']
            )
            
            results = []
            if tweets.data:
                for tweet in tweets.data:
                    results.append({
                        'id': tweet.id,
                        'text': tweet.text,
                        'created_at': tweet.created_at,
                        'metrics': tweet.public_metrics if hasattr(tweet, 'public_metrics') else {}
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche des tweets de {username}: {e}")
            return []