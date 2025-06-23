import json
import pickle
from pathlib import Path
from typing import Any, Dict, List
from whatsapp_warmer.utils.logger import get_logger

logger = get_logger(__name__)

def write_json(file_path: str, data: Any) -> bool:
    """Сохранение данных в JSON файл"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error writing JSON: {str(e)}")
        return False

def read_json(file_path: str) -> Any:
    """Чтение данных из JSON файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading JSON: {str(e)}")
        return None

def write_pickle(file_path: str, data: Any) -> bool:
    """Сохранение данных в pickle формате"""
    try:
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
        return True
    except Exception as e:
        logger.error(f"Error writing pickle: {str(e)}")
        return False

def read_pickle(file_path: str) -> Any:
    """Чтение данных из pickle файла"""
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        logger.error(f"Error reading pickle: {str(e)}")
        return None

def ensure_directory_exists(path: str) -> bool:
    """Создание директории, если она не существует"""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory: {str(e)}")
        return False