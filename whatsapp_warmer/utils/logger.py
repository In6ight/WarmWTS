import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logger(name: str = 'whatsapp_warmer',
                 log_file: str = 'logs/app.log',
                 level: int = logging.INFO,
                 max_bytes: int = 10 * 1024 * 1024,  # 10 MB
                 backup_count: int = 5) -> logging.Logger:
    """
    Настройка логгера с ротацией логов

    Args:
        name: Имя логгера
        log_file: Путь к файлу логов
        level: Уровень логирования
        max_bytes: Максимальный размер файла перед ротацией
        backup_count: Количество сохраняемых лог-файлов
    """
    # Создаем папку для логов, если её нет
    log_path = Path(log_file).parent
    log_path.mkdir(parents=True, exist_ok=True)

    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Формат сообщений
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Обработчик для файла с ротацией
    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Получение настроенного логгера

    Args:
        name: Имя логгера (если None, вернет корневой логгер)
    """
    return logging.getLogger(name or 'whatsapp_warmer')