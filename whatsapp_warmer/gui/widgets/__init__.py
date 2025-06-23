"""
Кастомные виджеты для интерфейса

Компоненты:
- account_card: Карточка аккаунта
- proxy_dialog: Диалог настройки прокси
- phrase_editor: Редактор фраз
"""
from .account_card import AccountCard
from .proxy_dialog import ProxySettingsDialog
from .phrase_editor import PhraseEditor

__all__ = ['AccountCard', 'ProxySettingsDialog', 'PhraseEditor']