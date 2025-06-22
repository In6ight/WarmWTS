import logging
from logging.handlers import RotatingFileHandler
from whatsapp_warmer.config import Paths
from typing import Optional, Dict, Any
import json
from datetime import datetime
import traceback


class JSONFormatter(logging.Formatter):
    """Форматирует логи в JSON-структуру"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        if record.exc_info:
            log_data["exception"] = traceback.format_exc()

        if hasattr(record, 'extra'):
            log_data.update(record.extra)

        return json.dumps(log_data, ensure_ascii=False)


class Logger:
    """Настройка системы логирования"""

    _initialized = False

    @classmethod
    def initialize(cls,
                   name: str = "app",
                   log_level: int = logging.INFO,
                   max_bytes: int = 10 * 1024 * 1024,  # 10 MB
                   backup_count: int = 5):
        """
        Инициализация логгера с ротацией файлов

        Args:
            name: Имя логгера
            log_level: Уровень логирования
            max_bytes: Макс. размер файла лога
            backup_count: Количество бэкапов
        """
        if cls._initialized:
            return

        logger = logging.getLogger(name)
        logger.setLevel(log_level)

        # Форматтер
        formatter = JSONFormatter() if name == "json" else logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Файловый обработчик с ротацией
        file_handler = RotatingFileHandler(
            filename=Paths.LOGS_DIR / f"{name}.log",
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)

        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        # Добавляем обработчики
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str = "app") -> logging.Logger:
        """Возвращает настроенный логгер"""
        if not cls._initialized:
            cls.initialize(name)
        return logging.getLogger(name)

    @staticmethod
    def log_exception(exc: Exception,
                      extra: Optional[Dict[str, Any]] = None,
                      logger_name: str = "app"):
        """Логирует исключение с дополнительными данными"""
        logger = logging.getLogger(logger_name)
        exc_info = (type(exc), exc, exc.__traceback__)

        if extra:
            logger.error(str(exc), exc_info=exc_info, extra={'extra': extra})
        else:
            logger.error(str(exc), exc_info=exc_info)


# Инициализация основного логгера при импорте
Logger.initialize()

# Алиасы для удобства
get_logger = Logger.get_logger
log_exception = Logger.log_exception