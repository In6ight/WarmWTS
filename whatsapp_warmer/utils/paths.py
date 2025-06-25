from pathlib import Path
import logging
import sys
import os

def get_app_data_dir(app_name: str = "WhatsAppWarmer") -> Path:
    """Возвращает путь к данным приложения"""
    if sys.platform == "win32":
        base = Path(os.getenv('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home()

    path = base / app_name
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_resource_path(relative_path: str) -> Path:
    """Возвращает абсолютный путь к ресурсу"""
    base_path = Path(__file__).parent.parent  # Переход в корень проекта
    resource_path = base_path / 'resources' / relative_path
    if not resource_path.exists():
        logging.warning(f"Resource not found: {resource_path}")
    return resource_path