from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QDialog, QMessageBox,
                             QFormLayout, QLineEdit, QComboBox, QHeaderView,
                             QAbstractItemView, QLabel, QInputDialog)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QIcon
from whatsapp_warmer.core.models.account import WhatsAppAccount
from whatsapp_warmer.core.models.proxy import ProxyConfig
from whatsapp_warmer.utils.helpers import get_resource_path, validate_phone
from whatsapp_warmer.utils.logger import get_logger

logger = get_logger(__name__)


class AccountDialog(QDialog):
    """Диалоговое окно для добавления/редактирования аккаунта"""

    account_saved = pyqtSignal(dict)

    def __init__(self, account_data=None, proxy_list=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить аккаунт" if not account_data else "Редактировать аккаунт")
        self.setModal(True)
        self.setFixedSize(400, 350)

        self.account_data = account_data or {}
        self.proxy_list = proxy_list or []
        self._init_ui()
        self._load_account_data()

    def _init_ui(self):
        """Инициализация интерфейса"""
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # Поля формы
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("79123456789")
        form_layout.addRow("Номер телефона:", self.phone_edit)

        # Выбор прокси
        self.proxy_combo = QComboBox()
        self.proxy_combo.addItem("Без прокси", None)
        for proxy in self.proxy_list:
            self.proxy_combo.addItem(
                f"{proxy.host}:{proxy.port} ({proxy.protocol})",
                proxy
            )
        form_layout.addRow("Прокси:", self.proxy_combo)

        # Кнопки
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self._save_account)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _load_account_data(self):
        """Загрузка данных аккаунта в форму"""
        if self.account_data:
            self.phone_edit.setText(self.account_data.get('phone', ''))

            # Установка выбранного прокси
            if 'proxy' in self.account_data and self.account_data['proxy']:
                for i in range(self.proxy_combo.count()):
                    proxy_data = self.proxy_combo.itemData(i)
                    if (proxy_data and
                            proxy_data.host == self.account_data['proxy']['host'] and
                            proxy_data.port == self.account_data['proxy']['port']):
                        self.proxy_combo.setCurrentIndex(i)
                        break

    def _save_account(self):
        """Сохранение данных аккаунта"""
        phone = self.phone_edit.text().strip()

        if not validate_phone(phone):
            QMessageBox.warning(self, "Ошибка", "Неверный формат номера телефона")
            return

        proxy = self.proxy_combo.currentData()

        account_data = {
            'phone': phone,
            'proxy': proxy.to_dict() if proxy else None
        }

        self.account_saved.emit(account_data)
        self.accept()


