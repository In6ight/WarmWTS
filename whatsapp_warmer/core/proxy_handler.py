from typing import List, Optional, Dict
from pathlib import Path
import json
import random
from whatsapp_warmer.core.models.proxy import ProxyConfig
from whatsapp_warmer.utils.logger import get_logger

logger = get_logger(__name__)

class ProxyHandler:
    """Менеджер для работы с прокси-серверами"""

    def __init__(self, storage_path: Optional[Path] = None):
        self.proxies: List[ProxyConfig] = []
        self.storage_path = storage_path
        if self.storage_path:
            self._load_from_file()

    def _load_from_file(self):
        """Загрузка прокси из файла"""
        try:
            if not self.storage_path.exists():
                return

            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.proxies = [ProxyConfig.from_dict(item) for item in data]
            logger.info(f"Загружено {len(self.proxies)} прокси из файла")
        except Exception as e:
            logger.error(f"Ошибка загрузки прокси: {str(e)}")

    def save_to_file(self):
        """Сохранение прокси в файл"""
        if not self.storage_path:
            return

        try:
            data = [proxy.to_dict() for proxy in self.proxies]
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Сохранено {len(self.proxies)} прокси в файл")
        except Exception as e:
            logger.error(f"Ошибка сохранения прокси: {str(e)}")

    def add_proxy(self, proxy: ProxyConfig) -> bool:
        """Добавление нового прокси"""
        if not self._validate_proxy(proxy):
            return False

        if any(p.id == proxy.id for p in self.proxies):
            logger.warning(f"Прокси {proxy.id} уже существует")
            return False

        self.proxies.append(proxy)
        self.save_to_file()
        logger.info(f"Добавлен прокси: {proxy.host}:{proxy.port}")
        return True

    def _validate_proxy(self, proxy: ProxyConfig) -> bool:
        """Валидация прокси"""
        if not proxy.host or not (1 <= proxy.port <= 65535):
            logger.error("Неверный хост или порт прокси")
            return False
        return True

    def get_proxy(self, index: int) -> Optional[ProxyConfig]:
        """Получение прокси по индексу"""
        try:
            return self.proxies[index]
        except IndexError:
            logger.warning(f"Индекс {index} вне диапазона (всего: {len(self.proxies)})")
            return None

    def get_proxy_for_account(self, account) -> Optional[ProxyConfig]:
        """Получение случайного активного прокси для аккаунта"""
        active_proxies = [p for p in self.proxies if p.is_active]
        if not active_proxies:
            logger.warning("Нет активных прокси")
            return None
        return random.choice(active_proxies)

    def clear_proxies(self):
        """Очистка списка прокси"""
        self.proxies.clear()
        self.save_to_file()
        logger.info("Все прокси удалены")

    def __len__(self) -> int:
        return len(self.proxies)

    def get_all_proxies(self) -> List[ProxyConfig]:
        """Получение всех прокси"""
        return self.proxies.copy()