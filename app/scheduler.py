#!/usr/bin/env python3
"""
Crypto Sentinel - Scheduler Service

Service de planification pour les tâches récurrentes : nettoyage de base de données,
maintenance système, analytics et monitoring de santé.

Author: Crypto Sentinel Team
Version: 1.0.0
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import time

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SchedulerService:
    """Service de planification des tâches récurrentes."""
    
    def __init__(self, services: Dict[str, Any]):
        self.services = services
        self.is_running = False
        self.start_time = datetime.utcnow()
        self.tasks = {}
        self.last_cleanup = None
        self.last_analytics = None
        self.last_health_check = None
        
        # Statistiques
        self.cleanup_count = 0
        self.analytics_count = 0
        self.health_checks_count = 0
        self.errors_count = 0
    
    def start(self):
        """Démarre le scheduler."""
        if self.is_running:
            logger.warning("⚠️ Scheduler déjà en cours d'exécution")
            return
        
        self.is_running = True
        self.start_time = datetime.utcnow()
        
        # Démarrage des tâches en arrière-plan
        asyncio.create_task(self._run_cleanup_task())
        asyncio.create_task(self._run_analytics_task())
        asyncio.create_task(self._run_health_check_task())
        
        logger.info("⏰ Scheduler démarré avec succès")
    
    def stop(self):
        """Arrête le scheduler."""
        self.is_running = False
        logger.info("🛑 Scheduler arrêté")
    
    @property
    def uptime(self) -> float:
        """Retourne l'uptime en secondes."""
        if self.start_time:
            return (datetime.utcnow() - self.start_time).total_seconds()
        return 0
    
    async def _run_cleanup_task(self):
        """Tâche de nettoyage de la base de données."""
        while self.is_running:
            try:
                await asyncio.sleep(settings.CLEANUP_INTERVAL_HOURS * 3600)  # Conversion en secondes
                
                if self.is_running:
                    await self._perform_cleanup()
                    
            except Exception as e:
                logger.error(f"❌ Erreur dans la tâche de nettoyage: {e}")
                self.errors_count += 1
                await asyncio.sleep(300)  # Attendre 5 minutes avant de réessayer
    
    async def _run_analytics_task(self):
        """Tâche de génération d'analytics."""
        while self.is_running:
            try:
                await asyncio.sleep(3600)  # Toutes les heures
                
                if self.is_running:
                    await self._generate_analytics()
                    
            except Exception as e:
                logger.error(f"❌ Erreur dans la tâche d'analytics: {e}")
                self.errors_count += 1
                await asyncio.sleep(300)
    
    async def _run_health_check_task(self):
        """Tâche de vérification de santé des services."""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Toutes les 5 minutes
                
                if self.is_running:
                    await self._perform_health_check()
                    
            except Exception as e:
                logger.error(f"❌ Erreur dans la tâche de health check: {e}")
                self.errors_count += 1
                await asyncio.sleep(60)
    
    async def _perform_cleanup(self):
        """Effectue le nettoyage de la base de données."""
        try:
            logger.info("🧹 Début du nettoyage de la base de données...")
            
            db = self.services.get('db')
            if not db:
                logger.warning("⚠️ Service de base de données non disponible")
                return
            
            # Nettoyage des anciennes analyses
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            deleted_count = await db.cleanup_old_analyses(cutoff_date)
            
            # Nettoyage des anciennes alertes
            alert_cutoff = datetime.utcnow() - timedelta(days=30)
            deleted_alerts = await db.cleanup_old_alerts(alert_cutoff)
            
            # Optimisation des index
            await db.optimize_indexes()
            
            self.cleanup_count += 1
            self.last_cleanup = datetime.utcnow()
            
            logger.info(f"✅ Nettoyage terminé - {deleted_count} analyses supprimées, {deleted_alerts} alertes supprimées")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du nettoyage: {e}")
            raise
    
    async def _generate_analytics(self):
        """Génère les analytics quotidiennes."""
        try:
            logger.info("📊 Génération des analytics...")
            
            db = self.services.get('db')
            if not db:
                logger.warning("⚠️ Service de base de données non disponible")
                return
            
            # Statistiques des dernières 24h
            since = datetime.utcnow() - timedelta(hours=24)
            
            stats = {
                'date': datetime.utcnow().date(),
                'tokens_detected': await db.count_tokens_since(since),
                'tokens_analyzed': await db.count_analyzed_tokens_since(since),
                'high_score_tokens': await db.count_high_score_tokens_since(since, 7.0),
                'notifications_sent': await db.count_notifications_since(since),
                'average_ai_score': await db.get_average_ai_score_since(since),
                'top_sources': await db.get_top_token_sources_since(since),
                'system_uptime': self.uptime,
                'cleanup_count': self.cleanup_count,
                'errors_count': self.errors_count
            }
            
            # Sauvegarde des analytics
            await db.save_daily_analytics(stats)
            
            self.analytics_count += 1
            self.last_analytics = datetime.utcnow()
            
            logger.info(f"✅ Analytics générées - {stats['tokens_detected']} tokens détectés")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la génération d'analytics: {e}")
            raise
    
    async def _perform_health_check(self):
        """Effectue une vérification de santé des services."""
        try:
            logger.debug("🔍 Vérification de santé des services...")
            
            health_status = {
                'timestamp': datetime.utcnow(),
                'services': {}
            }
            
            # Vérification de la base de données
            db = self.services.get('db')
            if db:
                health_status['services']['database'] = await db.health_check()
            
            # Vérification du WebSocket Ethereum
            eth_listener = self.services.get('eth_listener')
            if eth_listener:
                health_status['services']['ethereum_websocket'] = eth_listener.is_connected()
            
            # Vérification des autres services
            for service_name, service in self.services.items():
                if hasattr(service, 'health_check'):
                    try:
                        health_status['services'][service_name] = await service.health_check()
                    except Exception as e:
                        logger.warning(f"⚠️ Health check échoué pour {service_name}: {e}")
                        health_status['services'][service_name] = False
            
            # Compter les services en bonne santé
            healthy_services = sum(1 for status in health_status['services'].values() if status)
            total_services = len(health_status['services'])
            
            if healthy_services < total_services:
                logger.warning(f"⚠️ {total_services - healthy_services} service(s) en panne")
            
            self.health_checks_count += 1
            self.last_health_check = datetime.utcnow()
            
            # Envoyer une alerte si trop de services sont en panne
            if healthy_services < total_services * 0.5:  # Moins de 50% des services fonctionnent
                await self._send_critical_alert(health_status)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du health check: {e}")
            raise
    
    async def _send_critical_alert(self, health_status: Dict[str, Any]):
        """Envoie une alerte critique en cas de problème système."""
        try:
            notifier = self.services.get('telegram_notifier')
            if not notifier:
                return
            
            failed_services = [
                name for name, status in health_status['services'].items() 
                if not status
            ]
            
            message = f"🚨 **ALERTE CRITIQUE SYSTÈME**\n\n"
            message += f"Services en panne: {', '.join(failed_services)}\n"
            message += f"Uptime: {self.uptime:.0f}s\n"
            message += f"Timestamp: {health_status['timestamp']}"
            
            await notifier.send_system_alert(message)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'envoi d'alerte critique: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du scheduler."""
        return {
            'is_running': self.is_running,
            'uptime_seconds': self.uptime,
            'start_time': self.start_time,
            'last_cleanup': self.last_cleanup,
            'last_analytics': self.last_analytics,
            'last_health_check': self.last_health_check,
            'cleanup_count': self.cleanup_count,
            'analytics_count': self.analytics_count,
            'health_checks_count': self.health_checks_count,
            'errors_count': self.errors_count
        }
    
    async def force_cleanup(self):
        """Force l'exécution du nettoyage."""
        logger.info("🧹 Nettoyage forcé demandé")
        await self._perform_cleanup()
    
    async def force_analytics(self):
        """Force la génération d'analytics."""
        logger.info("📊 Génération d'analytics forcée")
        await self._generate_analytics()
    
    async def force_health_check(self):
        """Force la vérification de santé."""
        logger.info("🔍 Health check forcé")
        await self._perform_health_check()