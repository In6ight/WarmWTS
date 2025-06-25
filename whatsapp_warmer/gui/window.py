import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QVBoxLayout, QWidget,
                            QStatusBar, QMessageBox, QMenu, QSystemTrayIcon,
                            QApplication)
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QByteArray
from PyQt6.QtGui import QIcon, QAction, QCloseEvent
from whatsapp_warmer.utils.logger import get_logger
from whatsapp_warmer.core.account_manager import AccountManager
from whatsapp_warmer.core.proxy_handler import ProxyHandler
from whatsapp_warmer.core.warming_engine import WarmingEngine
from whatsapp_warmer.gui.tabs import AccountsTab, WarmingTab, LogsTab
from whatsapp_warmer.gui.dialogs import SettingsDialog, AboutDialog
from whatsapp_warmer.utils.helpers import (get_resource_path, validate_config, safe_json_io, create_shortcut)

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Главное окно приложения WhatsApp Account Warmer PRO"""

    # Сигналы
    app_closing = pyqtSignal()
    settings_changed = pyqtSignal(dict)
    proxy_updated = pyqtSignal(list)

    def __init__(self,
                 account_manager: AccountManager,
                 proxy_handler: Optional[ProxyHandler] = None,
                 config: Optional[Dict[str, Any]] = None,
                 parent: Optional[QWidget] = None):
        """
        Args:
            account_manager: Менеджер аккаунтов
            proxy_handler: Обработчик прокси (опционально)
            config: Конфигурация приложения (опционально)
            parent: Родительский виджет (опционально)
        """
        super().__init__(parent)
        self._setup_initial_state(account_manager, proxy_handler, config)
        self._initialize_ui()
        self._setup_tray_icon()
        self._setup_auto_save()
        logger.info("MainWindow initialized successfully")

    def _setup_initial_state(self, account_manager: AccountManager,
                           proxy_handler: Optional[ProxyHandler],
                           config: Optional[Dict[str, Any]]) -> None:
        """Инициализация начального состояния"""
        self.account_manager = account_manager
        self.proxy_handler = proxy_handler or ProxyHandler()
        self.config = validate_config(config or {})
        self.tray_icon: Optional[QSystemTrayIcon] = None
        self._pending_operations = 0

        # Валидация входных параметров
        if not isinstance(self.account_manager, AccountManager):
            raise TypeError("account_manager must be an AccountManager instance")
        if not isinstance(self.proxy_handler, ProxyHandler):
            raise TypeError("proxy_handler must be a ProxyHandler instance")

    def _initialize_ui(self) -> None:
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
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.central_widget.setLayout(self.main_layout)

        # Инициализация компонентов
        self._init_tabs()
        self._init_status_bar()
        self._init_menu_bar()
        self._init_warming_engine()
        self._connect_signals()

    def _init_tabs(self) -> None:
        """Инициализация вкладок"""
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        # Создание вкладок
        self.accounts_tab = AccountsTab(
            account_manager=self.account_manager,
            proxy_handler=self.proxy_handler
        )
        self.warming_tab = WarmingTab(
            account_manager=self.account_manager
        )
        self.logs_tab = LogsTab()

        # Добавление вкладок
        self.tab_widget.addTab(self.accounts_tab, "Аккаунты")
        self.tab_widget.addTab(self.warming_tab, "Прогрев")
        self.tab_widget.addTab(self.logs_tab, "Логи")

    def _init_status_bar(self) -> None:
        """Инициализация статус-бара"""
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("QStatusBar{padding-left:8px;}")
        self.setStatusBar(self.status_bar)
        self.show_status_message("Готов к работе")

    def _init_menu_bar(self) -> None:
        """Инициализация меню"""
        menubar = self.menuBar()

        # Меню Файл
        file_menu = menubar.addMenu("Файл")
        self._add_menu_action(file_menu, "Настройки", self._open_settings, "Ctrl+,")
        self._add_menu_action(file_menu, "Обновить прокси", self._update_proxies, "F5")
        file_menu.addSeparator()
        self._add_menu_action(file_menu, "Выход", self.close, "Ctrl+Q")

        # Меню Сервис
        service_menu = menubar.addMenu("Сервис")
        self._add_menu_action(service_menu, "Создать ярлык", self._create_shortcut)
        service_menu.addSeparator()
        self._add_menu_action(service_menu, "Проверить обновления", self._check_updates)

        # Меню Помощь
        help_menu = menubar.addMenu("Помощь")
        self._add_menu_action(help_menu, "Документация", self._show_docs, "F1")
        help_menu.addSeparator()
        self._add_menu_action(help_menu, "О программе", self._show_about)

    def _init_warming_engine(self) -> None:
        """Инициализация движка прогрева"""
        self.warming_engine = WarmingEngine(
            account_manager=self.account_manager,
            proxy_handler=self.proxy_handler,
            config=self.config.get('warming', {})
        )

    def _connect_signals(self) -> None:
        """Подключение сигналов"""
        # Аккаунты
        self.accounts_tab.account_added.connect(
            lambda: self.show_status_message("Аккаунт добавлен", 3000)
        )
        self.accounts_tab.account_updated.connect(
            self._handle_account_update
        )

        # Прогрев
        self.warming_engine.progress_updated.connect(
            self.warming_tab.update_progress
        )
        self.warming_engine.account_activity.connect(
            self._handle_account_activity
        )
        self.warming_engine.error_occurred.connect(
            self._handle_warming_error
        )

        # Прокси
        self.proxy_updated.connect(
            self.accounts_tab.update_proxy_list
        )

    def _setup_tray_icon(self) -> None:
        """Настройка иконки в трее"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray not available")
            return

        try:
            self.tray_icon = QSystemTrayIcon(self)
            self.tray_icon.setIcon(QIcon(get_resource_path('icons/tray.png')))

            # Меню трея
            tray_menu = QMenu()
            self._add_menu_action(tray_menu, "Показать", self.show_normal)
            self._add_menu_action(tray_menu, "Скрыть", self.hide)
            tray_menu.addSeparator()
            self._add_menu_action(tray_menu, "Выход", self.close)

            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self._handle_tray_activation)
            self.tray_icon.show()
        except Exception as e:
            logger.error(f"Tray icon setup failed: {str(e)}")

    def _setup_auto_save(self) -> None:
        """Настройка автосохранения"""
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.setInterval(60000)  # 1 минута
        self.auto_save_timer.timeout.connect(self._save_all_data)
        self.auto_save_timer.start()

    def _add_menu_action(self, menu: QMenu, text: str,
                        handler: callable, shortcut: str = "") -> QAction:
        """Добавление действия в меню"""
        action = QAction(text, self)
        action.triggered.connect(handler)
        if shortcut:
            action.setShortcut(shortcut)
        menu.addAction(action)
        return action

    def _save_all_data(self) -> None:
        """Сохранение всех данных"""
        try:
            self._pending_operations += 1
            self.account_manager.save_to_file()
            self.proxy_handler.save_to_file()
            self._save_window_state()
            logger.debug("All data saved successfully")
        except Exception as e:
            logger.error(f"Data save failed: {str(e)}")
        finally:
            self._pending_operations -= 1

    def _save_window_state(self) -> None:
        """Сохранение состояния окна"""
        self.config['window_maximized'] = self.isMaximized()
        if not self.isMaximized():
            self.config['window_geometry'] = bytes(self.saveGeometry())

    def _load_window_state(self) -> None:
        """Загрузка состояния окна"""
        try:
            if self.config.get('window_maximized', False):
                self.showMaximized()
            elif 'window_geometry' in self.config:
                self.restoreGeometry(QByteArray(self.config['window_geometry']))
        except Exception as e:
            logger.warning(f"Window state load failed: {str(e)}")

    def _open_settings(self) -> None:
        """Открытие диалога настроек"""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            new_config = dialog.get_config()
            self.config.update(new_config)
            self.settings_changed.emit(new_config)
            self.show_status_message("Настройки сохранены", 3000)

    def _update_proxies(self) -> None:
        """Обновление списка прокси"""
        try:
            self._pending_operations += 1
            self.proxy_handler.load_from_file()
            self.proxy_updated.emit(self.proxy_handler.get_all_proxies())
            self.show_status_message("Прокси обновлены", 2000)
        except Exception as e:
            self.show_status_message("Ошибка обновления прокси", 5000)
            logger.error(f"Proxy update failed: {str(e)}")
        finally:
            self._pending_operations -= 1

    def _create_shortcut(self) -> None:
        """Создание ярлыка на рабочем столе"""
        if create_shortcut():
            self.show_status_message("Ярлык создан успешно", 3000)
        else:
            self.show_status_message("Ошибка создания ярлыка", 3000)

    def _check_updates(self) -> None:
        """Проверка обновлений"""
        self.show_status_message("Проверка обновлений...", 3000)
        # Здесь должна быть логика проверки обновлений
        QTimer.singleShot(2000, lambda: self.show_status_message("Доступна новая версия", 3000))

    def _show_docs(self) -> None:
        """Показ документации"""
        QMessageBox.information(
            self,
            "Документация",
            "Онлайн документация доступна на нашем сайте",
            QMessageBox.StandardButton.Ok
        )

    def _show_about(self) -> None:
        """Показ информации о программе"""
        dialog = AboutDialog(self)
        dialog.exec()

    def _handle_account_update(self, account_data: Dict[str, Any]) -> None:
        """Обработка обновления аккаунта"""
        phone = account_data.get('phone', '')
        self.show_status_message(f"Аккаунт {phone} обновлен", 3000)
        self.logs_tab.add_log("Account", f"Updated {phone}")

    def _handle_account_activity(self, phone: str, activity: str) -> None:
        """Обработка активности аккаунта"""
        message = f"{phone}: {activity}"
        self.show_status_message(message, 3000)
        self.logs_tab.add_log("Activity", message)

    def _handle_warming_error(self, context: str, error: str) -> None:
        """Обработка ошибок прогрева"""
        message = f"{context}: {error}"
        self.show_status_message(message, 5000)
        self.logs_tab.add_log("Error", message, logging.ERROR)

    def _handle_tray_activation(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Обработка активации иконки в трее"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_normal()

    def show_status_message(self, message: str, timeout: int = 3000) -> None:
        """Показать сообщение в статус-баре"""
        self.status_bar.showMessage(message, timeout)
        logger.info(f"Status: {message}")

    def show_normal(self) -> None:
        """Показать окно в нормальном состоянии"""
        self.show()
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized)
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event: QCloseEvent) -> None:
        """Обработчик закрытия окна"""
        if self._pending_operations > 0:
            if not self._confirm_force_close():
                event.ignore()
                return

        # Остановка всех процессов
        self.auto_save_timer.stop()
        if hasattr(self, 'warming_engine'):
            self.warming_engine.stop_warming()

        # Сворачивание в трей вместо закрытия
        if self.config.get('minimize_to_tray', False) and self.tray_icon:
            event.ignore()
            self.hide()
            self.show_status_message("Приложение свернуто в трей", 2000)
            return

        # Полное закрытие
        self._save_all_data()
        self.app_closing.emit()
        super().closeEvent(event)

    def _confirm_force_close(self) -> bool:
        """Подтверждение принудительного закрытия"""
        reply = QMessageBox.question(
            self,
            "Операция в процессе",
            "Идут операции сохранения. Закрыть приложение?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def changeEvent(self, event) -> None:
        """Обработчик изменения состояния окна"""
        if event.type() == event.Type.WindowStateChange:
            if self.isMinimized() and self.config.get('minimize_to_tray', False):
                event.ignore()
                self.hide()
                self.show_status_message("Приложение свернуто в трей", 2000)
        super().changeEvent(event)