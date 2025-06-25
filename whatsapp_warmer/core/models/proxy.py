from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import random
from whatsapp_warmer.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ProxyConfig:
    """
    Конфигурация прокси-сервера для WhatsApp.
    Поддерживает HTTP, SOCKS4, SOCKS5 с аутентификацией.
    """
    host: str
    port: int
    protocol: str = "http"  # 'http', 'socks4', 'socks5'
    username: Optional[str] = None
    password: Optional[str] = None
    id: Optional[str] = None
    last_used: Optional[datetime] = None
    is_active: bool = True
    fail_count: int = 0

    def __post_init__(self):
        """Валидация при инициализации"""
        self._validate_protocol()
        self._generate_id()
        self.protocol = self.protocol.lower()

    def _validate_protocol(self):
        """Проверка поддерживаемых протоколов"""
        if self.protocol.lower() not in ('http', 'socks4', 'socks5'):
            raise ValueError(f"Неподдерживаемый протокол: {self.protocol}")

    def _generate_id(self):
        """Генерация уникального ID"""
        if not self.id:
            base = f"{self.protocol}_{self.host}_{self.port}"
            self.id = base if not self.username else f"{base}_{self.username}"

    @property
    def connection_string(self) -> str:
        """Строка подключения с аутентификацией"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь"""
        return {
            'host': self.host,
            'port': self.port,
            'protocol': self.protocol,
            'username': self.username,
            'password': self.password,
            'id': self.id,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'is_active': self.is_active,
            'fail_count': self.fail_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProxyConfig':
        """Десериализация из словаря"""
        return cls(
            host=data['host'],
            port=data['port'],
            protocol=data.get('protocol', 'http'),
            username=data.get('username'),
            password=data.get('password'),
            id=data.get('id'),
            last_used=datetime.fromisoformat(data['last_used']) if data.get('last_used') else None,
            is_active=data.get('is_active', True),
            fail_count=data.get('fail_count', 0)
        )