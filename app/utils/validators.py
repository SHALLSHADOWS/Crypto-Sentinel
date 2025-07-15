"""Validation utilities for Crypto Sentinel.

This module provides comprehensive validation functions for:
- Ethereum addresses and transaction hashes
- Token name sanitization and suspicious pattern detection
- Input validation for various blockchain-related data
"""

import re
from typing import List, Optional, Tuple
from web3 import Web3
from eth_utils import is_address, is_hex

# Suspicious patterns for token names and symbols
SUSPICIOUS_PATTERNS = [
    # Common scam keywords
    r'(?i)\b(elon|musk|tesla|spacex|doge|shib|pepe)\b',
    r'(?i)\b(moon|rocket|lambo|diamond|hands)\b',
    r'(?i)\b(safe|baby|mini|micro|nano)\b',
    r'(?i)\b(inu|coin|token|finance|swap)\b',
    r'(?i)\b(pump|dump|scam|rug|pull)\b',
    
    # Unicode and special characters abuse
    r'[\u200b-\u200f\u2060-\u206f]',  # Zero-width characters
    r'[\u0300-\u036f]',  # Combining diacritical marks
    r'[\u2000-\u206f]',  # General punctuation
    
    # Excessive repetition
    r'(.)\1{4,}',  # Same character repeated 5+ times
    r'\b(\w+)\s+\1\b',  # Repeated words
    
    # Common impersonation attempts
    r'(?i)\b(uniswap|pancake|sushi|compound|aave|maker)\b',
    r'(?i)\b(bitcoin|ethereum|binance|coinbase|kraken)\b',
    
    # Suspicious number patterns
    r'\d{10,}',  # Very long numbers
    r'\b(420|69|1337|9999)\b',  # Meme numbers
    
    # Marketing buzzwords
    r'(?i)\b(revolutionary|innovative|disruptive|game.?changer)\b',
    r'(?i)\b(guaranteed|profit|returns|investment)\b',
    r'(?i)\b(exclusive|limited|presale|whitelist)\b'
]

# Compiled regex patterns for performance
COMPILED_SUSPICIOUS_PATTERNS = [re.compile(pattern) for pattern in SUSPICIOUS_PATTERNS]

# Valid Ethereum address pattern
ETH_ADDRESS_PATTERN = re.compile(r'^0x[a-fA-F0-9]{40}$')

# Valid transaction hash pattern
TX_HASH_PATTERN = re.compile(r'^0x[a-fA-F0-9]{64}$')

def is_valid_ethereum_address(address: str) -> bool:
    """Validate Ethereum address format and checksum.
    
    Args:
        address: Ethereum address string
        
    Returns:
        True if valid Ethereum address, False otherwise
    """
    if not address or not isinstance(address, str):
        return False
    
    # Basic format check
    if not ETH_ADDRESS_PATTERN.match(address):
        return False
    
    # Use Web3 for checksum validation
    try:
        return is_address(address)
    except Exception:
        return False

def is_valid_transaction_hash(tx_hash: str) -> bool:
    """Validate Ethereum transaction hash format.
    
    Args:
        tx_hash: Transaction hash string
        
    Returns:
        True if valid transaction hash, False otherwise
    """
    if not tx_hash or not isinstance(tx_hash, str):
        return False
    
    # Basic format check
    if not TX_HASH_PATTERN.match(tx_hash):
        return False
    
    # Additional hex validation
    try:
        return is_hex(tx_hash) and len(tx_hash) == 66  # 0x + 64 hex chars
    except Exception:
        return False

def sanitize_token_name(name: str, max_length: int = 100) -> str:
    """Sanitize token name by removing suspicious characters and patterns.
    
    Args:
        name: Raw token name
        max_length: Maximum allowed length
        
    Returns:
        Sanitized token name
    """
    if not name or not isinstance(name, str):
        return "Unknown"
    
    # Remove zero-width and control characters
    sanitized = re.sub(r'[\u0000-\u001f\u007f-\u009f\u200b-\u200f\u2060-\u206f]', '', name)
    
    # Remove excessive whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].strip()
    
    # Replace empty result
    if not sanitized:
        return "Unknown"
    
    return sanitized

def detect_suspicious_patterns(text: str) -> Tuple[bool, List[str]]:
    """Detect suspicious patterns in token names, symbols, or descriptions.
    
    Args:
        text: Text to analyze
        
    Returns:
        Tuple of (is_suspicious, list_of_matched_patterns)
    """
    if not text or not isinstance(text, str):
        return False, []
    
    matched_patterns = []
    
    for i, pattern in enumerate(COMPILED_SUSPICIOUS_PATTERNS):
        if pattern.search(text):
            matched_patterns.append(SUSPICIOUS_PATTERNS[i])
    
    return len(matched_patterns) > 0, matched_patterns

