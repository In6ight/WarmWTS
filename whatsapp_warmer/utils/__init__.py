from .logger import setup_logger, get_logger
from .helpers import validate_phone, validate_proxy  # Только нужные функции

__all__ = [
    'setup_logger',
    'get_logger',
    'validate_phone',
    'validate_proxy'  # Добавляем валидацию прокси
]