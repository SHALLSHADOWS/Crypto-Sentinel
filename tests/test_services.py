#!/usr/bin/env python3
"""
Crypto Sentinel - Tests des Services

Tests unitaires pour les services principaux de Crypto Sentinel.

Author: Crypto Sentinel Team
Version: 1.0.0
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any, List
import json

# Import des services à tester
from app.token_scanner import TokenScannerService
from app.gpt_analyzer import GPTAnalyzerService
from app.telegram_notifier import TelegramNotifierService
from app.dexscanner import DexscannerService
from app.db import DatabaseManager
from app.websocket_listener import EthereumWebSocketListener
from app.scheduler import SchedulerService
from app.models import TokenInfo, AIAnalysis, TokenSource, AnalysisStatus, RiskLevel, Recommendation
from app.config import settings


class TestTokenScannerService:
    """Tests pour le service de scan de tokens."""
    
    @pytest.fixture
    def mock_web3(self):
        """Mock Web3 pour les tests."""
        with patch('app.token_scanner.web3') as mock:
            yield mock
    
    @pytest.fixture
    def mock_db(self):
        """Mock DatabaseManager pour les tests."""
        mock = AsyncMock(spec=DatabaseManager)
        return mock
    
    @pytest.fixture
    def scanner_service(self, mock_web3, mock_db):
        """Instance du service scanner avec mocks."""
        return TokenScannerService(mock_web3, mock_db)
    
    @pytest.mark.asyncio
    async def test_scan_token_valid_erc20(self, scanner_service, mock_web3, mock_db):
        """Test de scan d'un token ERC20 valide."""
        # Mock des données de contrat
        mock_contract = Mock()
        mock_contract.functions.name.return_value.call.return_value = "Test Token"
        mock_contract.functions.symbol.return_value.call.return_value = "TEST"
        mock_contract.functions.decimals.return_value.call.return_value = 18
        mock_contract.functions.totalSupply.return_value.call.return_value = 1000000 * 10**18
        
        mock_web3.eth.contract.return_value = mock_contract
        mock_web3.eth.get_code.return_value = b'\x60\x80\x60\x40'  # Bytecode non vide
        
        # Mock de la base de données
        mock_db.token_exists.return_value = False
        mock_db.save_token_analysis.return_value = True
        
        address = "0x1234567890123456789012345678901234567890"
        result = await scanner_service.scan_token(address)
        
        assert result is not None
        assert result.contract_address == address.lower()
        assert result.name == "Test Token"
        assert result.symbol == "TEST"
        assert result.decimals == 18
        assert result.total_supply == 1000000 * 10**18
    
    @pytest.mark.asyncio
    async def test_scan_token_invalid_address(self, scanner_service):
        """Test de scan avec une adresse invalide."""
        invalid_address = "0x123"  # Trop courte
        result = await scanner_service.scan_token(invalid_address)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_scan_token_already_exists(self, scanner_service, mock_db):
        """Test de scan d'un token déjà existant."""
        mock_db.token_exists.return_value = True
        
        address = "0x1234567890123456789012345678901234567890"
        result = await scanner_service.scan_token(address)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_token_holders_count(self, scanner_service, mock_web3):
        """Test de récupération du nombre de holders."""
        # Mock des événements Transfer
        mock_web3.eth.get_logs.return_value = [
            {'topics': ['0x' + '0' * 64, '0x' + '1' * 64, '0x' + '2' * 64]},
            {'topics': ['0x' + '0' * 64, '0x' + '3' * 64, '0x' + '4' * 64]},
        ]
        
        address = "0x1234567890123456789012345678901234567890"
        holders_count = await scanner_service.get_token_holders_count(address)
        
        assert holders_count >= 0


