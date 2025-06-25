import logging
from pathlib import Path
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, QWidget,
                             QStatusBar, QMessageBox, QMenu, QSystemTrayIcon)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QIcon, QAction
from whatsapp_warmer.utils.logger import get_logger
from whatsapp_warmer.core.account_manager import AccountManager
from whatsapp_warmer.core.proxy_handler import ProxyHandler
from whatsapp_warmer.core.warming_engine import WarmingEngine
from whatsapp_warmer.gui.tabs import AccountsTab, WarmingTab, LogsTab
from whatsapp_warmer.gui.dialogs import SettingsDialog
from whatsapp_warmer.utils.helpers import get_resource_path

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Главное окно приложения WhatsApp Account Warmer PRO"""

    # Сигналы
    app_closing = pyqtSignal()
    settings_changed = pyqtSignal(dict)

    def __init__(self, account_manager: AccountManager,
                 proxy_handler: ProxyHandler = None,
                 config: dict = None,
                 parent=None):
        """
        Args:
            account_manager: Менеджер аккаунтов
            proxy_handler: Обработчик прокси
            config: Конфигурация приложения
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.logger = logger.getChild('MainWindow')
        self.account_manager = account_manager
        self.proxy_handler = proxy_handler or ProxyHandler()
        self.config = config or {}
        self.tray_icon = None

        self._init_ui()
        self._init_components()
        self._setup_tray_icon()
        self._connect_signals()
        self._load_window_state()

        self.logger.info("MainWindow инициализирован")

    def _init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle("WhatsApp Account Warmer PRO")
        self.setWindowIcon(QIcon(get_resource_path('icons/app.png')))
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)

        # Центральный виджет
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Основной лейаут
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # Вкладки
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Меню
        self._setup_menu_bar()

    def _setup_menu_bar(self):
        """Настройка меню приложения"""
        menubar = self.menuBar()

        # Меню Файл
        file_menu = menubar.addMenu("Файл")

        self.settings_action = QAction("Настройки", self)
        self.settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(self.settings_action)

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню Помощь
        help_menu = menubar.addMenu("Помощь")
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _init_components(self):
        """Инициализация компонентов приложения"""
        self.logger.debug("Инициализация компонентов")

        # Создаем движок прогрева
        self.warming_engine = WarmingEngine(
            account_manager=self.account_manager,
            proxy_handler=self.proxy_handler,
            config=self.config.get('warming', {})
        )

        # Создаем вкладки
        self.accounts_tab = AccountsTab(
            account_manager=self.account_manager,
            proxy_handler=self.proxy_handler
        )

        self.warming_tab = WarmingTab(
            warming_engine=self.warming_engine,
            account_manager=self.account_manager
        )

        self.logs_tab = LogsTab()

        # Добавляем вкладки
        self.tab_widget.addTab(self.accounts_tab, "Аккаунты")
        self.tab_widget.addTab(self.warming_tab, "Прогрев")
        self.tab_widget.addTab(self.logs_tab, "Логи")

    def _connect_signals(self):
        """Подключение сигналов и слотов"""
        # Сигналы от вкладки аккаунтов
        self.accounts_tab.account_added.connect(
            lambda: self.show_status_message("Аккаунт добавлен", 3000)
        )
        self.accounts_tab.account_removed.connect(
            lambda: self.show_status_message("Аккаунт удален", 3000)
        )

        # Сигналы от движка прогрева
        self.warming_engine.progress_updated.connect(
            self.warming_tab.update_progress
        )
        self.warming_engine.account_activity.connect(
            self._handle_account_activity
        )
        self.warming_engine.error_occurred.connect(
            self._handle_warming_error
        )

        # Сигналы настроек
        self.settings_changed.connect(
            self.warming_engine.update_settings
        )

    def _setup_tray_icon(self):
        """Настройка иконки в трее"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.logger.warning("Системный трей не доступен")
            return

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(get_resource_path('icons/tray.png')))

        # Меню трея
        tray_menu = QMenu()

        show_action = QAction("Показать", self)
        show_action.triggered.connect(self.show_normal)
        tray_menu.addAction(show_action)

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        self.tray_icon.activated.connect(self._tray_icon_activated)

    def _load_window_state(self):
        """Загрузка состояния окна из конфига"""
        if self.config.get('window_maximized', False):
            self.showMaximized()
        else:
            geometry = self.config.get('window_geometry')
            if geometry:
                self.restoreGeometry(geometry)

    def _save_window_state(self):
        """Сохранение состояния окна в конфиг"""
        self.config['window_maximized'] = self.isMaximized()
        if not self.isMaximized():
            self.config['window_geometry'] = self.saveGeometry()

    def _tray_icon_activated(self, reason):
        """Обработчик кликов по иконке в трее"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_normal()

    def show_normal(self):
        """Показать окно в нормальном состоянии"""
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.activateWindow()

    def _open_settings(self):
        """Открытие диалога настроек"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            new_config = dialog.get_config()
            self.config.update(new_config)
            self.settings_changed.emit(new_config)
            self.show_status_message("Настройки сохранены", 3000)

    def _show_about(self):
        """Показать информацию о программе"""
        about_text = """
        <b>WhatsApp Account Warmer PRO</b><br><br>
        Версия: 1.0.0<br>
        Автор: Ваша Компания<br><br>
        Лицензия: Commercial<br>
        © 2023 Все права защищены
        """
        QMessageBox.about(self, "О программе", about_text)

    def _handle_account_activity(self, phone: str, activity: str):
        """Обработчик активности аккаунта"""
        self.show_status_message(f"{phone}: {activity}", 3000)
        self.logs_tab.add_log(phone, activity)

    def _handle_warming_error(self, context: str, error: str):
        """Обработчик ошибок прогрева"""
        self.show_status_message(f"Ошибка ({context}): {error}", 5000)
        self.logs_tab.add_log(context, error, level=logging.ERROR)

    def show_status_message(self, message: str, timeout: int = 3000):
        """Показать сообщение в статус баре"""
        self.status_bar.showMessage(message, timeout)
        self.logger.debug(f"Статус: {message}")

    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        self.logger.info("Завершение работы приложения")

        # Остановка прогрева при закрытии
        if hasattr(self, 'warming_engine'):
            self.warming_engine.stop_warming()

        # Сохранение состояния
        self._save_window_state()

        # Скрытие в трей вместо закрытия, если настроено
        if self.config.get('minimize_to_tray', False) and self.tray_icon:
            event.ignore()
            self.hide()
            self.show_status_message("Приложение свернуто в трей", 2000)
        else:
            self.app_closing.emit()
            super().closeEvent(event)

    def changeEvent(self, event):
        """Обработчик изменения состояния окна"""
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized() and self.config.get('minimize_to_tray', False) and self.tray_icon:
                event.ignore()
                self.hide()
                self.show_status_message("Приложение свернуто в трей", 2000)
        super().changeEvent(event)