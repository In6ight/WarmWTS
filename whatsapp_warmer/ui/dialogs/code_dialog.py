from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QDialogButtonBox,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class CodeInputDialog(QDialog):
    """Диалог для ввода кода подтверждения WhatsApp"""
    code_submitted = pyqtSignal(str)  # Сигнал с введенным кодом

    def __init__(self, phone: str, parent=None):
        super().__init__(parent)
        self.phone = phone
        self.setup_ui()
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

    def setup_ui(self):
        """Настройка интерфейса диалога"""
        self.setWindowTitle("Подтверждение номера")
        self.setFixedSize(350, 200)

        layout = QVBoxLayout(self)

        # Текст инструкции
        instruction = QLabel(
            f"Введите код из WhatsApp для номера:\n"
            f"+{self.phone}\n\n"
            "Код обычно приходит в течение 1-2 минут"
        )
        instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruction.setWordWrap(True)

        # Поле ввода кода
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("6-значный код")
        self.code_input.setMaxLength(6)
        self.code_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_input.setFont(QFont("Arial", 18))
        self.code_input.textChanged.connect(self.validate_code)

        # Кнопки
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.on_accept)
        button_box.rejected.connect(self.reject)

        # Добавляем элементы в layout
        layout.addWidget(instruction)
        layout.addWidget(self.code_input)
        layout.addSpacing(20)
        layout.addWidget(button_box)

    def validate_code(self, text: str):
        """Валидация вводимого кода"""
        if not text.isdigit():
            self.code_input.setText(''.join(filter(str.isdigit, text)))

    def on_accept(self):
        """Обработка нажатия OK"""
        code = self.code_input.text().strip()

        if len(code) != 6:
            QMessageBox.warning(
                self,
                "Неверный код",
                "Код должен содержать 6 цифр",
                QMessageBox.StandardButton.Ok
            )
            return

        self.code_submitted.emit(code)
        self.accept()

    @staticmethod
    def get_code(phone: str, parent=None) -> str:
        """
        Статический метод для быстрого вызова диалога
        Возвращает введенный код или пустую строку
        """
        dialog = CodeInputDialog(phone, parent)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            return dialog.code_input.text()
        return ""