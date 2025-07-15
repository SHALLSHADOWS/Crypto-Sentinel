#!/usr/bin/env python3
"""
Crypto Sentinel - Telegram Notifier Service

Service de notification via Telegram pour alerter les utilisateurs
des nouveaux tokens détectés et analysés.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx
from app.config import settings
from app.models import TokenInfo, AnalysisResult
from app.utils.logger import setup_logger
from app.utils.helpers import (
    format_usd, format_percentage, get_score_emoji, 
    get_price_change_emoji, truncate_address
)

logger = setup_logger(__name__)


class TelegramNotifierService:
    """Service de notification Telegram."""
    
    def __init__(self, bot_token: str, chat_ids: List[str]):
        self.bot_token = bot_token
        self.chat_ids = chat_ids
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.rate_limiter = asyncio.Semaphore(20)  # 20 messages simultanés max
        self.message_queue = asyncio.Queue()
        self.is_running = False
        
    async def start(self):
        """Démarre le service de notification."""
        logger.info("🚀 Démarrage du service Telegram...")
        
        # Vérifier la connexion
        if await self._test_connection():
            self.is_running = True
            # Démarrer le worker de traitement des messages
            asyncio.create_task(self._message_worker())
            logger.info("✅ Service Telegram démarré avec succès")
        else:
            logger.error("❌ Impossible de démarrer le service Telegram")
    
    async def stop(self):
        """Arrête le service de notification."""
        self.is_running = False
        await self.http_client.aclose()
        logger.info("🛑 Service Telegram arrêté")
    
    async def notify_new_token(self, token_info: TokenInfo, analysis_result: AnalysisResult):
        """Notifie la détection d'un nouveau token avec son analyse."""
        try:
            # Vérifier si le score justifie une notification
            if analysis_result.overall_score < settings.MIN_NOTIFICATION_SCORE:
                logger.debug(f"Score trop faible pour notification: {analysis_result.overall_score}")
                return
            
            message = self._format_token_notification(token_info, analysis_result)
            await self._queue_message(message)
            
            logger.info(f"📢 Notification envoyée pour {token_info.symbol} (Score: {analysis_result.overall_score})")
            
        except Exception as e:
            logger.error(f"Erreur lors de la notification du token: {e}")
    
    async def notify_alert(self, title: str, message: str, priority: str = "normal"):
        """Envoie une alerte générale."""
        try:
            alert_message = self._format_alert_message(title, message, priority)
            await self._queue_message(alert_message, priority="high" if priority == "critical" else "normal")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi d'alerte: {e}")
    
    async def notify_system_status(self, status: Dict[str, Any]):
        """Notifie le statut du système."""
        try:
            message = self._format_system_status(status)
            await self._queue_message(message, priority="low")
            
        except Exception as e:
            logger.error(f"Erreur lors de la notification de statut: {e}")
    
    def _format_token_notification(self, token_info: TokenInfo, analysis_result: AnalysisResult) -> str:
        """Formate le message de notification pour un nouveau token."""
        score_emoji = get_score_emoji(analysis_result.overall_score)
        price_emoji = get_price_change_emoji(token_info.price_change_24h)
        
        # En-tête avec score
        message = f"🎯 **NOUVEAU TOKEN DÉTECTÉ** {score_emoji}\n\n"
        
        # Informations de base
        message += f"**{token_info.name}** ({token_info.symbol})\n"
        message += f"📍 `{truncate_address(token_info.contract_address)}`\n\n"
        
        # Score et recommandation
        message += f"📊 **Score Global:** {analysis_result.overall_score:.1f}/10 {score_emoji}\n"
        message += f"💡 **Recommandation:** {analysis_result.recommendation}\n\n"
        
        # Données de marché
        message += f"💰 **Prix:** {format_usd(token_info.price_usd)}\n"
        message += f"💧 **Liquidité:** {format_usd(token_info.liquidity_usd)}\n"
        message += f"📈 **Volume 24h:** {format_usd(token_info.volume_24h_usd)}\n"
        message += f"{price_emoji} **Change 24h:** {format_percentage(token_info.price_change_24h)}\n"
        message += f"⏰ **Âge:** {token_info.age_hours:.1f}h\n\n"
        
        # Scores détaillés
        message += "📋 **Analyse Détaillée:**\n"
        if hasattr(analysis_result, 'technical_score'):
            message += f"🔧 Technique: {analysis_result.technical_score:.1f}/10\n"
        if hasattr(analysis_result, 'fundamental_score'):
            message += f"📊 Fondamental: {analysis_result.fundamental_score:.1f}/10\n"
        if hasattr(analysis_result, 'sentiment_score'):
            message += f"😊 Sentiment: {analysis_result.sentiment_score:.1f}/10\n"
        if hasattr(analysis_result, 'risk_score'):
            message += f"⚠️ Risque: {analysis_result.risk_score:.1f}/10\n\n"
        
        # Points clés de l'analyse
        if analysis_result.key_points:
            message += "🔍 **Points Clés:**\n"
            for point in analysis_result.key_points[:3]:  # Limiter à 3 points
                message += f"• {point}\n"
            message += "\n"
        
        # Risques identifiés
        if analysis_result.risks:
            message += "⚠️ **Risques:**\n"
            for risk in analysis_result.risks[:2]:  # Limiter à 2 risques
                message += f"• {risk}\n"
            message += "\n"
        
        # Liens utiles
        message += "🔗 **Liens:**\n"
        if token_info.dex_pair_address:
            message += f"[Dexscreener](https://dexscreener.com/ethereum/{token_info.dex_pair_address})\n"
        message += f"[Etherscan](https://etherscan.io/token/{token_info.contract_address})\n"
        message += f"[Uniswap](https://app.uniswap.org/#/swap?outputCurrency={token_info.contract_address})\n\n"
        
        # Footer avec timestamp
        message += f"⏱️ {datetime.now().strftime('%H:%M:%S')} | Source: {token_info.source.value}"
        
        return message
    
    def _format_alert_message(self, title: str, message: str, priority: str) -> str:
        """Formate un message d'alerte."""
        emoji_map = {
            "critical": "🚨",
            "warning": "⚠️",
            "info": "ℹ️",
            "normal": "📢"
        }
        
        emoji = emoji_map.get(priority, "📢")
        
        alert = f"{emoji} **{title.upper()}** {emoji}\n\n"
        alert += f"{message}\n\n"
        alert += f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return alert
    
    def _format_system_status(self, status: Dict[str, Any]) -> str:
        """Formate le message de statut système."""
        message = "📊 **STATUT SYSTÈME**\n\n"
        
        # Uptime
        if 'uptime' in status:
            message += f"⏰ **Uptime:** {status['uptime']}\n"
        
        # Tokens analysés
        if 'tokens_analyzed' in status:
            message += f"🔍 **Tokens analysés:** {status['tokens_analyzed']}\n"
        
        # Notifications envoyées
        if 'notifications_sent' in status:
            message += f"📢 **Notifications:** {status['notifications_sent']}\n"
        
        # Erreurs
        if 'errors' in status:
            message += f"❌ **Erreurs:** {status['errors']}\n"
        
        # Services actifs
        if 'active_services' in status:
            message += f"\n🔧 **Services actifs:**\n"
            for service, active in status['active_services'].items():
                emoji = "✅" if active else "❌"
                message += f"{emoji} {service}\n"
        
        message += f"\n⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
    
    async def _queue_message(self, message: str, priority: str = "normal"):
        """Ajoute un message à la queue d'envoi."""
        await self.message_queue.put({
            'message': message,
            'priority': priority,
            'timestamp': datetime.now()
        })
    
    async def _message_worker(self):
        """Worker qui traite la queue des messages."""
        while self.is_running:
            try:
                # Attendre un message avec timeout
                message_data = await asyncio.wait_for(
                    self.message_queue.get(), 
                    timeout=1.0
                )
                
                await self._send_message_to_all_chats(message_data['message'])
                
                # Marquer la tâche comme terminée
                self.message_queue.task_done()
                
                # Délai entre les messages pour éviter le spam
                await asyncio.sleep(0.5)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Erreur dans le worker de messages: {e}")
                await asyncio.sleep(1)
    
    async def _send_message_to_all_chats(self, message: str):
        """Envoie un message à tous les chats configurés."""
        tasks = []
        
        for chat_id in self.chat_ids:
            task = self._send_message(chat_id, message)
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_message(self, chat_id: str, message: str) -> bool:
        """Envoie un message à un chat spécifique."""
        async with self.rate_limiter:
            try:
                url = f"{self.base_url}/sendMessage"
                
                payload = {
                    'chat_id': chat_id,
                    'text': message,
                    'parse_mode': 'Markdown',
                    'disable_web_page_preview': True
                }
                
                response = await self.http_client.post(url, json=payload)
                response.raise_for_status()
                
                result = response.json()
                
                if result.get('ok'):
                    logger.debug(f"Message envoyé avec succès au chat {chat_id}")
                    return True
                else:
                    logger.error(f"Erreur Telegram API: {result.get('description')}")
                    return False
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Erreur HTTP lors de l'envoi du message: {e.response.status_code}")
                return False
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi du message: {e}")
                return False
    
    async def _test_connection(self) -> bool:
        """Teste la connexion avec l'API Telegram."""
        try:
            url = f"{self.base_url}/getMe"
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ok'):
                bot_info = result.get('result', {})
                logger.info(f"✅ Bot Telegram connecté: {bot_info.get('username')}")
                return True
            else:
                logger.error(f"Erreur de connexion Telegram: {result.get('description')}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors du test de connexion Telegram: {e}")
            return False
    
    async def send_startup_message(self):
        """Envoie un message de démarrage."""
        message = (
            "🚀 **CRYPTO SENTINEL DÉMARRÉ**\n\n"
            "Le système de surveillance des tokens est maintenant actif.\n"
            "Vous recevrez des notifications pour les nouveaux tokens prometteurs.\n\n"
            f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        await self._queue_message(message, priority="normal")
    
    async def send_shutdown_message(self):
        """Envoie un message d'arrêt."""
        message = (
            "🛑 **CRYPTO SENTINEL ARRÊTÉ**\n\n"
            "Le système de surveillance a été arrêté.\n\n"
            f"⏱️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        await self._queue_message(message, priority="normal")
        
        # Attendre que tous les messages soient envoyés
        await self.message_queue.join()


def create_telegram_notifier(bot_token: str, chat_ids: List[str]) -> TelegramNotifierService:
    """Crée une instance du service de notification Telegram."""
    if not bot_token:
        logger.error("Token du bot Telegram manquant")
        return None
    
    if not chat_ids:
        logger.error("Aucun chat ID configuré pour Telegram")
        return None
    
    return TelegramNotifierService(bot_token, chat_ids)