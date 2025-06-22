from PyQt6.QtWidgets import QWidget, QHBoxLayout, QCheckBox, QLabel
from PyQt6.QtCore import Qt, pyqtSignal


class AccountListItem(QWidget):
    """Кастомный виджет для отображения аккаунта в списке"""
    toggled = pyqtSignal(bool)

    def __init__(self, phone: str, login_method: str, proxy_used: bool, enabled: bool):
        super().__init__()

        self.checkbox = QCheckBox()
        self.checkbox.setChecked(enabled)
        self.checkbox.stateChanged.connect(self._on_toggle)

        self.label = QLabel(f"{phone} ({login_method})")
        if proxy_used:
            self.label.setText(f"{self.label.text()} [PROXY]")

        layout = QHBoxLayout()
        layout.addWidget(self.checkbox)
        layout.addWidget(self.label)
        layout.addStretch()
        self.setLayout(layout)

        self._update_style(enabled)

    def _on_toggle(self, state):
        enabled = state == Qt.CheckState.Checked.value
        self._update_style(enabled)
        self.toggled.emit(enabled)

    def _update_style(self, enabled):
        self.label.setStyleSheet(
            "font-weight: bold;" if enabled else "color: #888;"
        )