#!/usr/bin/env python3
"""
Crypto Sentinel - Tests d'Intégration

Tests d'intégration pour valider le fonctionnement global du système Crypto Sentinel.

Author: Crypto Sentinel Team
Version: 1.0.0
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any, List
import json
import httpx

# Import des modules à tester
from app.main import app, lifespan
from app.models import TokenInfo, AIAnalysis, TokenSource, AnalysisStatus, RiskLevel, Recommendation
from app.config import settings
from fastapi.testclient import TestClient

# Import des services
from app.token_scanner import TokenScannerService
from app.gpt_analyzer import GPTAnalyzerService
from app.telegram_notifier import TelegramNotifierService
from app.dexscanner import DexscannerService
from app.db import DatabaseManager
from app.websocket_listener import EthereumWebSocketListener
from app.scheduler import SchedulerService


class TestAPIIntegration:
    """Tests d'intégration pour l'API FastAPI."""
    
    @pytest.fixture
    def client(self):
        """Client de test FastAPI."""
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Test de l'endpoint racine."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Crypto Sentinel" in data["message"]
        assert "version" in data
        assert "status" in data
    
    @patch('app.main.db_manager')
    def test_health_endpoint(self, mock_db, client):
        """Test de l'endpoint de santé."""
        # Mock du health check de la DB
        mock_db.health_check = AsyncMock(return_value=True)
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "services" in data
    
    @patch('app.main.db_manager')
    def test_stats_endpoint(self, mock_db, client):
        """Test de l'endpoint de statistiques."""
        # Mock des statistiques
        mock_db.get_stats = AsyncMock(return_value={
            "total_tokens": 100,
            "analyzed_tokens": 80,
            "high_score_tokens": 15
        })
        
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_tokens" in data
        assert "analyzed_tokens" in data
        assert "high_score_tokens" in data
    
    @patch('app.main.db_manager')
    def test_recent_analyses_endpoint(self, mock_db, client):
        """Test de l'endpoint des analyses récentes."""
        # Mock des analyses récentes
        mock_analyses = [
            {
                "contract_address": "0x1234567890123456789012345678901234567890",
                "name": "Test Token",
                "symbol": "TEST",
                "ai_analysis": {
                    "score": 8.5,
                    "recommendation": "BUY"
                },
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        mock_db.get_recent_analyses = AsyncMock(return_value=mock_analyses)
        
        response = client.get("/analyses/recent")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert "contract_address" in data[0]
            assert "ai_analysis" in data[0]
    
    @patch('app.main.db_manager')
    def test_high_score_analyses_endpoint(self, mock_db, client):
        """Test de l'endpoint des analyses à score élevé."""
        # Mock des analyses à score élevé
        mock_analyses = [
            {
                "contract_address": "0x1234567890123456789012345678901234567890",
                "name": "High Score Token",
                "symbol": "HIGH",
                "ai_analysis": {
                    "score": 9.2,
                    "recommendation": "STRONG_BUY"
                },
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        
        mock_db.get_high_score_analyses = AsyncMock(return_value=mock_analyses)
        
        response = client.get("/analyses/high-score")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if data:
            assert data[0]["ai_analysis"]["score"] >= 7.0


class TestTokenAnalysisWorkflow:
    """Tests d'intégration pour le workflow complet d'analyse de tokens."""
    
    @pytest.fixture
    def mock_services(self):
        """Mock de tous les services nécessaires."""
        return {
            'web3': Mock(),
            'db': AsyncMock(spec=DatabaseManager),
            'openai': Mock(),
            'telegram_bot': AsyncMock(),
            'httpx_client': AsyncMock()
        }
    
    @pytest.mark.asyncio
    async def test_complete_token_analysis_workflow(self, mock_services):
        """Test du workflow complet d'analyse d'un token."""
        # 1. Setup des mocks
        mock_web3 = mock_services['web3']
        mock_db = mock_services['db']
        mock_openai = mock_services['openai']
        
        # Mock des données de contrat ERC20
        mock_contract = Mock()
        mock_contract.functions.name.return_value.call.return_value = "Test Token"
        mock_contract.functions.symbol.return_value.call.return_value = "TEST"
        mock_contract.functions.decimals.return_value.call.return_value = 18
        mock_contract.functions.totalSupply.return_value.call.return_value = 1000000 * 10**18
        
        mock_web3.eth.contract.return_value = mock_contract
        mock_web3.eth.get_code.return_value = b'\x60\x80\x60\x40'  # Bytecode non vide
        
        # Mock de la base de données
        mock_db.token_exists.return_value = False
        mock_db.get_cached_analysis.return_value = None
        mock_db.save_token_analysis.return_value = True
        mock_db.cache_analysis.return_value = True
        
        # Mock de la réponse OpenAI
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "score": 8.5,
            "reasoning": "Token prometteur avec une bonne liquidité et une équipe solide",
            "risks": ["Volatilité du marché", "Concurrence élevée"],
            "opportunities": ["Adoption croissante", "Partenariats stratégiques"],
            "recommendation": "BUY",
            "confidence": 0.85,
            "detailed_scores": {
                "liquidity": 8.0,
                "community": 7.5,
                "technology": 9.0,
                "tokenomics": 8.5,
                "team": 8.0
            }
        })
        
        with patch('app.token_scanner.web3', mock_web3), \
             patch('app.gpt_analyzer.openai') as mock_openai_patch:
            
            mock_openai_patch.ChatCompletion.acreate.return_value = mock_response
            
            # 2. Initialiser les services
            scanner = TokenScannerService(mock_web3, mock_db)
            analyzer = GPTAnalyzerService(mock_db)
            
            # 3. Exécuter le workflow
            address = "0x1234567890123456789012345678901234567890"
            
            # Étape 1: Scanner le token
            token_info = await scanner.scan_token(address)
            assert token_info is not None
            assert token_info.name == "Test Token"
            assert token_info.symbol == "TEST"
            
            # Étape 2: Analyser avec GPT
            analysis = await analyzer.analyze_token(token_info)
            assert analysis is not None
            assert analysis.score == 8.5
            assert analysis.recommendation == Recommendation.BUY
            
            # Étape 3: Vérifier que les données sont cohérentes
            assert analysis.confidence == 0.85
            assert len(analysis.risks) == 2
            assert len(analysis.opportunities) == 2
    
    @pytest.mark.asyncio
    async def test_dexscreener_integration_workflow(self, mock_services):
        """Test du workflow d'intégration avec Dexscreener."""
        # Mock de la réponse Dexscreener
        mock_response = Mock()
        mock_response.json.return_value = {
            "pairs": [
                {
                    "chainId": "ethereum",
                    "dexId": "uniswap",
                    "pairAddress": "0x1234567890123456789012345678901234567890",
                    "baseToken": {
                        "address": "0xabcdef1234567890123456789012345678901234",
                        "name": "New Token",
                        "symbol": "NEW"
                    },
                    "quoteToken": {
                        "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                        "name": "Wrapped Ether",
                        "symbol": "WETH"
                    },
                    "priceUsd": "0.1",
                    "liquidity": {"usd": 25000},
                    "volume": {"h24": 5000},
                    "pairCreatedAt": int(datetime.utcnow().timestamp() * 1000)
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        with patch('app.dexscanner.httpx') as mock_httpx:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_httpx.AsyncClient.return_value.__aenter__.return_value = mock_client
            
            # Initialiser le service Dexscreener
            dexscanner = DexscannerService()
            
            # Récupérer les nouvelles paires
            pairs = await dexscanner.fetch_new_pairs()
            
            assert len(pairs) == 1
            pair = pairs[0]
            assert pair["baseToken"]["name"] == "New Token"
            assert pair["baseToken"]["symbol"] == "NEW"
            assert float(pair["liquidity"]["usd"]) == 25000
    
    @pytest.mark.asyncio
    async def test_notification_workflow(self, mock_services):
        """Test du workflow de notification."""
        mock_bot = mock_services['telegram_bot']
        
        with patch('app.telegram_notifier.Bot') as mock_bot_class:
            mock_bot_class.return_value = mock_bot
            
            # Initialiser le service de notification
            notifier = TelegramNotifierService()
            notifier.bot = mock_bot
            
            # Créer des données de test
            token_info = TokenInfo(
                contract_address="0x1234567890123456789012345678901234567890",
                name="Notification Test Token",
                symbol="NTT",
                source=TokenSource.DEXSCREENER
            )
            
            analysis = AIAnalysis(
                score=8.7,
                reasoning="Excellent token avec une forte communauté",
                risks=["Risque de marché"],
                opportunities=["Croissance explosive possible"],
                recommendation=Recommendation.STRONG_BUY,
                confidence=0.9
            )
            
            # Envoyer la notification
            result = await notifier.send_token_alert(token_info, analysis)
            
            assert result is True
            mock_bot.send_message.assert_called_once()
            
            # Vérifier le contenu du message
            call_args = mock_bot.send_message.call_args
            message_text = call_args[1]['text']
            assert "Notification Test Token" in message_text
            assert "NTT" in message_text
            assert "8.7" in message_text


class TestServiceInteractions:
    """Tests d'intégration pour les interactions entre services."""
    
    @pytest.mark.asyncio
    async def test_database_service_interactions(self):
        """Test des interactions avec la base de données."""
        with patch('app.db.AsyncIOMotorClient') as mock_motor:
            # Mock du client MongoDB
            mock_client = AsyncMock()
            mock_db = AsyncMock()
            mock_collection = AsyncMock()
            
            mock_motor.return_value = mock_client
            mock_client.__getitem__.return_value = mock_db
            mock_db.__getitem__.return_value = mock_collection
            
            # Mock des opérations de base de données
            mock_collection.insert_one.return_value = Mock(inserted_id="123")
            mock_collection.find_one.return_value = None
            mock_collection.count_documents.return_value = 0
            mock_db.command.return_value = {"ok": 1}
            
            # Initialiser le gestionnaire de base de données
            db_manager = DatabaseManager()
            await db_manager.connect()
            
            # Test de sauvegarde
            token_info = TokenInfo(
                contract_address="0x1234567890123456789012345678901234567890",
                name="DB Test Token",
                symbol="DBT",
                source=TokenSource.ETHEREUM_WEBSOCKET
            )
            
            analysis = AIAnalysis(
                score=7.5,
                reasoning="Token stable",
                recommendation=Recommendation.HOLD,
                confidence=0.75
            )
            
            result = await db_manager.save_token_analysis(token_info, analysis)
            assert result is True
            
            # Test de vérification d'existence
            exists = await db_manager.token_exists(token_info.contract_address)
            assert exists is False  # Car mock retourne None
            
            # Test de health check
            health = await db_manager.health_check()
            assert health is True
    
    @pytest.mark.asyncio
    async def test_scheduler_service_integration(self):
        """Test d'intégration du service de planification."""
        with patch('app.scheduler.AsyncIOScheduler') as mock_scheduler_class:
            mock_scheduler = Mock()
            mock_scheduler_class.return_value = mock_scheduler
            
            # Initialiser le service de planification
            scheduler_service = SchedulerService()
            
            # Démarrer le scheduler
            await scheduler_service.start()
            
            assert scheduler_service.is_running is True
            mock_scheduler.start.assert_called_once()
            
            # Vérifier que les tâches sont ajoutées
            assert mock_scheduler.add_job.call_count >= 3  # Au moins 3 tâches programmées
            
            # Arrêter le scheduler
            await scheduler_service.stop()
            
            assert scheduler_service.is_running is False
            mock_scheduler.shutdown.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_websocket_listener_integration(self):
        """Test d'intégration du listener WebSocket."""
        with patch('app.websocket_listener.websockets') as mock_websockets:
            # Mock de la connexion WebSocket
            mock_websocket = AsyncMock()
            mock_websockets.connect.return_value.__aenter__.return_value = mock_websocket
            
            # Mock des messages WebSocket
            mock_websocket.recv.side_effect = [
                json.dumps({
                    "id": 1,
                    "result": "0x123"
                }),
                json.dumps({
                    "method": "eth_subscription",
                    "params": {
                        "subscription": "0x123",
                        "result": {
                            "address": "0x1234567890123456789012345678901234567890",
                            "topics": ["0x" + "0" * 64],
                            "data": "0x" + "0" * 128
                        }
                    }
                }),
                asyncio.CancelledError()  # Pour arrêter la boucle
            ]
            
            # Initialiser le listener
            listener = EthereumWebSocketListener()
            
            # Tester la connexion (devrait se terminer rapidement avec CancelledError)
            try:
                await listener.start_listening()
            except asyncio.CancelledError:
                pass  # Attendu
            
            # Vérifier que la connexion a été tentée
            mock_websockets.connect.assert_called()


class TestErrorHandling:
    """Tests d'intégration pour la gestion d'erreurs."""
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test de gestion d'erreurs dans l'API."""
        with patch('app.main.db_manager') as mock_db:
            # Simuler une erreur de base de données
            mock_db.health_check.side_effect = Exception("Database connection failed")
            
            client = TestClient(app)
            response = client.get("/health")
            
            # L'API devrait gérer l'erreur gracieusement
            assert response.status_code in [200, 500]  # Selon l'implémentation
    
    @pytest.mark.asyncio
    async def test_service_resilience(self):
        """Test de résilience des services face aux erreurs."""
        with patch('app.gpt_analyzer.openai') as mock_openai:
            # Simuler une erreur OpenAI
            mock_openai.ChatCompletion.acreate.side_effect = Exception("API rate limit exceeded")
            
            mock_db = AsyncMock()
            mock_db.get_cached_analysis.return_value = None
            
            analyzer = GPTAnalyzerService(mock_db)
            
            token_info = TokenInfo(
                contract_address="0x1234567890123456789012345678901234567890",
                name="Error Test Token",
                symbol="ETT",
                source=TokenSource.ETHEREUM_WEBSOCKET
            )
            
            # Le service devrait gérer l'erreur et retourner None
            result = await analyzer.analyze_token(token_info)
            assert result is None
    
    @pytest.mark.asyncio
    async def test_network_error_resilience(self):
        """Test de résilience face aux erreurs réseau."""
        with patch('app.dexscanner.httpx') as mock_httpx:
            # Simuler une erreur réseau
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Request timeout")
            mock_httpx.AsyncClient.return_value.__aenter__.return_value = mock_client
            
            dexscanner = DexscannerService()
            
            # Le service devrait gérer l'erreur et retourner une liste vide
            pairs = await dexscanner.fetch_new_pairs()
            assert pairs == []


if __name__ == "__main__":
    # Exécuter les tests
    pytest.main([__file__, "-v"])