class TestGPTAnalyzerService:
    """Tests pour le service d'analyse GPT."""
    
    @pytest.fixture
    def mock_openai(self):
        """Mock OpenAI pour les tests."""
        with patch('app.gpt_analyzer.openai') as mock:
            yield mock
    
    @pytest.fixture
    def mock_db(self):
        """Mock DatabaseManager pour les tests."""
        mock = AsyncMock(spec=DatabaseManager)
        return mock
    
    @pytest.fixture
    def analyzer_service(self, mock_openai, mock_db):
        """Instance du service d'analyse avec mocks."""
        return GPTAnalyzerService(mock_db)
    
    @pytest.mark.asyncio
    async def test_analyze_token_success(self, analyzer_service, mock_openai, mock_db):
        """Test d'analyse réussie d'un token."""
        # Mock de la réponse OpenAI
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "score": 8.5,
            "reasoning": "Token prometteur avec une bonne liquidité",
            "risks": ["Volatilité élevée"],
            "opportunities": ["Croissance potentielle"],
            "recommendation": "BUY",
            "confidence": 0.85,
            "detailed_scores": {
                "liquidity": 8.0,
                "community": 7.0,
                "technology": 9.0,
                "tokenomics": 8.0,
                "team": 7.5
            }
        })
        
        mock_openai.ChatCompletion.acreate.return_value = mock_response
        mock_db.get_cached_analysis.return_value = None
        mock_db.cache_analysis.return_value = True
        
        # Token d'exemple
        token_info = TokenInfo(
            contract_address="0x1234567890123456789012345678901234567890",
            name="Test Token",
            symbol="TEST",
            decimals=18,
            total_supply=1000000,
            source=TokenSource.ETHEREUM_WEBSOCKET
        )
        
        analysis = await analyzer_service.analyze_token(token_info)
        
        assert analysis is not None
        assert analysis.score == 8.5
        assert analysis.reasoning == "Token prometteur avec une bonne liquidité"
        assert analysis.recommendation == Recommendation.BUY
        assert analysis.confidence == 0.85
    
    @pytest.mark.asyncio
    async def test_analyze_token_cached(self, analyzer_service, mock_db):
        """Test d'analyse avec résultat en cache."""
        # Mock d'une analyse en cache
        cached_analysis = AIAnalysis(
            score=7.5,
            reasoning="Analyse en cache",
            risks=["Risque modéré"],
            opportunities=["Opportunité limitée"],
            recommendation=Recommendation.HOLD,
            confidence=0.75
        )
        
        mock_db.get_cached_analysis.return_value = cached_analysis
        
        token_info = TokenInfo(
            contract_address="0x1234567890123456789012345678901234567890",
            name="Test Token",
            symbol="TEST",
            source=TokenSource.ETHEREUM_WEBSOCKET
        )
        
        analysis = await analyzer_service.analyze_token(token_info)
        
        assert analysis == cached_analysis
        assert analysis.score == 7.5
    
    @pytest.mark.asyncio
    async def test_analyze_token_openai_error(self, analyzer_service, mock_openai, mock_db):
        """Test d'analyse avec erreur OpenAI."""
        mock_openai.ChatCompletion.acreate.side_effect = Exception("API Error")
        mock_db.get_cached_analysis.return_value = None
        
        token_info = TokenInfo(
            contract_address="0x1234567890123456789012345678901234567890",
            name="Test Token",
            symbol="TEST",
            source=TokenSource.ETHEREUM_WEBSOCKET
        )
        
        analysis = await analyzer_service.analyze_token(token_info)
        assert analysis is None
    
    def test_build_analysis_prompt(self, analyzer_service):
        """Test de construction du prompt d'analyse."""
        token_info = TokenInfo(
            contract_address="0x1234567890123456789012345678901234567890",
            name="Test Token",
            symbol="TEST",
            decimals=18,
            total_supply=1000000,
            source=TokenSource.ETHEREUM_WEBSOCKET
        )
        
        market_data = {
            "price_usd": 0.5,
            "liquidity_usd": 50000,
            "volume_24h": 10000
        }
        
        prompt = analyzer_service._build_analysis_prompt(token_info, market_data)
        
        assert "Test Token" in prompt
        assert "TEST" in prompt
        assert "0x1234567890123456789012345678901234567890" in prompt
        assert "$0.5" in prompt
        assert "$50,000" in prompt


