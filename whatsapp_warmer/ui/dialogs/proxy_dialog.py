from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QCheckBox,
    QDialogButtonBox,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIntValidator
from whatsapp_warmer.models.proxy import ProxyConfig


class ProxySettingsDialog(QDialog):
    """Диалог настройки прокси для аккаунта"""
    proxy_saved = pyqtSignal(dict)  # Сигнал с настройками прокси

    def __init__(self, proxy_config: ProxyConfig = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки прокси")
        self.setFixedSize(400, 300)

        # Инициализация UI
        self.setup_ui()

        # Загрузка переданных настроек
        if proxy_config:
            self.load_proxy_settings(proxy_config)

    def setup_ui(self):
        """Инициализация интерфейса"""
        layout = QFormLayout(self)

        # Чекбокс активации прокси
        self.enable_checkbox = QCheckBox("Использовать прокси")
        self.enable_checkbox.stateChanged.connect(self.toggle_proxy_fields)
        layout.addRow(self.enable_checkbox)

        # Тип прокси
        self.type_combo = QComboBox()
        self.type_combo.addItems(["HTTP", "SOCKS4", "SOCKS5"])
        layout.addRow("Тип прокси:", self.type_combo)

        # Хост и порт
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("example.com или IP-адрес")
        layout.addRow("Хост прокси:", self.host_input)

        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("8080")
        self.port_input.setValidator(QIntValidator(1, 65535))
        layout.addRow("Порт прокси:", self.port_input)

        # Аутентификация
        self.auth_checkbox = QCheckBox("Требуется аутентификация")
        self.auth_checkbox.stateChanged.connect(self.toggle_auth_fields)
        layout.addRow(self.auth_checkbox)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("логин")
        layout.addRow("Логин:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Пароль:", self.password_input)

        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.validate_and_save)
        button_box.rejected.connect(self.reject)

        layout.addRow(button_box)

        # Начальное состояние
        self.toggle_proxy_fields(False)
        self.toggle_auth_fields(False)

    def toggle_proxy_fields(self, state):
        """Активация/деактивация полей прокси"""
        enabled = state == Qt.CheckState.Checked.value
        self.type_combo.setEnabled(enabled)
        self.host_input.setEnabled(enabled)
        self.port_input.setEnabled(enabled)
        self.auth_checkbox.setEnabled(enabled)

        if not enabled:
            self.auth_checkbox.setChecked(False)
            self.toggle_auth_fields(False)

    def toggle_auth_fields(self, state):
        """Активация/деактивация полей аутентификации"""
        enabled = state == Qt.CheckState.Checked.value
        self.username_input.setEnabled(enabled)
        self.password_input.setEnabled(enabled)

    def load_proxy_settings(self, proxy: ProxyConfig):
        """Загрузка существующих настроек прокси"""
        self.enable_checkbox.setChecked(proxy.enabled)
        self.toggle_proxy_fields(proxy.enabled)

        if proxy.type:
            index = self.type_combo.findText(proxy.type.upper())
            if index >= 0:
                self.type_combo.setCurrentIndex(index)

        self.host_input.setText(proxy.host or "")
        self.port_input.setText(str(proxy.port) if proxy.port else "")

        has_auth = bool(proxy.username and proxy.password)
        self.auth_checkbox.setChecked(has_auth)
        self.toggle_auth_fields(has_auth)

        self.username_input.setText(proxy.username or "")
        self.password_input.setText(proxy.password or "")

    def validate_and_save(self):
        """Валидация и сохранение настроек"""
        if not self.enable_checkbox.isChecked():
            self.proxy_saved.emit({"enabled": False})
            self.accept()
            return

        # Проверка обязательных полей
        host = self.host_input.text().strip()
        port = self.port_input.text().strip()

        if not host or not port:
            QMessageBox.warning(
                self,
                "Ошибка",
                "Хост и порт прокси обязательны для заполнения",
                QMessageBox.StandardButton.Ok
            )
            return

        if self.auth_checkbox.isChecked():
            username = self.username_input.text().strip()
            password = self.password_input.text().strip()

            if not username or not password:
                QMessageBox.warning(
                    self,
                    "Ошибка",
                    "Логин и пароль обязательны при включенной аутентификации",
                    QMessageBox.StandardButton.Ok
                )
                return
        else:
            username = password = ""

        # Формируем конфигурацию прокси
        proxy_config = {
            "enabled": True,
            "type": self.type_combo.currentText().lower(),
            "host": host,
            "port": int(port),
            "username": username,
            "password": password
        }

        self.proxy_saved.emit(proxy_config)
        self.accept()

    @staticmethod
    def get_proxy_settings(proxy: ProxyConfig = None, parent=None) -> dict:
        """
        Статический метод для быстрого вызова диалога
        Возвращает конфигурацию прокси или пустой словарь
        """
        dialog = ProxySettingsDialog(proxy, parent)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            return dialog.proxy_config
        return {}