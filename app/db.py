#!/usr/bin/env python3
"""
Crypto Sentinel - Database Manager

Gestionnaire de base de données MongoDB pour la persistance des données de tokens,
analyses IA, notifications et analytics.

Author: Crypto Sentinel Team
Version: 1.0.0
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError, ConnectionFailure
from pymongo import IndexModel, ASCENDING, DESCENDING

from app.config import settings
from app.models import (
    TokenAnalysis, TokenInfo, AIAnalysis, NotificationAlert,
    AnalyticsData, AnalysisStatus, TokenSource
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class DatabaseManager:
    """Gestionnaire de base de données MongoDB."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.tokens_collection: Optional[AsyncIOMotorCollection] = None
        self.analytics_collection: Optional[AsyncIOMotorCollection] = None
        self.alerts_collection: Optional[AsyncIOMotorCollection] = None
        self._connected = False
    
    async def connect(self) -> bool:
        """Établit la connexion à MongoDB."""
        try:
            logger.info(f"🔌 Connexion à MongoDB: {settings.MONGODB_URL}")
            
            self.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000
            )
            
            # Test de connexion
            await self.client.admin.command('ping')
            
            # Initialisation de la base de données
            self.db = self.client[settings.MONGODB_DATABASE]
            self.tokens_collection = self.db[settings.MONGODB_COLLECTION_TOKENS]
            self.analytics_collection = self.db[settings.MONGODB_COLLECTION_ANALYTICS]
            self.alerts_collection = self.db[settings.MONGODB_COLLECTION_ALERTS]
            
            # Création des index
            await self._create_indexes()
            
            self._connected = True
            logger.info("✅ Connexion MongoDB établie avec succès")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur de connexion MongoDB: {e}")
            self._connected = False
            return False
    
    async def disconnect(self):
        """Ferme la connexion à MongoDB."""
        if self.client:
            self.client.close()
            self._connected = False
            logger.info("🔌 Connexion MongoDB fermée")
    
    async def health_check(self) -> bool:
        """Vérifie l'état de santé de la base de données."""
        try:
            if not self._connected or not self.client:
                return False
            
            await self.client.admin.command('ping')
            return True
            
        except Exception as e:
            logger.error(f"Health check MongoDB échoué: {e}")
            return False
    
    async def _create_indexes(self):
        """Crée les index nécessaires pour optimiser les performances."""
        try:
            # Index pour la collection tokens
            tokens_indexes = [
                IndexModel([("token_info.contract_address", ASCENDING)], unique=True),
                IndexModel([("created_at", DESCENDING)]),
                IndexModel([("ai_analysis.score", DESCENDING)]),
                IndexModel([("status", ASCENDING)]),
                IndexModel([("token_info.source", ASCENDING)]),
                IndexModel([("notification_sent", ASCENDING)]),
                IndexModel([("token_info.detected_at", DESCENDING)]),
                IndexModel([("ai_analysis.recommendation", ASCENDING)])
            ]
            
            await self.tokens_collection.create_indexes(tokens_indexes)
            
            # Index pour la collection analytics
            analytics_indexes = [
                IndexModel([("date", DESCENDING)], unique=True),
                IndexModel([("tokens_detected", DESCENDING)]),
                IndexModel([("average_ai_score", DESCENDING)])
            ]
            
            await self.analytics_collection.create_indexes(analytics_indexes)
            
            # Index pour la collection alerts
            alerts_indexes = [
                IndexModel([("token_address", ASCENDING)]),
                IndexModel([("sent_at", DESCENDING)]),
                IndexModel([("ai_score", DESCENDING)])
            ]
            
            await self.alerts_collection.create_indexes(alerts_indexes)
            
            logger.info("📊 Index MongoDB créés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de la création des index: {e}")
    
    # === OPÉRATIONS TOKENS ===
    
    async def save_token_analysis(self, analysis: TokenAnalysis) -> bool:
        """Sauvegarde ou met à jour une analyse de token."""
        try:
            analysis.updated_at = datetime.utcnow()
            
            # Conversion en dictionnaire
            analysis_dict = analysis.dict(by_alias=True, exclude_unset=True)
            
            # Upsert basé sur l'adresse du contrat
            result = await self.tokens_collection.replace_one(
                {"token_info.contract_address": analysis.token_info.contract_address},
                analysis_dict,
                upsert=True
            )
            
            if result.upserted_id:
                logger.info(f"💾 Nouveau token sauvegardé: {analysis.token_info.contract_address}")
            else:
                logger.info(f"🔄 Token mis à jour: {analysis.token_info.contract_address}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du token: {e}")
            return False
    
    async def get_token_analysis(self, contract_address: str) -> Optional[TokenAnalysis]:
        """Récupère l'analyse d'un token par son adresse."""
        try:
            result = await self.tokens_collection.find_one(
                {"token_info.contract_address": contract_address.lower()}
            )
            
            if result:
                return TokenAnalysis(**result)
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du token {contract_address}: {e}")
            return None
    
    async def get_recent_tokens(self, limit: int = 50) -> List[TokenAnalysis]:
        """Récupère les tokens récemment détectés."""
        try:
            cursor = self.tokens_collection.find().sort("created_at", DESCENDING).limit(limit)
            results = await cursor.to_list(length=limit)
            
            return [TokenAnalysis(**result) for result in results]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tokens récents: {e}")
            return []
    
    async def get_tokens_by_score(
        self, 
        min_score: float, 
        limit: int = 20,
        hours_back: int = 24
    ) -> List[TokenAnalysis]:
        """Récupère les tokens avec un score IA élevé."""
        try:
            since = datetime.utcnow() - timedelta(hours=hours_back)
            
            cursor = self.tokens_collection.find({
                "ai_analysis.score": {"$gte": min_score},
                "created_at": {"$gte": since},
                "status": AnalysisStatus.COMPLETED
            }).sort("ai_analysis.score", DESCENDING).limit(limit)
            
            results = await cursor.to_list(length=limit)
            return [TokenAnalysis(**result) for result in results]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tokens high-score: {e}")
            return []
    
    async def get_pending_analyses(self, limit: int = 10) -> List[TokenAnalysis]:
        """Récupère les analyses en attente."""
        try:
            cursor = self.tokens_collection.find({
                "status": AnalysisStatus.PENDING
            }).sort("created_at", ASCENDING).limit(limit)
            
            results = await cursor.to_list(length=limit)
            return [TokenAnalysis(**result) for result in results]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des analyses en attente: {e}")
            return []
    
    async def update_analysis_status(
        self, 
        contract_address: str, 
        status: AnalysisStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """Met à jour le statut d'une analyse."""
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            if error_message:
                update_data["error_message"] = error_message
            
            if status == AnalysisStatus.COMPLETED:
                update_data["analyzed_at"] = datetime.utcnow()
            
            result = await self.tokens_collection.update_one(
                {"token_info.contract_address": contract_address.lower()},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut: {e}")
            return False
    
    async def token_exists(self, contract_address: str) -> bool:
        """Vérifie si un token existe déjà en base."""
        try:
            count = await self.tokens_collection.count_documents(
                {"token_info.contract_address": contract_address.lower()}
            )
            return count > 0
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification d'existence du token: {e}")
            return False
    
    async def get_tokens_by_source(
        self, 
        source: TokenSource, 
        hours_back: int = 24,
        limit: int = 100
    ) -> List[TokenAnalysis]:
        """Récupère les tokens par source de détection."""
        try:
            since = datetime.utcnow() - timedelta(hours=hours_back)
            
            cursor = self.tokens_collection.find({
                "token_info.source": source,
                "created_at": {"$gte": since}
            }).sort("created_at", DESCENDING).limit(limit)
            
            results = await cursor.to_list(length=limit)
            return [TokenAnalysis(**result) for result in results]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des tokens par source: {e}")
            return []
    
    # === OPÉRATIONS NOTIFICATIONS ===
    
    async def save_notification_alert(self, alert: NotificationAlert) -> bool:
        """Sauvegarde une alerte de notification."""
        try:
            alert_dict = alert.dict(by_alias=True, exclude_unset=True)
            
            await self.alerts_collection.insert_one(alert_dict)
            logger.info(f"📢 Alerte sauvegardée pour {alert.token_address}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'alerte: {e}")
            return False
    
    async def mark_token_notified(self, contract_address: str, message_id: Optional[int] = None) -> bool:
        """Marque un token comme notifié."""
        try:
            update_data = {
                "notification_sent": True,
                "notification_sent_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            if message_id:
                update_data["telegram_message_id"] = message_id
            
            result = await self.tokens_collection.update_one(
                {"token_info.contract_address": contract_address.lower()},
                {"$set": update_data}
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Erreur lors du marquage de notification: {e}")
            return False
    
    async def get_recent_alerts(self, hours_back: int = 24, limit: int = 50) -> List[NotificationAlert]:
        """Récupère les alertes récentes."""
        try:
            since = datetime.utcnow() - timedelta(hours=hours_back)
            
            cursor = self.alerts_collection.find({
                "sent_at": {"$gte": since}
            }).sort("sent_at", DESCENDING).limit(limit)
            
            results = await cursor.to_list(length=limit)
            return [NotificationAlert(**result) for result in results]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des alertes: {e}")
            return []
    
    # === OPÉRATIONS ANALYTICS ===
    
    async def save_daily_analytics(self, analytics: AnalyticsData) -> bool:
        """Sauvegarde les analytics quotidiennes."""
        try:
            analytics_dict = analytics.dict(exclude_unset=True)
            
            # Upsert basé sur la date
            result = await self.analytics_collection.replace_one(
                {"date": analytics.date},
                analytics_dict,
                upsert=True
            )
            
            logger.info(f"📊 Analytics sauvegardées pour {analytics.date.date()}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des analytics: {e}")
            return False
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques système."""
        try:
            now = datetime.utcnow()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_ago = today - timedelta(days=7)
            
            # Statistiques aujourd'hui
            tokens_today = await self.tokens_collection.count_documents({
                "created_at": {"$gte": today}
            })
            
            analyzed_today = await self.tokens_collection.count_documents({
                "analyzed_at": {"$gte": today},
                "status": AnalysisStatus.COMPLETED
            })
            
            notifications_today = await self.alerts_collection.count_documents({
                "sent_at": {"$gte": today}
            })
            
            # Score moyen des 24 dernières heures
            pipeline = [
                {
                    "$match": {
                        "analyzed_at": {"$gte": today},
                        "ai_analysis.score": {"$exists": True}
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "avg_score": {"$avg": "$ai_analysis.score"},
                        "max_score": {"$max": "$ai_analysis.score"},
                        "min_score": {"$min": "$ai_analysis.score"}
                    }
                }
            ]
            
            score_stats = await self.tokens_collection.aggregate(pipeline).to_list(1)
            
            # Répartition par source (7 derniers jours)
            source_pipeline = [
                {
                    "$match": {
                        "created_at": {"$gte": week_ago}
                    }
                },
                {
                    "$group": {
                        "_id": "$token_info.source",
                        "count": {"$sum": 1}
                    }
                }
            ]
            
            source_stats = await self.tokens_collection.aggregate(source_pipeline).to_list(10)
            
            # Tokens avec score élevé (> 7)
            high_score_count = await self.tokens_collection.count_documents({
                "ai_analysis.score": {"$gte": 7.0},
                "analyzed_at": {"$gte": week_ago}
            })
            
            return {
                "tokens_detected_today": tokens_today,
                "tokens_analyzed_today": analyzed_today,
                "notifications_sent_today": notifications_today,
                "high_score_tokens_week": high_score_count,
                "average_score_today": score_stats[0]["avg_score"] if score_stats else None,
                "max_score_today": score_stats[0]["max_score"] if score_stats else None,
                "min_score_today": score_stats[0]["min_score"] if score_stats else None,
                "source_breakdown": {item["_id"]: item["count"] for item in source_stats},
                "total_tokens": await self.tokens_collection.count_documents({}),
                "total_alerts": await self.alerts_collection.count_documents({}),
                "last_updated": now
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stats: {e}")
            return {}
    
    # === OPÉRATIONS DE MAINTENANCE ===
    
    async def cleanup_old_data(self, days_to_keep: int = 30) -> Dict[str, int]:
        """Nettoie les anciennes données."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Suppression des anciens tokens avec score faible
            old_tokens_result = await self.tokens_collection.delete_many({
                "created_at": {"$lt": cutoff_date},
                "ai_analysis.score": {"$lt": 5.0}
            })
            
            # Suppression des anciennes alertes
            old_alerts_result = await self.alerts_collection.delete_many({
                "sent_at": {"$lt": cutoff_date}
            })
            
            # Suppression des anciennes analytics (garder plus longtemps)
            analytics_cutoff = datetime.utcnow() - timedelta(days=days_to_keep * 3)
            old_analytics_result = await self.analytics_collection.delete_many({
                "date": {"$lt": analytics_cutoff}
            })
            
            cleanup_stats = {
                "tokens_deleted": old_tokens_result.deleted_count,
                "alerts_deleted": old_alerts_result.deleted_count,
                "analytics_deleted": old_analytics_result.deleted_count
            }
            
            logger.info(f"🧹 Nettoyage terminé: {cleanup_stats}")
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage: {e}")
            return {"error": str(e)}
    
    async def get_database_size(self) -> Dict[str, Any]:
        """Récupère les informations de taille de la base de données."""
        try:
            stats = await self.db.command("dbStats")
            
            return {
                "database_size_mb": round(stats.get("dataSize", 0) / (1024 * 1024), 2),
                "index_size_mb": round(stats.get("indexSize", 0) / (1024 * 1024), 2),
                "total_size_mb": round(stats.get("storageSize", 0) / (1024 * 1024), 2),
                "collections": stats.get("collections", 0),
                "objects": stats.get("objects", 0)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la taille DB: {e}")
            return {}