class TestTelegramNotifierService:
    """Tests pour le service de notifications Telegram."""
    
    @pytest.fixture
    def mock_bot(self):
        """Mock du bot Telegram."""
        with patch('app.telegram_notifier.Bot') as mock:
            yield mock
    
    @pytest.fixture
    def notifier_service(self, mock_bot):
        """Instance du service de notification avec mocks."""
        return TelegramNotifierService()
    
    @pytest.mark.asyncio
    async def test_send_token_alert_success(self, notifier_service, mock_bot):
        """Test d'envoi d'alerte réussie."""
        # Mock du bot
        mock_bot_instance = AsyncMock()
        mock_bot.return_value = mock_bot_instance
        notifier_service.bot = mock_bot_instance
        
        # Token et analyse d'exemple
        token_info = TokenInfo(
            contract_address="0x1234567890123456789012345678901234567890",
            name="Test Token",
            symbol="TEST",
            source=TokenSource.ETHEREUM_WEBSOCKET
        )
        
        analysis = AIAnalysis(
            score=8.5,
            reasoning="Token prometteur",
            recommendation=Recommendation.BUY,
            confidence=0.85
        )
        
        result = await notifier_service.send_token_alert(token_info, analysis)
        assert result is True
        
        # Vérifier que send_message a été appelé
        mock_bot_instance.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_token_alert_cooldown(self, notifier_service):
        """Test de cooldown des notifications."""
        token_address = "0x1234567890123456789012345678901234567890"
        
        # Ajouter le token au cooldown
        notifier_service.notification_cooldown[token_address] = datetime.utcnow()
        
        token_info = TokenInfo(
            contract_address=token_address,
            name="Test Token",
            symbol="TEST",
            source=TokenSource.ETHEREUM_WEBSOCKET
        )
        
        analysis = AIAnalysis(
            score=8.5,
            reasoning="Token prometteur",
            recommendation=Recommendation.BUY,
            confidence=0.85
        )
        
        result = await notifier_service.send_token_alert(token_info, analysis)
        assert result is False  # Bloqué par le cooldown
    
    def test_format_token_message(self, notifier_service):
        """Test de formatage des messages."""
        token_info = TokenInfo(
            contract_address="0x1234567890123456789012345678901234567890",
            name="Test Token",
            symbol="TEST",
            source=TokenSource.ETHEREUM_WEBSOCKET
        )
        
        analysis = AIAnalysis(
            score=8.5,
            reasoning="Token prometteur avec une bonne liquidité",
            recommendation=Recommendation.BUY,
            confidence=0.85
        )
        
        message = notifier_service._format_token_message(token_info, analysis)
        
        assert "🚀" in message  # Emoji pour BUY
        assert "Test Token" in message
        assert "TEST" in message
        assert "8.5" in message
        assert "Token prometteur" in message


