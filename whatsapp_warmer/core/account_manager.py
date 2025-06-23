from typing import List, Dict, Optional
from whatsapp_warmer.utils.logger import get_logger
from whatsapp_warmer.utils.helpers import validate_phone
from whatsapp_warmer.core.models.account import WhatsAppAccount
from whatsapp_warmer.core.models.proxy import ProxyConfig

logger = get_logger(__name__)


class AccountManager:
    """Полнофункциональный менеджер аккаунтов без циклических импортов"""

    def __init__(self):
        self.accounts: List[WhatsAppAccount] = []
        self._account_index: Dict[str, WhatsAppAccount] = {}

    def add_account(self, account: WhatsAppAccount) -> bool:
        """Добавление нового аккаунта с валидацией"""
        if not isinstance(account, WhatsAppAccount):
            logger.error("Invalid account type")
            return False

        if not validate_phone(account.phone):
            logger.error(f"Invalid phone format: {account.phone}")
            return False

        if account.phone in self._account_index:
            logger.warning(f"Account {account.phone} already exists")
            return False

        self.accounts.append(account)
        self._account_index[account.phone] = account
        logger.info(f"Added account: {account.phone}")
        return True

    def remove_account(self, phone: str) -> bool:
        """Удаление аккаунта по номеру телефона"""
        if phone not in self._account_index:
            logger.warning(f"Account {phone} not found")
            return False

        account = self._account_index.pop(phone)
        self.accounts.remove(account)
        logger.info(f"Removed account: {phone}")
        return True

    def get_account(self, phone: str) -> Optional[WhatsAppAccount]:
        """Получение аккаунта по номеру"""
        return self._account_index.get(phone)

    def update_proxy(self, phone: str, proxy: Optional[ProxyConfig]) -> bool:
        """Обновление прокси для аккаунта"""
        account = self.get_account(phone)
        if not account:
            logger.error(f"Account {phone} not found")
            return False

        account.proxy = proxy
        logger.info(f"Updated proxy for {phone}")
        return True

    def enable_account(self, phone: str, enable: bool = True) -> bool:
        """Активация/деактивация аккаунта"""
        account = self.get_account(phone)
        if not account:
            return False

        account.enabled = enable
        status = "enabled" if enable else "disabled"
        logger.info(f"Account {phone} {status}")
        return True

    def get_all_accounts(self) -> List[WhatsAppAccount]:
        """Получение всех аккаунтов"""
        return self.accounts.copy()

    def get_active_accounts(self) -> List[WhatsAppAccount]:
        """Получение только активных аккаунтов"""
        return [acc for acc in self.accounts if acc.enabled]

    def load_accounts(self, accounts_data: List[Dict]) -> int:
        """Загрузка аккаунтов из списка словарей"""
        count = 0
        for data in accounts_data:
            try:
                account = WhatsAppAccount.from_dict(data)
                if self.add_account(account):
                    count += 1
            except Exception as e:
                logger.error(f"Failed to load account: {str(e)}")
        return count

    def save_accounts(self) -> List[Dict]:
        """Сохранение аккаунтов в список словарей"""
        return [acc.to_dict() for acc in self.accounts]

    def clear(self):
        """Очистка всех аккаунтов"""
        self.accounts.clear()
        self._account_index.clear()
        logger.info("Cleared all accounts")

    def __len__(self) -> int:
        """Количество аккаунтов"""
        return len(self.accounts)

    def __contains__(self, phone: str) -> bool:
        """Проверка наличия аккаунта"""
        return phone in self._account_index