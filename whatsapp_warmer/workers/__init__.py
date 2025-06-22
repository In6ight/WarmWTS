"""
Background workers and automation logic
"""

from .whatsapp_worker import WhatsAppWorker
from .web_view import WhatsAppWebView
from .selenium_manager import SeleniumSetup

__all__ = ['WhatsAppWorker', 'WhatsAppWebView', 'SeleniumSetup']