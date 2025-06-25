from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QLineEdit, QLabel, QComboBox,
    QAbstractItemView, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime
from whatsapp_warmer.utils.logger import get_logger
from whatsapp_warmer.core.models.account import WhatsAppAccount
from whatsapp_warmer.core.models.proxy import ProxyConfig
from typing import Optional, List
from datetime import datetime

logger = get_logger(__name__)


class AccountsTab(QWidget):
    """Полнофункциональная вкладка управления аккаунтами с поддержкой прокси"""

    # Сигналы
    account_added = pyqtSignal(dict)
    account_updated = pyqtSignal(str, dict)
    account_removed = pyqtSignal(str)
    proxy_changed = pyqtSignal(str, object)

    def __init__(self, account_manager, proxy_handler=None):
        super().__init__()
        self.logger = logger.getChild('AccountsTab')
        self.account_manager = account_manager
        self.proxy_handler = proxy_handler

        self._init_ui()
        self._setup_context_menu()
        self._load_accounts()

        # Обновляем список при изменении данных
        self.account_manager.accounts_changed.connect(self._load_accounts)

    def _init_ui(self):
        """Инициализация основного интерфейса"""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Панель инструментов
        toolbar = QHBoxLayout()

        self.add_btn = QPushButton("➕ Добавить")
        self.add_btn.clicked.connect(self._show_add_dialog)
        toolbar.addWidget(self.add_btn)

        self.import_btn = QPushButton("📁 Импорт")
        self.import_btn.clicked.connect(self._import_accounts)
        toolbar.addWidget(self.import_btn)

        self.export_btn = QPushButton("📤 Экспорт")
        self.export_btn.clicked.connect(self._export_accounts)
        toolbar.addWidget(self.export_btn)

        main_layout.addLayout(toolbar)

        # Таблица аккаунтов
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Номер", "Статус", "Прокси", "Активность", "Действия"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.verticalHeader().setVisible(False)
        main_layout.addWidget(self.table)

    def _setup_context_menu(self):
        """Настройка контекстного меню для таблицы"""
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

    def _load_accounts(self):
        """Загрузка и отображение аккаунтов в таблице"""
        self.table.setRowCount(0)

        for account in self.account_manager.get_all_accounts():
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Заполняем данные
            self._fill_account_row(row, account)

    def _fill_account_row(self, row: int, account: WhatsAppAccount):
        """Заполнение строки таблицы данными аккаунта"""
        # ID
        self.table.setItem(row, 0, QTableWidgetItem(str(account.id)))

        # Номер телефона
        phone_item = QTableWidgetItem(account.phone)
        phone_item.setData(Qt.ItemDataRole.UserRole, account.id)
        self.table.setItem(row, 1, phone_item)

        # Статус
        status_item = QTableWidgetItem()
        status_item.setText("✅ Активен" if account.enabled else "❌ Неактивен")
        status_item.setForeground(Qt.GlobalColor.darkGreen if account.enabled else Qt.GlobalColor.red)
        self.table.setItem(row, 2, status_item)

        # Прокси
        proxy_text = f"{account.proxy.host}:{account.proxy.port}" if account.proxy else "Нет"
        self.table.setItem(row, 3, QTableWidgetItem(proxy_text))

        # Активность
        last_active = account.last_active.strftime("%d.%m.%Y %H:%M") if account.last_active else "Никогда"
        self.table.setItem(row, 4, QTableWidgetItem(last_active))

        # Кнопки действий
        action_widget = QWidget()
        action_layout = QHBoxLayout()
        action_widget.setLayout(action_layout)

        edit_btn = QPushButton("✏️")
        edit_btn.clicked.connect(lambda: self._edit_account(account.id))
        action_layout.addWidget(edit_btn)

        toggle_btn = QPushButton("🔄")
        toggle_btn.clicked.connect(lambda: self._toggle_account(account.id))
        action_layout.addWidget(toggle_btn)

        remove_btn = QPushButton("🗑️")
        remove_btn.clicked.connect(lambda: self._remove_account(account.id))
        action_layout.addWidget(remove_btn)

        self.table.setCellWidget(row, 5, action_widget)

    def _show_add_dialog(self):
        """Диалог добавления нового аккаунта"""
        dialog = AccountDialog(self.account_manager, self.proxy_handler, self)
        if dialog.exec():
            account_data = dialog.get_account_data()
            try:
                self.account_manager.add_account(account_data)
                self.account_added.emit(account_data)
            except Exception as e:
                self._show_error(f"Ошибка добавления: {str(e)}")

    def _edit_account(self, account_id: str):
        """Редактирование существующего аккаунта"""
        account = self.account_manager.get_account(account_id)
        if not account:
            return

        dialog = AccountDialog(
            self.account_manager,
            self.proxy_handler,
            self,
            edit_mode=True,
            account=account
        )

        if dialog.exec():
            updated_data = dialog.get_account_data()
            try:
                self.account_manager.update_account(account_id, updated_data)
                self.account_updated.emit(account_id, updated_data)
            except Exception as e:
                self._show_error(f"Ошибка обновления: {str(e)}")

    def _toggle_account(self, account_id: str):
        """Переключение статуса аккаунта"""
        try:
            account = self.account_manager.get_account(account_id)
            if account:
                account.enabled = not account.enabled
                account.last_updated = datetime.now()
                self.account_manager.save_to_file()
                self._load_accounts()
        except Exception as e:
            self._show_error(f"Ошибка переключения: {str(e)}")

    def _remove_account(self, account_id: str):
        """Удаление аккаунта с подтверждением"""
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите удалить этот аккаунт?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.account_manager.remove_account(account_id)
                self.account_removed.emit(account_id)
            except Exception as e:
                self._show_error(f"Ошибка удаления: {str(e)}")

    def _show_context_menu(self, position):
        """Показ контекстного меню"""
        menu = QMenu()

        selected_row = self.table.rowAt(position.y())
        if selected_row >= 0:
            account_id = self.table.item(selected_row, 0).text()

            edit_action = menu.addAction("Редактировать")
            edit_action.triggered.connect(lambda: self._edit_account(account_id))

            toggle_action = menu.addAction("Вкл/Выкл")
            toggle_action.triggered.connect(lambda: self._toggle_account(account_id))

            remove_action = menu.addAction("Удалить")
            remove_action.triggered.connect(lambda: self._remove_account(account_id))

            menu.addSeparator()

        refresh_action = menu.addAction("Обновить список")
        refresh_action.triggered.connect(self._load_accounts)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def _import_accounts(self):
        """Импорт аккаунтов из файла"""
        # Реализация импорта...
        pass

    def _export_accounts(self):
        """Экспорт аккаунтов в файл"""
        # Реализация экспорта...
        pass

    def _show_error(self, message: str):
        """Показ сообщения об ошибке"""
        QMessageBox.critical(self, "Ошибка", message)
        self.logger.error(message)


