from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox,
    QDialogButtonBox, QMessageBox, QSpinBox
)
from PyQt6.QtCore import Qt
from whatsapp_warmer.utils.helpers import validate_phone
from typing import Optional, Dict, Any

class AccountDialog(QDialog):
    def __init__(self, proxy_handler=None, parent=None, account=None):
        super().__init__(parent)
        self.proxy_handler = proxy_handler
        self.account = account
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Редактировать аккаунт" if self.account else "Добавить аккаунт")
        self.setMinimumWidth(400)

        layout = QFormLayout()
        self.setLayout(layout)

        # Поле номера телефона
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("79XXXXXXXXX")
        if self.account:
            self.phone_edit.setText(self.account.phone)
            self.phone_edit.setEnabled(False)  # Запрещаем менять номер при редактировании
        layout.addRow("Номер телефона:", self.phone_edit)

        # Прокси (если есть обработчик)
        if self.proxy_handler:
            self.proxy_combo = QComboBox()
            self._load_proxies()
            layout.addRow("Прокси:", self.proxy_combo)

        # Кнопки
        buttons = QDialogButtonBox()
        buttons.addButton("Сохранить", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("Отмена", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _load_proxies(self):
        """Загрузка доступных прокси в комбобокс"""
        self.proxy_combo.clear()
        self.proxy_combo.addItem("Без прокси", None)

        if self.proxy_handler:
            for proxy in self.proxy_handler.get_all_proxies():
                self.proxy_combo.addItem(
                    f"{proxy.host}:{proxy.port} ({proxy.type})",
                    proxy
                )

        # Установка текущего прокси для редактирования
        if self.account and self.account.proxy:
            index = self.proxy_combo.findData(self.account.proxy)
            if index >= 0:
                self.proxy_combo.setCurrentIndex(index)

    def _validate_and_accept(self):
        """Валидация данных перед принятием"""
        phone = self.phone_edit.text().strip()

        if not phone:
            QMessageBox.warning(self, "Ошибка", "Введите номер телефона")
            return

        if not validate_phone(phone):
            QMessageBox.warning(self, "Ошибка", "Неверный формат номера. Используйте 79XXXXXXXXX")
            return

        self.accept()

    def get_data(self) -> dict:
        """Получение данных из формы"""
        data = {
            'phone': self.phone_edit.text().strip(),
            'enabled': True
        }

        if self.proxy_handler and hasattr(self, 'proxy_combo'):
            data['proxy'] = self.proxy_combo.currentData()

        return data


class ProxyDialog(QDialog):
    """Диалоговое окно для добавления/редактирования прокси"""

    def __init__(self, proxy_handler, parent=None, proxy=None):
        """
        Args:
            proxy_handler: Обработчик прокси
            parent: Родительский виджет
            proxy: Существующий прокси для редактирования (None для создания нового)
        """
        super().__init__(parent)
        self.proxy_handler = proxy_handler
        self.proxy = proxy
        self._init_ui()

    def _init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Редактировать прокси" if self.proxy else "Добавить прокси")
        self.setMinimumWidth(400)

        layout = QFormLayout()
        self.setLayout(layout)

        # Тип прокси
        self.type_combo = QComboBox()
        self.type_combo.addItems(["HTTP", "SOCKS4", "SOCKS5"])
        layout.addRow("Тип:", self.type_combo)

        # Хост
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("ip или домен")
        layout.addRow("Хост:", self.host_edit)

        # Порт
        self.port_edit = QSpinBox()
        self.port_edit.setRange(1, 65535)
        layout.addRow("Порт:", self.port_edit)

        # Логин (опционально)
        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Необязательно")
        layout.addRow("Логин:", self.login_edit)

        # Пароль (опционально)
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Необязательно")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Пароль:", self.password_edit)

        # Заполняем данные для редактирования
        if self.proxy:
            self.type_combo.setCurrentText(self.proxy.type.upper())
            self.host_edit.setText(self.proxy.host)
            self.port_edit.setValue(self.proxy.port)
            self.login_edit.setText(self.proxy.login or "")
            self.password_edit.setText(self.proxy.password or "")

        # Кнопки
        buttons = QDialogButtonBox()
        buttons.addButton("Сохранить", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("Отмена", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _validate_and_accept(self):
        """Валидация данных перед принятием"""
        host = self.host_edit.text().strip()

        if not host:
            QMessageBox.warning(self, "Ошибка", "Введите хост прокси")
            return

        self.accept()

    def get_data(self) -> dict:
        """Получение данных прокси из формы"""
        return {
            'type': self.type_combo.currentText().lower(),
            'host': self.host_edit.text().strip(),
            'port': self.port_edit.value(),
            'login': self.login_edit.text().strip() or None,
            'password': self.password_edit.text().strip() or None
        }


class ImportDialog(QDialog):
    """Диалог импорта аккаунтов"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Импорт аккаунтов")
        layout = QFormLayout()
        self.setLayout(layout)

        # TODO: Реализация формы импорта
        # Можно добавить выбор файла, формата и опций

        buttons = QDialogButtonBox()
        buttons.addButton("Импорт", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("Отмена", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_import_options(self) -> dict:
        """Получение параметров импорта"""
        return {
            'format': 'json',  # Может быть csv, json и т.д.
            'options': {}
        }