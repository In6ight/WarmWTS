#!/usr/bin/env python3
import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Добавляем корень проекта в PYTHONPATH
sys.path.append(str(Path(__file__).parent))

try:
    from whatsapp_warmer.ui.main_window import WhatsAppWarmerApp
    from whatsapp_warmer.config import Paths, UISettings, Defaults
    from whatsapp_warmer.utils.logger import get_logger
except ImportError as e:
    print(f"Ошибка импорта: {str(e)}")
    print("Проверьте структуру проекта и наличие файлов:")
    print("- whatsapp_warmer/__init__.py")
    print("- whatsapp_warmer/config.py")
    print("- whatsapp_warmer/ui/main_window.py")
    sys.exit(1)

logger = get_logger(__name__)


def check_dependencies() -> bool:
    """Проверяет наличие всех необходимых зависимостей"""
    try:
        # Проверка ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
        driver.quit()
        return True
    except Exception as e:
        logger.error(f"Ошибка проверки зависимостей: {str(e)}")
        return False


def show_error(title: str, message: str):
    """Показывает диалоговое окно с ошибкой"""
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.exec()


def main():
    # Инициализация путей
    try:
        Paths.init_paths()
        logger.info("Инициализация путей завершена")
    except Exception as e:
        logger.error(f"Ошибка инициализации путей: {str(e)}")
        show_error("Ошибка", "Не удалось создать системные директории")
        return 1

    # Проверка зависимостей
    if not check_dependencies():
        show_error(
            "Ошибка зависимостей",
            "Требуется установка:\n"
            "1. Google Chrome\n"
            "2. ChromeDriver\n\n"
            "Подробности в логах"
        )
        return 1

    # Создание приложения
    try:
        app = QApplication(sys.argv)
        app.setStyle(UISettings.THEME)

        window = WhatsAppWarmerApp()
        window.show()

        logger.info("Приложение успешно запущено")
        return app.exec()

    except Exception as e:
        logger.critical(f"Критическая ошибка: {str(e)}")
        show_error("Ошибка", f"Не удалось запустить приложение:\n{str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())