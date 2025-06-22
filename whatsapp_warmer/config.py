import os
from pathlib import Path
from typing import List, Dict, Any

class Paths:
    """Управление путями приложения"""
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    CONFIG_DIR = BASE_DIR / "configs"
    LOGS_DIR = DATA_DIR / "logs"
    PROFILES_DIR = DATA_DIR / "profiles"
    SCREENSHOTS_DIR = DATA_DIR / "screenshots"

    @classmethod
    def init_paths(cls):
        """Создает необходимые директории"""
        os.makedirs(cls.DATA_DIR, exist_ok=True)
        os.makedirs(cls.CONFIG_DIR, exist_ok=True)
        os.makedirs(cls.LOGS_DIR, exist_ok=True)
        os.makedirs(cls.PROFILES_DIR, exist_ok=True)
        os.makedirs(cls.SCREENSHOTS_DIR, exist_ok=True)

class Defaults:
    """Значения по умолчанию для конфигурации"""
    ACCOUNTS: List[Dict[str, Any]] = []
    PHRASES: List[str] = [
        "Привет! Как дела?",
        "Добрый день!",
        "Тестовое сообщение"
    ]
    SETTINGS: Dict[str, Any] = {
        "rounds": 5,
        "min_delay": 5,
        "max_delay": 30,
        "round_delay": 120
    }

class UISettings:
    """Настройки интерфейса"""
    WINDOW_SIZE = (1400, 900)
    THEME = "Fusion"
    FONT_FAMILY = "Segoe UI"
    FONT_SIZE = 10
    STYLESHEET = """
        QMainWindow { background-color: #f5f5f5; }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #ccc;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 15px;
        }
        QPushButton { min-width: 80px; padding: 5px; }
    """

class SeleniumConfig:
    """Настройки Selenium"""
    WEBDRIVER_TIMEOUT = 30
    PAGE_LOAD_TIMEOUT = 60
    CHROME_OPTIONS = [
        "--disable-notifications",
        "--disable-infobars",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--remote-debugging-port=9222"
    ]

# Инициализация путей при импорте
Paths.init_paths()