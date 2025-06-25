#!/usr/bin/env python3
import sys
import os
import logging
import json
from pathlib import Path
from typing import Optional, Union, Dict
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon


# ==================== Встроенные функции из helpers.py ====================
def get_app_data_dir(app_name: str = "WhatsAppWarmer") -> Path:
    """Возвращает путь к данным приложения (для Windows/macOS/Linux)"""
    if sys.platform == "win32":
        base = Path(os.getenv('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home()

    path = base / app_name
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_directory_exists(path: Union[str, Path]) -> bool:
    """Создает директорию, если её не существует"""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Directory creation failed: {str(e)}")
        return False


def get_resource_path(relative_path: str) -> Path:
    """Возвращает абсолютный путь к ресурсу в папке resources/"""
    base_path = Path(__file__).parent
    resource_path = base_path / 'resources' / relative_path
    if not resource_path.exists():
        logging.warning(f"Resource not found: {resource_path}")
    return resource_path


def setup_logging(log_file: Optional[Path] = None):
    """Настраивает систему логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8') if log_file else logging.StreamHandler()
        ]
    )


# ==================== Основной код ====================
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
    """Загружает конфигурацию из файла"""
    config_path = get_app_data_dir() / 'config.json'
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
    except Exception as e:
        logging.error(f"Config load error: {str(e)}")
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    """Сохраняет конфигурацию в файл"""
    try:
        config_path = get_app_data_dir() / 'config.json'
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Config save error: {str(e)}")


def handle_exception(exc_type, exc_value, exc_traceback):
    """Обрабатывает неотловленные исключения"""
    logging.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    QMessageBox.critical(
        None,
        "Critical Error",
        f"An unexpected error occurred:\n\n{str(exc_value)}\n\nSee logs for details."
    )
    sys.exit(1)


def main():
    """Точка входа в приложение"""
    sys.excepthook = handle_exception

    # Настройка директорий
    data_dir = get_app_data_dir()
    ensure_directory_exists(data_dir / 'logs')
    ensure_directory_exists(data_dir / 'data')

    # Настройка логов
    setup_logging(log_file=data_dir / 'logs/app.log')
    logging.info("Starting WhatsApp Warmer PRO")
    logging.info(f"Python version: {sys.version}")
    logging.info(f"Working directory: {Path.cwd()}")

    # Загрузка конфигурации
    config = load_config()
    logging.debug(f"Loaded config: {config}")

    # Создание QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("WhatsApp Warmer PRO")
    app.setApplicationVersion("1.0.0")
    app.setWindowIcon(QIcon(str(get_resource_path('icons/app.png'))))

    # Здесь должна быть инициализация основных компонентов
    # account_manager = AccountManager(...)
    # proxy_handler = ProxyHandler(...)
    # window = MainWindow(...)

    # Запуск основного цикла
    return_code = app.exec()

    # Сохранение конфига перед выходом
    save_config(config)
    logging.info(f"Application exited with code: {return_code}")
    return return_code


if __name__ == "__main__":
    sys.exit(main())