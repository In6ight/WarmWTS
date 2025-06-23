from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from whatsapp_warmer.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class WarmingStats:
    """Статистика прогрева аккаунта WhatsApp"""
    messages_sent: int = 0
    last_warming: Optional[datetime] = None
    sessions: int = 0
    errors: int = 0
    avg_response_time: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь"""
        return {
            'messages_sent': self.messages_sent,
            'last_warming': self.last_warming.isoformat() if self.last_warming else None,
            'sessions': self.sessions,
            'errors': self.errors,
            'avg_response_time': self.avg_response_time
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WarmingStats':
        """Десериализация из словаря"""
        return cls(
            messages_sent=data.get('messages_sent', 0),
            last_warming=datetime.fromisoformat(data['last_warming']) if data.get('last_warming') else None,
            sessions=data.get('sessions', 0),
            errors=data.get('errors', 0),
            avg_response_time=data.get('avg_response_time')
        )