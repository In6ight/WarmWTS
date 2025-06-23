from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from PyQt6.QtCore import QObject, pyqtSignal
from typing import List, Dict, Optional
import time
import random
import logging
from whatsapp_warmer.core.models.account import WhatsAppAccount

logger = logging.getLogger(__name__)


class WarmingEngine(QObject):
    """Движок прогрева аккаунтов WhatsApp через Selenium"""

    progress_updated = pyqtSignal(int, str)  # percent, status
    account_activity = pyqtSignal(str, str)  # phone, activity
    error_occurred = pyqtSignal(str, str)  # context, error
    warming_completed = pyqtSignal(bool)  # success

    def __init__(self):
        super().__init__()
        self._running = False
        self._paused = False
        self._current_round = 0
        self.settings = {
            'rounds': 3,
            'min_delay': 15,
            'max_delay': 45,
            'messages_per_round': 2,
            'round_delay': 120,
            'strategy': 'random_pairs'
        }
        self._active_accounts: List[WhatsAppAccount] = []
        self._drivers: Dict[str, webdriver.Chrome] = {}

    def update_settings(self, settings: Dict):
        """Обновление настроек прогрева"""
        self.settings.update(settings)

    def start_warming(self, accounts: List[WhatsAppAccount]):
        """Запуск прогрева аккаунтов"""
        if self._running:
            logger.warning("Прогрев уже запущен")
            return

        self._running = True
        self._active_accounts = [acc for acc in accounts if acc.enabled]

        try:
            self._run_warming_cycle()
        except Exception as e:
            logger.error(f"Ошибка прогрева: {str(e)}")
            self.error_occurred.emit("global", str(e))
            self.stop_warming()

    def _run_warming_cycle(self):
        """Основной цикл прогрева"""
        for round_num in range(1, self.settings['rounds'] + 1):
            if not self._running:
                break

            self._current_round = round_num
            status = f"Раунд {round_num}/{self.settings['rounds']}"
            self.progress_updated.emit(
                int((round_num / self.settings['rounds']) * 100),
                status
            )

            self._process_round()

            if round_num < self.settings['rounds']:
                self._wait_with_checks(self.settings['round_delay'])

        self.warming_completed.emit(self._running)
        self._running = False

    def _process_round(self):
        """Обработка одного раунда прогрева"""
        accounts = random.sample(self._active_accounts, min(2, len(self._active_accounts)))

        for account in accounts:
            if not self._running:
                break

            try:
                self._warm_account(account)
            except Exception as e:
                logger.error(f"Ошибка прогрева аккаунта {account.phone}: {str(e)}")
                self.error_occurred.emit(account.phone, str(e))

    def _warm_account(self, account: WhatsAppAccount):
        """Прогрев одного аккаунта"""
        driver = self._init_driver(account)

        try:
            # Пример действий для прогрева
            self._open_whatsapp_web(driver, account)
            self._send_test_messages(driver, account)

            account.update_activity()
            account.add_message_stat(self.settings['messages_per_round'])
            self.account_activity.emit(account.phone, "warming_completed")

        finally:
            driver.quit()
            self._drivers.pop(account.phone, None)

    def _init_driver(self, account: WhatsAppAccount) -> webdriver.Chrome:
        """Инициализация Selenium WebDriver с настройками прокси"""
        options = webdriver.ChromeOptions()

        if account.proxy:
            options.add_argument(f"--proxy-server={account.proxy.get_formatted()}")

        driver = webdriver.Chrome(
            ChromeDriverManager().install(),
            options=options
        )
        self._drivers[account.phone] = driver
        return driver

    def _open_whatsapp_web(self, driver: webdriver.Chrome, account: WhatsAppAccount):
        """Открытие WhatsApp Web и ожидание загрузки"""
        driver.get("https://web.whatsapp.com")

        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located((By.XPATH, '//div[@title="Новый чат"]'))
            )
            self.account_activity.emit(account.phone, "whatsapp_loaded")
        except Exception as e:
            raise Exception(f"Не удалось загрузить WhatsApp Web: {str(e)}")

    def _send_test_messages(self, driver: webdriver.Chrome, account: WhatsAppAccount):
        """Отправка тестовых сообщений"""
        # Реализация стратегий прогрева
        if self.settings['strategy'] == 'random_pairs':
            self._send_random_messages(driver, account)

    def _send_random_messages(self, driver: webdriver.Chrome, account: WhatsAppAccount):
        """Отправка случайных сообщений"""
        contacts = driver.find_elements(By.XPATH, '//div[@role="listitem"]')

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

    def _wait_with_checks(self, seconds: int):
        """Ожидание с проверкой флагов running/paused"""
        for _ in range(seconds):
            if not self._running:
                break
            if self._paused:
                time.sleep(1)
                continue
            time.sleep(1)

    def stop_warming(self):
        """Остановка прогрева"""
        self._running = False
        for driver in self._drivers.values():
            try:
                driver.quit()
            except:
                pass
        self._drivers.clear()

    def toggle_pause(self):
        """Пауза/продолжение прогрева"""
        self._paused = not self._paused
        return self._paused