def calculate_suspicion_score(name: str, symbol: str, description: str = "") -> float:
    """Calculate a suspicion score based on multiple factors.
    
    Args:
        name: Token name
        symbol: Token symbol
        description: Token description (optional)
        
    Returns:
        Suspicion score from 0.0 (not suspicious) to 10.0 (highly suspicious)
    """
    score = 0.0
    
    # Check name
    name_suspicious, name_patterns = detect_suspicious_patterns(name)
    if name_suspicious:
        score += len(name_patterns) * 1.5
    
    # Check symbol
    symbol_suspicious, symbol_patterns = detect_suspicious_patterns(symbol)
    if symbol_suspicious:
        score += len(symbol_patterns) * 2.0  # Symbol patterns are more critical
    
    # Check description
    if description:
        desc_suspicious, desc_patterns = detect_suspicious_patterns(description)
        if desc_suspicious:
            score += len(desc_patterns) * 1.0
    
    # Additional checks
    
    # Very short or very long names
    if len(name) < 3 or len(name) > 50:
        score += 1.0
    
    # Very short or very long symbols
    if len(symbol) < 2 or len(symbol) > 10:
        score += 1.5
    
    # All caps (often used in scams)
    if name.isupper() and len(name) > 5:
        score += 0.5
    
    # Numbers in symbol (unusual for legitimate tokens)
    if re.search(r'\d', symbol):
        score += 1.0
    
    # Special characters in symbol
    if re.search(r'[^a-zA-Z0-9]', symbol):
        score += 1.5
    
    # Cap the score at 10.0
    return min(score, 10.0)

def is_contract_address(address: str, web3_instance: Optional[Web3] = None) -> bool:
    """Check if an address is a smart contract.
    
    Args:
        address: Ethereum address
        web3_instance: Web3 instance (optional)
        
    Returns:
        True if address is a contract, False otherwise
    """
    if not is_valid_ethereum_address(address):
        return False
    
    if web3_instance is None:
        return True  # Assume it's a contract if we can't check
    
    try:
        code = web3_instance.eth.get_code(Web3.to_checksum_address(address))
        return len(code) > 0
    except Exception:
        return False

def validate_token_metadata(name: str, symbol: str, decimals: int) -> Tuple[bool, List[str]]:
    """Validate token metadata for basic sanity checks.
    
    Args:
        name: Token name
        symbol: Token symbol
        decimals: Token decimals
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Validate name
    if not name or len(name.strip()) == 0:
        errors.append("Token name is empty")
    elif len(name) > 100:
        errors.append("Token name is too long")
    
    # Validate symbol
    if not symbol or len(symbol.strip()) == 0:
        errors.append("Token symbol is empty")
    elif len(symbol) > 20:
        errors.append("Token symbol is too long")
    elif not re.match(r'^[a-zA-Z0-9]+$', symbol):
        errors.append("Token symbol contains invalid characters")
    
    # Validate decimals
    if not isinstance(decimals, int):
        errors.append("Decimals must be an integer")
    elif decimals < 0 or decimals > 77:  # ERC20 standard allows up to 77
        errors.append("Decimals must be between 0 and 77")
    
    return len(errors) == 0, errors

def extract_addresses_from_text(text: str) -> List[str]:
    """Extract Ethereum addresses from text.
    
    Args:
        text: Text to search for addresses
        
    Returns:
        List of valid Ethereum addresses found
    """
    if not text:
        return []
    
    # Find potential addresses
    potential_addresses = ETH_ADDRESS_PATTERN.findall(text)
    
    # Validate each address
    valid_addresses = []
    for addr in potential_addresses:
        if is_valid_ethereum_address(addr):
            valid_addresses.append(Web3.to_checksum_address(addr))
    
    return list(set(valid_addresses))  # Remove duplicates

def is_honeypot_pattern(name: str, symbol: str) -> bool:
    """Detect potential honeypot patterns in token names/symbols.
    
    Args:
        name: Token name
        symbol: Token symbol
        
    Returns:
        True if honeypot patterns detected
    """
    honeypot_patterns = [
        r'(?i)\b(honey|pot|trap|lock|freeze)\b',
        r'(?i)\b(no.?sell|cant.?sell|unable.?sell)\b',
        r'(?i)\b(tax|fee).*100',
        r'(?i)\b(burn|black.?hole|dead)\b'
    ]
    
    text = f"{name} {symbol}".lower()
    
    for pattern in honeypot_patterns:
        if re.search(pattern, text):
            return True
    
    return False

# Example usage and testing
if __name__ == "__main__":
    # Test address validation
    test_addresses = [
        "0x1234567890123456789012345678901234567890",  # Valid format
        "0xA0b86a33E6441e8e5c3F27d9C387b8B2C4b4B8B2",  # Valid checksum
        "0xinvalid",  # Invalid
        "not_an_address",  # Invalid
    ]
    
    print("Address validation tests:")
    for addr in test_addresses:
        print(f"{addr}: {is_valid_ethereum_address(addr)}")
    
    # Test suspicious pattern detection
    test_tokens = [
        ("SafeMoonElonDoge", "SMED"),
        ("Ethereum", "ETH"),
        ("Bitcoin", "BTC"),
        ("🚀🚀🚀MOON🚀🚀🚀", "MOON"),
    ]
    
    print("\nSuspicious pattern tests:")
    for name, symbol in test_tokens:
        score = calculate_suspicion_score(name, symbol)
        print(f"{name} ({symbol}): Suspicion score = {score:.1f}")
    
    # Test metadata validation
    print("\nMetadata validation tests:")
    test_metadata = [
        ("Valid Token", "VTK", 18),
        ("", "EMPTY", 18),  # Empty name
        ("Valid", "", 18),  # Empty symbol
        ("Valid", "VTK", -1),  # Invalid decimals
    ]
    
    for name, symbol, decimals in test_metadata:
        is_valid, errors = validate_token_metadata(name, symbol, decimals)
        print(f"{name}/{symbol}/{decimals}: Valid = {is_valid}, Errors = {errors}")