import json
import os
import time
from typing import List, Dict, Optional

from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QListWidget,
    QLineEdit, QLabel, QMessageBox, QProgressBar, QSpinBox, QGroupBox,
    QFormLayout, QTabWidget, QTextEdit, QComboBox, QCheckBox, QPlainTextEdit,
    QDialog, QDialogButtonBox, QMenu, QListWidgetItem, QInputDialog
)
from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtWebEngineWidgets import QWebEngineView

from whatsapp_warmer.models.account import WhatsAppAccount
from whatsapp_warmer.workers.whatsapp_worker import WhatsAppWorker
from whatsapp_warmer.workers.web_view import WhatsAppWebView
from whatsapp_warmer.utils.file_operations import load_json, save_json
from whatsapp_warmer.config import Paths, UISettings, Defaults
from whatsapp_warmer.ui.widgets.account_widget import AccountListItem
from whatsapp_warmer.ui.widgets.phrase_widget import PhraseListItem
from whatsapp_warmer.utils.helpers import Helpers


class WhatsAppWarmerApp(QMainWindow):
    """Главное окно приложения для прогрева аккаунтов WhatsApp"""

    update_log_signal = pyqtSignal(str)
    webview_created = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.accounts: List[WhatsAppAccount] = []
        self.warmup_phrases: List[str] = []
        self.worker: Optional[WhatsAppWorker] = None
        self.web_views: List[WhatsAppWebView] = []

        self.init_ui()
        self.load_data()
        self.setup_connections()

    def init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle("WhatsApp Account Warmer PRO")
        self.setGeometry(100, 100, *UISettings.WINDOW_SIZE)
        self.setStyleSheet(UISettings.STYLESHEET)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Левая панель (управление)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)

        # Группа управления аккаунтами
        account_group = self._create_account_group()
        left_layout.addWidget(account_group)

        # Список аккаунтов
        accounts_label = QLabel("Список аккаунтов:")
        self.accounts_list = QListWidget()
        self.accounts_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.accounts_list.customContextMenuRequested.connect(self.show_account_menu)
        left_layout.addWidget(accounts_label)
        left_layout.addWidget(self.accounts_list)

        # Настройки прогрева
        settings_group = self._create_settings_group()
        left_layout.addWidget(settings_group)

        # Фразы для прогрева
        phrases_group = self._create_phrases_group()
        left_layout.addWidget(phrases_group)

        # Управление
        control_buttons = self._create_control_buttons()
        left_layout.addLayout(control_buttons)

        left_layout.addStretch()
        main_layout.addWidget(left_panel, stretch=1)

        # Правая панель (информация)
        right_panel = QTabWidget()

        # Вкладка журнала
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        self.log_area = QPlainTextEdit()
        self.log_area.setReadOnly(True)
        log_layout.addWidget(QLabel("Журнал событий:"))
        log_layout.addWidget(self.log_area)
        right_panel.addTab(log_tab, "Журнал")

        # Вкладка WhatsApp Web
        self.web_tabs = QTabWidget()
        web_tab = QWidget()
        web_layout = QVBoxLayout(web_tab)
        web_layout.addWidget(self.web_tabs)
        right_panel.addTab(web_tab, "WhatsApp Web")

        main_layout.addWidget(right_panel, stretch=2)

    def _create_account_group(self) -> QGroupBox:
        """Создает группу для управления аккаунтами"""
        group = QGroupBox("Управление аккаунтами")
        layout = QFormLayout()

        # Поле ввода номера телефона
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Номер телефона (только цифры)")
        layout.addRow("Номер телефона:", self.phone_input)

        # Выбор метода входа
        self.login_method = QComboBox()
        self.login_method.addItems(["QR-код", "Номер телефона"])
        layout.addRow("Метод входа:", self.login_method)

        # Кнопка добавления аккаунта
        add_account_btn = QPushButton("Добавить аккаунт")
        add_account_btn.clicked.connect(self.add_account)
        layout.addRow(add_account_btn)

        group.setLayout(layout)
        return group

    def _create_settings_group(self) -> QGroupBox:
        """Создает группу настроек прогрева"""
        group = QGroupBox("Настройки прогрева")
        layout = QFormLayout()

        self.rounds_spin = QSpinBox()
        self.rounds_spin.setRange(1, 100)
        self.rounds_spin.setValue(5)

        self.min_delay_spin = QSpinBox()
        self.min_delay_spin.setRange(1, 60)
        self.min_delay_spin.setValue(5)

        self.max_delay_spin = QSpinBox()
        self.max_delay_spin.setRange(1, 300)
        self.max_delay_spin.setValue(30)

        self.round_delay_spin = QSpinBox()
        self.round_delay_spin.setRange(10, 600)
        self.round_delay_spin.setValue(120)

        layout.addRow("Количество раундов:", self.rounds_spin)
        layout.addRow("Минимальная задержка (сек):", self.min_delay_spin)
        layout.addRow("Максимальная задержка (сек):", self.max_delay_spin)
        layout.addRow("Задержка между раундами (сек):", self.round_delay_spin)

        group.setLayout(layout)
        return group

    def _create_phrases_group(self) -> QGroupBox:
        """Создает группу для управления фразами"""
        group = QGroupBox("Фразы для прогрева")
        layout = QVBoxLayout()

        self.phrases_list = QListWidget()
        self.phrase_input = QTextEdit()
        self.phrase_input.setMaximumHeight(60)

        add_phrase_btn = QPushButton("Добавить фразу")
        add_phrase_btn.clicked.connect(self.add_phrase)

        layout.addWidget(self.phrases_list)
        layout.addWidget(self.phrase_input)
        layout.addWidget(add_phrase_btn)

        group.setLayout(layout)
        return group

    def _create_control_buttons(self) -> QHBoxLayout:
        """Создает кнопки управления"""
        layout = QHBoxLayout()

        self.start_btn = QPushButton("Начать прогрев")
        self.start_btn.clicked.connect(self.start_warming)

        self.stop_btn = QPushButton("Остановить")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_warming)

        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        return layout

    def setup_connections(self):
        """Настраивает сигналы и слоты"""
        self.update_log_signal.connect(self.update_log)
        self.webview_created.connect(self.create_web_view)

    def load_data(self):
        """Загружает данные из файлов"""
        try:
            # Загрузка аккаунтов
            accounts_data = load_json(Paths.ACCOUNTS_FILE, Defaults.ACCOUNTS)
            self.accounts = [WhatsAppAccount(**data) for data in accounts_data]

            # Загрузка фраз
            self.warmup_phrases = load_json(Paths.PHRASES_FILE, Defaults.PHRASES)
            self.update_phrases_list()

            self.log("Данные успешно загружены")
        except Exception as e:
            self.log(f"Ошибка загрузки данных: {str(e)}")

    def save_data(self):
        """Сохраняет данные в файлы"""
        try:
            accounts_data = [acc.__dict__ for acc in self.accounts]
            save_json(Paths.ACCOUNTS_FILE, accounts_data)
            save_json(Paths.PHRASES_FILE, self.warmup_phrases)
            self.log("Данные сохранены")
        except Exception as e:
            self.log(f"Ошибка сохранения: {str(e)}")

    def log(self, message: str):
        """Добавляет сообщение в лог"""
        self.update_log_signal.emit(message)

    def update_log(self, message: str):
        """Обновляет область лога"""
        self.log_area.appendPlainText(f"{time.strftime('%H:%M:%S')} - {message}")

    def create_web_view(self, account_info: dict):
        """Создает WebView для аккаунта"""
        web_view = WhatsAppWebView(account_info)
        tab_name = f"{account_info['phone']} ({account_info['index']})"
        self.web_tabs.addTab(web_view, tab_name)
        self.web_views.append(web_view)
        self.log(f"Создана вкладка для {account_info['phone']}")

    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
        self.save_data()
        event.accept()

    def add_account(self):
        """Добавляет новый аккаунт в список"""
        phone = self.phone_input.text().strip()
        if not phone:
            self.log("Введите номер телефона")
            return

        if not Helpers.validate_phone(phone):
            self.log("Некорректный номер телефона")
            return

        phone = Helpers.format_phone(phone)
        login_method = "qr" if self.login_method.currentIndex() == 0 else "phone"

        # Проверяем, не добавлен ли уже такой номер
        if any(acc.phone == phone for acc in self.accounts):
            self.log(f"Аккаунт {phone} уже добавлен")
            return

        # Создаем новый аккаунт
        new_account = WhatsAppAccount(
            phone=phone,
            login_method=login_method
        )

        # Добавляем в список
        self.accounts.append(new_account)
        self.update_accounts_list()
        self.log(f"Добавлен аккаунт: {phone} ({login_method})")
        self.save_data()

    def update_accounts_list(self):
        """Обновляет список аккаунтов в UI"""
        self.accounts_list.clear()
        for account in self.accounts:
            item = QListWidgetItem()
            widget = AccountListItem(
                phone=account.phone,
                login_method=account.login_method,
                proxy_used=account.proxy.enabled,
                enabled=account.enabled
            )
            widget.toggled.connect(lambda state, acc=account: self.toggle_account(acc, state))
            item.setSizeHint(widget.sizeHint())
            self.accounts_list.addItem(item)
            self.accounts_list.setItemWidget(item, widget)

    def toggle_account(self, account: WhatsAppAccount, enabled: bool):
        """Включает/выключает аккаунт"""
        account.enabled = enabled
        self.save_data()
        self.log(f"Аккаунт {account.phone} {'включен' if enabled else 'выключен'}")

    def add_phrase(self):
        """Добавляет новую фразу для прогрева"""
        phrase = self.phrase_input.toPlainText().strip()
        if not phrase:
            self.log("Введите текст фразы")
            return

        if phrase in self.warmup_phrases:
            self.log("Такая фраза уже есть в списке")
            return

        self.warmup_phrases.append(phrase)
        self.update_phrases_list()
        self.phrase_input.clear()
        self.log(f"Добавлена фраза: {phrase[:20]}...")
        self.save_data()

    def update_phrases_list(self):
        """Обновляет список фраз в UI"""
        self.phrases_list.clear()
        for phrase in self.warmup_phrases:
            item = QListWidgetItem()
            widget = PhraseListItem(phrase)
            widget.phrase_edited.connect(self.edit_phrase)
            widget.phrase_deleted.connect(self.delete_phrase)
            item.setSizeHint(widget.sizeHint())
            self.phrases_list.addItem(item)
            self.phrases_list.setItemWidget(item, widget)

    def edit_phrase(self, old_phrase: str, new_phrase: str):
        """Редактирует существующую фразу"""
        if new_phrase and new_phrase != old_phrase:
            index = self.warmup_phrases.index(old_phrase)
            self.warmup_phrases[index] = new_phrase
            self.update_phrases_list()
            self.save_data()
            self.log(f"Фраза изменена: {old_phrase[:20]}... -> {new_phrase[:20]}...")

    def delete_phrase(self, phrase: str):
        """Удаляет фразу из списка"""
        self.warmup_phrases.remove(phrase)
        self.update_phrases_list()
        self.save_data()
        self.log(f"Фраза удалена: {phrase[:20]}...")

    def show_account_menu(self, position):
        """Показывает контекстное меню для аккаунта"""
        item = self.accounts_list.itemAt(position)
        if not item:
            return

        widget = self.accounts_list.itemWidget(item)
        if not widget:
            return

        menu = QMenu()

        # Действие удаления
        delete_action = QAction("Удалить аккаунт", self)
        delete_action.triggered.connect(lambda: self.delete_account(widget))
        menu.addAction(delete_action)

        # Действие настройки прокси
        proxy_action = QAction("Настроить прокси", self)
        proxy_action.triggered.connect(lambda: self.configure_proxy(widget))
        menu.addAction(proxy_action)

        menu.exec(self.accounts_list.mapToGlobal(position))

    def delete_account(self, widget):
        """Удаляет выбранный аккаунт"""
        phone = widget.label.text().split()[0]
        account = next((acc for acc in self.accounts if acc.phone == phone), None)
        if account:
            self.accounts.remove(account)
            self.update_accounts_list()
            self.save_data()
            self.log(f"Аккаунт {phone} удален")

    def configure_proxy(self, widget):
        """Настраивает прокси для аккаунта"""
        phone = widget.label.text().split()[0]
        account = next((acc for acc in self.accounts if acc.phone == phone), None)
        if account:
            # Здесь должна быть логика настройки прокси
            self.log(f"Настройка прокси для {phone}")

    def start_warming(self):
        """Запускает процесс прогрева аккаунтов"""
        if not self.accounts:
            self.log("Нет аккаунтов для прогрева")
            return

        if not self.warmup_phrases:
            self.log("Нет фраз для прогрева")
            return

        self.log("Запуск прогрева аккаунтов...")
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        settings = {
            "rounds": self.rounds_spin.value(),
            "min_delay": self.min_delay_spin.value(),
            "max_delay": self.max_delay_spin.value(),
            "round_delay": self.round_delay_spin.value()
        }

        self.worker = WhatsAppWorker(
            accounts=self.accounts,
            settings=settings,
            warmup_phrases=self.warmup_phrases
        )

        # Подключаем сигналы
        self.worker.status_update.connect(self.log)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.operation_complete.connect(self.warming_complete)
        self.worker.qr_code_required.connect(self.handle_qr_code)
        self.worker.verification_code_required.connect(self.handle_verification_code)
        self.worker.webview_ready.connect(self.create_web_view)

        self.worker.start()

    def stop_warming(self):
        """Останавливает процесс прогрева"""
        if self.worker and self.worker.isRunning():
            self.log("Остановка прогрева...")
            self.worker.stop()
            self.worker.wait()
            self.warming_complete(False)

    def update_progress(self, percent: int):
        """Обновляет прогресс выполнения"""
        self.log(f"Прогресс: {percent}%")

    def warming_complete(self, success: bool):
        """Обработчик завершения прогрева"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        status = "успешно завершен" if success else "прерван"
        self.log(f"Прогрев {status}")

    def handle_qr_code(self, phone: str, qr_data: str):
        """Обрабатывает запрос на сканирование QR-кода"""
        self.log(f"Для аккаунта {phone} требуется сканирование QR-кода")

    def handle_verification_code(self, phone: str):
        """Обрабатывает запрос на ввод кода подтверждения"""
        self.log(f"Для аккаунта {phone} требуется код подтверждения")