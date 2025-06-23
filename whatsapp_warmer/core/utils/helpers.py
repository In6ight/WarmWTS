import re
from typing import Union
from whatsapp_warmer.utils.logger import get_logger

logger = get_logger(__name__)


def validate_phone(phone: Union[str, int]) -> bool:
    """Валидация номера телефона для WhatsApp"""
    if isinstance(phone, int):
        phone = str(phone)

    # Проверка для российских номеров: 79XXXXXXXXX
    pattern = r'^79\d{9}$'
    if not re.match(pattern, phone):
        logger.warning(f"Invalid phone format: {phone}")
        return False
    return True


# Добавленная функция для валидации email
def validate_email(email: str) -> bool:
    """Валидация email адреса"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        logger.warning(f"Invalid email format: {email}")
        return False
    return True