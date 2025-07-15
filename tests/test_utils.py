#!/usr/bin/env python3
"""
Crypto Sentinel - Tests des Utilitaires

Tests unitaires pour les modules utilitaires de Crypto Sentinel.

Author: Crypto Sentinel Team
Version: 1.0.0
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

# Import des modules à tester
from app.utils.validators import (
    is_valid_ethereum_address,
    is_valid_contract_address,
    validate_token_amount,
    validate_score,
    is_recent_token
)
from app.utils.helpers import (
    sanitize_text,
    format_number,
    calculate_percentage_change,
    truncate_address,
    create_progress_bar,
    safe_divide,
    parse_duration,
    get_pending_analyses_count
)
from app.utils.web3_helpers import (
    get_contract_info,
    is_erc20_contract,
    get_token_metadata,
    estimate_gas_price,
    format_wei_to_ether,
    get_transaction_receipt
)


class TestValidators:
    """Tests pour le module validators."""
    
    def test_is_valid_ethereum_address_valid(self):
        """Test avec des adresses Ethereum valides."""
        valid_addresses = [
            "0x1234567890123456789012345678901234567890",
            "0xA0b86a33E6441e8e5c3F27d9C387b8B2C4B4B4B4",
            "0xa0b86a33e6441e8e5c3f27d9c387b8b2c4b4b4b4",  # lowercase
            "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
        ]
        
        for address in valid_addresses:
            assert is_valid_ethereum_address(address), f"Adresse {address} devrait être valide"
    
    def test_is_valid_ethereum_address_invalid(self):
        """Test avec des adresses Ethereum invalides."""
        invalid_addresses = [
            "0x123",  # Trop courte
            "0x12345678901234567890123456789012345678901",  # Trop longue
            "1234567890123456789012345678901234567890",  # Pas de préfixe 0x
            "0xGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG",  # Caractères invalides
            "",  # Vide
            None,  # None
            "0x",  # Seulement le préfixe
        ]
        
        for address in invalid_addresses:
            assert not is_valid_ethereum_address(address), f"Adresse {address} devrait être invalide"
    
    @pytest.mark.asyncio
    async def test_is_valid_contract_address_mock(self):
        """Test de validation d'adresse de contrat avec mock."""
        with patch('app.utils.validators.web3') as mock_web3:
            # Mock pour un contrat valide
            mock_web3.eth.get_code.return_value = b'\x60\x80\x60\x40'  # Bytecode non vide
            
            result = await is_valid_contract_address("0x1234567890123456789012345678901234567890")
            assert result is True
            
            # Mock pour une adresse EOA (pas de contrat)
            mock_web3.eth.get_code.return_value = b''  # Bytecode vide
            
            result = await is_valid_contract_address("0x1234567890123456789012345678901234567890")
            assert result is False
    
    def test_validate_token_amount(self):
        """Test de validation des montants de tokens."""
        # Montants valides
        assert validate_token_amount(100) is True
        assert validate_token_amount(0.001) is True
        assert validate_token_amount(1000000) is True
        
        # Montants invalides
        assert validate_token_amount(-1) is False
        assert validate_token_amount(0) is False
        assert validate_token_amount(None) is False
        assert validate_token_amount("invalid") is False
    
    def test_validate_score(self):
        """Test de validation des scores."""
        # Scores valides
        assert validate_score(5.0) is True
        assert validate_score(0.0) is True
        assert validate_score(10.0) is True
        assert validate_score(7.5) is True
        
        # Scores invalides
        assert validate_score(-1.0) is False
        assert validate_score(11.0) is False
        assert validate_score(None) is False
        assert validate_score("invalid") is False
    
    def test_is_recent_token(self):
        """Test de vérification de récence des tokens."""
        now = datetime.utcnow()
        
        # Token récent (1 heure)
        recent_time = now - timedelta(hours=1)
        assert is_recent_token(recent_time) is True
        
        # Token ancien (25 heures)
        old_time = now - timedelta(hours=25)
        assert is_recent_token(old_time) is False
        
        # Token limite (24 heures exactement)
        limit_time = now - timedelta(hours=24)
        assert is_recent_token(limit_time) is True


