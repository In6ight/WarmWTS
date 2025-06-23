from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton,
    QInputDialog, QMessageBox, QMenu, QLabel, QLineEdit, QComboBox,
    QFormLayout, QListWidgetItem, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction
from ..widgets.account_card import AccountCard
from ..widgets.proxy_dialog import ProxySettingsDialog
from core.models.account import WhatsAppAccount
from core.models.proxy import ProxyConfig
from utils.file_manager import write_json, read_json
from pathlib import Path
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)


class AccountsTab(QWidget):
    """Вкладка управления аккаунтами с поддержкой прокси"""
    account_selected = pyqtSignal(WhatsAppAccount)
    accounts_updated = pyqtSignal()

    def __init__(self, account_manager):
        super().__init__()
        self.account_manager = account_manager
        self._setup_ui()
        self._connect_signals()
        self.refresh_accounts_list()

    def _setup_ui(self):
        """Инициализация интерфейса"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(10)

        # Панель управления
        self.control_panel = QWidget()
        self.control_layout = QHBoxLayout(self.control_panel)
        self.control_layout.setContentsMargins(0, 0, 0, 0)

        # Кнопки управления
        self.btn_add = QPushButton("Добавить")
        self.btn_add.setIcon(QIcon("assets/icons/add.png"))
        self.btn_add.setToolTip("Добавить новый аккаунт")

        self.btn_remove = QPushButton("Удалить")
        self.btn_remove.setIcon(QIcon("assets/icons/remove.png"))
        self.btn_remove.setToolTip("Удалить выбранный аккаунт")

        self.btn_edit = QPushButton("Изменить")
        self.btn_edit.setIcon(QIcon("assets/icons/edit.png"))
        self.btn_edit.setToolTip("Изменить выбранный аккаунт")

        self.btn_import = QPushButton("Импорт")
        self.btn_import.setIcon(QIcon("assets/icons/import.png"))
        self.btn_import.setToolTip("Импортировать аккаунты из файла")

        self.btn_export = QPushButton("Экспорт")
        self.btn_export.setIcon(QIcon("assets/icons/export.png"))
        self.btn_export.setToolTip("Экспортировать аккаунты в файл")

        # Добавление кнопок на панель
        self.control_layout.addWidget(self.btn_add)
        self.control_layout.addWidget(self.btn_edit)
        self.control_layout.addWidget(self.btn_remove)
        self.control_layout.addStretch()
        self.control_layout.addWidget(self.btn_import)
        self.control_layout.addWidget(self.btn_export)

        # Список аккаунтов
        self.accounts_list = QListWidget()
        self.accounts_list.setAlternatingRowColors(True)
        self.accounts_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.accounts_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

        # Статус
        self.status_label = QLabel("Аккаунтов: 0")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Добавление элементов в основной лейаут
        self.layout.addWidget(self.control_panel)
        self.layout.addWidget(self.accounts_list)
        self.layout.addWidget(self.status_label)

    def _connect_signals(self):
        """Подключение сигналов и слотов"""
        self.btn_add.clicked.connect(self._add_account)
        self.btn_edit.clicked.connect(self._edit_account)
        self.btn_remove.clicked.connect(self._remove_account)
        self.btn_import.clicked.connect(self._import_accounts)
        self.btn_export.clicked.connect(self._export_accounts)
        self.accounts_list.customContextMenuRequested.connect(self._show_context_menu)
        self.accounts_list.itemDoubleClicked.connect(self._on_account_double_click)

    def refresh_accounts_list(self):
        """Обновление списка аккаунтов"""
        self.accounts_list.clear()

        for account in self.account_manager.get_all_accounts():
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, account)
            item.setSizeHint(QSize(0, 60))  # Фиксированная высота элемента

            widget = AccountCard(account)
            widget.proxy_settings_requested.connect(self._edit_proxy_settings)

            self.accounts_list.addItem(item)
            self.accounts_list.setItemWidget(item, widget)

        self._update_status()

    def _update_status(self):
        """Обновление статусной строки"""
        count = self.accounts_list.count()
        enabled = sum(1 for i in range(count) if self._get_account(i).enabled)
        self.status_label.setText(f"Аккаунтов: {count} (активных: {enabled})")

    def _get_account(self, index: int) -> Optional[WhatsAppAccount]:
        """Получение аккаунта по индексу"""
        if 0 <= index < self.accounts_list.count():
            item = self.accounts_list.item(index)
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _get_selected_account(self) -> Optional[WhatsAppAccount]:
        """Получение выбранного аккаунта"""
        selected = self.accounts_list.currentRow()
        return self._get_account(selected) if selected >= 0 else None

    def _add_account(self):
        """Добавление нового аккаунта"""
        phone, ok = QInputDialog.getText(
            self,
            "Добавить аккаунт",
            "Введите номер телефона:",
            flags=Qt.WindowType.WindowCloseButtonHint
        )

        if ok and phone:
            if not self._validate_phone(phone):
                QMessageBox.warning(self, "Ошибка", "Неверный формат номера телефона")
                return

            login_method = self._select_login_method()
            if login_method is None:
                return

            if self.account_manager.add_account(phone, login_method):
                self.refresh_accounts_list()
                self.accounts_updated.emit()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось добавить аккаунт")

    def _edit_account(self):
        """Редактирование существующего аккаунта"""
        account = self._get_selected_account()
        if not account:
            QMessageBox.warning(self, "Ошибка", "Выберите аккаунт для редактирования")
            return

        new_phone, ok = QInputDialog.getText(
            self,
            "Редактирование аккаунта",
            "Новый номер телефона:",
            text=account.phone
        )

        if ok and new_phone:
            if not self._validate_phone(new_phone):
                QMessageBox.warning(self, "Ошибка", "Неверный формат номера телефона")
                return

            login_method = self._select_login_method(account.login_method)
            if login_method is None:
                return

            if self.account_manager.update_account(account.phone, phone=new_phone, login_method=login_method):
                self.refresh_accounts_list()
                self.accounts_updated.emit()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось обновить аккаунт")

    def _remove_account(self):
        """Удаление аккаунта"""
        account = self._get_selected_account()
        if not account:
            QMessageBox.warning(self, "Ошибка", "Выберите аккаунт для удаления")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить аккаунт {account.phone}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.account_manager.remove_account(account.phone):
                self.refresh_accounts_list()
                self.accounts_updated.emit()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить аккаунт")

    def _edit_proxy_settings(self, account: WhatsAppAccount):
        """Редактирование настроек прокси для аккаунта"""
        dialog = ProxySettingsDialog(account.proxy, self)
        if dialog.exec():
            proxy_config = dialog.get_proxy_settings()
            if proxy_config and self.account_manager.update_account(
                    account.phone,
                    proxy=proxy_config
            ):
                self.refresh_accounts_list()
                self.accounts_updated.emit()

    def _import_accounts(self):
        """Импорт аккаунтов из файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Импорт аккаунтов",
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                data = read_json(file_path)
                if not isinstance(data, list):
                    raise ValueError("Invalid file format")

                imported = 0
                for item in data:
                    if isinstance(item, dict) and 'phone' in item:
                        proxy = ProxyConfig(**item.get('proxy', {})) if item.get('proxy') else None
                        account = WhatsAppAccount(
                            phone=item['phone'],
                            login_method=item.get('login_method', 'qr'),
                            proxy=proxy
                        )
                        if self.account_manager.add_account(account.phone, account.login_method):
                            if proxy:
                                self.account_manager.update_account(account.phone, proxy=proxy)
                            imported += 1

                self.refresh_accounts_list()
                self.accounts_updated.emit()
                QMessageBox.information(
                    self,
                    "Импорт завершен",
                    f"Успешно импортировано {imported} аккаунтов"
                )
            except Exception as e:
                logger.error(f"Ошибка импорта: {str(e)}")
                QMessageBox.critical(
                    self,
                    "Ошибка импорта",
                    f"Не удалось импортировать аккаунты: {str(e)}"
                )

    def _export_accounts(self):
        """Экспорт аккаунтов в файл"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт аккаунтов",
            "whatsapp_accounts.json",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            accounts = [acc.to_dict() for acc in self.account_manager.get_all_accounts()]
            if write_json(file_path, accounts):
                QMessageBox.information(
                    self,
                    "Экспорт завершен",
                    f"Успешно экспортировано {len(accounts)} аккаунтов"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Ошибка экспорта",
                    "Не удалось сохранить файл"
                )

    def _show_context_menu(self, position):
        """Отображение контекстного меню"""
        account = self._get_selected_account()
        if not account:
            return

        menu = QMenu()

        # Действия
        edit_action = QAction("Редактировать", self)
        edit_action.triggered.connect(self._edit_account)

        proxy_action = QAction("Настройки прокси", self)
        proxy_action.triggered.connect(lambda: self._edit_proxy_settings(account))

        toggle_action = QAction(
            "Деактивировать" if account.enabled else "Активировать",
            self
        )
        toggle_action.triggered.connect(lambda: self._toggle_account(account))

        remove_action = QAction("Удалить", self)
        remove_action.triggered.connect(self._remove_account)

        # Добавление действий
        menu.addAction(edit_action)
        menu.addAction(proxy_action)
        menu.addAction(toggle_action)
        menu.addSeparator()
        menu.addAction(remove_action)

        menu.exec(self.accounts_list.mapToGlobal(position))

    def _on_account_double_click(self, item):
        """Обработчик двойного клика по аккаунту"""
        account = item.data(Qt.ItemDataRole.UserRole)
        if account:
            self.account_selected.emit(account)

    def _toggle_account(self, account: WhatsAppAccount):
        """Активация/деактивация аккаунта"""
        if self.account_manager.update_account(
                account.phone,
                enabled=not account.enabled
        ):
            self.refresh_accounts_list()
            self.accounts_updated.emit()

    def _select_login_method(self, current: str = 'qr') -> Optional[str]:
        """Выбор метода входа"""
        methods = {
            'qr': 'QR-код',
            'phone': 'Номер телефона'
        }

        method, ok = QInputDialog.getItem(
            self,
            "Метод входа",
            "Выберите метод авторизации:",
            list(methods.values()),
            current=methods.get(current, 'qr'),
            editable=False
        )

        if ok and method:
            return next(k for k, v in methods.items() if v == method)
        return None

    @staticmethod
    def _validate_phone(phone: str) -> bool:
        """Валидация номера телефона"""
        cleaned = ''.join(c for c in phone if c.isdigit())
        return len(cleaned) >= 10 and cleaned.isdigit()

    def get_selected_accounts(self) -> List[WhatsAppAccount]:
        """Получение списка выбранных аккаунтов"""
        return [
            self._get_account(i)
            for i in range(self.accounts_list.count())
            if self.accounts_list.item(i).isSelected()
        ]