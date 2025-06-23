from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QPushButton,
    QComboBox, QLabel, QFileDialog, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QTextCursor, QTextCharFormat, QColor, QIcon
from pathlib import Path
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List
import gzip
import re

logger = logging.getLogger(__name__)


class LogsTab(QWidget):
    """Вкладка для просмотра и анализа логов"""
    log_file_changed = pyqtSignal(str)

    def __init__(self, log_dir: Path = Path("logs")):
        super().__init__()
        self.log_dir = log_dir
        self.current_file: Optional[Path] = None
        self.log_filters = {
            "level": "ALL",
            "search_text": "",
            "time_range": None
        }
        self._setup_ui()
        self._connect_signals()
        self._load_last_log_file()

    def _setup_ui(self):
        """Инициализация интерфейса"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(10)

        # Панель управления
        self.control_panel = QWidget()
        self.control_layout = QHBoxLayout(self.control_panel)
        self.control_layout.setContentsMargins(0, 0, 0, 0)

        # Элементы управления
        self.file_combo = QComboBox()
        self.file_combo.setMinimumWidth(200)

        self.level_combo = QComboBox()
        self.level_combo.addItems(["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск...")

        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.setIcon(QIcon("assets/icons/refresh.png"))

        self.clear_btn = QPushButton("Очистить")
        self.clear_btn.setIcon(QIcon("assets/icons/clear.png"))

        self.export_btn = QPushButton("Экспорт")
        self.export_btn.setIcon(QIcon("assets/icons/export.png"))

        # Добавление элементов на панель
        self.control_layout.addWidget(QLabel("Файл:"))
        self.control_layout.addWidget(self.file_combo)
        self.control_layout.addWidget(QLabel("Уровень:"))
        self.control_layout.addWidget(self.level_combo)
        self.control_layout.addWidget(self.search_input)
        self.control_layout.addWidget(self.refresh_btn)
        self.control_layout.addWidget(self.clear_btn)
        self.control_layout.addWidget(self.export_btn)
        self.control_layout.addStretch()

        # Основное поле логов
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.log_view.setStyleSheet("font-family: 'Courier New'; font-size: 10pt;")

        # Статус бар
        self.status_bar = QLabel()
        self.status_bar.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Добавление в основной лейаут
        self.layout.addWidget(self.control_panel)
        self.layout.addWidget(self.log_view)
        self.layout.addWidget(self.status_bar)

        # Таймер для автообновления
        self.refresh_timer = QTimer()
        self.refresh_timer.setInterval(5000)  # 5 секунд

    def _connect_signals(self):
        """Подключение сигналов и слотов"""
        self.file_combo.currentTextChanged.connect(self._on_file_changed)
        self.level_combo.currentTextChanged.connect(self._apply_filters)
        self.search_input.textChanged.connect(self._apply_filters)
        self.refresh_btn.clicked.connect(self.refresh_logs)
        self.clear_btn.clicked.connect(self.clear_logs)
        self.export_btn.clicked.connect(self.export_logs)
        self.refresh_timer.timeout.connect(self.refresh_logs)

    def _load_last_log_file(self):
        """Загрузка последнего лог-файла"""
        log_files = self._find_log_files()
        if log_files:
            self.file_combo.addItems([f.name for f in log_files])
            self.file_combo.setCurrentIndex(0)
            self._load_log_file(log_files[0])

    def _find_log_files(self) -> List[Path]:
        """Поиск лог-файлов в директории"""
        try:
            log_files = sorted(
                [f for f in self.log_dir.glob("*.log*") if f.is_file()],
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            return log_files
        except Exception as e:
            logger.error(f"Ошибка поиска лог-файлов: {str(e)}")
            return []

    def _load_log_file(self, file_path: Path):
        """Загрузка содержимого лог-файла"""
        try:
            self.current_file = file_path

            # Определение формата файла
            if file_path.suffix == ".gz":
                with gzip.open(file_path, "rt", encoding="utf-8") as f:
                    content = f.read()
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

            self.log_view.setPlainText(content)
            self._scroll_to_bottom()
            self._update_status()
            self.log_file_changed.emit(str(file_path))
        except Exception as e:
            logger.error(f"Ошибка чтения лог-файла {file_path}: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл: {str(e)}")

    def _on_file_changed(self, file_name: str):
        """Обработчик изменения выбранного файла"""
        if file_name:
            file_path = self.log_dir / file_name
            self._load_log_file(file_path)

    def _apply_filters(self):
        """Применение фильтров к логам"""
        self.log_filters["level"] = self.level_combo.currentText()
        self.log_filters["search_text"] = self.search_input.text().strip()

        if not self.current_file:
            return

        try:
            with open(self.current_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            filtered_lines = []
            for line in lines:
                if self._filter_line(line):
                    filtered_lines.append(line)

            self.log_view.setPlainText("".join(filtered_lines))
            self._highlight_search_matches()
            self._scroll_to_bottom()
        except Exception as e:
            logger.error(f"Ошибка фильтрации логов: {str(e)}")

    def _filter_line(self, line: str) -> bool:
        """Фильтрация строки лога по критериям"""
        # Фильтр по уровню
        level = self.log_filters["level"]
        if level != "ALL" and f"[{level}]" not in line:
            return False

        # Фильтр по тексту
        search_text = self.log_filters["search_text"]
        if search_text and search_text.lower() not in line.lower():
            return False

        return True

    def _highlight_search_matches(self):
        """Подсветка совпадений при поиске"""
        search_text = self.log_filters["search_text"]
        if not search_text:
            return

        cursor = self.log_view.textCursor()
        format = QTextCharFormat()
        format.setBackground(QColor("#FFFF00"))

        # Сброс предыдущей подсветки
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(QTextCursor.MoveOperation.End, QTextCursor.MoveMode.KeepAnchor)
        cursor.setCharFormat(QTextCharFormat())

        # Поиск и подсветка совпадений
        regex = re.compile(re.escape(search_text), re.IGNORECASE)
        cursor.movePosition(QTextCursor.MoveOperation.Start)

        while True:
            cursor = self.log_view.document().find(regex, cursor)
            if cursor.isNull():
                break
            cursor.mergeCharFormat(format)

    def _scroll_to_bottom(self):
        """Прокрутка к концу лога"""
        cursor = self.log_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_view.setTextCursor(cursor)
        self.log_view.ensureCursorVisible()

    def _update_status(self):
        """Обновление статусной строки"""
        if not self.current_file:
            self.status_bar.setText("Нет данных")
            return

        try:
            size = self.current_file.stat().st_size
            size_mb = size / (1024 * 1024)
            lines = self.log_view.document().lineCount()

            self.status_bar.setText(
                f"Файл: {self.current_file.name} | "
                f"Размер: {size_mb:.2f} MB | "
                f"Строк: {lines}"
            )
        except Exception as e:
            logger.error(f"Ошибка обновления статуса: {str(e)}")
            self.status_bar.setText("Ошибка обновления статуса")

    def refresh_logs(self):
        """Обновление логов"""
        if self.current_file:
            self._load_log_file(self.current_file)

    def clear_logs(self):
        """Очистка текущего лога"""
        self.log_view.clear()
        self.status_bar.setText("Логи очищены")

    def export_logs(self):
        """Экспорт логов в файл"""
        if not self.log_view.toPlainText():
            QMessageBox.warning(self, "Ошибка", "Нет данных для экспорта")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт логов",
            f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.log_view.toPlainText())
                QMessageBox.information(self, "Успех", "Логи успешно экспортированы")
            except Exception as e:
                logger.error(f"Ошибка экспорта логов: {str(e)}")
                QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать логи: {str(e)}")

    def start_auto_refresh(self, interval: int = 5000):
        """Запуск автоматического обновления логов"""
        self.refresh_timer.setInterval(interval)
        self.refresh_timer.start()

    def stop_auto_refresh(self):
        """Остановка автоматического обновления"""
        self.refresh_timer.stop()

    def load_json_logs(self, file_path: Path):
        """Загрузка и парсинг JSON логов"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                logs = [json.loads(line) for line in f if line.strip()]

            formatted_logs = []
            for log in logs:
                timestamp = log.get("timestamp", "")
                level = log.get("level", "INFO")
                message = log.get("message", "")
                module = log.get("module", "")

                formatted_logs.append(
                    f"{timestamp} [{level}] {module}: {message}\n"
                )

            self.log_view.setPlainText("".join(formatted_logs))
            self._scroll_to_bottom()
            self._update_status()
        except Exception as e:
            logger.error(f"Ошибка загрузки JSON логов: {str(e)}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить JSON логи: {str(e)}")

    def contextMenuEvent(self, event):
        """Контекстное меню для логов"""
        menu = self.log_view.createStandardContextMenu()

        copy_action = QAction("Копировать", self)
        copy_action.triggered.connect(self._copy_selected_text)

        select_all_action = QAction("Выделить все", self)
        select_all_action.triggered.connect(self.log_view.selectAll)

        menu.addSeparator()
        menu.addAction(copy_action)
        menu.addAction(select_all_action)

        menu.exec(event.globalPos())

    def _copy_selected_text(self):
        """Копирование выделенного текста"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.log_view.textCursor().selectedText())