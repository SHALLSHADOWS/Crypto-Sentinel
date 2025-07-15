#!/usr/bin/env python3
"""
Crypto Sentinel - Telegram Scraper Service

Service de surveillance des channels Telegram pour détecter les mentions de nouveaux
tokens ERC20 et extraire les adresses de contrats depuis les messages.

Author: Crypto Sentinel Team
Version: 1.0.0
"""

import asyncio
import re
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Set

try:
    from telethon import TelegramClient, events
    from telethon.errors import SessionPasswordNeededError, FloodWaitError
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    logger.warning("📱 Telethon non installé - Scraping Telegram désactivé")

from app.config import settings
from app.models import TokenInfo, TokenSource
from app.utils.logger import setup_logger
from app.utils.validators import is_valid_ethereum_address
from app.utils.helpers import sanitize_text

logger = setup_logger(__name__)


class TelegramScraperService:
    """Service de scraping des channels Telegram."""
    
    def __init__(self):
        self.client: Optional[TelegramClient] = None
        self.is_running = False
        self.monitored_channels = []
        self.processed_messages: Set[int] = set()
        
        # Statistiques
        self.messages_processed = 0
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
        
        # Mots-clés d'intérêt
        self.interest_keywords = [
            'new token', 'nouveau token', 'fresh launch', 'just launched',
            'stealth launch', 'fair launch', 'presale', 'gem', 'moonshot',
            'x100', 'x1000', 'potential', 'early', 'degen', 'ape'
        ]
        
        # Channels à surveiller (configurables)
        self.default_channels = [
            '@cryptogemhunters',
            '@degengemhunters', 
            '@earlygemhunters',
            '@moonshotalerts',
            '@cryptosignals',
            '@dexgemhunters'
        ]
        
        if not TELETHON_AVAILABLE:
            logger.error("❌ Telethon requis pour le scraping Telegram")
            return
        
        # Initialisation du client Telegram
        if settings.TELEGRAM_API_ID and settings.TELEGRAM_API_HASH:
            self.client = TelegramClient(
                'crypto_sentinel_session',
                settings.TELEGRAM_API_ID,
                settings.TELEGRAM_API_HASH
            )
        else:
            logger.warning("⚠️ API Telegram non configurée - Scraping désactivé")
    
    async def start_monitoring(self):
        """Démarre la surveillance des channels Telegram."""
        if not TELETHON_AVAILABLE or not self.client:
            logger.warning("⚠️ Scraping Telegram non disponible")
            return
        
        if self.is_running:
            logger.warning("⚠️ Scraping Telegram déjà en cours")
            return
        
        try:
            logger.info("📱 Démarrage du scraping Telegram...")
            
            # Connexion au client
            await self.client.start()
            
            if not await self.client.is_user_authorized():
                logger.error("❌ Utilisateur Telegram non autorisé")
                return
            
            self.is_running = True
            self.start_time = datetime.utcnow()
            
            # Configuration des handlers d'événements
            self._setup_event_handlers()
            
            # Récupération des channels à surveiller
            await self._setup_monitored_channels()
            
            logger.info(f"✅ Scraping Telegram démarré - {len(self.monitored_channels)} channels surveillés")
            
            # Maintenir la connexion
            await self.client.run_until_disconnected()
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du démarrage du scraping Telegram: {e}")
            self.is_running = False
    
    async def stop_monitoring(self):
        """Arrête la surveillance Telegram."""
        self.is_running = False
        if self.client:
            await self.client.disconnect()
        logger.info("🛑 Scraping Telegram arrêté")
    
    def _setup_event_handlers(self):
        """Configure les handlers d'événements Telegram."""
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            try:
                await self._process_message(event)
            except Exception as e:
                logger.error(f"Erreur lors du traitement du message: {e}")
        
        logger.info("📱 Handlers d'événements configurés")
    
    async def _setup_monitored_channels(self):
        """Configure la liste des channels à surveiller."""
        try:
            self.monitored_channels = []
            
            # Ajouter les channels par défaut
            for channel_username in self.default_channels:
                try:
                    entity = await self.client.get_entity(channel_username)
                    self.monitored_channels.append(entity)
                    logger.info(f"📱 Channel ajouté: {channel_username}")
                except Exception as e:
                    logger.warning(f"⚠️ Impossible d'ajouter {channel_username}: {e}")
            
            # Ajouter le channel configuré
            if settings.TELEGRAM_CHANNEL_USERNAME:
                try:
                    entity = await self.client.get_entity(settings.TELEGRAM_CHANNEL_USERNAME)
                    if entity not in self.monitored_channels:
                        self.monitored_channels.append(entity)
                        logger.info(f"📱 Channel configuré ajouté: {settings.TELEGRAM_CHANNEL_USERNAME}")
                except Exception as e:
                    logger.warning(f"⚠️ Channel configuré inaccessible: {e}")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la configuration des channels: {e}")
    
    async def _process_message(self, event):
        """Traite un nouveau message Telegram."""
        try:
            # Vérifier si le message vient d'un channel surveillé
            if not self._is_monitored_channel(event.chat_id):
                return
            
            # Éviter de traiter le même message plusieurs fois
            if event.message.id in self.processed_messages:
                return
            
            self.processed_messages.add(event.message.id)
            self.messages_processed += 1
            
            # Extraire le texte du message
            message_text = event.message.text or ""
            if not message_text:
                return
            
            # Nettoyer le texte
            clean_text = sanitize_text(message_text)
            
            # Vérifier si le message contient des mots-clés d'intérêt
            if not self._contains_interest_keywords(clean_text.lower()):
                return
            
            logger.debug(f"📱 Message d'intérêt détecté: {clean_text[:100]}...")
            
            # Extraire les adresses de contrats
            contract_addresses = self._extract_contract_addresses(clean_text)
            
            if contract_addresses:
                logger.info(f"📱 {len(contract_addresses)} contrat(s) trouvé(s) dans le message")
                self.contracts_found += len(contract_addresses)
                
                # Traiter chaque adresse trouvée
                for address in contract_addresses:
                    await self._process_contract_address(address, event, clean_text)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du traitement du message: {e}")
    
    def _is_monitored_channel(self, chat_id: int) -> bool:
        """Vérifie si le chat est un channel surveillé."""
        return any(channel.id == chat_id for channel in self.monitored_channels)
    
    def _contains_interest_keywords(self, text: str) -> bool:
        """Vérifie si le texte contient des mots-clés d'intérêt."""
        return any(keyword in text for keyword in self.interest_keywords)
    
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
    
    async def _process_contract_address(self, address: str, event, message_text: str):
        """Traite une adresse de contrat trouvée."""
        try:
            # Créer les informations de base du token
            token_info = TokenInfo(
                contract_address=address,
                source=TokenSource.TELEGRAM,
                detected_at=datetime.utcnow()
            )
            
            # Ajouter des métadonnées du message
            metadata = {
                'telegram_channel': getattr(event.chat, 'username', 'unknown'),
                'message_id': event.message.id,
                'message_date': event.message.date,
                'message_text': message_text[:500],  # Limiter la taille
                'sender_id': event.sender_id
            }
            
            logger.info(f"📱 Token détecté via Telegram: {address}")
            
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
            if not TELETHON_AVAILABLE or not self.client:
                return False
            
            return self.is_running and self.client.is_connected()
            
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
            'monitored_channels': len(self.monitored_channels),
            'messages_processed': self.messages_processed,
            'contracts_found': self.contracts_found,
            'tokens_triggered': self.tokens_triggered,
            'processed_messages_count': len(self.processed_messages),
            'telethon_available': TELETHON_AVAILABLE
        }
    
    async def add_channel(self, channel_username: str) -> bool:
        """Ajoute un nouveau channel à surveiller."""
        try:
            if not self.client:
                return False
            
            entity = await self.client.get_entity(channel_username)
            if entity not in self.monitored_channels:
                self.monitored_channels.append(entity)
                logger.info(f"📱 Nouveau channel ajouté: {channel_username}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'ajout du channel {channel_username}: {e}")
            return False
    
    async def remove_channel(self, channel_username: str) -> bool:
        """Retire un channel de la surveillance."""
        try:
            for channel in self.monitored_channels:
                if getattr(channel, 'username', '') == channel_username.replace('@', ''):
                    self.monitored_channels.remove(channel)
                    logger.info(f"📱 Channel retiré: {channel_username}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la suppression du channel {channel_username}: {e}")
            return False
    
    def clear_processed_messages(self):
        """Vide le cache des messages traités."""
        self.processed_messages.clear()
        logger.info("📱 Cache des messages traités vidé")