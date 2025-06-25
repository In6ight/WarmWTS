#!/usr/bin/env python3
import sys
import logging
import json
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon  # Добавлен импорт QIcon
from whatsapp_warmer.utils.logger import setup_logger, get_logger
from whatsapp_warmer.core.account_manager import AccountManager
from whatsapp_warmer.core.proxy_handler import ProxyHandler
from whatsapp_warmer.gui.window import MainWindow
from whatsapp_warmer.utils.helpers import get_config_path, ensure_directory_exists, get_resource_path

# Инициализация логгера
logger = get_logger(__name__)

DEFAULT_CONFIG = {
    "window_maximized": True,
    "window_geometry": None,
    "minimize_to_tray": True,
    "warming": {
        "rounds": 3,
        "min_delay": 15,
        "max_delay": 45,
        "messages_per_round": 2,
        "round_delay": 120
    }
}


def load_config() -> dict:
    """Загрузка конфигурации из файла"""
    config_path = get_config_path('config.json')
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Объединяем с дефолтными значениями
                return {**DEFAULT_CONFIG, **config}
    except Exception as e:
        logger.error(f"Ошибка загрузки конфига: {str(e)}")

    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    """Сохранение конфигурации в файл"""
    try:
        config_path = get_config_path('config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Ошибка сохранения конфига: {str(e)}")


def setup_directories():
    """Создание необходимых директорий"""
    dirs = [
        'data',
        'logs',
        'config'
    ]
    for dir_name in dirs:
        ensure_directory_exists(get_config_path(dir_name))


def handle_exception(exc_type, exc_value, exc_traceback):
    """Глобальный обработчик исключений"""
    logger.critical("Необработанное исключение:", exc_info=(exc_type, exc_value, exc_traceback))
    QMessageBox.critical(
        None,
        "Критическая ошибка",
        f"Произошла непредвиденная ошибка:\n\n{str(exc_value)}\n\nПодробности в логах."
    )
    sys.exit(1)


def main():
    """Точка входа в приложение"""
    try:
        # Настройка обработчика неотловленных исключений
        sys.excepthook = handle_exception

        # Создание необходимых директорий
        setup_directories()

        # Настройка логгера
        setup_logger(
            name='whatsapp_warmer',
            log_file=get_config_path('logs/app.log'),
            level=logging.DEBUG
        )

        logger.info("Запуск WhatsApp Account Warmer PRO")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Working directory: {Path.cwd()}")

        # Загрузка конфигурации
        config = load_config()
        logger.debug(f"Загружена конфигурация: {config}")

        # Создание QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("WhatsApp Warmer PRO")
        app.setApplicationVersion("1.0.0")
        app.setWindowIcon(QIcon(str(get_resource_path('icons/app.png'))))  # Исправлено: закрыты скобки

        # Инициализация основных компонентов
        account_manager = AccountManager(
            storage_path=get_config_path('data/accounts.json')
        )

        proxy_handler = ProxyHandler(
            storage_path=get_config_path('data/proxies.json')
        )

        # Создание главного окна
        window = MainWindow(
            account_manager=account_manager,
            proxy_handler=proxy_handler,
            config=config
        )
        window.show()

        # Запуск основного цикла
        return_code = app.exec()

        # Сохранение конфига перед выходом
        save_config(config)

        logger.info(f"Приложение завершено с кодом: {return_code}")
        return return_code

    except Exception as e:
        logger.critical("Критическая ошибка в main():", exc_info=True)
        QMessageBox.critical(
            None,
            "Ошибка запуска",
            f"Не удалось запустить приложение:\n\n{str(e)}\n\nПодробности в логах."
        )
        return 1


if __name__ == "__main__":
    # Добавление корневой директории в PYTHONPATH
    sys.path.append(str(Path(__file__).parent))

    # Запуск приложения
    sys.exit(main())