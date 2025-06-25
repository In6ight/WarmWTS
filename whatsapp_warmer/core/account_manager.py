from pathlib import Path
import json
from typing import List, Dict, Optional
from whatsapp_warmer.core.models.account import WhatsAppAccount
from whatsapp_warmer.utils.logger import get_logger

logger = get_logger(__name__)


class AccountManager:
    """Менеджер аккаунтов с полной поддержкой файлового хранилища"""

    def __init__(self, storage_path: Optional[Path] = None):
        self.accounts: List[WhatsAppAccount] = []
        self._account_index: Dict[str, WhatsAppAccount] = {}
        self.storage_path = storage_path

        if self.storage_path:
            self._init_storage()
            self._load_from_file()

    def _init_storage(self):
        """Инициализация файлового хранилища"""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            if not self.storage_path.exists():
                self.storage_path.write_text("[]", encoding='utf-8')
        except Exception as e:
            logger.error(f"Ошибка инициализации хранилища: {str(e)}")

    def _load_from_file(self):
        """Безопасная загрузка аккаунтов из файла"""
        try:
            if not self.storage_path.exists():
                logger.info(f"Файл {self.storage_path} не существует")
                return

            content = self.storage_path.read_text(encoding='utf-8').strip()
            if not content:
                logger.info("Файл хранилища пуст")
                return

            data = json.loads(content)
            if not isinstance(data, list):
                raise ValueError("Ожидается список аккаунтов")

            self.load_accounts(data)
            logger.info(f"Успешно загружено {len(self.accounts)} аккаунтов")

        except json.JSONDecodeError:
            logger.error("Неверный формат JSON в файле хранилища")
        except Exception as e:
            logger.error(f"Критическая ошибка загрузки: {str(e)}")

    def save_to_file(self) -> bool:
        """Безопасное сохранение аккаунтов в файл"""
        if not self.storage_path:
            return False

        try:
            data = self.save_accounts()
            temp_path = self.storage_path.with_suffix('.tmp')

            # Пишем во временный файл
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Заменяем оригинальный файл
            temp_path.replace(self.storage_path)
            logger.info(f"Успешно сохранено {len(data)} аккаунтов")
            return True

        except Exception as e:
            logger.error(f"Ошибка сохранения: {str(e)}")
            return False

    def add_account(self, account: WhatsAppAccount) -> bool:
        """Добавление нового аккаунта с валидацией"""
        try:
            if not isinstance(account, WhatsAppAccount):
                raise ValueError("Неверный тип аккаунта")

            if account.phone in self._account_index:
                logger.warning(f"Аккаунт {account.phone} уже существует")
                return False

            self.accounts.append(account)
            self._account_index[account.phone] = account
            logger.info(f"Добавлен аккаунт: {account.phone}")
            return True

        except Exception as e:
            logger.error(f"Ошибка добавления аккаунта: {str(e)}")
            return False

    def load_accounts(self, accounts_data: List[Dict]) -> int:
        """Загрузка аккаунтов из списка словарей"""
        success_count = 0
        for idx, data in enumerate(accounts_data, 1):
            try:
                account = WhatsAppAccount.from_dict(data)
                if self.add_account(account):
                    success_count += 1
            except Exception as e:
                logger.error(f"Ошибка в аккаунте #{idx}: {str(e)}")
        return success_count

    def save_accounts(self) -> List[Dict]:
        """Сериализация аккаунтов в список словарей"""
        return [acc.to_dict() for acc in self.accounts]

    def get_account(self, phone: str) -> Optional[WhatsAppAccount]:
        """Получение аккаунта по номеру телефона"""
        return self._account_index.get(phone)

    def remove_account(self, phone: str) -> bool:
        """Удаление аккаунта по номеру телефона"""
        account = self._account_index.pop(phone, None)
        if account:
            self.accounts.remove(account)
            logger.info(f"Удален аккаунт: {phone}")
            return True
        return False

    def clear(self):
        """Полная очистка всех аккаунтов"""
        self.accounts.clear()
        self._account_index.clear()
        logger.info("Все аккаунты очищены")

    def __len__(self) -> int:
        return len(self.accounts)

    def __contains__(self, phone: str) -> bool:
        return phone in self._account_index

    def get_all_accounts(self) -> List[WhatsAppAccount]:
        """Получение всех аккаунтов"""
        return self.accounts.copy()

    def get_active_accounts(self) -> List[WhatsAppAccount]:
        """Получение только активных аккаунтов"""
        return [acc for acc in self.accounts if acc.enabled]