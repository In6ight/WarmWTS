from dataclasses import dataclass
from typing import Optional
from whatsapp_warmer.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProxyConfig:
    """Конфигурация прокси-сервера для аккаунтов WhatsApp"""
    host: str
    port: int
    type: str = "http"  # http, https, socks4, socks5
    username: Optional[str] = None
    password: Optional[str] = None

    def __post_init__(self):
        """Валидация параметров прокси"""
        if not isinstance(self.port, int) or not (1 <= self.port <= 65535):
            raise ValueError("Порт должен быть числом от 1 до 65535")

        if self.type not in ["http", "https", "socks4", "socks5"]:
            raise ValueError("Неподдерживаемый тип прокси")

    def get_formatted(self) -> str:
        """
        Форматирует прокси для использования в Selenium
        Возвращает строку в формате: type://user:pass@host:port
        """
        if self.username and self.password:
            return f"{self.type}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.type}://{self.host}:{self.port}"

    def to_dict(self) -> dict:
        """Сериализация в словарь"""
        return {
            'host': self.host,
            'port': self.port,
            'type': self.type,
            'username': self.username,
            'password': self.password
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ProxyConfig':
        """Десериализация из словаря"""
        return cls(
            host=data['host'],
            port=int(data['port']),
            type=data.get('type', 'http'),
            username=data.get('username'),
            password=data.get('password')
        )

    def test_connection(self) -> bool:
        """Тестирование соединения с прокси (заглушка)"""
        try:
            # Здесь должна быть реальная проверка подключения
            logger.info(f"Testing proxy connection: {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Proxy connection failed: {str(e)}")
            return False