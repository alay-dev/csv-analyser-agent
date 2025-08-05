"""
Logging configuration for the CSV Analyzer application
"""
import logging
import sys
from typing import Optional

def setup_logging(level: str = "INFO", format_style: str = "detailed") -> None:
    """
    Set up logging configuration for the application
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_style: Format style ("simple", "detailed", "json")
    """
    
    # Define format styles
    formats = {
        "simple": "%(levelname)s: %(message)s",
        "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "json": '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
    }
    
    # Get the format
    log_format = formats.get(format_style, formats["detailed"])
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific logger levels
    loggers_config = {
        "session_manager": level.upper(),
        "main": level.upper(),
        "motor": "WARNING",  # Reduce motor (MongoDB driver) verbosity
        "pymongo": "WARNING",  # Reduce pymongo verbosity
    }
    
    for logger_name, logger_level in loggers_config.items():
        logging.getLogger(logger_name).setLevel(getattr(logging, logger_level))

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(name)

# Example usage:
if __name__ == "__main__":
    # Test different logging levels
    setup_logging("DEBUG", "detailed")
    
    logger = get_logger("test")
    
    logger.debug("🐛 This is a debug message")
    logger.info("ℹ️ This is an info message")
    logger.warning("⚠️ This is a warning message")
    logger.error("❌ This is an error message")
    logger.critical("🚨 This is a critical message")