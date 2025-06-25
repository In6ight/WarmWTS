from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging
from whatsapp_warmer.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProxyConfig:
    """
    Класс для хранения и управления конфигурацией прокси-сервера.
    Поддерживает HTTP, SOCKS4 и SOCKS5 прокси с аутентификацией.
    """
    host: str
    port: int
    type: str  # 'http', 'socks4', 'socks5'
    username: Optional[str] = None
    password: Optional[str] = None
    id: Optional[str] = None
    is_active: bool = True
    last_used: Optional[str] = None

    def __post_init__(self):
        """Валидация параметров при инициализации"""
        self._validate_proxy_type()
        self._generate_id_if_needed()
        self._normalize_type()

    def _validate_proxy_type(self):
        """Проверка корректности типа прокси"""
        valid_types = ['http', 'socks4', 'socks5', 'https']
        if self.type.lower() not in valid_types:
            raise ValueError(
                f"Неподдерживаемый тип прокси: {self.type}. "
                f"Допустимые типы: {', '.join(valid_types)}"
            )

    def _normalize_type(self):
        """Приведение типа прокси к нижнему регистру"""
        self.type = self.type.lower()

    def _generate_id_if_needed(self):
        """Генерация ID если не предоставлен"""
        if not self.id:
            self.id = f"{self.host}:{self.port}"

    def to_dict(self) -> Dict[str, Any]:
        """
        Сериализация конфигурации в словарь
        Returns:
            Словарь с параметрами прокси
        """
        return {
            'host': self.host,
            'port': self.port,
            'type': self.type,
            'username': self.username,
            'password': self.password,
            'id': self.id,
            'is_active': self.is_active,
            'last_used': self.last_used
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProxyConfig':
        """
        Десериализация конфигурации из словаря
        Args:
            data: Словарь с параметрами прокси
        Returns:
            Экземпляр ProxyConfig
        """
        return cls(
            host=data['host'],
            port=int(data['port']),
            type=data['type'],
            username=data.get('username'),
            password=data.get('password'),
            id=data.get('id'),
            is_active=data.get('is_active', True),
            last_used=data.get('last_used')
        )

    def get_connection_string(self, masked: bool = False) -> str:
        """
        Получение строки подключения
        Args:
            masked: Скрывать ли пароль в строке подключения
        Returns:
            Строка подключения в формате type://user:pass@host:port
        """
        creds = ""
        if self.username:
            password = self.password if not masked else "***"
            creds = f"{self.username}:{password}@"

        return f"{self.type}://{creds}{self.host}:{self.port}"

    def test_connection(self) -> bool:
        """
        Проверка работоспособности прокси (заглушка для реализации)
        Returns:
            bool: Результат проверки подключения
        """
        # Здесь должна быть реализация проверки прокси
        # Например, попытка подключения к тестовому ресурсу
        return True  # Заглушка для примера

    def mark_as_used(self):
        """Обновление времени последнего использования"""
        from datetime import datetime
        self.last_used = datetime.now().isoformat()