import logging
import os
import sys
from typing import Any, Dict, Optional

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()

class AppLogger:
    _logger: Optional[logging.LoggerAdapter] = None

    @classmethod
    def get_instance(cls) -> logging.LoggerAdapter:
        if cls._logger is None:
            logger = logging.getLogger('chatgpt-bot')
            logger.setLevel(LOG_LEVEL)
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(asctime)s] %(name)s.%(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
            handler.setFormatter(formatter)
            logger.handlers = []  # Remove any default handlers
            logger.addHandler(handler)
            cls._logger = logging.LoggerAdapter(logger, extra={})
        return cls._logger

    @classmethod
    def debug(cls, msg: str, context: Optional[Dict[str, Any]] = None):
        cls.get_instance().debug(msg, extra={'context': context or {}})

    @classmethod
    def info(cls, msg: str, context: Optional[Dict[str, Any]] = None):
        cls.get_instance().info(msg, extra={'context': context or {}})

    @classmethod
    def warning(cls, msg: str, context: Optional[Dict[str, Any]] = None):
        cls.get_instance().warning(msg, extra={'context': context or {}})

    @classmethod
    def error(cls, msg: str, context: Optional[Dict[str, Any]] = None):
        cls.get_instance().error(msg, extra={'context': context or {}})

    @classmethod
    def critical(cls, msg: str, context: Optional[Dict[str, Any]] = None):
        cls.get_instance().critical(msg, extra={'context': context or {}})
        sys.exit(1)

# For convenience, provide module-level functions
info = AppLogger.info
debug = AppLogger.debug
warning = AppLogger.warning
error = AppLogger.error
critical = AppLogger.critical
