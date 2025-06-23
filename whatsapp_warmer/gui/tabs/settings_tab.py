from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox
from PyQt6.QtCore import pyqtSignal
from whatsapp_warmer.utils.logger import get_logger

logger = get_logger(__name__)


class SettingsTab(QWidget):
    """Вкладка настроек приложения"""

    settings_changed = pyqtSignal(dict)  # Сигнал при изменении настроек

    def __init__(self, initial_settings=None):
        super().__init__()
        self.settings = initial_settings or {}
        self._setup_ui()

    def _setup_ui(self):
        """Инициализация пользовательского интерфейса"""
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Поле для API ключа
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Введите API ключ")
        self.api_key_input.textChanged.connect(self._on_settings_changed)
        form_layout.addRow("API Ключ:", self.api_key_input)

        # Настройка интервала проверки
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 3600)
        self.interval_spin.setSuffix(" сек")
        self.interval_spin.valueChanged.connect(self._on_settings_changed)
        form_layout.addRow("Интервал проверки:", self.interval_spin)

        # Загрузка начальных настроек
        self._load_settings()

        layout.addLayout(form_layout)
        layout.addStretch()

    def _load_settings(self):
        """Загрузка начальных настроек"""
        if 'api_key' in self.settings:
            self.api_key_input.setText(self.settings['api_key'])
        if 'check_interval' in self.settings:
            self.interval_spin.setValue(self.settings['check_interval'])

    def _on_settings_changed(self):
        """Обработчик изменений настроек"""
        self.settings = {
            'api_key': self.api_key_input.text(),
            'check_interval': self.interval_spin.value()
        }
        self.settings_changed.emit(self.settings)
        logger.info("Настройки обновлены")

    def get_settings(self) -> dict:
        """Получение текущих настроек"""
        return self.settings