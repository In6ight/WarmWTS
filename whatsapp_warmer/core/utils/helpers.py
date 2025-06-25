import re
import sys
import json
import logging
from pathlib import Path
from typing import Union, Optional, Any, Dict, List
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QStandardPaths

logger = logging.getLogger(__name__)


def get_config_path(file_name: str) -> Path:
    """
    Получение абсолютного пути к файлу конфигурации.
    Для Windows: C:\Users\<User>\.whatsapp_warmer\
    Для Linux/Mac: ~/.whatsapp_warmer/
    """
    if getattr(sys, 'frozen', False):
        # Для собранного приложения (PyInstaller)
        base_dir = Path(sys.executable).parent
    else:
        # Для разработки
        base_dir = Path.home() / '.whatsapp_warmer'

    return base_dir / file_name


def ensure_directory_exists(dir_path: Union[str, Path]):
    """Рекурсивное создание директории если не существует"""
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)


def get_resource_path(relative_path: str) -> Path:
    """
    Получение абсолютного пути к ресурсам (иконки, UI-файлы).
    Работает в режиме разработки и после сборки.
    """
    if getattr(sys, 'frozen', False):
        # Для собранного приложения
        base_path = Path(sys.executable).parent
    else:
        # Для разработки
        base_path = Path(__file__).parent.parent

    return base_path / relative_path


def validate_phone(phone: Union[str, int]) -> bool:
    """
    Валидация номера телефона для WhatsApp.
    Формат: 79XXXXXXXXX (11 цифр, начинается с 79)
    """
    if isinstance(phone, int):
        phone = str(phone)
    return bool(re.fullmatch(r'79\d{9}', phone))


def validate_email(email: str) -> bool:
    """Базовая валидация email адреса"""
    return bool(re.fullmatch(r'[^@]+@[^@]+\.[^@]+', email))


def validate_proxy(proxy: Dict[str, Any]) -> bool:
    """Валидация конфигурации прокси"""
    required = ['host', 'port', 'type']
    return all(key in proxy for key in required)


def read_json_file(file_path: Union[str, Path]) -> Optional[Dict]:
    """Безопасное чтение JSON файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка чтения {file_path}: {str(e)}")
        return None


def write_json_file(file_path: Union[str, Path], data: Any) -> bool:
    """Безопасная запись в JSON файл"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            return True
    except Exception as e:
        logger.error(f"Ошибка записи {file_path}: {str(e)}")
        return False


def setup_qt_resources():
    """Инициализация Qt ресурсов (если используется .qrc)"""
    try:
        from PyQt6.QtCore import QResource
        resources_path = get_resource_path('resources.qrc')
        if resources_path.exists():
            QResource.registerResource(str(resources_path))
    except ImportError:
        pass


def get_platform_specific_config() -> Dict:
    """Получение платформозависимых настроек"""
    platform = sys.platform.lower()
    config = {
        'windows': {'config_dir': Path.home() / 'AppData' / 'Local' / 'WhatsAppWarmer'},
        'linux': {'config_dir': Path.home() / '.config' / 'whatsapp-warmer'},
        'darwin': {'config_dir': Path.home() / 'Library' / 'Application Support' / 'WhatsAppWarmer'}
    }

    if platform.startswith('win'):
        return config['windows']
    elif platform.startswith('linux'):
        return config['linux']
    elif platform.startswith('darwin'):
        return config['darwin']
    else:
        return {'config_dir': Path.home() / '.whatsapp_warmer'}


def sanitize_filename(filename: str) -> str:
    """Очистка имени файла от недопустимых символов"""
    return re.sub(r'[\\/*?:"<>|]', "_", filename)


def humanize_bytes(size: int) -> str:
    """Конвертация размера в байтах в читаемый формат"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def setup_custom_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """Настройка кастомного логгера"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Консольный обработчик
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Файловый обработчик (если указан файл)
    if log_file:
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


def qt_connect(signal, slot):
    """Безопасное подключение сигналов Qt с обработкой ошибок"""
    try:
        signal.connect(slot)
    except Exception as e:
        logger.error(f"Ошибка подключения сигнала: {str(e)}")


def get_default_icon() -> QIcon:
    """Получение иконки по умолчанию"""
    icon_path = get_resource_path('icons/app.png')
    if icon_path.exists():
        return QIcon(str(icon_path))
    return QIcon()


def merge_dicts(base: Dict, update: Dict) -> Dict:
    """Рекурсивное слияние словарей"""
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = merge_dicts(base[key], value)
        else:
            base[key] = value
    return base


def is_frozen() -> bool:
    """Проверка, запущено ли приложение в frozen-режиме (PyInstaller)"""
    return getattr(sys, 'frozen', False)