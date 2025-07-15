#!/usr/bin/env python3
"""
Crypto Sentinel - Main Application Entry Point

Point d'entrée principal du backend FastAPI pour l'assistant IA crypto autonome.
Gère l'initialisation des services, les routes API et l'orchestration des modules.

Author: Crypto Sentinel Team
Version: 1.0.0
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.config import settings
from app.db import DatabaseManager
from app.websocket_listener import EthereumWebSocketListener
from app.dexscanner import DexscannerService
from app.telegram_scraper import TelegramScraperService
from app.twitter_monitor import TwitterMonitorService
from app.token_scanner import TokenScannerService
from app.gpt_analyzer import GPTAnalyzerService
from app.telegram_notifier import TelegramNotifierService
from app.scheduler import SchedulerService
from app.models import TokenAnalysis, SystemStatus
from app.utils.logger import setup_logger

# Configuration du logging
logger = setup_logger(__name__)

# Services globaux
services: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestionnaire de cycle de vie de l'application FastAPI."""
    logger.info("🚀 Démarrage de Crypto Sentinel...")
    
    try:
        # Initialisation de la base de données
        logger.info("📊 Initialisation de la base de données MongoDB...")
        services['db'] = DatabaseManager()
        await services['db'].connect()
        
        # Initialisation des services
        logger.info("🔧 Initialisation des services...")
        services['token_scanner'] = TokenScannerService()
        services['gpt_analyzer'] = GPTAnalyzerService()
        services['telegram_notifier'] = TelegramNotifierService()
        services['dexscanner'] = DexscannerService()
        services['telegram_scraper'] = TelegramScraperService()
        services['twitter_monitor'] = TwitterMonitorService()
        
        # Initialisation du WebSocket Ethereum
        logger.info("🔗 Connexion au WebSocket Ethereum...")
        services['eth_listener'] = EthereumWebSocketListener(
            token_scanner=services['token_scanner'],
            gpt_analyzer=services['gpt_analyzer'],
            notifier=services['telegram_notifier'],
            db=services['db']
        )
        
        # Initialisation du scheduler
        logger.info("⏰ Démarrage du scheduler...")
        services['scheduler'] = SchedulerService(services)
        services['scheduler'].start()
        
        # Démarrage des services en arrière-plan
        logger.info("🎯 Démarrage des services de monitoring...")
        asyncio.create_task(services['eth_listener'].start())
        asyncio.create_task(services['dexscanner'].start_monitoring())
        asyncio.create_task(services['telegram_scraper'].start_monitoring())
        
        if settings.ENABLE_TWITTER_MONITORING:
            asyncio.create_task(services['twitter_monitor'].start_monitoring())
        
        logger.info("✅ Crypto Sentinel démarré avec succès !")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du démarrage: {e}")
        raise
    
    finally:
        # Nettoyage lors de l'arrêt
        logger.info("🛑 Arrêt de Crypto Sentinel...")
        
        if 'scheduler' in services:
            services['scheduler'].stop()
        
        if 'eth_listener' in services:
            await services['eth_listener'].stop()
        
        if 'db' in services:
            await services['db'].disconnect()
        
        logger.info("✅ Crypto Sentinel arrêté proprement.")


# Création de l'application FastAPI
app = FastAPI(
    title="Crypto Sentinel API",
    description="Assistant IA crypto autonome pour la détection de tokens à potentiel",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # À restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=Dict[str, str])
async def root():
    """Endpoint racine avec informations de base."""
    return {
        "service": "Crypto Sentinel",
        "version": "1.0.0",
        "status": "running",
        "description": "Assistant IA crypto autonome"
    }


@app.get("/health", response_model=SystemStatus)
async def health_check():
    """Vérification de l'état de santé du système."""
    try:
        # Vérification de la base de données
        db_status = await services['db'].health_check() if 'db' in services else False
        
        # Vérification des services
        eth_status = services['eth_listener'].is_connected() if 'eth_listener' in services else False
        
        return SystemStatus(
            status="healthy" if db_status and eth_status else "degraded",
            database_connected=db_status,
            ethereum_connected=eth_status,
            services_running=len([s for s in services.values() if hasattr(s, 'is_running') and s.is_running()]),
            uptime=services.get('scheduler', {}).get('uptime', 0)
        )
    
    except Exception as e:
        logger.error(f"Erreur lors du health check: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@app.get("/stats", response_model=Dict[str, Any])
async def get_stats():
    """Statistiques du système et des analyses."""
    try:
        if 'db' not in services:
            raise HTTPException(status_code=503, detail="Database not available")
        
        stats = await services['db'].get_system_stats()
        return stats
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve stats")


@app.get("/tokens/recent", response_model=list[TokenAnalysis])
async def get_recent_tokens(limit: int = 50):
    """Récupère les tokens récemment analysés."""
    try:
        if 'db' not in services:
            raise HTTPException(status_code=503, detail="Database not available")
        
        tokens = await services['db'].get_recent_tokens(limit)
        return tokens
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des tokens: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tokens")


@app.get("/tokens/high-score", response_model=list[TokenAnalysis])
async def get_high_score_tokens(min_score: float = 7.0, limit: int = 20):
    """Récupère les tokens avec un score élevé."""
    try:
        if 'db' not in services:
            raise HTTPException(status_code=503, detail="Database not available")
        
        tokens = await services['db'].get_tokens_by_score(min_score, limit)
        return tokens
    
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des tokens high-score: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve high-score tokens")


@app.post("/analyze/token")
async def analyze_token_manual(contract_address: str, background_tasks: BackgroundTasks):
    """Analyse manuelle d'un token spécifique."""
    try:
        if 'token_scanner' not in services or 'gpt_analyzer' not in services:
            raise HTTPException(status_code=503, detail="Services not available")
        
        # Validation de l'adresse
        if not contract_address or len(contract_address) != 42:
            raise HTTPException(status_code=400, detail="Invalid contract address")
        
        # Lancement de l'analyse en arrière-plan
        background_tasks.add_task(
            analyze_token_background,
            contract_address
        )
        
        return {
            "message": "Analyse lancée",
            "contract_address": contract_address,
            "status": "processing"
        }
    
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse manuelle: {e}")
        raise HTTPException(status_code=500, detail="Failed to start analysis")


async def analyze_token_background(contract_address: str):
    """Analyse d'un token en arrière-plan."""
    try:
        # Scan du token
        token_info = await services['token_scanner'].scan_token(contract_address)
        
        if token_info:
            # Analyse IA
            analysis = await services['gpt_analyzer'].analyze_token(token_info)
            
            # Sauvegarde en base
            await services['db'].save_token_analysis(analysis)
            
            # Notification si score élevé
            if analysis.ai_score >= settings.MIN_NOTIFICATION_SCORE:
                await services['telegram_notifier'].send_alert(analysis)
            
            logger.info(f"✅ Analyse terminée pour {contract_address} - Score: {analysis.ai_score}")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse en arrière-plan de {contract_address}: {e}")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Gestionnaire global d'exceptions."""
    logger.error(f"Erreur non gérée: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__}
    )


if __name__ == "__main__":
    # Configuration pour le développement
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )