from typing import Dict
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineSettings
from PyQt6.QtCore import QUrl, Qt, pyqtSignal, QTimer
from whatsapp_warmer.config import Paths
from whatsapp_warmer.utils.logger import get_logger

logger = get_logger(__name__)


class WhatsAppWebView(QWebEngineView):
    """Расширенный WebView для работы с WhatsApp Web"""

    # Сигналы
    page_loaded = pyqtSignal(bool)  # Успешна ли загрузка
    qr_code_ready = pyqtSignal(str, str)  # phone, qr_data
    login_success = pyqtSignal(str)  # phone
    error_occurred = pyqtSignal(str, str)  # phone, error_message

    def __init__(self, account_info: Dict, parent=None):
        super().__init__(parent)
        self.account_info = account_info
        self.phone = account_info.get('phone', 'unknown')
        self._is_logged_in = False
        self._qr_check_timer = QTimer(self)

        try:
            self._init_webview()
            self._setup_connections()
            logger.info(f"WebView инициализирован для {self.phone}")
        except Exception as e:
            logger.error(f"Ошибка инициализации WebView: {str(e)}")
            raise

    def _init_webview(self):
        """Инициализация WebView с правильными путями профилей"""
        # Создаем уникальный путь к профилю
        profile_name = f"wa_profile_{self.account_info.get('index', 0)}"
        self.profile_path = Paths.PROFILES_DIR / profile_name
        self.profile_path.mkdir(parents=True, exist_ok=True)

        # Настройка профиля
        self.profile = QWebEngineProfile(str(self.profile_path), self)
        self.page = QWebEnginePage(self.profile, self)
        self.setPage(self.page)

        # Настройки WebEngine
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, True)

        # Оптимизация производительности
        self.setZoomFactor(0.85)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

    def _setup_connections(self):
        """Настройка сигналов и таймеров"""
        self.page.loadStarted.connect(self._on_load_started)
        self.page.loadFinished.connect(self._on_load_finished)
        self._qr_check_timer.timeout.connect(self._check_qr_code)
        self._qr_check_timer.setInterval(2000)  # Проверка каждые 2 секунды

    def load_whatsapp(self):
        """Загружает WhatsApp Web с обработкой ошибок"""
        try:
            self.load(QUrl("https://web.whatsapp.com/"))
            logger.info(f"Загрузка WhatsApp Web для {self.phone}")
        except Exception as e:
            error_msg = f"Ошибка загрузки: {str(e)}"
            logger.error(error_msg)
            self.error_occurred.emit(self.phone, error_msg)

    def _on_load_started(self):
        """Обработчик начала загрузки"""
        self._is_logged_in = False
        self._qr_check_timer.stop()

    def _on_load_finished(self, success: bool):
        """Обработчик завершения загрузки"""
        self.page_loaded.emit(success)

        if success:
            try:
                self.page.runJavaScript(self._get_auth_script(), self._handle_auth_status)
                if not self._is_logged_in:
                    self._qr_check_timer.start()
            except Exception as e:
                error_msg = f"Ошибка проверки авторизации: {str(e)}"
                logger.error(error_msg)
                self.error_occurred.emit(self.phone, error_msg)
        else:
            error_msg = "Ошибка загрузки страницы"
            logger.error(error_msg)
            self.error_occurred.emit(self.phone, error_msg)

    def _check_qr_code(self):
        """Проверяет наличие QR кода на странице"""
        if not self._is_logged_in:
            try:
                self.page.runJavaScript(self._get_qr_script(), self._handle_qr_detection)
            except Exception as e:
                error_msg = f"Ошибка проверки QR: {str(e)}"
                logger.error(error_msg)
                self.error_occurred.emit(self.phone, error_msg)

    def _handle_qr_detection(self, result):
        """Обрабатывает обнаружение QR кода"""
        if result and isinstance(result, dict):
            qr_data = result.get('qrData')
            if qr_data:
                self.qr_code_ready.emit(self.phone, qr_data)
                logger.info(f"QR код обнаружен для {self.phone}")

    def _handle_auth_status(self, result):
        """Обрабатывает статус авторизации"""
        self._is_logged_in = result is True
        if self._is_logged_in:
            self._qr_check_timer.stop()
            self.login_success.emit(self.phone)
            logger.info(f"Успешный вход для {self.phone}")

    def cleanup(self):
        """Очистка ресурсов"""
        try:
            self._qr_check_timer.stop()
            self.page.deleteLater()
            self.profile.deleteLater()
            logger.info(f"Ресурсы WebView очищены для {self.phone}")
        except Exception as e:
            logger.error(f"Ошибка очистки WebView: {str(e)}")

    @staticmethod
    def _get_qr_script() -> str:
        """Возвращает JavaScript для проверки QR кода"""
        return """
            (function() {
                const qrCanvas = document.querySelector('canvas[aria-label="Scan me!"]');
                if (!qrCanvas) return null;
                return {
                    qrData: qrCanvas.toDataURL('image/png'),
                    timestamp: Date.now()
                };
            })();
        """

    @staticmethod
    def _get_auth_script() -> str:
        """Возвращает JavaScript для проверки авторизации"""
        return """
            (function() {
                return !!document.querySelector('div[title="Меню"], div[title="New chat"]');
            })();
        """

    def __del__(self):
        """Деструктор для гарантированной очистки"""
        self.cleanup()