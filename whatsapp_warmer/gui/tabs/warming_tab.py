from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QProgressBar, QTextEdit, QSpinBox, QFormLayout,
    QMessageBox, QComboBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QTextCursor, QColor
from core.warming_engine import WarmingEngine
from typing import Dict, Optional
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)


class WarmingTab(QWidget):
    """Вкладка управления прогревом аккаунтов"""
    warming_started = pyqtSignal()
    warming_stopped = pyqtSignal()

    def __init__(self, warming_engine: WarmingEngine):
        super().__init__()
        self.warming_engine = warming_engine
        self._setup_ui()
        self._connect_signals()
        self._load_default_settings()

    def _setup_ui(self):
        """Инициализация интерфейса"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(15)

        # Панель управления
        self.control_group = QGroupBox("Управление прогревом")
        self.control_layout = QHBoxLayout(self.control_group)

        self.start_btn = QPushButton("Старт")
        self.start_btn.setIcon(QIcon("assets/icons/start.png"))
        self.start_btn.setObjectName("startButton")

        self.stop_btn = QPushButton("Стоп")
        self.stop_btn.setIcon(QIcon("assets/icons/stop.png"))
        self.stop_btn.setEnabled(False)
        self.stop_btn.setObjectName("stopButton")

        self.pause_btn = QPushButton("Пауза")
        self.pause_btn.setIcon(QIcon("assets/icons/pause.png"))
        self.pause_btn.setEnabled(False)

        self.control_layout.addWidget(self.start_btn)
        self.control_layout.addWidget(self.pause_btn)
        self.control_layout.addWidget(self.stop_btn)
        self.control_layout.addStretch()

        # Настройки прогрева
        self.settings_group = QGroupBox("Настройки прогрева")
        settings_layout = QFormLayout(self.settings_group)

        self.rounds_spin = QSpinBox()
        self.rounds_spin.setRange(1, 100)
        self.rounds_spin.setToolTip("Количество циклов прогрева")

        self.min_delay_spin = QSpinBox()
        self.min_delay_spin.setRange(5, 3600)
        self.min_delay_spin.setSuffix(" сек")

        self.max_delay_spin = QSpinBox()
        self.max_delay_spin.setRange(5, 3600)
        self.max_delay_spin.setSuffix(" сек")

        self.messages_spin = QSpinBox()
        self.messages_spin.setRange(1, 50)
        self.messages_spin.setToolTip("Сообщений на аккаунт за раунд")

        self.round_delay_spin = QSpinBox()
        self.round_delay_spin.setRange(10, 86400)
        self.round_delay_spin.setSuffix(" сек")

        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "Случайные пары",
            "Кольцевая переписка",
            "Групповой чат"
        ])

        settings_layout.addRow("Количество раундов:", self.rounds_spin)
        settings_layout.addRow("Мин. задержка:", self.min_delay_spin)
        settings_layout.addRow("Макс. задержка:", self.max_delay_spin)
        settings_layout.addRow("Сообщений за раунд:", self.messages_spin)
        settings_layout.addRow("Задержка между раундами:", self.round_delay_spin)
        settings_layout.addRow("Стратегия:", self.strategy_combo)

        # Прогресс и логи
        self.progress_group = QGroupBox("Прогресс")
        progress_layout = QVBoxLayout(self.progress_group)

        self.progress_bar = QProgressBar()
        self.progress_bar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.time_label = QLabel("Осталось: --:--:--")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_label = QLabel("Статус: Ожидание запуска")
        self.status_label.setWordWrap(True)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setPlaceholderText("Логи прогрева...")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.log_area)

        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.time_label)
        progress_layout.addWidget(self.status_label)
        progress_layout.addWidget(scroll)

        # Сборка основного интерфейса
        self.layout.addWidget(self.control_group)
        self.layout.addWidget(self.settings_group, stretch=1)
        self.layout.addWidget(self.progress_group, stretch=2)

    def _connect_signals(self):
        """Подключение сигналов"""
        self.start_btn.clicked.connect(self.start_warming)
        self.stop_btn.clicked.connect(self.stop_warming)
        self.pause_btn.clicked.connect(self.toggle_pause)

        # Сигналы от движка прогрева
        self.warming_engine.progress_updated.connect(self.update_progress)
        self.warming_engine.account_activity.connect(self.log_activity)
        self.warming_engine.error_occurred.connect(self.log_error)
        self.warming_engine.warming_completed.connect(self.on_warming_complete)

    def _load_default_settings(self):
        """Загрузка настроек по умолчанию"""
        default_settings = {
            'rounds': 3,
            'min_delay': 15,
            'max_delay': 45,
            'messages_per_round': 2,
            'round_delay': 120
        }

        self.rounds_spin.setValue(default_settings['rounds'])
        self.min_delay_spin.setValue(default_settings['min_delay'])
        self.max_delay_spin.setValue(default_settings['max_delay'])
        self.messages_spin.setValue(default_settings['messages_per_round'])
        self.round_delay_spin.setValue(default_settings['round_delay'])

    def get_current_settings(self) -> Dict:
        """Получение текущих настроек"""
        return {
            'rounds': self.rounds_spin.value(),
            'min_delay': self.min_delay_spin.value(),
            'max_delay': self.max_delay_spin.value(),
            'messages_per_round': self.messages_spin.value(),
            'round_delay': self.round_delay_spin.value(),
            'strategy': self.strategy_combo.currentText()
        }

    def start_warming(self):
        """Запуск процесса прогрева"""
        if self.warming_engine._running:
            logger.warning("Прогрев уже запущен")
            return

        settings = self.get_current_settings()
        if settings['min_delay'] > settings['max_delay']:
            QMessageBox.warning(self, "Ошибка", "Минимальная задержка не может быть больше максимальной")
            return

        self.warming_engine.update_settings(settings)

        try:
            self.warming_engine.start_warming()
            self._update_controls(True)
            self.warming_started.emit()
            self.log_message("=== Прогрев запущен ===")
        except Exception as e:
            logger.error(f"Ошибка запуска прогрева: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось запустить прогрев: {str(e)}")

    def stop_warming(self):
        """Остановка прогрева"""
        if not self.warming_engine._running:
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы уверены, что хотите остановить прогрев?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.warming_engine.stop_warming()
            self.log_message("=== Прогрев принудительно остановлен ===")
            self._update_controls(False)
            self.warming_stopped.emit()

    def toggle_pause(self):
        """Пауза/продолжение прогрева"""
        # Реализация паузы требует модификации WarmingEngine
        # В текущей версии это заглушка
        if self.pause_btn.text() == "Пауза":
            self.pause_btn.setText("Продолжить")
            self.log_message("=== Прогрев на паузе ===")
        else:
            self.pause_btn.setText("Пауза")
            self.log_message("=== Прогрев продолжен ===")

    def update_progress(self, percent: int, status: str):
        """Обновление прогресса"""
        self.progress_bar.setValue(percent)
        self.status_label.setText(f"Статус: {status}")

        # Расчет оставшегося времени (примерный)
        if percent > 0:
            elapsed = self.warming_engine._current_round - 1
            remaining = self.warming_engine.settings['rounds'] - elapsed
            round_time = (self.warming_engine.settings['min_delay'] +
                          self.warming_engine.settings['max_delay']) / 2
            total_seconds = int(remaining * round_time)
            time_str = str(timedelta(seconds=total_seconds))
            self.time_label.setText(f"Осталось: {time_str}")

    def log_activity(self, phone: str, activity: str):
        """Логирование активности аккаунта"""
        if "message_sent" in activity:
            _, target, msg = activity.split(":")
            text = f"[MSG] {phone} -> {target}: {msg}"
            self.log_message(text, QColor("#2E7D32"))  # Зеленый
        elif "whatsapp_loaded" in activity:
            self.log_message(f"[LOAD] {phone}: WhatsApp загружен", QColor("#1565C0"))  # Синий
        else:
            self.log_message(f"[ACT] {phone}: {activity}")

    def log_error(self, context: str, error: str):
        """Логирование ошибок"""
        self.log_message(f"[ERROR] {context}: {error}", QColor("#C62828"))  # Красный
        if "critical" in error.lower():
            self.stop_warming()

    def log_message(self, message: str, color: Optional[QColor] = None):
        """Добавление сообщения в лог"""
        cursor = self.log_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        if color:
            format = cursor.charFormat()
            format.setForeground(color)
            cursor.setCharFormat(format)

        cursor.insertText(message + "\n")
        self.log_area.setTextCursor(cursor)
        self.log_area.ensureCursorVisible()

    def on_warming_complete(self, success: bool):
        """Обработчик завершения прогрева"""
        self._update_controls(False)
        if success:
            self.log_message("=== Прогрев успешно завершен ===", QColor("#2E7D32"))
            self.progress_bar.setValue(100)
            self.status_label.setText("Статус: Завершено")
        else:
            self.log_message("=== Прогрев завершен с ошибками ===", QColor("#C62828"))

    def _update_controls(self, is_running: bool):
        """Обновление состояния кнопок"""
        self.start_btn.setEnabled(not is_running)
        self.stop_btn.setEnabled(is_running)
        self.pause_btn.setEnabled(is_running)

        self.rounds_spin.setEnabled(not is_running)
        self.min_delay_spin.setEnabled(not is_running)
        self.max_delay_spin.setEnabled(not is_running)
        self.messages_spin.setEnabled(not is_running)
        self.round_delay_spin.setEnabled(not is_running)
        self.strategy_combo.setEnabled(not is_running)

    def clear_logs(self):
        """Очистка логов"""
        self.log_area.clear()