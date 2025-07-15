#!/usr/bin/env python3
"""
Crypto Sentinel - Ethereum WebSocket Listener

Écoute en temps réel les nouveaux contrats déployés sur Ethereum via WebSocket
(Alchemy ou Infura) et déclenche l'analyse des tokens ERC20 potentiels.

Author: Crypto Sentinel Team
Version: 1.0.0
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime

import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatusCode
from web3 import Web3
from web3.exceptions import ContractLogicError

from app.config import settings, ERC20_ABI
from app.models import TokenInfo, TokenSource, WebSocketMessage
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class EthereumWebSocketListener:
    """Écouteur WebSocket pour les nouveaux contrats Ethereum."""
    
    def __init__(self, token_scanner, gpt_analyzer, notifier, db):
        self.token_scanner = token_scanner
        self.gpt_analyzer = gpt_analyzer
        self.notifier = notifier
        self.db = db
        
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.web3: Optional[Web3] = None
        self.is_running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = settings.MAX_RECONNECT_ATTEMPTS
        self.reconnect_delay = settings.WEBSOCKET_RECONNECT_DELAY
        
        # Statistiques
        self.messages_received = 0
        self.contracts_detected = 0
        self.tokens_processed = 0
        self.last_block_number = 0
        self.start_time = datetime.utcnow()
        
        # Initialisation Web3 pour les appels HTTP
        self._init_web3()
    
    def _init_web3(self):
        """Initialise la connexion Web3 HTTP."""
        try:
            self.web3 = Web3(Web3.HTTPProvider(settings.ethereum_http_url))
            if self.web3.is_connected():
                logger.info("🌐 Connexion Web3 HTTP établie")
            else:
                logger.error("❌ Impossible de se connecter à Web3 HTTP")
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation Web3: {e}")
    
    async def start(self):
        """Démarre l'écoute WebSocket avec reconnexion automatique."""
        self.is_running = True
        logger.info("🚀 Démarrage de l'écouteur WebSocket Ethereum...")
        
        while self.is_running:
            try:
                await self._connect_and_listen()
            except Exception as e:
                logger.error(f"Erreur dans l'écouteur WebSocket: {e}")
                
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    self.reconnect_attempts += 1
                    wait_time = self.reconnect_delay * self.reconnect_attempts
                    logger.info(f"🔄 Tentative de reconnexion {self.reconnect_attempts}/{self.max_reconnect_attempts} dans {wait_time}s")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("❌ Nombre maximum de tentatives de reconnexion atteint")
                    break
    
    async def stop(self):
        """Arrête l'écoute WebSocket."""
        self.is_running = False
        if self.websocket:
            await self.websocket.close()
        logger.info("🛑 Écouteur WebSocket arrêté")
    
    def is_connected(self) -> bool:
        """Vérifie si le WebSocket est connecté."""
        return self.websocket is not None and not self.websocket.closed
    
    async def _connect_and_listen(self):
        """Établit la connexion WebSocket et écoute les messages."""
        try:
            logger.info(f"🔌 Connexion au WebSocket: {settings.ethereum_websocket_url}")
            
            async with websockets.connect(
                settings.ethereum_websocket_url,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=10
            ) as websocket:
                self.websocket = websocket
                self.reconnect_attempts = 0
                
                # Souscription aux nouveaux blocs
                await self._subscribe_to_new_blocks()
                
                # Souscription aux transactions en attente (optionnel)
                if settings.DEBUG:
                    await self._subscribe_to_pending_transactions()
                
                logger.info("✅ WebSocket connecté et souscriptions actives")
                
                # Écoute des messages
                async for message in websocket:
                    await self._handle_message(message)
                    
        except ConnectionClosed:
            logger.warning("🔌 Connexion WebSocket fermée")
        except InvalidStatusCode as e:
            logger.error(f"❌ Code de statut WebSocket invalide: {e}")
        except Exception as e:
            logger.error(f"❌ Erreur WebSocket: {e}")
            raise
    
    async def _subscribe_to_new_blocks(self):
        """Souscrit aux nouveaux blocs pour détecter les contrats."""
        subscription = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_subscribe",
            "params": ["newHeads"]
        }
        
        await self.websocket.send(json.dumps(subscription))
        logger.info("📦 Souscription aux nouveaux blocs activée")
    
    async def _subscribe_to_pending_transactions(self):
        """Souscrit aux transactions en attente (mode debug)."""
        subscription = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "eth_subscribe",
            "params": ["newPendingTransactions"]
        }
        
        await self.websocket.send(json.dumps(subscription))
        logger.info("⏳ Souscription aux transactions en attente activée")
    
    async def _handle_message(self, message: str):
        """Traite un message WebSocket reçu."""
        try:
            self.messages_received += 1
            data = json.loads(message)
            
            # Ignorer les messages de confirmation de souscription
            if "result" in data and isinstance(data.get("result"), str):
                logger.debug(f"Souscription confirmée: {data['result']}")
                return
            
            # Traiter les notifications
            if "params" in data and "result" in data["params"]:
                await self._process_notification(data["params"]["result"])
                
        except json.JSONDecodeError:
            logger.error(f"Message JSON invalide: {message[:100]}...")
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {e}")
    
    async def _process_notification(self, result: Dict[str, Any]):
        """Traite une notification de nouveau bloc ou transaction."""
        try:
            # Nouveau bloc
            if "number" in result:
                await self._process_new_block(result)
            
            # Transaction en attente (si activé)
            elif isinstance(result, str) and result.startswith("0x"):
                await self._process_pending_transaction(result)
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la notification: {e}")
    
    async def _process_new_block(self, block_data: Dict[str, Any]):
        """Traite un nouveau bloc pour détecter les contrats."""
        try:
            block_number = int(block_data["number"], 16)
            self.last_block_number = block_number
            
            logger.debug(f"📦 Nouveau bloc: {block_number}")
            
            # Récupérer les détails du bloc avec les transactions
            block_details = await self._get_block_with_transactions(block_number)
            
            if block_details and "transactions" in block_details:
                await self._scan_block_transactions(block_details["transactions"])
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du bloc: {e}")
    
    async def _process_pending_transaction(self, tx_hash: str):
        """Traite une transaction en attente (mode debug uniquement)."""
        try:
            if not settings.DEBUG:
                return
            
            # Récupérer les détails de la transaction
            tx_details = await self._get_transaction_details(tx_hash)
            
            if tx_details and self._is_contract_creation(tx_details):
                logger.debug(f"🔍 Transaction de création de contrat détectée: {tx_hash}")
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement de la transaction en attente: {e}")
    
    async def _get_block_with_transactions(self, block_number: int) -> Optional[Dict[str, Any]]:
        """Récupère un bloc avec ses transactions."""
        try:
            if not self.web3:
                return None
            
            block = self.web3.eth.get_block(block_number, full_transactions=True)
            return dict(block)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du bloc {block_number}: {e}")
            return None
    
    async def _get_transaction_details(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Récupère les détails d'une transaction."""
        try:
            if not self.web3:
                return None
            
            tx = self.web3.eth.get_transaction(tx_hash)
            return dict(tx)
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la transaction {tx_hash}: {e}")
            return None
    
    async def _scan_block_transactions(self, transactions: list):
        """Scanne les transactions d'un bloc pour détecter les créations de contrats."""
        contract_creations = []
        
        for tx in transactions:
            if self._is_contract_creation(tx):
                contract_creations.append(tx)
        
        if contract_creations:
            logger.info(f"🏭 {len(contract_creations)} création(s) de contrat détectée(s)")
            
            # Traiter les créations de contrats en parallèle (limité)
            semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_ANALYSES)
            tasks = [
                self._process_contract_creation(tx, semaphore)
                for tx in contract_creations
            ]
            
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def _is_contract_creation(self, transaction: Dict[str, Any]) -> bool:
        """Vérifie si une transaction est une création de contrat."""
        return (
            transaction.get("to") is None and
            transaction.get("input") is not None and
            len(transaction.get("input", "")) > 2
        )
    
    async def _process_contract_creation(self, transaction: Dict[str, Any], semaphore: asyncio.Semaphore):
        """Traite une création de contrat potentielle."""
        async with semaphore:
            try:
                self.contracts_detected += 1
                tx_hash = transaction["hash"].hex() if hasattr(transaction["hash"], 'hex') else transaction["hash"]
                
                logger.debug(f"🔍 Analyse de la création de contrat: {tx_hash}")
                
                # Attendre que la transaction soit minée
                await asyncio.sleep(2)
                
                # Récupérer le reçu de transaction pour obtenir l'adresse du contrat
                receipt = await self._get_transaction_receipt(tx_hash)
                
                if receipt and receipt.get("contractAddress"):
                    contract_address = receipt["contractAddress"]
                    
                    # Vérifier si c'est un token ERC20
                    if await self._is_erc20_token(contract_address):
                        await self._handle_new_erc20_token(contract_address, transaction)
                        
            except Exception as e:
                logger.error(f"Erreur lors du traitement de la création de contrat: {e}")
    
    async def _get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """Récupère le reçu d'une transaction."""
        try:
            if not self.web3:
                return None
            
            receipt = self.web3.eth.get_transaction_receipt(tx_hash)
            return dict(receipt)
            
        except Exception as e:
            logger.debug(f"Reçu de transaction non disponible pour {tx_hash}: {e}")
            return None
    
    async def _is_erc20_token(self, contract_address: str) -> bool:
        """Vérifie si un contrat est un token ERC20."""
        try:
            if not self.web3:
                return False
            
            contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(contract_address),
                abi=ERC20_ABI
            )
            
            # Tenter d'appeler les fonctions ERC20 de base
            try:
                name = contract.functions.name().call()
                symbol = contract.functions.symbol().call()
                decimals = contract.functions.decimals().call()
                total_supply = contract.functions.totalSupply().call()
                
                # Vérifications de base
                return (
                    isinstance(name, str) and len(name) > 0 and
                    isinstance(symbol, str) and len(symbol) > 0 and
                    isinstance(decimals, int) and 0 <= decimals <= 18 and
                    isinstance(total_supply, int) and total_supply > 0
                )
                
            except ContractLogicError:
                return False
                
        except Exception as e:
            logger.debug(f"Erreur lors de la vérification ERC20 pour {contract_address}: {e}")
            return False
    
    async def _handle_new_erc20_token(self, contract_address: str, transaction: Dict[str, Any]):
        """Traite un nouveau token ERC20 détecté."""
        try:
            self.tokens_processed += 1
            
            logger.info(f"🪙 Nouveau token ERC20 détecté: {contract_address}")
            
            # Vérifier si le token existe déjà
            if await self.db.token_exists(contract_address):
                logger.debug(f"Token déjà en base: {contract_address}")
                return
            
            # Créer les informations de base du token
            token_info = TokenInfo(
                contract_address=contract_address,
                source=TokenSource.ETHEREUM_WEBSOCKET,
                creation_block=transaction.get("blockNumber"),
                creation_timestamp=datetime.utcnow()
            )
            
            # Lancer l'analyse complète en arrière-plan
            asyncio.create_task(self._analyze_token_async(token_info))
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du nouveau token {contract_address}: {e}")
    
    async def _analyze_token_async(self, token_info: TokenInfo):
        """Analyse complète d'un token en arrière-plan."""
        try:
            # Scanner le token pour récupérer toutes les informations
            complete_token_info = await self.token_scanner.scan_token(token_info.contract_address)
            
            if complete_token_info:
                # Mise à jour avec les informations complètes
                complete_token_info.source = token_info.source
                complete_token_info.creation_block = token_info.creation_block
                complete_token_info.creation_timestamp = token_info.creation_timestamp
                
                # Analyse IA
                analysis = await self.gpt_analyzer.analyze_token(complete_token_info)
                
                # Sauvegarde en base
                await self.db.save_token_analysis(analysis)
                
                # Notification si score élevé
                if analysis.ai_score >= settings.MIN_NOTIFICATION_SCORE:
                    await self.notifier.send_alert(analysis)
                
                logger.info(f"✅ Analyse terminée pour {token_info.contract_address} - Score: {analysis.ai_score}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse async de {token_info.contract_address}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques de l'écouteur."""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        return {
            "is_connected": self.is_connected(),
            "is_running": self.is_running,
            "uptime_seconds": uptime,
            "messages_received": self.messages_received,
            "contracts_detected": self.contracts_detected,
            "tokens_processed": self.tokens_processed,
            "last_block_number": self.last_block_number,
            "reconnect_attempts": self.reconnect_attempts,
            "messages_per_minute": round((self.messages_received / uptime) * 60, 2) if uptime > 0 else 0
        }