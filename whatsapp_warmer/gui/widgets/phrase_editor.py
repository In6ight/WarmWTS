from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLineEdit, QTextEdit, QComboBox, QLabel,
    QMessageBox, QInputDialog, QMenu, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QTextCursor, QColor, QAction
from utils.file_manager import write_json, read_json
from pathlib import Path
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class PhraseEditor(QWidget):
    """Редактор фраз для переписки с поддержкой категорий"""
    phrases_updated = pyqtSignal(list)

    def __init__(self, initial_phrases: Optional[List[Dict]] = None):
        super().__init__()
        self.phrases = initial_phrases or []
        self.current_category = "Общие"
        self._setup_ui()
        self._load_phrases()
        self._setup_context_menu()

    def _setup_ui(self):
        """Инициализация интерфейса"""
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(10)

        # Панель категорий
        self.category_panel = QHBoxLayout()

        self.category_combo = QComboBox()
        self.category_combo.addItems(["Общие", "Приветствия", "Вопросы", "Продажи"])
        self.category_combo.setEditable(True)
        self.category_combo.currentTextChanged.connect(self._on_category_changed)

        self.add_category_btn = QPushButton("+")
        self.add_category_btn.setFixedWidth(30)
        self.add_category_btn.setToolTip("Добавить категорию")
        self.add_category_btn.clicked.connect(self._add_category)

        self.category_panel.addWidget(QLabel("Категория:"))
        self.category_panel.addWidget(self.category_combo, stretch=1)
        self.category_panel.addWidget(self.add_category_btn)

        # Список фраз
        self.phrase_list = QListWidget()
        self.phrase_list.setMinimumHeight(150)
        self.phrase_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.phrase_list.itemDoubleClicked.connect(self._edit_phrase)

        # Редактор фразы
        self.phrase_edit = QTextEdit()
        self.phrase_edit.setPlaceholderText("Введите текст фразы...")
        self.phrase_edit.setMaximumHeight(100)

        # Кнопки управления
        self.button_panel = QHBoxLayout()

        self.add_btn = QPushButton("Добавить")
        self.add_btn.setIcon(QIcon("assets/icons/add.png"))
        self.add_btn.clicked.connect(self._add_phrase)

        self.edit_btn = QPushButton("Изменить")
        self.edit_btn.setIcon(QIcon("assets/icons/edit.png"))
        self.edit_btn.clicked.connect(self._edit_phrase)

        self.remove_btn = QPushButton("Удалить")
        self.remove_btn.setIcon(QIcon("assets/icons/remove.png"))
        self.remove_btn.clicked.connect(self._remove_phrase)

        self.import_btn = QPushButton("Импорт")
        self.import_btn.setIcon(QIcon("assets/icons/import.png"))
        self.import_btn.clicked.connect(self._import_phrases)

        self.export_btn = QPushButton("Экспорт")
        self.export_btn.setIcon(QIcon("assets/icons/export.png"))
        self.export_btn.clicked.connect(self._export_phrases)

        self.button_panel.addWidget(self.add_btn)
        self.button_panel.addWidget(self.edit_btn)
        self.button_panel.addWidget(self.remove_btn)
        self.button_panel.addStretch()
        self.button_panel.addWidget(self.import_btn)
        self.button_panel.addWidget(self.export_btn)

        # Сборка интерфейса
        self.layout.addLayout(self.category_panel)
        self.layout.addWidget(self.phrase_list, stretch=1)
        self.layout.addWidget(self.phrase_edit)
        self.layout.addLayout(self.button_panel)

    def _setup_context_menu(self):
        """Настройка контекстного меню для списка фраз"""
        self.phrase_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.phrase_list.customContextMenuRequested.connect(self._show_phrase_context_menu)

    def _show_phrase_context_menu(self, pos):
        """Отображение контекстного меню для фразы"""
        selected = self.phrase_list.currentItem()
        if not selected:
            return

        menu = QMenu()

        edit_action = QAction("Редактировать", self)
        edit_action.triggered.connect(self._edit_phrase)

        move_action = QAction("Переместить в...", self)
        move_action.triggered.connect(self._move_phrase_to_category)

        remove_action = QAction("Удалить", self)
        remove_action.triggered.connect(self._remove_phrase)

        menu.addAction(edit_action)
        menu.addAction(move_action)
        menu.addSeparator()
        menu.addAction(remove_action)

        menu.exec(self.phrase_list.mapToGlobal(pos))

    def _load_phrases(self):
        """Загрузка фраз для текущей категории"""
        self.phrase_list.clear()
        for phrase in self._get_current_category_phrases():
            item = QListWidgetItem(phrase['text'])
            item.setData(Qt.ItemDataRole.UserRole, phrase)
            self.phrase_list.addItem(item)

    def _get_current_category_phrases(self) -> List[Dict]:
        """Получение фраз текущей категории"""
        return [
            p for p in self.phrases
            if p.get('category', 'Общие') == self.current_category
        ]

    def _on_category_changed(self, category: str):
        """Обработчик изменения категории"""
        self.current_category = category
        self._load_phrases()

    def _add_category(self):
        """Добавление новой категории"""
        category, ok = QInputDialog.getText(
            self,
            "Новая категория",
            "Введите название категории:",
            flags=Qt.WindowType.WindowCloseButtonHint
        )

        if ok and category and category not in [
            self.category_combo.itemText(i)
            for i in range(self.category_combo.count())
        ]:
            self.category_combo.addItem(category)
            self.category_combo.setCurrentText(category)

    def _add_phrase(self):
        """Добавление новой фразы"""
        text = self.phrase_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Ошибка", "Текст фразы не может быть пустым")
            return

        new_phrase = {
            'text': text,
            'category': self.current_category,
            'usage_count': 0
        }

        # Проверка на дубликат
        if any(p['text'].lower() == text.lower()
               and p['category'] == self.current_category
               for p in self.phrases):
            QMessageBox.warning(self, "Ошибка", "Такая фраза уже существует в этой категории")
            return

        self.phrases.append(new_phrase)
        self._load_phrases()
        self.phrase_edit.clear()
        self.phrases_updated.emit(self.phrases)

        # Автопрокрутка к новой фразе
        self.phrase_list.setCurrentRow(self.phrase_list.count() - 1)

    def _edit_phrase(self):
        """Редактирование выбранной фразы"""
        selected = self.phrase_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите фразу для редактирования")
            return

        old_text = selected.text()
        new_text, ok = QInputDialog.getMultiLineText(
            self,
            "Редактирование фразы",
            "Измените текст фразы:",
            old_text
        )

        if ok and new_text.strip():
            new_text = new_text.strip()
            # Обновляем в общем списке
            for phrase in self.phrases:
                if (phrase['text'] == old_text and
                        phrase.get('category', 'Общие') == self.current_category):
                    phrase['text'] = new_text
                    break

            self._load_phrases()
            self.phrases_updated.emit(self.phrases)

    def _remove_phrase(self):
        """Удаление выбранной фразы"""
        selected = self.phrase_list.currentItem()
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите фразу для удаления")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить выбранную фразу?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Удаляем из общего списка
            self.phrases = [
                p for p in self.phrases
                if not (p['text'] == selected.text() and
                        p.get('category', 'Общие') == self.current_category)
            ]

            self._load_phrases()
            self.phrases_updated.emit(self.phrases)

    def _move_phrase_to_category(self):
        """Перемещение фразы в другую категорию"""
        selected = self.phrase_list.currentItem()
        if not selected:
            return

        categories = [
            self.category_combo.itemText(i)
            for i in range(self.category_combo.count())
            if self.category_combo.itemText(i) != self.current_category
        ]

        if not categories:
            QMessageBox.information(self, "Информация", "Нет других категорий для перемещения")
            return

        category, ok = QInputDialog.getItem(
            self,
            "Перемещение фразы",
            "Выберите категорию:",
            categories,
            0,
            False
        )

        if ok and category:
            # Обновляем в общем списке
            for phrase in self.phrases:
                if (phrase['text'] == selected.text() and
                        phrase.get('category', 'Общие') == self.current_category):
                    phrase['category'] = category
                    break

            self._load_phrases()
            self.phrases_updated.emit(self.phrases)

    def _import_phrases(self):
        """Импорт фраз из файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Импорт фраз",
            "",
            "JSON Files (*.json);;Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                if file_path.endswith('.json'):
                    data = read_json(file_path)
                    if not isinstance(data, list):
                        raise ValueError("Invalid JSON format - expected array")

                    imported = 0
                    for item in data:
                        if isinstance(item, dict) and 'text' in item:
                            category = item.get('category', self.current_category)
                            self.phrases.append({
                                'text': item['text'],
                                'category': category,
                                'usage_count': item.get('usage_count', 0)
                            })
                            imported += 1
                else:  # TXT файл
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            text = line.strip()
                            if text:
                                self.phrases.append({
                                    'text': text,
                                    'category': self.current_category,
                                    'usage_count': 0
                                })
                                imported += 1

                self._load_phrases()
                self.phrases_updated.emit(self.phrases)
                QMessageBox.information(
                    self,
                    "Импорт завершен",
                    f"Успешно импортировано {imported} фраз"
                )
            except Exception as e:
                logger.error(f"Ошибка импорта фраз: {str(e)}")
                QMessageBox.critical(
                    self,
                    "Ошибка импорта",
                    f"Не удалось импортировать фразы: {str(e)}"
                )

    def _export_phrases(self):
        """Экспорт фраз в файл"""
        if not self.phrases:
            QMessageBox.warning(self, "Ошибка", "Нет фраз для экспорта")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспорт фраз",
            f"whatsapp_phrases_{self.current_category}.json",
            "JSON Files (*.json);;Text Files (*.txt);;All Files (*)"
        )

        if file_path:
            try:
                if file_path.endswith('.json'):
                    write_json(file_path, self.phrases)
                else:  # TXT файл
                    with open(file_path, 'w', encoding='utf-8') as f:
                        for phrase in self._get_current_category_phrases():
                            f.write(phrase['text'] + "\n")

                QMessageBox.information(
                    self,
                    "Экспорт завершен",
                    f"Фразы успешно экспортированы в {file_path}"
                )
            except Exception as e:
                logger.error(f"Ошибка экспорта фраз: {str(e)}")
                QMessageBox.critical(
                    self,
                    "Ошибка экспорта",
                    f"Не удалось экспортировать фразы: {str(e)}"
                )

    def get_phrases(self) -> List[Dict]:
        """Получение текущего списка фраз"""
        return self.phrases

    def set_phrases(self, phrases: List[Dict]):
        """Установка списка фраз"""
        self.phrases = phrases
        self._load_phrases()