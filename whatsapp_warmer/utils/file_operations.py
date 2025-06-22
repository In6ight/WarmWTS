import json
import pickle
from pathlib import Path
from typing import Any, Union
import logging
from datetime import datetime

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FileManager:
    """Универсальный менеджер для работы с файлами"""

    @staticmethod
    def read_json(file_path: Union[str, Path], default: Any = None,
                  create_if_missing: bool = False) -> Any:
        """
        Чтение JSON файла с обработкой ошибок

        Args:
            file_path: Путь к файлу
            default: Значение по умолчанию если файл не существует или поврежден
            create_if_missing: Создать файл с default если не существует

        Returns:
            Данные из файла или default
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Ошибка чтения {file_path}: {str(e)}")
            if create_if_missing and default is not None:
                FileManager.write_json(file_path, default)
            return default

    @staticmethod
    def write_json(file_path: Union[str, Path], data: Any,
                   indent: int = 2, ensure_ascii: bool = False) -> bool:
        """
        Запись данных в JSON файл

        Args:
            file_path: Путь к файлу
            data: Данные для записи
            indent: Отступы в файле
            ensure_ascii: Экранирование не-ASCII символов

        Returns:
            True если запись успешна, False при ошибке
        """
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
            return True
        except (IOError, TypeError) as e:
            logger.error(f"Ошибка записи {file_path}: {str(e)}")
            return False

    @staticmethod
    def read_pickle(file_path: Union[str, Path], default: Any = None) -> Any:
        """Чтение pickle файла"""
        try:
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        except (FileNotFoundError, pickle.PickleError) as e:
            logger.warning(f"Ошибка чтения pickle {file_path}: {str(e)}")
            return default

    @staticmethod
    def write_pickle(file_path: Union[str, Path], data: Any) -> bool:
        """Запись данных в pickle файл"""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
            return True
        except (IOError, pickle.PickleError) as e:
            logger.error(f"Ошибка записи pickle {file_path}: {str(e)}")
            return False

    @staticmethod
    def backup_file(file_path: Union[str, Path],
                    backup_dir: Union[str, Path] = None,
                    max_backups: int = 3) -> bool:
        """
        Создание резервной копии файла

        Args:
            file_path: Путь к оригинальному файлу
            backup_dir: Директория для бэкапов (по умолчанию рядом с файлом)
            max_backups: Максимальное количество хранимых бэкапов

        Returns:
            True если бэкап создан успешно
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                return False

            # Определяем директорию для бэкапов
            backup_dir = Path(backup_dir) if backup_dir else file_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)

            # Формируем имя бэкапа с timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = backup_dir / backup_name

            # Копируем файл
            with open(file_path, 'rb') as src, open(backup_path, 'wb') as dst:
                dst.write(src.read())

            # Удаляем старые бэкапы
            backups = sorted(backup_dir.glob(f"{file_path.stem}_*{file_path.suffix}"))
            for old_backup in backups[:-max_backups]:
                old_backup.unlink()

            return True
        except Exception as e:
            logger.error(f"Ошибка создания бэкапа {file_path}: {str(e)}")
            return False

    @staticmethod
    def safe_save(file_path: Union[str, Path], data: Any,
                  backup: bool = True, serializer: str = 'json') -> bool:
        """
        Безопасное сохранение данных с созданием бэкапа

        Args:
            file_path: Путь к файлу
            data: Данные для сохранения
            backup: Создавать ли резервную копию
            serializer: Формат сохранения (json/pickle)

        Returns:
            True если операция успешна
        """
        if backup:
            FileManager.backup_file(file_path)

        if serializer == 'json':
            return FileManager.write_json(file_path, data)
        elif serializer == 'pickle':
            return FileManager.write_pickle(file_path, data)
        else:
            raise ValueError(f"Неизвестный сериализатор: {serializer}")


# Алиасы для обратной совместимости
load_json = FileManager.read_json
save_json = FileManager.write_json