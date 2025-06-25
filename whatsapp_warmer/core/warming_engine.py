from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import time
import random
import logging
from typing import List, Dict, Optional
from whatsapp_warmer.utils.logger import get_logger

logger = get_logger(__name__)


class WarmingEngine(QObject):
    progress_updated = pyqtSignal(int, str)  # percent, status
    account_activity = pyqtSignal(str, str)  # phone, activity
    error_occurred = pyqtSignal(str, str)  # context, error
    warming_completed = pyqtSignal(bool)  # success

    def __init__(self, account_manager=None, proxy_handler=None, parent=None):
        super().__init__(parent)
        self.account_manager = account_manager
        self.proxy_handler = proxy_handler
        self._running = False
        self._paused = False
        self._current_round = 0
        self._active_accounts = []
        self._drivers = {}

        # Настройки по умолчанию
        self.settings = {
            'rounds': 3,
            'min_delay': 15,
            'max_delay': 45,
            'messages_per_round': 2,
            'round_delay': 120,
            'strategy': 'random_pairs'
        }

    def update_settings(self, new_settings: Dict):
        """Обновление настроек прогрева"""
        if not isinstance(new_settings, dict):
            logger.warning("Invalid settings format, using defaults")
            return

        self.settings.update(new_settings)
        logger.info(f"Updated warming settings: {self.settings}")

    def _process_round(self):
        """Обработка одного раунда прогрева"""
        if not self._running:
            return

        accounts = random.sample(
            self._active_accounts,
            min(2, len(self._active_accounts))
        )

        for account in accounts:
            if not self._running:
                break

            try:
                self._warm_account(account)
            except Exception as e:
                logger.error(f"Account warming error ({account.phone}): {e}")
                self.error_occurred.emit(account.phone, str(e))

    def _warm_account(self, account):
        """Прогрев одного аккаунта"""
        driver = self._init_driver(account)
        if not driver:
            return

        try:
            self._open_whatsapp_web(driver, account)
            self._send_test_messages(driver, account)

            # Обновление статистики
            account.update_activity()
            account.add_message_stat(self.settings['messages_per_round'])
            self.account_activity.emit(account.phone, "warming_completed")
        finally:
            driver.quit()
            self._drivers.pop(account.phone, None)

    def _init_driver(self, account):
        """Инициализация WebDriver с настройками прокси"""
        try:
            options = webdriver.ChromeOptions()

            if account.proxy and self.proxy_handler:
                proxy = self.proxy_handler.get_proxy_for_account(account)
                if proxy:
                    options.add_argument(f"--proxy-server={proxy.connection_string}")

            driver = webdriver.Chrome(
                ChromeDriverManager().install(),
                options=options
            )
            self._drivers[account.phone] = driver
            return driver
        except Exception as e:
            logger.error(f"Driver initialization failed: {e}")
            self.error_occurred.emit(account.phone, f"Driver error: {e}")
            return None

    def _open_whatsapp_web(self, driver, account):
        """Открытие WhatsApp Web"""
        driver.get("https://web.whatsapp.com")

        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, '//div[@title="Новый чат"]'))
            )
            self.account_activity.emit(account.phone, "whatsapp_loaded")
        except Exception as e:
            raise Exception(f"Failed to load WhatsApp: {e}")

    def _send_test_messages(self, driver, account):
        """Отправка тестовых сообщений"""
        if self.settings['strategy'] == 'random_pairs':
            self._send_random_messages(driver, account)

    def _send_random_messages(self, driver, account):
        """Отправка случайных сообщений"""
        try:
            contacts = driver.find_elements(By.XPATH, '//div[@role="listitem"]')
            if not contacts:
                raise Exception("No contacts found")

            for _ in range(self.settings['messages_per_round']):
                if not self._running:
                    break

                contact = random.choice(contacts)
                contact.click()
                time.sleep(1)

                msg_box = driver.find_element(By.XPATH, '//div[@title="Введите сообщение"]')
                msg_box.send_keys(f"Тестовое сообщение от {account.phone[:4]}...")
                driver.find_element(By.XPATH, '//button[@aria-label="Отправить"]').click()

                self.account_activity.emit(account.phone, f"message_sent:{contact.text[:10]}...")
                self._wait_with_checks(random.randint(
                    self.settings['min_delay'],
                    self.settings['max_delay']
                ))
        except Exception as e:
            raise Exception(f"Message sending failed: {e}")

    def _wait_with_checks(self, seconds: int):
        """Ожидание с проверкой флагов"""
        for _ in range(seconds):
            if not self._running:
                break
            if self._paused:
                time.sleep(1)
                continue
            time.sleep(1)

    def start_warming(self, accounts: Optional[List] = None):
        """Запуск прогрева"""
        if self._running:
            logger.warning("Warming already in progress")
            return

        self._running = True
        self._active_accounts = accounts or self.account_manager.get_active_accounts()

        if not self._active_accounts:
            logger.error("No active accounts to warm")
            self._running = False
            return

        logger.info(f"Starting warming for {len(self._active_accounts)} accounts")
        self._current_round = 0

        for _ in range(self.settings['rounds']):
            if not self._running:
                break
            self._process_round()
            self._wait_with_checks(self.settings['round_delay'])
            self._current_round += 1

        self._running = False
        self.warming_completed.emit(True)

    def stop_warming(self):
        """Экстренная остановка прогрева"""
        self._running = False
        for driver in self._drivers.values():
            try:
                driver.quit()
            except:
                pass
        self._drivers.clear()
        logger.info("Warming stopped")

    def toggle_pause(self):
        """Пауза/продолжение прогрева"""
        self._paused = not self._paused
        status = "paused" if self._paused else "resumed"
        logger.info(f"Warming {status}")
        return self._paused

    def is_running(self) -> bool:
        """Проверка активности прогрева"""
        return self._running

    def is_paused(self) -> bool:
        """Проверка состояния паузы"""
        return self._paused