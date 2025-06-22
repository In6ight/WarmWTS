from dataclasses import dataclass
from typing import Optional

@dataclass
class ProxyConfig:
    """Конфигурация прокси-сервера для аккаунта"""
    enabled: bool = False
    type: str = "http"  # http/socks4/socks5
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None

    def validate(self) -> bool:
        """Проверяет, что прокси правильно настроен"""
        if not self.enabled:
            return True
        return all([self.host, self.port])