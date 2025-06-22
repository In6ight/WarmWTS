from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from ..models.account import WhatsAppAccount
from ..models.proxy import ProxyConfig
import os


class SeleniumSetup:
    """Настройка Selenium WebDriver для аккаунта"""

    @staticmethod
    def create_driver(account: WhatsAppAccount, profile_index: int) -> webdriver.Chrome:
        options = Options()
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-infobars")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--remote-debugging-port=9222")

        # Настройка прокси
        if account.proxy.enabled and account.proxy.validate():
            proxy = account.proxy
            proxy_str = f"{proxy.host}:{proxy.port}"
            if proxy.username and proxy.password:
                proxy_str = f"{proxy.username}:{proxy.password}@{proxy_str}"
            options.add_argument(f"--proxy-server={proxy.type}://{proxy_str}")

        # Настройка профиля
        profile_path = os.path.abspath(f"./whatsapp_profile_{profile_index}")
        os.makedirs(profile_path, exist_ok=True)
        options.add_argument(f"--user-data-dir={profile_path}")

        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)