def validate_phone(phone: str) -> bool:
    """Валидация номера телефона для WhatsApp"""
    # Российские номера: 79XXXXXXXXX
    return phone.startswith('79') and len(phone) == 11 and phone.isdigit()

def validate_proxy(proxy_config: dict) -> bool:
    """Валидация конфигурации прокси"""
    required = ['host', 'port', 'type']
    return all(key in proxy_config for key in required)