class AccountDialog(QDialog):
    """Диалоговое окно для добавления/редактирования аккаунта"""

    def __init__(self, account_manager, proxy_handler=None, parent=None, edit_mode=False, account=None):
        super().__init__(parent)
        self.account_manager = account_manager
        self.proxy_handler = proxy_handler
        self.edit_mode = edit_mode
        self.account = account

        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса диалога"""
        self.setWindowTitle("Редактировать аккаунт" if self.edit_mode else "Добавить аккаунт")
        layout = QFormLayout()
        self.setLayout(layout)

        # Поле номера телефона
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("79XXXXXXXXX")
        if self.edit_mode and self.account:
            self.phone_edit.setText(self.account.phone)
            self.phone_edit.setEnabled(False)  # Нельзя менять номер при редактировании
        layout.addRow("Номер телефона:", self.phone_edit)

        # Выбор прокси
        if self.proxy_handler:
            self.proxy_combo = QComboBox()
            self._load_proxies()
            layout.addRow("Прокси:", self.proxy_combo)

        # Кнопки
        btn_box = QDialogButtonBox()
        btn_box.addButton("Сохранить", QDialogButtonBox.ButtonRole.AcceptRole)
        btn_box.addButton("Отмена", QDialogButtonBox.ButtonRole.RejectRole)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addRow(btn_box)

    def _load_proxies(self):
        """Загрузка списка прокси в комбобокс"""
        self.proxy_combo.clear()
        self.proxy_combo.addItem("Без прокси", None)

        for proxy in self.proxy_handler.get_all_proxies():
            self.proxy_combo.addItem(
                f"{proxy.host}:{proxy.port} ({proxy.type})",
                proxy
            )

        if self.edit_mode and self.account and self.account.proxy:
            index = self.proxy_combo.findData(self.account.proxy)
            if index >= 0:
                self.proxy_combo.setCurrentIndex(index)

    def get_account_data(self) -> dict:
        """Получение данных аккаунта из формы"""
        data = {
            'phone': self.phone_edit.text().strip(),
            'enabled': True
        }

        if self.proxy_handler:
            data['proxy'] = self.proxy_combo.currentData()

        return data