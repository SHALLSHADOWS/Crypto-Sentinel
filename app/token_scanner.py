"""Token Scanner Service for Crypto Sentinel.

This service handles:
- ERC20 token information retrieval (name, symbol, decimals, supply)
- Market data collection (price, liquidity, volume)
- Holder analysis and distribution
- Token age and deployment information
- Integration with multiple data sources
"""

import asyncio
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx
from web3 import Web3
from web3.exceptions import ContractLogicError, BadFunctionCallOutput
from eth_utils import to_checksum_address

from .config import get_settings
from .models import TokenInfo, SocialMetrics
from .utils.logger import get_logger
from .utils.validators import is_valid_ethereum_address, validate_token_metadata

# ERC20 ABI for basic token functions
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
    }
]

@dataclass
class MarketData:
    """Market data for a token."""
    price_usd: float = 0.0
    market_cap: float = 0.0
    liquidity_usd: float = 0.0
    volume_24h: float = 0.0
    price_change_24h: float = 0.0
    holders_count: int = 0
    transactions_24h: int = 0
    
class TokenScannerService:
    """Service for scanning and analyzing ERC20 tokens."""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger("token_scanner")
        self.web3 = None
        self.http_client = None
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes
        self.stats = {
            "tokens_scanned": 0,
            "successful_scans": 0,
            "failed_scans": 0,
            "cache_hits": 0,
            "api_calls": 0
        }
        
    async def initialize(self) -> bool:
        """Initialize the token scanner service.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Initialize Web3 connection
            if self.settings.ethereum_rpc_url:
                self.web3 = Web3(Web3.HTTPProvider(self.settings.ethereum_rpc_url))
                
                if not self.web3.is_connected():
                    self.logger.error("Failed to connect to Ethereum RPC")
                    return False
                    
                self.logger.info(f"Connected to Ethereum RPC: {self.settings.ethereum_rpc_url}")
            else:
                self.logger.error("Ethereum RPC URL not configured")
                return False
            
            # Initialize HTTP client
            self.http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
            )
            
            self.logger.info("✅ Token Scanner Service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Token Scanner Service: {e}")
            return False
    
    async def shutdown(self):
        """Shutdown the service and cleanup resources."""
        if self.http_client:
            await self.http_client.aclose()
        self.logger.info("Token Scanner Service shutdown complete")
    
    def _get_cache_key(self, token_address: str, data_type: str) -> str:
        """Generate cache key for token data."""
        return f"{token_address.lower()}_{data_type}"
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid."""
        return time.time() - cache_entry.get("timestamp", 0) < self._cache_ttl
    
    def _get_from_cache(self, token_address: str, data_type: str) -> Optional[Any]:
        """Get data from cache if valid."""
        cache_key = self._get_cache_key(token_address, data_type)
        cache_entry = self._cache.get(cache_key)
        
        if cache_entry and self._is_cache_valid(cache_entry):
            self.stats["cache_hits"] += 1
            return cache_entry["data"]
        
        return None
    
    def _set_cache(self, token_address: str, data_type: str, data: Any):
        """Set data in cache."""
        cache_key = self._get_cache_key(token_address, data_type)
        self._cache[cache_key] = {
            "data": data,
            "timestamp": time.time()
        }
    
    async def get_token_basic_info(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get basic ERC20 token information from blockchain.
        
        Args:
            token_address: Ethereum address of the token contract
            
        Returns:
            Dictionary with basic token info or None if failed
        """
        if not is_valid_ethereum_address(token_address):
            self.logger.error(f"Invalid token address: {token_address}")
            return None
        
        # Check cache first
        cached_data = self._get_from_cache(token_address, "basic_info")
        if cached_data:
            return cached_data
        
        try:
            checksum_address = to_checksum_address(token_address)
            contract = self.web3.eth.contract(address=checksum_address, abi=ERC20_ABI)
            
            # Get basic token information
            name = "Unknown"
            symbol = "UNKNOWN"
            decimals = 18
            total_supply = 0
            
            try:
                name = contract.functions.name().call()
            except (ContractLogicError, BadFunctionCallOutput, Exception):
                self.logger.warning(f"Could not get name for token {token_address}")
            
            try:
                symbol = contract.functions.symbol().call()
            except (ContractLogicError, BadFunctionCallOutput, Exception):
                self.logger.warning(f"Could not get symbol for token {token_address}")
            
            try:
                decimals = contract.functions.decimals().call()
            except (ContractLogicError, BadFunctionCallOutput, Exception):
                self.logger.warning(f"Could not get decimals for token {token_address}")
            
            try:
                total_supply = contract.functions.totalSupply().call()
            except (ContractLogicError, BadFunctionCallOutput, Exception):
                self.logger.warning(f"Could not get total supply for token {token_address}")
            
            # Get deployment block (approximate age)
            deployment_block = await self._get_deployment_block(checksum_address)
            
            basic_info = {
                "address": checksum_address,
                "name": name,
                "symbol": symbol,
                "decimals": decimals,
                "total_supply": total_supply,
                "deployment_block": deployment_block,
                "scanned_at": datetime.utcnow().isoformat()
            }
            
            # Cache the result
            self._set_cache(token_address, "basic_info", basic_info)
            
            self.logger.info(f"Retrieved basic info for token {symbol} ({checksum_address})")
            return basic_info
            
        except Exception as e:
            self.logger.error(f"Error getting basic info for token {token_address}: {e}")
            return None
    
    async def _get_deployment_block(self, token_address: str) -> Optional[int]:
        """Get the deployment block number for a contract.
        
        Args:
            token_address: Contract address
            
        Returns:
            Block number or None if not found
        """
        try:
            # Binary search to find deployment block
            latest_block = self.web3.eth.block_number
            start_block = max(0, latest_block - 100000)  # Search last ~2 weeks
            
            # Simple approach: check if contract exists at different blocks
            for block_num in range(latest_block, start_block, -1000):
                try:
                    code = self.web3.eth.get_code(token_address, block_identifier=block_num)
                    if len(code) == 0:
                        # Contract doesn't exist at this block, deployment is after
                        return block_num + 1000  # Approximate
                except Exception:
                    continue
            
            return start_block  # Fallback
            
        except Exception as e:
            self.logger.warning(f"Could not determine deployment block for {token_address}: {e}")
            return None
    
    async def get_market_data(self, token_address: str) -> Optional[MarketData]:
        """Get market data for a token from various sources.
        
        Args:
            token_address: Token contract address
            
        Returns:
            MarketData object or None if failed
        """
        # Check cache first
        cached_data = self._get_from_cache(token_address, "market_data")
        if cached_data:
            return MarketData(**cached_data)
        
        market_data = MarketData()
        
        # Try multiple data sources
        sources = [
            self._get_dexscreener_data,
            self._get_coingecko_data,
            self._get_etherscan_data
        ]
        
        for source in sources:
            try:
                data = await source(token_address)
                if data:
                    # Merge data (prioritize first successful source)
                    for key, value in data.items():
                        if hasattr(market_data, key) and value is not None:
                            setattr(market_data, key, value)
                    break
            except Exception as e:
                self.logger.warning(f"Failed to get data from {source.__name__}: {e}")
                continue
        
        # Cache the result
        market_data_dict = market_data.__dict__
        self._set_cache(token_address, "market_data", market_data_dict)
        
        return market_data
    
    async def _get_dexscreener_data(self, token_address: str) -> Optional[Dict]:
        """Get market data from Dexscreener API."""
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
            
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            data = response.json()
            pairs = data.get("pairs", [])
            
            if not pairs:
                return None
            
            # Get the pair with highest liquidity
            best_pair = max(pairs, key=lambda p: float(p.get("liquidity", {}).get("usd", 0)))
            
            return {
                "price_usd": float(best_pair.get("priceUsd", 0)),
                "liquidity_usd": float(best_pair.get("liquidity", {}).get("usd", 0)),
                "volume_24h": float(best_pair.get("volume", {}).get("h24", 0)),
                "price_change_24h": float(best_pair.get("priceChange", {}).get("h24", 0)),
                "transactions_24h": int(best_pair.get("txns", {}).get("h24", {}).get("buys", 0) + 
                                       best_pair.get("txns", {}).get("h24", {}).get("sells", 0))
            }
            
        except Exception as e:
            self.logger.warning(f"Dexscreener API error for {token_address}: {e}")
            return None
    
    async def _get_coingecko_data(self, token_address: str) -> Optional[Dict]:
        """Get market data from CoinGecko API."""
        try:
            # Note: CoinGecko requires token to be listed
            url = f"https://api.coingecko.com/api/v3/coins/ethereum/contract/{token_address}"
            
            response = await self.http_client.get(url)
            if response.status_code == 404:
                return None  # Token not listed on CoinGecko
            
            response.raise_for_status()
            data = response.json()
            
            market_data = data.get("market_data", {})
            
            return {
                "price_usd": float(market_data.get("current_price", {}).get("usd", 0)),
                "market_cap": float(market_data.get("market_cap", {}).get("usd", 0)),
                "volume_24h": float(market_data.get("total_volume", {}).get("usd", 0)),
                "price_change_24h": float(market_data.get("price_change_percentage_24h", 0))
            }
            
        except Exception as e:
            self.logger.warning(f"CoinGecko API error for {token_address}: {e}")
            return None
    
    async def _get_etherscan_data(self, token_address: str) -> Optional[Dict]:
        """Get basic data from Etherscan API."""
        try:
            # This would require Etherscan API key and specific endpoints
            # For now, return None as placeholder
            return None
            
        except Exception as e:
            self.logger.warning(f"Etherscan API error for {token_address}: {e}")
            return None
    
    async def get_holder_analysis(self, token_address: str) -> Dict[str, Any]:
        """Analyze token holder distribution.
        
        Args:
            token_address: Token contract address
            
        Returns:
            Dictionary with holder analysis data
        """
        # Check cache first
        cached_data = self._get_from_cache(token_address, "holder_analysis")
        if cached_data:
            return cached_data
        
        try:
            # This is a simplified version - in production, you'd want to:
            # 1. Query blockchain for Transfer events
            # 2. Build holder list from events
            # 3. Analyze distribution patterns
            
            # For now, return basic structure
            holder_analysis = {
                "total_holders": 0,
                "top_10_percentage": 0.0,
                "whale_count": 0,
                "distribution_score": 0.0,
                "analyzed_at": datetime.utcnow().isoformat()
            }
            
            # Cache the result
            self._set_cache(token_address, "holder_analysis", holder_analysis)
            
            return holder_analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing holders for {token_address}: {e}")
            return {}
    
    async def scan_token(self, token_address: str) -> Optional[TokenInfo]:
        """Perform complete token scan and return TokenInfo object.
        
        Args:
            token_address: Token contract address
            
        Returns:
            TokenInfo object or None if scan failed
        """
        start_time = time.time()
        self.stats["tokens_scanned"] += 1
        
        try:
            self.logger.info(f"Starting complete scan for token: {token_address}")
            
            # Get basic token information
            basic_info = await self.get_token_basic_info(token_address)
            if not basic_info:
                self.stats["failed_scans"] += 1
                return None
            
            # Validate metadata
            is_valid, errors = validate_token_metadata(
                basic_info["name"],
                basic_info["symbol"],
                basic_info["decimals"]
            )
            
            if not is_valid:
                self.logger.warning(f"Invalid token metadata for {token_address}: {errors}")
            
            # Get market data
            market_data = await self.get_market_data(token_address)
            
            # Get holder analysis
            holder_analysis = await self.get_holder_analysis(token_address)
            
            # Calculate token age
            token_age_hours = 0
            if basic_info.get("deployment_block"):
                current_block = self.web3.eth.block_number
                blocks_diff = current_block - basic_info["deployment_block"]
                token_age_hours = blocks_diff * 12 / 3600  # ~12 seconds per block
            
            # Create TokenInfo object
            token_info = TokenInfo(
                contract_address=basic_info["address"],
                name=basic_info["name"],
                symbol=basic_info["symbol"],
                decimals=basic_info["decimals"],
                total_supply=basic_info["total_supply"],
                price_usd=market_data.price_usd if market_data else 0.0,
                market_cap_usd=market_data.market_cap if market_data else 0.0,
                liquidity_usd=market_data.liquidity_usd if market_data else 0.0,
                volume_24h_usd=market_data.volume_24h if market_data else 0.0,
                holders_count=holder_analysis.get("total_holders", 0),
                deployment_block=basic_info.get("deployment_block"),
                created_at=datetime.utcnow()
            )
            
            scan_duration = time.time() - start_time
            self.stats["successful_scans"] += 1
            
            self.logger.info(
                f"✅ Token scan completed for {token_info.symbol} in {scan_duration:.2f}s"
            )
            
            return token_info
            
        except Exception as e:
            self.stats["failed_scans"] += 1
            scan_duration = time.time() - start_time
            
            self.logger.error(
                f"❌ Token scan failed for {token_address} after {scan_duration:.2f}s: {e}"
            )
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics.
        
        Returns:
            Dictionary with service statistics
        """
        return {
            **self.stats,
            "cache_size": len(self._cache),
            "success_rate": (
                self.stats["successful_scans"] / max(self.stats["tokens_scanned"], 1) * 100
            )
        }
    
    def clear_cache(self):
        """Clear the internal cache."""
        self._cache.clear()
        self.logger.info("Token scanner cache cleared")

# Example usage
if __name__ == "__main__":
    async def test_scanner():
        scanner = TokenScannerService()
        
        if await scanner.initialize():
            # Test with a known token (USDC)
            usdc_address = "0xA0b86a33E6441e8e5c3F27d9C387b8B2C4b4B8B2"
            token_info = await scanner.scan_token(usdc_address)
            
            if token_info:
                print(f"Token: {token_info.name} ({token_info.symbol})")
                print(f"Price: ${token_info.price_usd}")
                print(f"Liquidity: ${token_info.liquidity_usd:,.2f}")
            
            print(f"Scanner stats: {scanner.get_stats()}")
            
        await scanner.shutdown()
    
    asyncio.run(test_scanner())