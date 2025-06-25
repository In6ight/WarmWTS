import logging
from pathlib import Path
import os


def setup_logger(name='app', log_file='app.log', level=logging.INFO):
    """Настройка основного логгера"""
    # Создаем директорию для логов если нужно
    log_path = Path(log_file).parent
    log_path.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Файловый обработчик
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Добавляем обработчики
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def get_logger(name=None):
    """Получение настроенного логгера"""
    return logging.getLogger(name or 'whatsapp_warmer')