class AccountsTab(QWidget):
    """Вкладка для управления аккаунтами"""

    account_added = pyqtSignal()
    account_removed = pyqtSignal()
    account_updated = pyqtSignal(dict)

    def __init__(self, account_manager, proxy_handler, parent=None):
        super().__init__(parent)
        self.account_manager = account_manager
        self.proxy_handler = proxy_handler
        self._init_ui()
        self._load_accounts()

    def _init_ui(self):
        """Инициализация интерфейса"""
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Таблица аккаунтов
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(4)
        self.accounts_table.setHorizontalHeaderLabels([
            "Номер телефона",
            "Прокси",
            "Статус",
            "Действия"
        ])
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.accounts_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.accounts_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        # Кнопки управления
        self.add_btn = QPushButton("Добавить аккаунт")
        self.add_btn.setIcon(create_qt_icon('add.png'))
        self.add_btn.clicked.connect(self._add_account)

        self.remove_btn = QPushButton("Удалить выбранное")
        self.remove_btn.setIcon(QIcon(get_resource_path('icons/remove.png')))
        self.remove_btn.clicked.connect(self._remove_account)
        self.remove_btn.setEnabled(False)

        # Расположение элементов
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.remove_btn)
        button_layout.addStretch()

        self.layout.addWidget(self.accounts_table)
        self.layout.addLayout(button_layout)

        # Обработчики событий
        self.accounts_table.itemSelectionChanged.connect(
            lambda: self.remove_btn.setEnabled(len(self.accounts_table.selectedItems()) > 0)
        )

    def _load_accounts(self):
        """Загрузка аккаунтов в таблицу"""
        self.accounts_table.setRowCount(0)

        for account in self.account_manager.get_all_accounts():
            self._add_account_to_table(account)

    def _add_account_to_table(self, account):
        """Добавление аккаунта в таблицу"""
        row = self.accounts_table.rowCount()
        self.accounts_table.insertRow(row)

        # Номер телефона
        phone_item = QTableWidgetItem(account.phone)
        phone_item.setData(Qt.ItemDataRole.UserRole, account.phone)
        self.accounts_table.setItem(row, 0, phone_item)

        # Прокси
        proxy_text = "Без прокси"
        if account.proxy:
            proxy_text = f"{account.proxy.host}:{account.proxy.port}"
        self.accounts_table.setItem(row, 1, QTableWidgetItem(proxy_text))

        # Статус
        status_item = QTableWidgetItem("Активен" if account.enabled else "Неактивен")
        status_item.setForeground(Qt.GlobalColor.green if account.enabled else Qt.GlobalColor.red)
        self.accounts_table.setItem(row, 2, status_item)

        # Кнопки действий
        action_widget = QWidget()
        action_layout = QHBoxLayout()
        action_layout.setContentsMargins(0, 0, 0, 0)

        edit_btn = QPushButton()
        edit_btn.setIcon(QIcon(get_resource_path('icons/edit.png')))
        edit_btn.setToolTip("Редактировать")
        edit_btn.clicked.connect(lambda: self._edit_account(row))

        toggle_btn = QPushButton()
        toggle_btn.setIcon(QIcon(get_resource_path('icons/toggle.png')))
        toggle_btn.setToolTip("Активировать/Деактивировать")
        toggle_btn.clicked.connect(lambda: self._toggle_account(row))

        action_layout.addWidget(edit_btn)
        action_layout.addWidget(toggle_btn)
        action_widget.setLayout(action_layout)

        self.accounts_table.setCellWidget(row, 3, action_widget)

    def _add_account(self):
        """Добавление нового аккаунта"""
        dialog = AccountDialog(proxy_list=self.proxy_handler.get_all_proxies(), parent=self)
        dialog.account_saved.connect(self._handle_account_save)
        dialog.exec()

    def _edit_account(self, row):
        """Редактирование существующего аккаунта"""
        phone = self.accounts_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        account = self.account_manager.get_account(phone)

        if account:
            dialog = AccountDialog(
                account_data={
                    'phone': account.phone,
                    'proxy': account.proxy.to_dict() if account.proxy else None
                },
                proxy_list=self.proxy_handler.get_all_proxies(),
                parent=self
            )
            dialog.account_saved.connect(self._handle_account_update)
            dialog.exec()

    def _toggle_account(self, row):
        """Активация/деактивация аккаунта"""
        phone = self.accounts_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        account = self.account_manager.get_account(phone)

        if account:
            account.enabled = not account.enabled
            self._load_accounts()
            self.account_updated.emit({'phone': phone, 'enabled': account.enabled})

    def _remove_account(self):
        """Удаление выбранных аккаунтов"""
        selected_rows = set(index.row() for index in self.accounts_table.selectedIndexes())

        if not selected_rows:
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить {len(selected_rows)} аккаунт(ов)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            for row in selected_rows:
                phone = self.accounts_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
                self.account_manager.remove_account(phone)
                self.account_removed.emit()

            self._load_accounts()

    @pyqtSlot(dict)
    def _handle_account_save(self, account_data):
        """Обработка сохранения нового аккаунта"""
        proxy = None
        if account_data['proxy']:
            proxy = ProxyConfig(**account_data['proxy'])

        account = WhatsAppAccount(
            phone=account_data['phone'],
            proxy=proxy
        )

        if self.account_manager.add_account(account):
            self._load_accounts()
            self.account_added.emit()

    @pyqtSlot(dict)
    def _handle_account_update(self, account_data):
        """Обработка обновления аккаунта"""
        phone = account_data['phone']
        account = self.account_manager.get_account(phone)

        if account:
            proxy = None
            if account_data['proxy']:
                proxy = ProxyConfig(**account_data['proxy'])

            account.proxy = proxy
            self._load_accounts()
            self.account_updated.emit(account_data)

    def update_proxy_list(self, proxies):
        """Обновление списка прокси (для внешних вызовов)"""
        # В текущей реализации прокси обновляются при открытии диалога
        pass