class TestHelpers:
    """Tests pour le module helpers."""
    
    def test_sanitize_text(self):
        """Test de nettoyage de texte."""
        # Texte avec caractères spéciaux
        dirty_text = "Hello\n\tWorld!\r\x00\x01"
        clean_text = sanitize_text(dirty_text)
        assert clean_text == "Hello World!"
        
        # Texte avec emojis
        emoji_text = "🚀 Token to the moon! 🌙"
        clean_emoji = sanitize_text(emoji_text)
        assert "🚀" not in clean_emoji
        assert "🌙" not in clean_emoji
        
        # Texte vide
        assert sanitize_text("") == ""
        assert sanitize_text(None) == ""
    
    def test_format_number(self):
        """Test de formatage des nombres."""
        assert format_number(1234) == "1,234"
        assert format_number(1234567) == "1,234,567"
        assert format_number(1234.56) == "1,234.56"
        assert format_number(0) == "0"
        assert format_number(-1234) == "-1,234"
    
    def test_calculate_percentage_change(self):
        """Test de calcul de pourcentage de changement."""
        # Augmentation
        assert calculate_percentage_change(100, 150) == 50.0
        
        # Diminution
        assert calculate_percentage_change(150, 100) == -33.33
        
        # Pas de changement
        assert calculate_percentage_change(100, 100) == 0.0
        
        # Division par zéro
        assert calculate_percentage_change(0, 100) == 0.0
    
    def test_truncate_address(self):
        """Test de troncature d'adresse."""
        address = "0x1234567890123456789012345678901234567890"
        
        # Troncature par défaut
        truncated = truncate_address(address)
        assert truncated == "0x1234...7890"
        
        # Troncature personnalisée
        truncated_custom = truncate_address(address, start_chars=6, end_chars=6)
        assert truncated_custom == "0x1234...567890"
        
        # Adresse courte
        short_address = "0x1234"
        assert truncate_address(short_address) == short_address
    
    def test_create_progress_bar(self):
        """Test de création de barre de progression."""
        # Progression à 50%
        bar = create_progress_bar(50, 100)
        assert "50%" in bar
        assert "█" in bar
        assert "░" in bar
        
        # Progression complète
        bar_complete = create_progress_bar(100, 100)
        assert "100%" in bar_complete
        
        # Progression nulle
        bar_zero = create_progress_bar(0, 100)
        assert "0%" in bar_zero
    
    def test_safe_divide(self):
        """Test de division sécurisée."""
        # Division normale
        assert safe_divide(10, 2) == 5.0
        
        # Division par zéro
        assert safe_divide(10, 0) == 0.0
        assert safe_divide(10, 0, default=999) == 999
        
        # Division avec nombres décimaux
        assert safe_divide(7, 3) == pytest.approx(2.333, rel=1e-2)
    
    def test_parse_duration(self):
        """Test de parsing de durée."""
        # Secondes
        assert parse_duration("30s") == 30
        assert parse_duration("45") == 45  # Par défaut en secondes
        
        # Minutes
        assert parse_duration("5m") == 300
        
        # Heures
        assert parse_duration("2h") == 7200
        
        # Jours
        assert parse_duration("1d") == 86400
        
        # Format invalide
        assert parse_duration("invalid") == 0
        assert parse_duration("") == 0
    
    @pytest.mark.asyncio
    async def test_get_pending_analyses_count_mock(self):
        """Test de comptage des analyses en attente avec mock."""
        with patch('app.utils.helpers.DatabaseManager') as mock_db:
            # Mock du gestionnaire de base de données
            mock_db_instance = AsyncMock()
            mock_db.return_value = mock_db_instance
            mock_db_instance.count_pending_analyses.return_value = 5
            
            count = await get_pending_analyses_count()
            assert count == 5
            
            # Test avec erreur
            mock_db_instance.count_pending_analyses.side_effect = Exception("DB Error")
            count_error = await get_pending_analyses_count()
            assert count_error == 0


