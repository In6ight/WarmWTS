from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional
from whatsapp_warmer.utils.helpers import validate_phone
from whatsapp_warmer.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProxyConfig:
    """Конфигурация прокси (временно перенесено сюда для избежания циклических импортов)"""
    host: str
    port: int
    type: str = "http"
    username: Optional[str] = None
    password: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class WarmingStats:
    """Статистика прогрева (временно перенесено сюда)"""
    messages_sent: int = 0
    last_warming: Optional[datetime] = None
    sessions: int = 0
    errors: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}


@dataclass
class WhatsAppAccount:
    """Полная модель аккаунта WhatsApp со всеми зависимостями"""

    phone: str
    login_method: str = "qr"  # 'qr' или 'sms'
    proxy: Optional[ProxyConfig] = None
    enabled: bool = True
    last_active: Optional[datetime] = None
    warming_stats: WarmingStats = field(default_factory=WarmingStats)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Валидация данных при инициализации"""
        if not validate_phone(self.phone):
            raise ValueError(f"Неверный формат телефона: {self.phone}")
        if self.login_method not in ("qr", "sms"):
            raise ValueError("Метод входа должен быть 'qr' или 'sms'")

    @property
    def is_active(self) -> bool:
        """Проверяет активность аккаунта (последние 24 часа)"""
        return self.last_active and (datetime.now() - self.last_active).total_seconds() < 86400

    def update_activity(self):
        """Обновляет метку последней активности"""
        self.last_active = datetime.now()
        self.warming_stats.sessions += 1

    def add_message_stat(self, count: int = 1):
        """Обновляет статистику сообщений"""
        self.warming_stats.messages_sent += count
        self.warming_stats.last_warming = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь"""
        return {
            'phone': self.phone,
            'login_method': self.login_method,
            'proxy': self.proxy.to_dict() if self.proxy else None,
            'enabled': self.enabled,
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'warming_stats': self.warming_stats.to_dict(),
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WhatsAppAccount':
        """Десериализация из словаря"""
        proxy_data = data.get('proxy')
        proxy = ProxyConfig(**proxy_data) if proxy_data else None

        return cls(
            phone=data['phone'],
            login_method=data.get('login_method', 'qr'),
            proxy=proxy,
            enabled=data.get('enabled', True),
            last_active=datetime.fromisoformat(data['last_active']) if data.get('last_active') else None,
            warming_stats=WarmingStats(**data.get('warming_stats', {})),
            metadata=data.get('metadata', {})
        )