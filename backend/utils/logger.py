"""
Production-grade structured logging
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
import os

class ProductionLogger:
    """Production-grade logging with file rotation"""

    def __init__(self, name: str = "smart_doctor"):
        self.logger = logging.getLogger(name)
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.setup_handlers()

    def setup_handlers(self):
        """Setup logging handlers"""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        self.logger.setLevel(level_map.get(self.log_level, logging.INFO))

        # Remove existing handlers
        self.logger.handlers = []

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        # File handlers (only in production/development)
        if os.getenv("ENVIRONMENT", "development") in ["production", "development"]:
            self.setup_file_handlers()

    def setup_file_handlers(self):
        """Setup file logging handlers"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # General log file
        file_handler = logging.FileHandler(
            log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)

        # Error log file
        error_handler = logging.FileHandler(
            log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_format)
        self.logger.addHandler(error_handler)

    def info(self, message: str, **kwargs):
        """Log info message"""
        extra_info = f" | {kwargs}" if kwargs else ""
        self.logger.info(f"{message}{extra_info}")

    def error(self, message: str, exc_info=None, **kwargs):
        """Log error message"""
        extra_info = f" | {kwargs}" if kwargs else ""
        self.logger.error(f"{message}{extra_info}", exc_info=exc_info)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        extra_info = f" | {kwargs}" if kwargs else ""
        self.logger.warning(f"{message}{extra_info}")

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        extra_info = f" | {kwargs}" if kwargs else ""
        self.logger.debug(f"{message}{extra_info}")

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        extra_info = f" | {kwargs}" if kwargs else ""
        self.logger.critical(f"{message}{extra_info}")

# Global logger instance
logger = ProductionLogger()
