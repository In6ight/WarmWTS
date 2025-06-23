from typing import List, Optional
from whatsapp_warmer.core.models.proxy import ProxyConfig
from whatsapp_warmer.utils.logger import get_logger

logger = get_logger(__name__)


class ProxyHandler:
    """Менеджер для работы с прокси"""

    def __init__(self):
        self.proxies: List[ProxyConfig] = []

    def add_proxy(self, proxy: ProxyConfig) -> bool:
        """Добавление прокси в список"""
        if not self._validate_proxy(proxy):
            return False

        self.proxies.append(proxy)
        logger.info(f"Added proxy: {proxy.host}:{proxy.port}")
        return True

    def _validate_proxy(self, proxy: ProxyConfig) -> bool:
        """Валидация прокси"""
        if not proxy.host or not (1 <= proxy.port <= 65535):
            logger.error("Invalid proxy host or port")
            return False
        return True

    def get_proxy(self, index: int) -> Optional[ProxyConfig]:
        """Получение прокси по индексу"""
        try:
            return self.proxies[index]
        except IndexError:
            logger.warning(f"Proxy index {index} out of range")
            return None

    def clear_proxies(self):
        """Очистка списка прокси"""
        self.proxies.clear()
        logger.info("All proxies cleared")