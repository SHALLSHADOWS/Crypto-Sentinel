"""Advanced logging configuration for Crypto Sentinel.

This module provides a comprehensive logging setup with:
- Rich console output with colors and formatting
- Rotating file handler for persistent logs
- Different log levels for different components
- Structured logging for better analysis
"""

import os
import sys
from pathlib import Path
from typing import Optional
from loguru import logger
from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install
from datetime import datetime

# Install rich traceback handler
install(show_locals=True)

# Rich console for beautiful output
console = Console()

class CryptoSentinelLogger:
    """Custom logger class for Crypto Sentinel with advanced features."""
    
    def __init__(self):
        self.logger = logger
        self._setup_complete = False
        
    def setup_logger(
        self,
        log_level: str = "INFO",
        log_file_path: Optional[str] = None,
        max_file_size: str = "10 MB",
        backup_count: int = 5,
        enable_rich_console: bool = True,
        enable_json_logs: bool = False
    ) -> None:
        """Setup comprehensive logging configuration.
        
        Args:
            log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file_path: Path to log file (default: logs/crypto_sentinel.log)
            max_file_size: Maximum size before rotation (e.g., "10 MB")
            backup_count: Number of backup files to keep
            enable_rich_console: Enable Rich console output
            enable_json_logs: Enable JSON structured logging
        """
        if self._setup_complete:
            return
            
        # Remove default logger
        self.logger.remove()
        
        # Setup log directory
        if log_file_path is None:
            log_file_path = "logs/crypto_sentinel.log"
            
        log_dir = Path(log_file_path).parent
        log_dir.mkdir(exist_ok=True)
        
        # Console handler with Rich
        if enable_rich_console:
            self.logger.add(
                sys.stdout,
                level=log_level,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                       "<level>{level: <8}</level> | "
                       "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                       "<level>{message}</level>",
                colorize=True,
                backtrace=True,
                diagnose=True
            )
        
        # File handler with rotation
        self.logger.add(
            log_file_path,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            rotation=max_file_size,
            retention=f"{backup_count} files",
            compression="zip",
            backtrace=True,
            diagnose=True
        )
        
        # JSON logs for structured logging (optional)
        if enable_json_logs:
            json_log_path = log_file_path.replace('.log', '_structured.json')
            self.logger.add(
                json_log_path,
                level=log_level,
                format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {name}:{function}:{line} | {message}",
                serialize=True,
                rotation=max_file_size,
                retention=f"{backup_count} files"
            )
        
        # Error-only log file
        error_log_path = log_file_path.replace('.log', '_errors.log')
        self.logger.add(
            error_log_path,
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}\n{exception}",
            rotation="1 day",
            retention="30 days"
        )
        
        self._setup_complete = True
        self.logger.info("🚀 Crypto Sentinel Logger initialized successfully")
        
    def get_component_logger(self, component_name: str):
        """Get a logger for a specific component.
        
        Args:
            component_name: Name of the component (e.g., 'websocket', 'gpt_analyzer')
            
        Returns:
            Logger instance bound to the component
        """
        return self.logger.bind(component=component_name)
    
    def log_token_analysis(self, token_address: str, score: float, status: str):
        """Log token analysis with structured data.
        
        Args:
            token_address: Ethereum address of the token
            score: AI analysis score
            status: Analysis status
        """
        self.logger.info(
            "Token analysis completed",
            extra={
                "token_address": token_address,
                "ai_score": score,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": "token_analysis"
            }
        )
    
    def log_notification_sent(self, chat_id: str, token_address: str, score: float):
        """Log notification sending with structured data.
        
        Args:
            chat_id: Telegram chat ID
            token_address: Token address
            score: AI score
        """
        self.logger.info(
            "Notification sent",
            extra={
                "chat_id": chat_id,
                "token_address": token_address,
                "ai_score": score,
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": "notification_sent"
            }
        )
    
    def log_error_with_context(self, error: Exception, context: dict):
        """Log error with additional context.
        
        Args:
            error: Exception that occurred
            context: Additional context information
        """
        self.logger.error(
            f"Error occurred: {str(error)}",
            extra={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context,
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": "error"
            }
        )
    
    def log_performance_metric(self, operation: str, duration: float, success: bool):
        """Log performance metrics.
        
        Args:
            operation: Name of the operation
            duration: Duration in seconds
            success: Whether operation was successful
        """
        self.logger.info(
            f"Performance metric: {operation}",
            extra={
                "operation": operation,
                "duration_seconds": duration,
                "success": success,
                "timestamp": datetime.utcnow().isoformat(),
                "event_type": "performance_metric"
            }
        )

# Global logger instance
_crypto_logger = CryptoSentinelLogger()

def setup_logger(
    log_level: str = "INFO",
    log_file_path: Optional[str] = None,
    max_file_size: str = "10 MB",
    backup_count: int = 5,
    enable_rich_console: bool = True,
    enable_json_logs: bool = False
) -> None:
    """Setup the global logger configuration.
    
    Args:
        log_level: Minimum log level
        log_file_path: Path to log file
        max_file_size: Maximum file size before rotation
        backup_count: Number of backup files
        enable_rich_console: Enable Rich console output
        enable_json_logs: Enable JSON structured logging
    """
    _crypto_logger.setup_logger(
        log_level=log_level,
        log_file_path=log_file_path,
        max_file_size=max_file_size,
        backup_count=backup_count,
        enable_rich_console=enable_rich_console,
        enable_json_logs=enable_json_logs
    )

def get_logger(component_name: Optional[str] = None):
    """Get logger instance.
    
    Args:
        component_name: Optional component name for context
        
    Returns:
        Logger instance
    """
    if component_name:
        return _crypto_logger.get_component_logger(component_name)
    return _crypto_logger.logger

# Convenience functions for structured logging
def log_token_analysis(token_address: str, score: float, status: str):
    """Log token analysis event."""
    _crypto_logger.log_token_analysis(token_address, score, status)

def log_notification_sent(chat_id: str, token_address: str, score: float):
    """Log notification sent event."""
    _crypto_logger.log_notification_sent(chat_id, token_address, score)

def log_error_with_context(error: Exception, context: dict):
    """Log error with context."""
    _crypto_logger.log_error_with_context(error, context)

def log_performance_metric(operation: str, duration: float, success: bool):
    """Log performance metric."""
    _crypto_logger.log_performance_metric(operation, duration, success)

# Example usage and testing
if __name__ == "__main__":
    # Setup logger for testing
    setup_logger(log_level="DEBUG", enable_json_logs=True)
    
    logger = get_logger("test")
    
    # Test different log levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    
    # Test structured logging
    log_token_analysis("0x1234567890abcdef", 8.5, "completed")
    log_notification_sent("123456789", "0x1234567890abcdef", 8.5)
    
    # Test error logging
    try:
        raise ValueError("Test error")
    except Exception as e:
        log_error_with_context(e, {"test_context": "example"})
    
    # Test performance logging
    log_performance_metric("token_analysis", 2.5, True)
    
    logger.success("✅ Logger testing completed successfully!")