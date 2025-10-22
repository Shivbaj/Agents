"""
Logging configuration and setup
"""
import sys
from pathlib import Path
from typing import Union

from loguru import logger


def setup_logging(
    level: str = "INFO",
    format_type: str = "json",
    log_file: Union[str, Path] = "./logs/app.log",
    max_size: str = "10MB",
    backup_count: int = 5,
) -> None:
    """
    Setup application logging with loguru
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type (json or text)
        log_file: Path to log file
        max_size: Maximum log file size
        backup_count: Number of backup files to keep
    """
    
    # Remove default logger
    logger.remove()
    
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define formats
    if format_type.lower() == "json":
        log_format = (
            "{"
            '"time": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
            '"level": "{level}", '
            '"module": "{module}", '
            '"function": "{function}", '
            '"line": {line}, '
            '"message": "{message}"'
            "}"
        )
    else:
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
    
    # Add console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level=level,
        colorize=format_type.lower() != "json",
        serialize=format_type.lower() == "json",
    )
    
    # Add file handler
    logger.add(
        log_file,
        format=log_format,
        level=level,
        rotation=max_size,
        retention=backup_count,
        serialize=format_type.lower() == "json",
        compression="gz",
    )
    
    logger.info(f"Logging setup complete - Level: {level}, Format: {format_type}")


def get_logger(name: str = None):
    """Get a logger instance"""
    if name:
        return logger.bind(name=name)
    return logger