class TestDexscannerService:
    """Tests pour le service Dexscreener."""
    
    @pytest.fixture
    def mock_httpx(self):
        """Mock httpx pour les tests."""
        with patch('app.dexscanner.httpx') as mock:
            yield mock
    
    @pytest.fixture
    def dexscanner_service(self, mock_httpx):
        """Instance du service Dexscreener avec mocks."""
        return DexscannerService()
    
    @pytest.mark.asyncio
    async def test_fetch_new_pairs_success(self, dexscanner_service, mock_httpx):
        """Test de récupération de nouvelles paires."""
        # Mock de la réponse API
        mock_response = Mock()
        mock_response.json.return_value = {
            "pairs": [
                {
                    "chainId": "ethereum",
                    "dexId": "uniswap",
                    "url": "https://dexscreener.com/ethereum/0x123",
                    "pairAddress": "0x1234567890123456789012345678901234567890",
                    "baseToken": {
                        "address": "0xabcdef1234567890123456789012345678901234",
                        "name": "Test Token",
                        "symbol": "TEST"
                    },
                    "quoteToken": {
                        "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                        "name": "Wrapped Ether",
                        "symbol": "WETH"
                    },
                    "priceUsd": "0.5",
                    "liquidity": {"usd": 50000},
                    "volume": {"h24": 10000},
                    "pairCreatedAt": 1640995200000
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_httpx.AsyncClient.return_value.__aenter__.return_value = mock_client
        
        pairs = await dexscanner_service.fetch_new_pairs()
        
        assert len(pairs) == 1
        assert pairs[0]["baseToken"]["name"] == "Test Token"
        assert pairs[0]["baseToken"]["symbol"] == "TEST"
    
    @pytest.mark.asyncio
    async def test_get_token_data_success(self, dexscanner_service, mock_httpx):
        """Test de récupération de données de token."""
        # Mock de la réponse API
        mock_response = Mock()
        mock_response.json.return_value = {
            "pairs": [
                {
                    "priceUsd": "1.25",
                    "liquidity": {"usd": 100000},
                    "volume": {"h24": 25000},
                    "priceChange": {"h24": 5.5}
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_httpx.AsyncClient.return_value.__aenter__.return_value = mock_client
        
        address = "0x1234567890123456789012345678901234567890"
        data = await dexscanner_service.get_token_data(address)
        
        assert data is not None
        assert data["price_usd"] == 1.25
        assert data["liquidity_usd"] == 100000
        assert data["volume_24h"] == 25000
        assert data["price_change_24h"] == 5.5


class TestDatabaseManager:
    """Tests pour le gestionnaire de base de données."""
    
    @pytest.fixture
    def mock_motor(self):
        """Mock Motor pour les tests."""
        with patch('app.db.AsyncIOMotorClient') as mock:
            yield mock
    
    @pytest.fixture
    def db_manager(self, mock_motor):
        """Instance du gestionnaire DB avec mocks."""
        return DatabaseManager()
    
    @pytest.mark.asyncio
    async def test_connect_success(self, db_manager, mock_motor):
        """Test de connexion réussie à la base de données."""
        mock_client = AsyncMock()
        mock_motor.return_value = mock_client
        
        result = await db_manager.connect()
        assert result is True
        assert db_manager.client is not None
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, db_manager):
        """Test de vérification de santé réussie."""
        # Mock du client et de la commande ping
        mock_client = AsyncMock()
        mock_db = AsyncMock()
        mock_client.__getitem__.return_value = mock_db
        mock_db.command.return_value = {"ok": 1}
        
        db_manager.client = mock_client
        db_manager.db = mock_db
        
        result = await db_manager.health_check()
        assert result is True
    
    @pytest.mark.asyncio
    async def test_save_token_analysis_success(self, db_manager):
        """Test de sauvegarde d'analyse réussie."""
        # Mock de la collection
        mock_collection = AsyncMock()
        mock_collection.insert_one.return_value = Mock(inserted_id="123")
        
        mock_db = AsyncMock()
        mock_db.__getitem__.return_value = mock_collection
        
        db_manager.db = mock_db
        
        # Données d'exemple
        token_info = TokenInfo(
            contract_address="0x1234567890123456789012345678901234567890",
            name="Test Token",
            symbol="TEST",
            source=TokenSource.ETHEREUM_WEBSOCKET
        )
        
        analysis = AIAnalysis(
            score=8.5,
            reasoning="Token prometteur",
            recommendation=Recommendation.BUY,
            confidence=0.85
        )
        
        result = await db_manager.save_token_analysis(token_info, analysis)
        assert result is True


class TestSchedulerService:
    """Tests pour le service de planification."""
    
    @pytest.fixture
    def mock_scheduler(self):
        """Mock APScheduler pour les tests."""
        with patch('app.scheduler.AsyncIOScheduler') as mock:
            yield mock
    
    @pytest.fixture
    def scheduler_service(self, mock_scheduler):
        """Instance du service scheduler avec mocks."""
        return SchedulerService()
    
    @pytest.mark.asyncio
    async def test_start_scheduler(self, scheduler_service, mock_scheduler):
        """Test de démarrage du scheduler."""
        mock_scheduler_instance = Mock()
        mock_scheduler.return_value = mock_scheduler_instance
        
        await scheduler_service.start()
        
        assert scheduler_service.is_running is True
        mock_scheduler_instance.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_scheduler(self, scheduler_service, mock_scheduler):
        """Test d'arrêt du scheduler."""
        mock_scheduler_instance = Mock()
        scheduler_service.scheduler = mock_scheduler_instance
        scheduler_service.is_running = True
        
        await scheduler_service.stop()
        
        assert scheduler_service.is_running is False
        mock_scheduler_instance.shutdown.assert_called_once()
    
    def test_get_stats(self, scheduler_service):
        """Test de récupération des statistiques."""
        scheduler_service.is_running = True
        scheduler_service.tasks_executed = 10
        scheduler_service.last_cleanup = datetime.utcnow()
        
        stats = scheduler_service.get_stats()
        
        assert stats["is_running"] is True
        assert stats["tasks_executed"] == 10
        assert "last_cleanup" in stats
        assert "uptime_seconds" in stats


if __name__ == "__main__":
    # Exécuter les tests
    pytest.main([__file__, "-v"])