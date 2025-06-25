# whatsapp_warmer/utils/helpers.py
from pathlib import Path
import logging
import sys
import os
import json
from typing import Union, Optional, Dict, Any
from datetime import datetime

# Для Windows-специфичных функций
if sys.platform == 'win32':
    try:
        import winshell
        from win32com.client import Dispatch
    except ImportError:
        winshell = None
        Dispatch = None


def get_app_data_dir(app_name: str = "WhatsAppWarmer") -> Path:
    """Возвращает путь к данным приложения с автоматическим созданием директории"""
    try:
        if sys.platform == "win32":
            base = Path(os.getenv('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
        elif sys.platform == "darwin":
            base = Path.home() / "Library" / "Application Support"
        else:
            base = Path.home()

        path = base / app_name
        path.mkdir(parents=True, exist_ok=True)
        return path
    except Exception as e:
        logging.error(f"Failed to get app data dir: {e}")
        return Path.cwd() / app_name  # Fallback to current directory


def get_resource_path(relative_path: str) -> Path:
    """Возвращает путь к ресурсу без проверки существования файла"""
    try:
        base_path = Path(__file__).parent.parent
        return base_path / 'resources' / relative_path
    except Exception as e:
        logging.debug(f"Resource path error: {e}")
        return Path(relative_path)  # Fallback to relative path


def validate_phone(phone: str) -> bool:
    """Упрощенная валидация номера телефона"""
    if not isinstance(phone, str):
        return False
    return phone.startswith(('7', '+7')) and len(phone) in (11, 12) and phone.lstrip('+').isdigit()


def ensure_directory_exists(path: Union[str, Path]) -> bool:
    """Создает директорию (игнорирует ошибки)"""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception:
        return False


def setup_logging(log_file: Optional[Path] = None, level=logging.INFO):
    """Гибкая настройка логирования"""
    handlers = []

    if log_file:
        try:
            ensure_directory_exists(log_file.parent)
            handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
        except Exception as e:
            logging.warning(f"Failed to setup file logging: {e}")

    handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def validate_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Валидация конфига с подстановкой значений по умолчанию"""
    default_config = {
        "window_maximized": True,
        "window_geometry": None,
        "minimize_to_tray": False,  # Отключено по умолчанию
        "warming": {
            "rounds": 3,
            "min_delay": 15,
            "max_delay": 45,
            "messages_per_round": 2,
            "round_delay": 120
        }
    }

    if not config:
        return default_config.copy()

    # Рекурсивное обновление словарей
    def deep_update(target, source):
        for key, value in source.items():
            if isinstance(value, dict) and key in target:
                deep_update(target[key], value)
            else:
                target[key] = value
        return target

    return deep_update(default_config.copy(), config)


def safe_json_io(file_path: Union[str, Path], mode: str = 'r', data: Optional[Dict] = None):
    """Устойчивая работа с JSON файлами"""
    try:
        file_path = Path(file_path)
        if mode == 'r':
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return None
        elif mode == 'w' and data is not None:
            temp_path = file_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            if file_path.exists():
                file_path.unlink()
            temp_path.rename(file_path)
            return True
    except Exception as e:
        logging.error(f"JSON operation failed: {e}")
        return None if mode == 'r' else False


def create_shortcut() -> bool:
    """Попытка создания ярлыка (работает только на Windows)"""
    if sys.platform != 'win32' or winshell is None or Dispatch is None:
        return False

    try:
        desktop = winshell.desktop()
        shortcut_path = os.path.join(desktop, "WhatsApp Warmer.lnk")
        target = sys.executable
        wdir = os.path.dirname(os.path.abspath(sys.argv[0]))

        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target
        shortcut.WorkingDirectory = wdir
        shortcut.save()
        return True
    except Exception as e:
        logging.debug(f"Shortcut creation skipped: {e}")
        return False


def format_timestamp(ts: Optional[datetime] = None, fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    """Форматирование времени с обработкой None"""
    return (ts or datetime.now()).strftime(fmt)