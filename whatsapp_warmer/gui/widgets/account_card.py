from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QCheckBox, QMenu, QToolTip
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QIcon, QColor, QPainter, QPen, QAction
from whatsapp_warmer.core.models.account import WhatsAppAccount
from whatsapp_warmer.core.models.proxy import ProxyConfig
from whatsapp_warmer.utils.logger import get_logger
from typing import Optional

logger = get_logger(__name__)


class AccountCard(QWidget):
    """Виджет карточки аккаунта с интерактивными элементами"""

    proxy_settings_requested = pyqtSignal(WhatsAppAccount)
    status_changed = pyqtSignal(str, bool)  # phone, enabled

    def __init__(self, account: WhatsAppAccount, parent=None):
        super().__init__(parent)
        self.account = account
        self._setup_ui()
        self._setup_context_menu()
        self.update_style()

    def _setup_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setMinimumHeight(70)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Основной макет
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)

        # Чекбокс активности
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(self.account.enabled)
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        self.checkbox.setToolTip("Активировать/деактивировать аккаунт")

        # Иконка статуса
        self.status_icon = QLabel()
        self.status_icon.setFixedSize(16, 16)
        self._update_status_icon()

        # Информация об аккаунте
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.phone_label = QLabel(self.account.phone)
        self.phone_label.setStyleSheet("font-weight: bold;")

        self.details_label = QLabel(self._get_account_details())
        self.details_label.setStyleSheet("color: #666; font-size: 11px;")

        info_layout.addWidget(self.phone_label)
        info_layout.addWidget(self.details_label)

        # Кнопка прокси
        self.proxy_btn = QPushButton()
        self.proxy_btn.setIcon(QIcon("assets/icons/proxy.png"))
        self.proxy_btn.setFixedSize(24, 24)
        self.proxy_btn.setToolTip("Настройки прокси")
        self.proxy_btn.clicked.connect(
            lambda: self.proxy_settings_requested.emit(self.account)
        )

        # Сборка виджета
        layout.addWidget(self.checkbox)
        layout.addWidget(self.status_icon)
        layout.addLayout(info_layout, stretch=1)
        layout.addWidget(self.proxy_btn)

    def _setup_context_menu(self):
        """Настройка контекстного меню"""
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        """Отображение контекстного меню"""
        menu = QMenu(self)

        # Действия меню
        toggle_action = QAction(
            "Деактивировать" if self.account.enabled else "Активировать",
            self
        )
        toggle_action.triggered.connect(self._toggle_account)

        proxy_action = QAction("Настройки прокси", self)
        proxy_action.triggered.connect(
            lambda: self.proxy_settings_requested.emit(self.account)
        )

        copy_action = QAction("Копировать номер", self)
        copy_action.triggered.connect(self._copy_phone)

        # Добавление действий
        menu.addAction(toggle_action)
        menu.addAction(proxy_action)
        menu.addSeparator()
        menu.addAction(copy_action)

        menu.exec(self.mapToGlobal(pos))

    def _get_account_details(self) -> str:
        """Формирование строки с деталями аккаунта"""
        details = []

        # Метод входа
        method = "QR" if self.account.login_method == "qr" else "SMS"
        details.append(f"Метод: {method}")

        # Прокси
        if self.account.proxy and self.account.proxy.host:
            proxy_type = self.account.proxy.type.upper()
            details.append(f"Прокси: {proxy_type}")

        # Статистика
        if self.account.warming_stats.messages_sent > 0:
            details.append(f"Сообщений: {self.account.warming_stats.messages_sent}")

        return " | ".join(details)

    def _on_checkbox_changed(self, state):
        """Обработчик изменения чекбокса"""
        new_status = state == Qt.CheckState.Checked.value
        if self.account.enabled != new_status:
            self.account.enabled = new_status
            self._update_status_icon()
            self.status_changed.emit(self.account.phone, new_status)
            self.update_style()

    def _toggle_account(self):
        """Переключение состояния аккаунта"""
        self.checkbox.setChecked(not self.account.enabled)

    def _copy_phone(self):
        """Копирование номера телефона в буфер обмена"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.account.phone)
        QToolTip.showText(self.mapToGlobal(QPoint(0, 0)), "Номер скопирован", self)

    def _update_status_icon(self):
        """Обновление иконки статуса"""
        icon = "active.png" if self.account.enabled else "inactive.png"
        self.status_icon.setPixmap(QIcon(f"assets/icons/{icon}").pixmap(16, 16))

    def update_style(self):
        """Обновление стиля в зависимости от статуса"""
        if self.account.enabled:
            self.setStyleSheet("""
                AccountCard {
                    background: #FFFFFF;
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                }
                AccountCard:hover {
                    border-color: #BDBDBD;
                }
            """)
        else:
            self.setStyleSheet("""
                AccountCard {
                    background: #F5F5F5;
                    border: 1px solid #E0E0E0;
                    border-radius: 4px;
                    color: #9E9E9E;
                }
                QLabel {
                    color: #9E9E9E;
                }
            """)

    def paintEvent(self, event):
        """Кастомная отрисовка виджета"""
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        pen = QPen()
        pen.setWidth(1)
        pen.setColor(QColor("#E0E0E0"))
        painter.setPen(pen)

        painter.drawRoundedRect(
            0, 0, self.width() - 1, self.height() - 1, 4, 4)

    def update_account(self, account: WhatsAppAccount):
        """Обновление данных аккаунта"""
        self.account = account
        self.phone_label.setText(account.phone)
        self.details_label.setText(self._get_account_details())
        self.checkbox.setChecked(account.enabled)
        self._update_status_icon()
        self.update_style()

    def set_active_style(self, is_active: bool):
        """Установка стиля для активного/неактивного состояния"""
        color = "#E8F5E9" if is_active else "#FFEBEE"
        self.setStyleSheet(f"background: {color};")
        QTimer.singleShot(1000, self.update_style)