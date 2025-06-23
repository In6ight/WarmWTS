from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QStatusBar, QMessageBox, QSystemTrayIcon, QMenu
)
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtCore import Qt, pyqtSignal
from .tabs.accounts_tab import AccountsTab
from .tabs.warming_tab import WarmingTab
from .tabs.settings_tab import SettingsTab
from core.account_manager import AccountManager
from core.proxy_handler import ProxyHandler
from core.warming_engine import WarmingEngine
from whatsapp_warmer.utils.logger import get_logger
logger = get_logger(__name__)
import sys
import os
from pathlib import Path


class MainWindow(QMainWindow):
    """Главное окно приложения с полным функционалом"""
    shutdown_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("WhatsApp Warmer PRO")
        self.resize(1200, 800)

        # Инициализация компонентов ядра
        self._init_core_components()

        # Настройка интерфейса
        self._setup_ui()

        # Настройка системного трея
        self._setup_tray_icon()

        # Подключение сигналов
        self._connect_signals()

        # Загрузка данных
        self._load_data()

    def _init_core_components(self):
        """Инициализация основных компонентов"""
        self.account_manager = AccountManager(
            storage_path=Path("data/accounts.json")
        )
        self.proxy_handler = ProxyHandler()
        self.warming_engine = WarmingEngine(
            self.account_manager,
            self.proxy_handler
        )

        # Настройка логгера
        self.logger = setup_logger(
            "gui",
            log_file=Path("data/logs/gui.log")
        )

    def _setup_ui(self):
        """Настройка основного интерфейса"""
        self.setWindowIcon(QIcon("assets/icon.png"))

        # Центральный виджет с табами
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.West)

        # Создание вкладок
        self.accounts_tab = AccountsTab(self.account_manager)
        self.warming_tab = WarmingTab(self.warming_engine)
        self.settings_tab = SettingsTab()

        # Добавление вкладок
        self.tab_widget.addTab(self.accounts_tab, "Аккаунты")
        self.tab_widget.addTab(self.warming_tab, "Прогрев")
        self.tab_widget.addTab(self.settings_tab, "Настройки")

        # Установка центрального виджета
        self.setCentralWidget(self.tab_widget)

        # Строка состояния
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Готово")

        # Меню
        self._setup_menu()

    def _setup_menu(self):
        """Настройка главного меню"""
        menubar = self.menuBar()

        # Меню Файл
        file_menu = menubar.addMenu("Файл")

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Меню Сервис
        service_menu = menubar.addMenu("Сервис")

        reload_action = QAction("Перезагрузить данные", self)
        reload_action.triggered.connect(self._load_data)
        service_menu.addAction(reload_action)

        # Меню Помощь
        help_menu = menubar.addMenu("Помощь")

        about_action = QAction("О программе", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_tray_icon(self):
        """Настройка иконки в системном трее"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon("assets/tray_icon.png"))

        tray_menu = QMenu()

        show_action = QAction("Показать", self)
        show_action.triggered.connect(self.show_normal)

        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)

        tray_menu.addAction(show_action)
        tray_menu.addAction(exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def _connect_signals(self):
        """Подключение сигналов и слотов"""
        # Сигналы от движка прогрева
        self.warming_engine.progress_updated.connect(
            self._update_progress_status
        )
        self.warming_engine.error_occurred.connect(
            self._show_error_message
        )

        # Сигнал завершения работы
        self.shutdown_signal.connect(
            self._cleanup_before_exit
        )

    def _load_data(self):
        """Загрузка данных при запуске"""
        try:
            self.account_manager._load_accounts()
            self.accounts_tab.refresh_accounts_list()
            self.logger.info("Данные успешно загружены")
            self.status_bar.showMessage("Данные загружены", 3000)
        except Exception as e:
            self._show_error_message(
                "system",
                f"Ошибка загрузки данных: {str(e)}"
            )

    def _update_progress_status(self, progress: int, message: str):
        """Обновление статуса прогрева"""
        self.warming_tab.update_progress(progress)
        self.status_bar.showMessage(f"Прогрев: {message}")

    def _show_error_message(self, context: str, message: str):
        """Отображение сообщения об ошибке"""
        self.logger.error(f"{context}: {message}")
        QMessageBox.critical(
            self,
            "Ошибка",
            f"{context.upper()}: {message}"
        )

    def _show_about(self):
        """Отображение окна 'О программе'"""
        about_text = """
        WhatsApp Warmer PRO v1.0
        Автоматизация прогрева аккаунтов WhatsApp

        © 2025 Команда разработчиков
        Лицензия: GPLv3
        """
        QMessageBox.about(self, "О программе", about_text)

    def show_normal(self):
        """Восстановление окна из трея"""
        self.show()
        self.setWindowState(
            self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive
        )
        self.activateWindow()

    def closeEvent(self, event):
        """Обработчик закрытия окна"""
        if self.warming_engine._running:
            reply = QMessageBox.question(
                self,
                "Прогрев выполняется",
                "Прогрев все еще выполняется. Вы уверены, что хотите выйти?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        # Сворачивание в трей вместо закрытия
        if self.settings_tab.minimize_to_tray():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "WhatsApp Warmer",
                "Приложение продолжает работать в фоновом режиме",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
        else:
            self.shutdown_signal.emit()
            event.accept()

    def _cleanup_before_exit(self):
        """Очистка ресурсов перед выходом"""
        self.logger.info("Завершение работы приложения")

        try:
            if self.warming_engine._running:
                self.warming_engine.stop_warming()

            self.account_manager._save_accounts()
            self.tray_icon.hide()
        except Exception as e:
            self.logger.error(f"Ошибка при завершении: {str(e)}")

    def changeEvent(self, event):
        """Обработка изменения состояния окна"""
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized() and self.settings_tab.minimize_to_tray():
                self.hide()
                self.tray_icon.showMessage(
                    "WhatsApp Warmer",
                    "Приложение свернуто в трей",
                    QSystemTrayIcon.MessageIcon.Information,
                    2000
                )
        super().changeEvent(event)