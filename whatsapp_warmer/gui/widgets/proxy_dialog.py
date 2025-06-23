from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QPushButton, QLabel,
    QMessageBox, QSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QIntValidator
from core.models.proxy import ProxyConfig
from typing import Optional


class ProxySettingsDialog(QDialog):
    """Диалог настройки прокси с проверкой валидности"""
    proxy_validated = pyqtSignal(bool)

    def __init__(self, proxy_config: Optional[ProxyConfig] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки прокси")
        self.setWindowIcon(QIcon("assets/icons/proxy.png"))
        self.setMinimumWidth(400)

        self.proxy = proxy_config or ProxyConfig(host="", port=0)
        self._setup_ui()
        self._load_proxy_settings()

    def _setup_ui(self):
        """Инициализация интерфейса"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        self.layout.setSpacing(15)

        # Форма настроек
        self.form_layout = QFormLayout()
        self.form_layout.setVerticalSpacing(10)

        # Тип прокси
        self.type_combo = QComboBox()
        self.type_combo.addItems(["HTTP", "HTTPS", "SOCKS4", "SOCKS5"])
        self.type_combo.currentTextChanged.connect(self._update_proxy_type)

        # Хост и порт
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("example.com или IP-адрес")

        self.port_input = QLineEdit()
        self.port_input.setValidator(QIntValidator(1, 65535))
        self.port_input.setPlaceholderText("8080")

        # Аутентификация
        self.auth_checkbox = QCheckBox("Требуется аутентификация")
        self.auth_checkbox.toggled.connect(self._toggle_auth_fields)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("логин")
        self.username_input.setEnabled(False)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setEnabled(False)

        # Тест соединения
        self.test_btn = QPushButton("Проверить соединение")
        self.test_btn.setIcon(QIcon("assets/icons/test.png"))
        self.test_btn.clicked.connect(self._test_connection)

        self.test_label = QLabel()
        self.test_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.test_label.setWordWrap(True)

        # Кнопки
        self.button_layout = QHBoxLayout()

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setIcon(QIcon("assets/icons/save.png"))
        self.save_btn.clicked.connect(self.accept)

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setIcon(QIcon("assets/icons/cancel.png"))
        self.cancel_btn.clicked.connect(self.reject)

        self.button_layout.addStretch()
        self.button_layout.addWidget(self.save_btn)
        self.button_layout.addWidget(self.cancel_btn)

        # Добавление элементов в форму
        self.form_layout.addRow("Тип прокси:", self.type_combo)
        self.form_layout.addRow("Хост:", self.host_input)
        self.form_layout.addRow("Порт:", self.port_input)
        self.form_layout.addRow(self.auth_checkbox)
        self.form_layout.addRow("Логин:", self.username_input)
        self.form_layout.addRow("Пароль:", self.password_input)
        self.form_layout.addRow(self.test_btn)
        self.form_layout.addRow(self.test_label)

        # Сборка интерфейса
        self.layout.addLayout(self.form_layout)
        self.layout.addLayout(self.button_layout)

    def _load_proxy_settings(self):
        """Загрузка текущих настроек прокси"""
        if self.proxy.host:
            self.host_input.setText(self.proxy.host)
            self.port_input.setText(str(self.proxy.port))

            # Установка типа прокси
            proxy_type = self.proxy.type.upper()
            if proxy_type == "HTTP":
                self.type_combo.setCurrentIndex(0)
            elif proxy_type == "HTTPS":
                self.type_combo.setCurrentIndex(1)
            elif proxy_type == "SOCKS4":
                self.type_combo.setCurrentIndex(2)
            elif proxy_type == "SOCKS5":
                self.type_combo.setCurrentIndex(3)

            # Аутентификация
            if self.proxy.username and self.proxy.password:
                self.auth_checkbox.setChecked(True)
                self.username_input.setText(self.proxy.username)
                self.password_input.setText(self.proxy.password)

    def _toggle_auth_fields(self, checked: bool):
        """Переключение полей аутентификации"""
        self.username_input.setEnabled(checked)
        self.password_input.setEnabled(checked)

        if not checked:
            self.username_input.clear()
            self.password_input.clear()

    def _update_proxy_type(self, proxy_type: str):
        """Обновление типа прокси"""
        self.proxy.type = proxy_type.lower()

    def _test_connection(self):
        """Тестирование соединения через прокси"""
        if not self._validate_inputs():
            return

        # Здесь должна быть реальная проверка соединения
        # В демо-версии просто имитация

        from PyQt6.QtCore import QTimer
        self.test_btn.setEnabled(False)
        self.test_label.setText("Проверка соединения...")
        self.test_label.setStyleSheet("color: #FFA000;")  # Оранжевый

        # Имитация задержки проверки
        QTimer.singleShot(2000, self._simulate_connection_test)

    def _simulate_connection_test(self):
        """Имитация проверки соединения (заглушка)"""
        import random
        success = random.random() > 0.3  # 70% успешных проверок

        if success:
            self.test_label.setText("✓ Соединение успешно установлено")
            self.test_label.setStyleSheet("color: #4CAF50;")  # Зеленый
        else:
            self.test_label.setText("✗ Не удалось подключиться к прокси")
            self.test_label.setStyleSheet("color: #F44336;")  # Красный

        self.test_btn.setEnabled(True)
        self.proxy_validated.emit(success)

    def _validate_inputs(self) -> bool:
        """Проверка валидности введенных данных"""
        errors = []

        if not self.host_input.text().strip():
            errors.append("Укажите хост прокси")

        if not self.port_input.text().isdigit():
            errors.append("Укажите корректный порт")
        elif not (1 <= int(self.port_input.text()) <= 65535):
            errors.append("Порт должен быть в диапазоне 1-65535")

        if self.auth_checkbox.isChecked():
            if not self.username_input.text().strip():
                errors.append("Укажите логин для аутентификации")
            if not self.password_input.text().strip():
                errors.append("Укажите пароль для аутентификации")

        if errors:
            QMessageBox.warning(
                self,
                "Ошибка валидации",
                "\n".join(errors)
            )
            return False
        return True

    def get_proxy_settings(self) -> Optional[ProxyConfig]:
        """Получение настроек прокси"""
        if not self._validate_inputs():
            return None

        return ProxyConfig(
            host=self.host_input.text().strip(),
            port=int(self.port_input.text()),
            type=self.type_combo.currentText().lower(),
            username=self.username_input.text().strip() if self.auth_checkbox.isChecked() else None,
            password=self.password_input.text().strip() if self.auth_checkbox.isChecked() else None
        )

    def accept(self):
        """Обработчик подтверждения диалога"""
        if not self._validate_inputs():
            return

        self.proxy = self.get_proxy_settings()
        super().accept()