class TestWeb3Helpers:
    """Tests pour le module web3_helpers."""
    
    @pytest.mark.asyncio
    async def test_get_contract_info_mock(self):
        """Test de récupération d'informations de contrat avec mock."""
        with patch('app.utils.web3_helpers.web3') as mock_web3:
            # Mock des données de contrat
            mock_contract = Mock()
            mock_contract.functions.name.return_value.call.return_value = "Test Token"
            mock_contract.functions.symbol.return_value.call.return_value = "TEST"
            mock_contract.functions.decimals.return_value.call.return_value = 18
            mock_contract.functions.totalSupply.return_value.call.return_value = 1000000 * 10**18
            
            mock_web3.eth.contract.return_value = mock_contract
            
            info = await get_contract_info("0x1234567890123456789012345678901234567890")
            
            assert info is not None
            assert info["name"] == "Test Token"
            assert info["symbol"] == "TEST"
            assert info["decimals"] == 18
            assert info["total_supply"] == 1000000 * 10**18
    
    @pytest.mark.asyncio
    async def test_is_erc20_contract_mock(self):
        """Test de vérification ERC20 avec mock."""
        with patch('app.utils.web3_helpers.web3') as mock_web3:
            # Mock pour un contrat ERC20 valide
            mock_contract = Mock()
            mock_contract.functions.name.return_value.call.return_value = "Test Token"
            mock_contract.functions.symbol.return_value.call.return_value = "TEST"
            mock_contract.functions.decimals.return_value.call.return_value = 18
            
            mock_web3.eth.contract.return_value = mock_contract
            
            is_erc20 = await is_erc20_contract("0x1234567890123456789012345678901234567890")
            assert is_erc20 is True
            
            # Mock pour un contrat non-ERC20
            mock_contract.functions.name.return_value.call.side_effect = Exception("Not ERC20")
            
            is_erc20_invalid = await is_erc20_contract("0x1234567890123456789012345678901234567890")
            assert is_erc20_invalid is False
    
    @pytest.mark.asyncio
    async def test_get_token_metadata_mock(self):
        """Test de récupération de métadonnées avec mock."""
        with patch('app.utils.web3_helpers.get_contract_info') as mock_get_info:
            mock_get_info.return_value = {
                "name": "Test Token",
                "symbol": "TEST",
                "decimals": 18,
                "total_supply": 1000000 * 10**18
            }
            
            metadata = await get_token_metadata("0x1234567890123456789012345678901234567890")
            
            assert metadata is not None
            assert metadata["name"] == "Test Token"
            assert metadata["symbol"] == "TEST"
    
    def test_format_wei_to_ether(self):
        """Test de conversion Wei vers Ether."""
        # 1 Ether = 10^18 Wei
        assert format_wei_to_ether(10**18) == 1.0
        
        # 0.5 Ether
        assert format_wei_to_ether(5 * 10**17) == 0.5
        
        # 0 Wei
        assert format_wei_to_ether(0) == 0.0
        
        # Très petit montant
        assert format_wei_to_ether(1) == 1e-18
    
    @pytest.mark.asyncio
    async def test_estimate_gas_price_mock(self):
        """Test d'estimation du prix du gaz avec mock."""
        with patch('app.utils.web3_helpers.web3') as mock_web3:
            mock_web3.eth.gas_price = 20000000000  # 20 Gwei
            
            gas_price = await estimate_gas_price()
            assert gas_price == 20000000000
    
    @pytest.mark.asyncio
    async def test_get_transaction_receipt_mock(self):
        """Test de récupération de reçu de transaction avec mock."""
        with patch('app.utils.web3_helpers.web3') as mock_web3:
            # Mock du reçu de transaction
            mock_receipt = {
                'transactionHash': '0xabc123',
                'blockNumber': 12345,
                'gasUsed': 21000,
                'status': 1
            }
            
            mock_web3.eth.get_transaction_receipt.return_value = mock_receipt
            
            receipt = await get_transaction_receipt("0xabc123")
            
            assert receipt is not None
            assert receipt['transactionHash'] == '0xabc123'
            assert receipt['blockNumber'] == 12345
            assert receipt['status'] == 1


if __name__ == "__main__":
    # Exécuter les tests
    pytest.main([__file__, "-v"])