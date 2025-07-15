#!/usr/bin/env python3
"""
Crypto Sentinel - Web3 Helpers

Utilitaires pour l'interaction avec la blockchain Ethereum via Web3.
"""

import asyncio
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime

from web3 import Web3
from web3.exceptions import ContractLogicError, TransactionNotFound
from eth_account import Account
from app.utils.logger import setup_logger
from app.utils.validators import is_valid_ethereum_address

logger = setup_logger(__name__)

# ABI pour les contrats ERC20 standard
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"},
            {"name": "_spender", "type": "address"}
        ],
        "name": "allowance",
        "outputs": [{"name": "remaining", "type": "uint256"}],
        "type": "function"
    }
]

# ABI pour récupérer le créateur d'un contrat
CONTRACT_CREATION_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "owner",
        "outputs": [{"name": "", "type": "address"}],
        "type": "function"
    }
]


class Web3Helper:
    """Classe utilitaire pour les interactions Web3."""
    
    def __init__(self, web3_provider: Web3):
        self.w3 = web3_provider
        self.logger = setup_logger(__name__)
    
    async def get_token_info(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """Récupère les informations de base d'un token ERC20."""
        if not is_valid_ethereum_address(contract_address):
            return None
        
        try:
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=ERC20_ABI
            )
            
            # Récupérer les informations de base
            name = await self._safe_contract_call(contract.functions.name)
            symbol = await self._safe_contract_call(contract.functions.symbol)
            decimals = await self._safe_contract_call(contract.functions.decimals)
            total_supply = await self._safe_contract_call(contract.functions.totalSupply)
            
            if name is None or symbol is None or decimals is None:
                return None
            
            return {
                'name': name,
                'symbol': symbol,
                'decimals': decimals,
                'total_supply': total_supply,
                'contract_address': contract_address
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des infos token {contract_address}: {e}")
            return None
    
    async def get_token_balance(self, contract_address: str, wallet_address: str) -> Optional[int]:
        """Récupère le solde d'un token pour une adresse donnée."""
        if not is_valid_ethereum_address(contract_address) or not is_valid_ethereum_address(wallet_address):
            return None
        
        try:
            contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=ERC20_ABI
            )
            
            balance = await self._safe_contract_call(
                contract.functions.balanceOf,
                Web3.to_checksum_address(wallet_address)
            )
            
            return balance
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du solde: {e}")
            return None
    
    async def get_contract_creation_info(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """Récupère les informations de création d'un contrat."""
        if not is_valid_ethereum_address(contract_address):
            return None
        
        try:
            # Récupérer le code du contrat
            code = self.w3.eth.get_code(Web3.to_checksum_address(contract_address))
            
            if code == b'':
                self.logger.warning(f"Aucun code trouvé pour le contrat {contract_address}")
                return None
            
            # Essayer de trouver la transaction de création
            creation_info = await self._find_contract_creation_tx(contract_address)
            
            return {
                'contract_address': contract_address,
                'has_code': len(code) > 0,
                'code_size': len(code),
                'creation_info': creation_info
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des infos de création: {e}")
            return None
    
    async def _find_contract_creation_tx(self, contract_address: str) -> Optional[Dict[str, Any]]:
        """Trouve la transaction de création d'un contrat (méthode simplifiée)."""
        try:
            # Cette méthode est simplifiée car trouver la transaction de création
            # nécessite généralement un indexeur ou une recherche extensive
            
            # Pour l'instant, on retourne les informations de base disponibles
            latest_block = self.w3.eth.get_block('latest')
            
            return {
                'found': False,
                'method': 'simplified',
                'latest_block': latest_block.number,
                'note': 'Recherche complète nécessite un indexeur'
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la recherche de la tx de création: {e}")
            return None
    
    async def get_transaction_info(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Récupère les informations d'une transaction."""
        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            tx_receipt = self.w3.eth.get_transaction_receipt(tx_hash)
            
            return {
                'hash': tx_hash,
                'from': tx['from'],
                'to': tx['to'],
                'value': tx['value'],
                'gas': tx['gas'],
                'gas_price': tx['gasPrice'],
                'gas_used': tx_receipt['gasUsed'],
                'status': tx_receipt['status'],
                'block_number': tx_receipt['blockNumber'],
                'block_hash': tx_receipt['blockHash'],
                'transaction_index': tx_receipt['transactionIndex']
            }
            
        except TransactionNotFound:
            self.logger.warning(f"Transaction non trouvée: {tx_hash}")
            return None
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération de la transaction: {e}")
            return None
    
    async def get_block_info(self, block_identifier) -> Optional[Dict[str, Any]]:
        """Récupère les informations d'un bloc."""
        try:
            block = self.w3.eth.get_block(block_identifier, full_transactions=False)
            
            return {
                'number': block.number,
                'hash': block.hash.hex(),
                'timestamp': block.timestamp,
                'datetime': datetime.fromtimestamp(block.timestamp),
                'gas_limit': block.gasLimit,
                'gas_used': block.gasUsed,
                'transaction_count': len(block.transactions),
                'miner': block.miner,
                'difficulty': block.difficulty,
                'size': block.size
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du bloc: {e}")
            return None
    
    async def estimate_gas(self, transaction: Dict[str, Any]) -> Optional[int]:
        """Estime le gas nécessaire pour une transaction."""
        try:
            gas_estimate = self.w3.eth.estimate_gas(transaction)
            return gas_estimate
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'estimation du gas: {e}")
            return None
    
    async def get_gas_price(self) -> Optional[int]:
        """Récupère le prix du gas actuel."""
        try:
            gas_price = self.w3.eth.gas_price
            return gas_price
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du prix du gas: {e}")
            return None
    
    async def get_eth_balance(self, address: str) -> Optional[int]:
        """Récupère le solde ETH d'une adresse."""
        if not is_valid_ethereum_address(address):
            return None
        
        try:
            balance = self.w3.eth.get_balance(Web3.to_checksum_address(address))
            return balance
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du solde ETH: {e}")
            return None
    
    async def _safe_contract_call(self, contract_function, *args):
        """Effectue un appel de contrat sécurisé."""
        try:
            if args:
                result = contract_function(*args).call()
            else:
                result = contract_function().call()
            return result
            
        except ContractLogicError as e:
            self.logger.warning(f"Erreur logique du contrat: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Erreur lors de l'appel du contrat: {e}")
            return None
    
    def is_contract(self, address: str) -> bool:
        """Vérifie si une adresse est un contrat."""
        if not is_valid_ethereum_address(address):
            return False
        
        try:
            code = self.w3.eth.get_code(Web3.to_checksum_address(address))
            return len(code) > 0
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification du contrat: {e}")
            return False
    
    def to_wei(self, amount: float, unit: str = 'ether') -> int:
        """Convertit un montant en wei."""
        try:
            return self.w3.to_wei(amount, unit)
        except Exception as e:
            self.logger.error(f"Erreur lors de la conversion en wei: {e}")
            return 0
    
    def from_wei(self, amount: int, unit: str = 'ether') -> float:
        """Convertit un montant depuis wei."""
        try:
            return float(self.w3.from_wei(amount, unit))
        except Exception as e:
            self.logger.error(f"Erreur lors de la conversion depuis wei: {e}")
            return 0.0
    
    def format_token_amount(self, amount: int, decimals: int) -> float:
        """Formate un montant de token avec ses décimales."""
        try:
            return float(amount) / (10 ** decimals)
        except Exception as e:
            self.logger.error(f"Erreur lors du formatage du montant: {e}")
            return 0.0
    
    async def get_latest_block_number(self) -> Optional[int]:
        """Récupère le numéro du dernier bloc."""
        try:
            return self.w3.eth.block_number
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération du dernier bloc: {e}")
            return None
    
    def is_connected(self) -> bool:
        """Vérifie si la connexion Web3 est active."""
        try:
            return self.w3.is_connected()
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification de la connexion: {e}")
            return False


def create_web3_instance(provider_url: str) -> Optional[Web3]:
    """Crée une instance Web3 avec le provider donné."""
    try:
        if provider_url.startswith('ws'):
            from web3 import WebsocketProvider
            provider = WebsocketProvider(provider_url)
        else:
            from web3 import HTTPProvider
            provider = HTTPProvider(provider_url)
        
        w3 = Web3(provider)
        
        if w3.is_connected():
            logger.info(f"✅ Connexion Web3 établie: {provider_url}")
            return w3
        else:
            logger.error(f"❌ Impossible de se connecter à: {provider_url}")
            return None
            
    except Exception as e:
        logger.error(f"Erreur lors de la création de l'instance Web3: {e}")
        return None


def get_checksum_address(address: str) -> Optional[str]:
    """Convertit une adresse en format checksum."""
    try:
        if is_valid_ethereum_address(address):
            return Web3.to_checksum_address(address)
        return None
    except Exception as e:
        logger.error(f"Erreur lors de la conversion en checksum: {e}")
        return None


def generate_random_wallet() -> Dict[str, str]:
    """Génère un wallet Ethereum aléatoire (pour les tests)."""
    try:
        account = Account.create()
        return {
            'address': account.address,
            'private_key': account.key.hex(),
            'public_key': account._key_obj.public_key.to_hex()
        }
    except Exception as e:
        logger.error(f"Erreur lors de la génération du wallet: {e}")
        return {}


async def batch_contract_calls(web3_helper: Web3Helper, calls: List[Dict[str, Any]]) -> List[Any]:
    """Effectue plusieurs appels de contrat en parallèle."""
    tasks = []
    
    for call in calls:
        contract_address = call.get('contract_address')
        function_name = call.get('function')
        args = call.get('args', [])
        
        if contract_address and function_name:
            task = web3_helper.get_token_info(contract_address)
            tasks.append(task)
    
    try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    except Exception as e:
        logger.error(f"Erreur lors des appels batch: {e}")
        return []