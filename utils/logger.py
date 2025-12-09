"""
Logging configuration and utilities.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from config.config_manager import get_config


class InterceptHandler(logging.Handler):
    """
    Intercept standard logging and redirect to loguru.
    """
    
    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging(log_file: Optional[str] = None, log_level: Optional[str] = None) -> None:
    """
    Setup logging configuration.
    
    Args:
        log_file: Path to log file. If None, uses config value.
        log_level: Logging level. If None, uses config value.
    """
    try:
        config = get_config()
        log_file = log_file or config.env["LOG_FILE"]
        log_level = log_level or config.env["LOG_LEVEL"]
    except:
        log_file = log_file or "logs/job_agent.log"
        log_level = log_level or "INFO"
    
    # Create logs directory
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove default logger
    logger.remove()
    
    # Add console handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )
    
    # Add file handler
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
    )
    
    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Set levels for specific loggers
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")


def get_logger(name: str) -> logger:
    """
    Get logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logger.bind(name=name)
