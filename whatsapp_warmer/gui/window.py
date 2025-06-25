from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget,
    QStatusBar, QSystemTrayIcon, QMenu, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QIcon, QAction, QCloseEvent
import logging
from typing import Dict, Optional, Any

from whatsapp_warmer.core.account_manager import AccountManager
from whatsapp_warmer.core.proxy_handler import ProxyHandler
from whatsapp_warmer.core.warming_engine import WarmingEngine
from whatsapp_warmer.utils.helpers import get_resource_path, safe_json_io

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    app_closing = pyqtSignal()
    settings_changed = pyqtSignal(dict)
    proxy_updated = pyqtSignal(list)

    def __init__(self, account_manager: AccountManager,
                 proxy_handler: ProxyHandler,
                 config: Optional[Dict[str, Any]] = None,
                 parent=None):
        super().__init__(parent)

        # Инициализация с проверкой параметров
        if not isinstance(account_manager, AccountManager):
            raise ValueError("account_manager must be AccountManager instance")
        if not isinstance(proxy_handler, ProxyHandler):
            raise ValueError("proxy_handler must be ProxyHandler instance")

        self.account_manager = account_manager
        self.proxy_handler = proxy_handler
        self.config = config or {}
        self.tray_icon = None
        self._pending_operations = 0

        # Настройка интерфейса
        self._init_ui()
        self._setup_tray_icon()
        self._setup_auto_save()

        # Инициализация движка прогрева (исправленная версия)
        self._init_warming_engine()

        # Восстановление состояния
        self._load_window_state()
        logger.info("Main window initialized")

    def _init_ui(self):
        """Инициализация пользовательского интерфейса"""
        self.setWindowTitle("WhatsApp Warmer PRO")
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной лейаут
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        central_widget.setLayout(main_layout)

        # Вкладки
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.show_status_message("Ready")

        # Меню
        self._init_menu_bar()

    def _init_warming_engine(self):
        """Безопасная инициализация движка прогрева"""
        try:
            self.warming_engine = WarmingEngine(
                account_manager=self.account_manager,
                proxy_handler=self.proxy_handler
            )

            # Попытка установки конфигурации, если метод доступен
            if hasattr(self.warming_engine, 'update_settings'):
                warming_config = self.config.get('warming', {})
                default_config = {
                    'rounds': 3,
                    'min_delay': 15,
                    'max_delay': 45,
                    'messages_per_round': 2,
                    'round_delay': 120
                }
                final_config = {**default_config, **warming_config}
                self.warming_engine.update_settings(final_config)

        except Exception as e:
            logger.error(f"Failed to initialize warming engine: {e}")
            self.warming_engine = None
            QMessageBox.warning(
                self,
                "Warning",
                "Warming engine initialized with limited functionality"
            )

    def _init_menu_bar(self):
        """Инициализация меню"""
        menubar = self.menuBar()

        # Меню File
        file_menu = menubar.addMenu("File")
        self._add_menu_action(file_menu, "Exit", self.close, "Ctrl+Q")

        # Меню Settings
        settings_menu = menubar.addMenu("Settings")
        self._add_menu_action(settings_menu, "Preferences", self._open_settings)

    def _setup_tray_icon(self):
        """Настройка иконки в трее"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        try:
            self.tray_icon = QSystemTrayIcon(self)

            # Попытка загрузки иконки
            try:
                icon_path = get_resource_path('icons/tray.png')
                if icon_path.exists():
                    self.tray_icon.setIcon(QIcon(str(icon_path)))
            except Exception as e:
                logger.debug(f"Tray icon not loaded: {e}")

            # Меню трея
            tray_menu = QMenu()
            self._add_menu_action(tray_menu, "Show", self.show_normal)
            self._add_menu_action(tray_menu, "Exit", self.close)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.show()

        except Exception as e:
            logger.error(f"Tray icon setup failed: {e}")

    def _setup_auto_save(self):
        """Настройка автосохранения"""
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setInterval(30000)  # 30 секунд
        self.auto_save_timer.timeout.connect(self._save_all_data)
        self.auto_save_timer.start()

    def _add_menu_action(self, menu, text, handler, shortcut=""):
        """Добавление действия в меню"""
        action = QAction(text, self)
        action.triggered.connect(handler)
        if shortcut:
            action.setShortcut(shortcut)
        menu.addAction(action)
        return action

    def _save_all_data(self):
        """Сохранение всех данных"""
        try:
            self._pending_operations += 1
            self.account_manager.save_to_file()
            self.proxy_handler.save_to_file()
            self._save_window_state()
        except Exception as e:
            logger.error(f"Data save failed: {e}")
        finally:
            self._pending_operations -= 1

    def _save_window_state(self):
        """Сохранение состояния окна"""
        self.config['window_maximized'] = self.isMaximized()
        if not self.isMaximized():
            self.config['window_geometry'] = bytes(self.saveGeometry())

    def _load_window_state(self):
        """Загрузка состояния окна"""
        try:
            if self.config.get('window_maximized', False):
                self.showMaximized()
            elif 'window_geometry' in self.config:
                self.restoreGeometry(self.config['window_geometry'])
        except Exception as e:
            logger.warning(f"Window state load failed: {e}")

    def _open_settings(self):
        """Открытие диалога настроек"""
        try:
            from whatsapp_warmer.gui.dialogs import SettingsDialog
            dialog = SettingsDialog(self.config, self)
            if dialog.exec():
                new_config = dialog.get_config()
                self.config.update(new_config)
                self.settings_changed.emit(new_config)

                # Обновляем настройки движка, если он существует
                if self.warming_engine and hasattr(self.warming_engine, 'update_settings'):
                    self.warming_engine.update_settings(self.config.get('warming', {}))

        except Exception as e:
            logger.error(f"Settings dialog error: {e}")
            QMessageBox.critical(self, "Error", "Failed to open settings")

    def show_status_message(self, message: str, timeout: int = 3000):
        """Показ сообщения в статусбаре"""
        self.status_bar.showMessage(message, timeout)
        logger.info(f"Status: {message}")

    def show_normal(self):
        """Восстановление окна из трея"""
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event: QCloseEvent):
        """Обработчик закрытия окна"""
        if self._pending_operations > 0:
            if not self._confirm_force_close():
                event.ignore()
                return

        # Остановка всех процессов
        self.auto_save_timer.stop()
        if hasattr(self, 'warming_engine') and self.warming_engine:
            self.warming_engine.stop_warming()

        # Сворачивание в трей вместо закрытия
        if self.config.get('minimize_to_tray', False) and self.tray_icon:
            event.ignore()
            self.hide()
            self.show_status_message("Minimized to tray", 2000)
            return

        # Полное закрытие
        self._save_all_data()
        self.app_closing.emit()
        super().closeEvent(event)

    def _confirm_force_close(self) -> bool:
        """Подтверждение принудительного закрытия"""
        reply = QMessageBox.question(
            self,
            "Operation in progress",
            "Background operations are running. Close anyway?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes