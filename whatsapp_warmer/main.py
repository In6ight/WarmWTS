import sys
import logging
from pathlib import Path
from typing import Dict, Optional

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon

from whatsapp_warmer.utils.helpers import (
    get_app_data_dir,
    get_resource_path,
    setup_logging,
    validate_config,
    safe_json_io
)
from whatsapp_warmer.core.account_manager import AccountManager
from whatsapp_warmer.core.proxy_handler import ProxyHandler
from whatsapp_warmer.gui.window import MainWindow

# Настройка логирования до создания QApplication
setup_logging(log_file=get_app_data_dir() / 'logs/app.log')
logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "window_maximized": True,
    "window_geometry": None,
    "minimize_to_tray": False,  # Отключаем трей для упрощения
    "warming": {
        "rounds": 3,
        "min_delay": 15,
        "max_delay": 45,
        "messages_per_round": 2,
        "round_delay": 120
    }
}


def load_config() -> Dict:
    """Загрузка конфигурации с обработкой ошибок"""
    config_path = get_app_data_dir() / 'config.json'
    try:
        if config_path.exists():
            return validate_config(safe_json_io(config_path, 'r') or DEFAULT_CONFIG)
    except Exception as e:
        logger.error(f"Config load error: {e}")
    return DEFAULT_CONFIG.copy()


def handle_exception(exc_type, exc_value, exc_traceback):
    """Упрощенный обработчик исключений"""
    logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    QMessageBox.critical(
        None,
        "Error",
        f"An error occurred:\n\n{str(exc_value)}"
    )
    sys.exit(1)


def main():
    sys.excepthook = handle_exception
    logger.info("Starting WhatsApp Warmer")

    # Инициализация QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("WhatsApp Warmer")
    app.setApplicationVersion("1.0.0")

    # Упрощенная загрузка иконки (игнорируем ошибки)
    try:
        icon = QIcon(str(get_resource_path('icons/app.png')))
        if not icon.isNull():
            app.setWindowIcon(icon)
    except:
        pass

    # Инициализация основных компонентов
    try:
        config = load_config()
        account_manager = AccountManager(get_app_data_dir() / 'accounts.json')
        proxy_handler = ProxyHandler(get_app_data_dir() / 'proxies.json')

        window = MainWindow(
            account_manager=account_manager,
            proxy_handler=proxy_handler,
            config=config
        )

        if config.get('window_maximized'):
            window.showMaximized()
        else:
            window.show()

        return app.exec()
    except Exception as e:
        logger.critical(f"Initialization failed: {e}")
        QMessageBox.critical(None, "Startup Error", f"Cannot start application:\n{e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())