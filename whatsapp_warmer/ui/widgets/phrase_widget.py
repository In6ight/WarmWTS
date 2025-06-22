from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QMenu,
    QInputDialog,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction


class PhraseListItem(QWidget):
    """Кастомный виджет элемента списка фраз"""
    phrase_edited = pyqtSignal(str, str)  # old_phrase, new_phrase
    phrase_deleted = pyqtSignal(str)      # phrase

    def __init__(self, phrase: str, parent=None):
        super().__init__(parent)
        self.original_phrase = phrase
        self.setup_ui()
        self.setup_context_menu()

    def setup_ui(self):
        """Инициализирует UI элементы"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # Текст фразы с автоматическим переносом слов
        self.label = QLabel(self.original_phrase)
        self.label.setWordWrap(True)
        self.label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )

        # Кнопка удаления
        self.delete_btn = QPushButton("×")
        self.delete_btn.setFixedSize(24, 24)
        self.delete_btn.setStyleSheet("""
            QPushButton {
                font-weight: bold;
                border: none;
                color: #ff0000;
            }
            QPushButton:hover {
                background-color: #ffecec;
            }
        """)
        self.delete_btn.clicked.connect(self.confirm_delete)

        layout.addWidget(self.label)
        layout.addWidget(self.delete_btn)
        self.setLayout(layout)

    def setup_context_menu(self):
        """Настраивает контекстное меню"""
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        # Действие редактирования
        edit_action = QAction("Редактировать", self)
        edit_action.triggered.connect(self.edit_phrase)
        self.addAction(edit_action)

        # Действие копирования
        copy_action = QAction("Копировать", self)
        copy_action.triggered.connect(self.copy_phrase)
        self.addAction(copy_action)

    def edit_phrase(self):
        """Редактирование фразы"""
        new_phrase, ok = QInputDialog.getText(
            self,
            "Редактирование фразы",
            "Введите новую фразу:",
            text=self.original_phrase
        )

        if ok and new_phrase.strip() and new_phrase != self.original_phrase:
            self.phrase_edited.emit(self.original_phrase, new_phrase.strip())

    def copy_phrase(self):
        """Копирование фразы в буфер обмена"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.original_phrase)
        QMessageBox.information(
            self,
            "Скопировано",
            f"Фраза скопирована в буфер:\n{self.original_phrase}"
        )

    def confirm_delete(self):
        """Подтверждение удаления фразы"""
        reply = QMessageBox.question(
            self,
            "Удаление фразы",
            f"Удалить фразу:\n{self.original_phrase}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.phrase_deleted.emit(self.original_phrase)

    def update_phrase(self, new_phrase: str):
        """Обновляет текст фразы"""
        self.original_phrase = new_phrase
        self.label.setText(new_phrase)