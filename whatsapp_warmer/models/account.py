from dataclasses import dataclass, field
from typing import List
from .proxy import ProxyConfig

@dataclass
class WhatsAppAccount:
    """Аккаунт WhatsApp с настройками"""
    phone: str
    login_method: str = "qr"  # qr/phone
    enabled: bool = True
    proxy: ProxyConfig = field(default_factory=ProxyConfig)
    used_phrases: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.proxy, ProxyConfig):
            self.proxy = ProxyConfig(**self.proxy) if self.proxy else ProxyConfig()