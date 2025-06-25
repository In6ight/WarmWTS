from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QComboBox,
    QDialogButtonBox, QMessageBox, QSpinBox, QVBoxLayout,
    QLabel, QTextEdit
)
from PyQt6.QtCore import Qt
from typing import Dict, Any, Optional
from whatsapp_warmer.utils.helpers import validate_phone


class AccountDialog(QDialog):
    def __init__(self, proxy_handler=None, parent=None, account=None):
        super().__init__(parent)
        self.proxy_handler = proxy_handler
        self.account = account
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Редактировать аккаунт" if self.account else "Добавить аккаунт")
        self.setMinimumWidth(400)

        layout = QFormLayout()
        self.setLayout(layout)

        # Поле номера телефона
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText("79XXXXXXXXX")
        if self.account:
            self.phone_edit.setText(self.account.phone)
            self.phone_edit.setEnabled(False)
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
        self.proxy_combo.clear()
        self.proxy_combo.addItem("Без прокси", None)

        if self.proxy_handler:
            for proxy in self.proxy_handler.get_all_proxies():
                self.proxy_combo.addItem(
                    f"{proxy.host}:{proxy.port} ({proxy.protocol})",
                    proxy
                )

        if self.account and self.account.proxy:
            index = self.proxy_combo.findData(self.account.proxy)
            if index >= 0:
                self.proxy_combo.setCurrentIndex(index)

    def _validate_and_accept(self):
        phone = self.phone_edit.text().strip()

        if not phone:
            QMessageBox.warning(self, "Ошибка", "Введите номер телефона")
            return

        if not validate_phone(phone):
            QMessageBox.warning(self, "Ошибка", "Неверный формат номера. Используйте 79XXXXXXXXX")
            return

        self.accept()

    def get_data(self) -> dict:
        data = {
            'phone': self.phone_edit.text().strip(),
            'enabled': True
        }

        if self.proxy_handler and hasattr(self, 'proxy_combo'):
            data['proxy'] = self.proxy_combo.currentData()

        return data


class SettingsDialog(QDialog):
    def __init__(self, config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.config = config
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(500)

        layout = QVBoxLayout()
        form = QFormLayout()

        # Настройки прогрева
        self.rounds_spin = QSpinBox()
        self.rounds_spin.setRange(1, 10)
        self.rounds_spin.setValue(self.config['warming'].get('rounds', 3))
        form.addRow("Количество раундов:", self.rounds_spin)

        self.min_delay_spin = QSpinBox()
        self.min_delay_spin.setRange(5, 300)
        self.min_delay_spin.setValue(self.config['warming'].get('min_delay', 15))
        form.addRow("Минимальная задержка (сек):", self.min_delay_spin)

        self.max_delay_spin = QSpinBox()
        self.max_delay_spin.setRange(5, 300)
        self.max_delay_spin.setValue(self.config['warming'].get('max_delay', 45))
        form.addRow("Максимальная задержка (сек):", self.max_delay_spin)

        self.messages_spin = QSpinBox()
        self.messages_spin.setRange(1, 20)
        self.messages_spin.setValue(self.config['warming'].get('messages_per_round', 2))
        form.addRow("Сообщений за раунд:", self.messages_spin)

        # Общие настройки
        self.tray_check = QComboBox()
        self.tray_check.addItems(["Да", "Нет"])
        self.tray_check.setCurrentIndex(0 if self.config.get('minimize_to_tray', True) else 1)
        form.addRow("Сворачивать в трей:", self.tray_check)

        layout.addLayout(form)

        # Кнопки
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_config(self) -> Dict[str, Any]:
        return {
            'window_maximized': self.config['window_maximized'],
            'window_geometry': self.config['window_geometry'],
            'minimize_to_tray': self.tray_check.currentIndex() == 0,
            'warming': {
                'rounds': self.rounds_spin.value(),
                'min_delay': self.min_delay_spin.value(),
                'max_delay': self.max_delay_spin.value(),
                'messages_per_round': self.messages_spin.value(),
                'round_delay': self.config['warming'].get('round_delay', 120)
            }
        }


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("О программе")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        title = QLabel("WhatsApp Warmer PRO")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        version = QLabel("Версия 1.0.0")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        desc = QTextEdit()
        desc.setReadOnly(True)
        desc.setPlainText(
            "Программа для прогрева аккаунтов WhatsApp.\n\n"
            "Автор: Ваше имя\n"
            "Контакты: ваш@email.com"
        )
        layout.addWidget(desc)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

        self.setLayout(layout)


class ProxyDialog(QDialog):
    def __init__(self, proxy_handler, parent=None, proxy=None):
        super().__init__(parent)
        self.proxy_handler = proxy_handler
        self.proxy = proxy
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("Редактировать прокси" if self.proxy else "Добавить прокси")
        self.setMinimumWidth(400)

        layout = QFormLayout()
        self.setLayout(layout)

        # Тип прокси
        self.type_combo = QComboBox()
        self.type_combo.addItems(["http", "socks4", "socks5"])
        layout.addRow("Тип:", self.type_combo)

        # Хост
        self.host_edit = QLineEdit()
        self.host_edit.setPlaceholderText("ip или домен")
        layout.addRow("Хост:", self.host_edit)

        # Порт
        self.port_edit = QSpinBox()
        self.port_edit.setRange(1, 65535)
        layout.addRow("Порт:", self.port_edit)

        # Логин
        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Необязательно")
        layout.addRow("Логин:", self.login_edit)

        # Пароль
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Необязательно")
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Пароль:", self.password_edit)

        # Заполнение данных при редактировании
        if self.proxy:
            self.type_combo.setCurrentText(self.proxy.protocol)
            self.host_edit.setText(self.proxy.host)
            self.port_edit.setValue(self.proxy.port)
            self.login_edit.setText(self.proxy.username or "")
            self.password_edit.setText(self.proxy.password or "")

        # Кнопки
        buttons = QDialogButtonBox()
        buttons.addButton("Сохранить", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton("Отмена", QDialogButtonBox.ButtonRole.RejectRole)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _validate_and_accept(self):
        host = self.host_edit.text().strip()

        if not host:
            QMessageBox.warning(self, "Ошибка", "Введите хост прокси")
            return

        self.accept()

    def get_data(self) -> dict:
        return {
            'protocol': self.type_combo.currentText(),
            'host': self.host_edit.text().strip(),
            'port': self.port_edit.value(),
            'username': self.login_edit.text().strip() or None,
            'password': self.password_edit.text().strip() or None
        }