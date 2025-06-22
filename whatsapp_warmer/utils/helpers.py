import re
import time
import random
import string
from typing import Optional, Union, List, Dict
from pathlib import Path
from datetime import timedelta
from PyQt6.QtCore import QObject, pyqtSignal
from whatsapp_warmer.config import Paths
import logging

logger = logging.getLogger(__name__)


class Helpers(QObject):
    """Класс со вспомогательными методами"""

    # Сигналы
    status_message = pyqtSignal(str)
    progress_update = pyqtSignal(int)

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Проверяет валидность номера телефона"""
        phone = ''.join(filter(str.isdigit, phone))
        return len(phone) >= 10 and phone.isdigit()

    @staticmethod
    def format_phone(phone: str) -> str:
        """Форматирует номер телефона в международный формат"""
        digits = ''.join(filter(str.isdigit, phone))
        if digits.startswith('8'):
            return '7' + digits[1:]
        return digits

    @staticmethod
    def generate_random_string(length: int = 8) -> str:
        """Генерирует случайную строку из букв и цифр"""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Очищает строку для использования в имени файла"""
        sanitized = re.sub(r'[\\/*?:"<>|]', "_", filename)
        return sanitized.strip()

    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> str:
        """Возвращает размер файла в удобочитаемом формате"""
        size = Path(file_path).stat().st_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    @staticmethod
    def humanize_time(seconds: int) -> str:
        """Форматирует время в человекочитаемый формат"""
        periods = [
            ('день', 86400),
            ('час', 3600),
            ('минута', 60),
            ('секунда', 1)
        ]
        parts = []
        for period_name, period_seconds in periods:
            if seconds >= period_seconds:
                period_value, seconds = divmod(seconds, period_seconds)
                parts.append(
                    f"{period_value} {period_name}{'ы' if period_value % 10 in [2, 3, 4] and period_value % 100 not in [12, 13, 14] else '' if 5 <= period_value % 10 <= 9 or period_value % 10 == 0 or period_value % 100 in [11, 12, 13, 14] else 'а'}")

        return ' '.join(parts[:2]) if parts else "0 секунд"

    @classmethod
    def timeit(cls, func):
        """Декоратор для измерения времени выполнения функции"""

        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            logger.info(f"{func.__name__} выполнена за {elapsed:.2f} сек")
            return result

        return wrapper

    @staticmethod
    def parse_timedelta(time_str: str) -> Optional[timedelta]:
        """
        Парсит строку временного интервала в timedelta
        Форматы: "1h30m", "2d5h", "45m" и т.д.
        """
        pattern = r"(?P<value>\d+)(?P<unit>[dhms])"
        units = {
            'd': 'days',
            'h': 'hours',
            'm': 'minutes',
            's': 'seconds'
        }
        kwargs = {}
        for match in re.finditer(pattern, time_str.lower()):
            value = int(match.group('value'))
            unit = match.group('unit')
            kwargs[units[unit]] = value

        return timedelta(**kwargs) if kwargs else None

    @staticmethod
    def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
        """Рекурсивное объединение словарей"""
        result = dict1.copy()
        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Helpers.merge_dicts(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def chunk_list(lst: List, size: int) -> List[List]:
        """Разбивает список на части указанного размера"""
        return [lst[i:i + size] for i in range(0, len(lst), size)]

    @staticmethod
    def get_app_data_dir() -> Path:
        """Возвращает путь к директории данных приложения"""
        data_dir = Paths.DATA_DIR
        data_dir.mkdir(exist_ok=True)
        return data_dir

    @staticmethod
    def setup_logging(log_file: str = "app.log") -> None:
        """Настройка логгирования"""
        log_path = Helpers.get_app_data_dir() / log_file
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler()
            ]
        )

    @classmethod
    def retry(cls, max_attempts: int = 3, delay: int = 1, exceptions=(Exception,)):
        """Декоратор для повторного выполнения функции при ошибках"""

        def decorator(func):
            def wrapper(*args, **kwargs):
                last_exception = None
                for attempt in range(1, max_attempts + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        logger.warning(f"Попытка {attempt} из {max_attempts} не удалась: {str(e)}")
                        if attempt < max_attempts:
                            time.sleep(delay)
                raise last_exception

            return wrapper

        return decorator