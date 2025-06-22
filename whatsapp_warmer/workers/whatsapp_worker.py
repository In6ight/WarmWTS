import time
import random
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (TimeoutException)
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from whatsapp_warmer.models.account import WhatsAppAccount
from whatsapp_warmer.utils.logger import get_logger
from whatsapp_warmer.config import Paths, SeleniumConfig

logger = get_logger(__name__)


class WhatsAppWorker(QThread):
    """
    Worker thread for handling WhatsApp account warming operations
    with enhanced error handling and progress tracking
    """
    # Status signals
    status_update = pyqtSignal(str, str)  # phone, message
    progress_update = pyqtSignal(int)  # percentage
    operation_complete = pyqtSignal(bool)  # success

    # Authentication signals
    qr_code_required = pyqtSignal(str, str)  # phone, qr_data_base64
    verification_code_required = pyqtSignal(str)  # phone

    # WebView management
    webview_ready = pyqtSignal(dict)  # account_info

    def __init__(self,
                 accounts: List[WhatsAppAccount],
                 settings: Dict,
                 warmup_phrases: List[str],
                 parent: Optional[QObject] = None):
        super().__init__(parent)
        self.accounts = [acc for acc in accounts if acc.enabled]
        self.settings = settings
        self.warmup_phrases = warmup_phrases
        self._running = True
        self._drivers = []
        self._verification_code = None
        self._current_round = 0

    def run(self):
        """Main execution method for the worker thread"""
        try:
            if not self._validate_environment():
                self.operation_complete.emit(False)
                return

            self._warm_up_accounts()
            self.operation_complete.emit(True)
        except Exception as e:
            logger.error(f"Critical error in worker thread: {str(e)}")
            self.status_update.emit("system", f"Critical error: {str(e)}")
            self.operation_complete.emit(False)
        finally:
            self._cleanup_drivers()

    def stop(self):
        """Gracefully stop the worker thread"""
        self._running = False
        self.status_update.emit("system", "Stopping worker...")
        logger.info("Worker stop requested")

    def set_verification_code(self, code: str):
        """Set the verification code for phone login"""
        self._verification_code = code

    def _validate_environment(self) -> bool:
        """Validate required environment and settings"""
        if not self.accounts:
            self.status_update.emit("system", "No enabled accounts found")
            return False

        if not self.warmup_phrases:
            self.status_update.emit("system", "No warmup phrases configured")
            return False

        if not self.settings.get('rounds', 0) > 0:
            self.status_update.emit("system", "Invalid rounds count")
            return False

        return True

    def _warm_up_accounts(self):
        """Main warming process for all accounts"""
        total_accounts = len(self.accounts)
        target_phones = [acc.phone for acc in self.accounts]

        for idx, account in enumerate(self.accounts):
            if not self._running:
                break

            try:
                driver = self._init_driver(account, idx)
                if not driver:
                    continue

                self._drivers.append(driver)
                self._login_account(driver, account, idx + 1)
                self._add_contacts(driver, target_phones, idx + 1)
                self._notify_webview_ready(account, idx + 1)

                progress = int(((idx + 1) / total_accounts) * 100)
                self.progress_update.emit(progress)

            except Exception as e:
                logger.error(f"Error processing account {account.phone}: {str(e)}")
                self.status_update.emit(account.phone, f"Error: {str(e)}")

        if len(self._drivers) >= 2 and self._running:
            self._perform_warming_rounds(target_phones)

    def _init_driver(self, account: WhatsAppAccount, idx: int) -> Optional[webdriver.Chrome]:
        """Initialize and configure Chrome WebDriver"""
        try:
            options = Options()

            # Apply standard Chrome options
            for opt in SeleniumConfig.CHROME_OPTIONS:
                options.add_argument(opt)

            # Configure proxy if enabled
            if account.proxy and account.proxy.enabled and account.proxy.validate():
                self._configure_proxy(options, account.proxy)
                self.status_update.emit(
                    account.phone,
                    f"Using proxy: {account.proxy.host}:{account.proxy.port}"
                )

            # Set up user profile
            profile_path = Paths.DATA_DIR / "profiles" / f"whatsapp_{idx}"
            profile_path.mkdir(parents=True, exist_ok=True)
            options.add_argument(f"--user-data-dir={profile_path}")

            # Initialize WebDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(SeleniumConfig.PAGE_LOAD_TIMEOUT)

            return driver

        except Exception as e:
            logger.error(f"Failed to initialize driver for {account.phone}: {str(e)}")
            self.status_update.emit(account.phone, f"Driver init failed: {str(e)}")
            return None

    def _configure_proxy(self, options: Options, proxy_config):
        """Configure proxy settings for WebDriver"""
        proxy_str = f"{proxy_config.host}:{proxy_config.port}"
        if proxy_config.username and proxy_config.password:
            proxy_str = f"{proxy_config.username}:{proxy_config.password}@{proxy_str}"

        options.add_argument(f"--proxy-server={proxy_config.type}://{proxy_str}")

    def _login_account(self, driver: webdriver.Chrome, account: WhatsAppAccount, account_idx: int) -> bool:
        """Handle account login process"""
        try:
            self.status_update.emit(account.phone, "Starting login process...")

            if account.login_method == 'qr':
                return self._login_with_qr(driver, account, account_idx)
            else:
                return self._login_with_phone(driver, account, account_idx)
        except Exception as e:
            logger.error(f"Login failed for {account.phone}: {str(e)}")
            self.status_update.emit(account.phone, f"Login failed: {str(e)}")
            return False

    def _login_with_qr(self, driver: webdriver.Chrome, account: WhatsAppAccount, account_idx: int) -> bool:
        """Login using QR code method"""
        self.status_update.emit(account.phone, "Waiting for QR code scan...")
        driver.get("https://web.whatsapp.com/")

        try:
            # Wait for QR code to appear
            qr_element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//canvas[@aria-label="Scan me!"]'))
            )

            # Emit QR code data
            qr_data = qr_element.screenshot_as_base64
            self.qr_code_required.emit(account.phone, qr_data)

            # Wait for QR code to disappear (successful scan)
            WebDriverWait(driver, 180).until(
                EC.invisibility_of_element_located((By.XPATH, '//canvas[@aria-label="Scan me!"]'))
            )

            # Verify successful login
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[@title="Меню"] | //div[@title="New chat"]'))
            )

            self.status_update.emit(account.phone, "Successfully logged in via QR")
            return True

        except TimeoutException:
            self.status_update.emit(account.phone, "QR code scan timed out")
            return False

    def _login_with_phone(self, driver: webdriver.Chrome, account: WhatsAppAccount, account_idx: int) -> bool:
        """Login using phone number method"""
        self.status_update.emit(account.phone, "Starting phone login...")
        driver.get("https://web.whatsapp.com/")

        try:
            # Click phone number button
            phone_btn = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Use phone number")]'))
            )
            phone_btn.click()

            # Enter phone number
            phone_input = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '//input[@id="phone-number"]'))
            )
            phone_input.clear()
            phone_input.send_keys(account.phone)

            # Click next
            next_btn = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Next")]'))
            )
            next_btn.click()

            # Request verification code
            self.status_update.emit(account.phone, "Waiting for verification code...")
            self.verification_code_required.emit(account.phone)

            # Wait for code input
            code_inputs = WebDriverWait(driver, 120).until(
                EC.presence_of_all_elements_located((By.XPATH, '//input[@aria-label="Enter code"]'))
            )

            if not self._verification_code or len(self._verification_code) != 6:
                self.status_update.emit(account.phone, "Invalid verification code")
                return False

            # Enter verification code
            for i, digit in enumerate(self._verification_code):
                if i < len(code_inputs):
                    code_inputs[i].send_keys(digit)
                    time.sleep(0.3)

            # Verify successful login
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[@title="Меню"] | //div[@title="New chat"]'))
            )

            self.status_update.emit(account.phone, "Successfully logged in via phone")
            return True

        except Exception as e:
            self.status_update.emit(account.phone, f"Phone login failed: {str(e)}")
            return False

    def _add_contacts(self, driver: webdriver.Chrome, target_phones: List[str], account_idx: int):
        """Add target contacts to the account"""
        current_phone = self.accounts[account_idx - 1].phone

        for phone in target_phones:
            if not self._running:
                break

            if phone != current_phone:
                self._add_contact(driver, phone, account_idx)

    def _add_contact(self, driver: webdriver.Chrome, phone: str, account_idx: int):
        """Add single contact to the account"""
        try:
            self.status_update.emit(self.accounts[account_idx - 1].phone, f"Adding contact: {phone}")

            # Click new chat button
            new_chat_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//div[@title="Новый чат"] | //div[@title="New chat"]'))
            )
            new_chat_btn.click()

            # Search for contact
            search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
            )
            search_input.clear()
            search_input.send_keys(phone)
            time.sleep(2)

            # Check if contact exists
            add_contact_btn = driver.find_elements(
                By.XPATH, '//span[contains(text(), "Добавить")] | //span[contains(text(), "Add")]')

            if add_contact_btn:
                add_contact_btn[0].click()
                time.sleep(1)

                # Confirm adding contact
                confirm_btn = driver.find_elements(
                    By.XPATH, '//button//span[contains(text(), "Готово")] | //button//span[contains(text(), "Done")]')

                if confirm_btn:
                    confirm_btn[0].click()
                    self.status_update.emit(
                        self.accounts[account_idx - 1].phone,
                        f"Contact added: {phone}"
                    )
                else:
                    self.status_update.emit(
                        self.accounts[account_idx - 1].phone,
                        f"Failed to confirm adding {phone}"
                    )
            else:
                self.status_update.emit(
                    self.accounts[account_idx - 1].phone,
                    f"Contact already exists: {phone}"
                )

        except Exception as e:
            self.status_update.emit(
                self.accounts[account_idx - 1].phone,
                f"Error adding contact {phone}: {str(e)}"
            )

    def _perform_warming_rounds(self, target_phones: List[str]):
        """Perform the actual warming rounds between accounts"""
        total_rounds = self.settings.get('rounds', 5)

        for round_num in range(1, total_rounds + 1):
            if not self._running:
                break

            self._current_round = round_num
            self.status_update.emit(
                "system",
                f"Starting warming round {round_num}/{total_rounds}"
            )

            for driver, account in zip(self._drivers, self.accounts):
                if not self._running:
                    break

                try:
                    self._perform_account_warming(driver, account, target_phones)
                except Exception as e:
                    self.status_update.emit(
                        account.phone,
                        f"Error in round {round_num}: {str(e)}"
                    )

            if round_num < total_rounds and self._running:
                round_delay = self.settings.get('round_delay', 150)
                self.status_update.emit(
                    "system",
                    f"Waiting {round_delay} sec before next round..."
                )
                time.sleep(round_delay)

    def _perform_account_warming(self, driver: webdriver.Chrome, account: WhatsAppAccount, target_phones: List[str]):
        """Perform warming actions for a single account"""
        other_phones = [p for p in target_phones if p != account.phone]
        if not other_phones:
            return

        target_phone = random.choice(other_phones)

        if self._select_chat_with_contact(driver, target_phone):
            phrase = self._select_warming_phrase(account)
            if phrase:
                self._send_message(driver, phrase, account, target_phone)

                # Random delay between min and max settings
                min_delay = self.settings.get('min_delay', 5)
                max_delay = self.settings.get('max_delay', 30)
                delay = random.uniform(min_delay, max_delay)
                time.sleep(delay)

    def _select_chat_with_contact(self, driver: webdriver.Chrome, phone: str) -> bool:
        """Select chat with specified contact"""
        try:
            # Find search input
            search_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
            )
            search_input.clear()
            search_input.send_keys(phone)
            time.sleep(2)

            # Find and click the chat
            chat = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.XPATH, f'//span[@title="{phone}"]/ancestor::div[@role="row"]'))
            )
            chat.click()
            return True

        except Exception:
            return False

    def _select_warming_phrase(self, account: WhatsAppAccount) -> Optional[str]:
        """Select a warming phrase that hasn't been used recently"""
        available_phrases = [
            p for p in self.warmup_phrases
            if p not in account.used_phrases
        ]

        if not available_phrases:
            account.used_phrases = []
            available_phrases = self.warmup_phrases.copy()

        if available_phrases:
            phrase = random.choice(available_phrases)
            account.used_phrases.append(phrase)
            return phrase

        return None

    def _send_message(self, driver: webdriver.Chrome, message: str,
                      account: WhatsAppAccount, target_phone: str):
        """Send message to selected contact"""
        try:
            # Find message input
            input_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
            )
            input_box.clear()
            input_box.send_keys(message)

            # Find and click send button
            send_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, '//button[@aria-label="Отправить"] | //button[@aria-label="Send"]'))
            )
            send_button.click()
            time.sleep(1)

            # Verify message delivery
            if self._check_message_delivery(driver):
                self.status_update.emit(
                    account.phone,
                    f"Message delivered to {target_phone}: {message[:20]}..."
                )
            else:
                self.status_update.emit(
                    account.phone,
                    f"Message not delivered to {target_phone}"
                )

        except Exception as e:
            self.status_update.emit(
                account.phone,
                f"Error sending message: {str(e)}"
            )

    def _check_message_delivery(self, driver: webdriver.Chrome, timeout: int = 10) -> bool:
        """Check if message was delivered"""
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//span[@data-testid="msg-dblcheck"] | //span[@data-testid="msg-check"]'))
            )
            return True
        except TimeoutException:
            return False

    def _notify_webview_ready(self, account: WhatsAppAccount, account_idx: int):
        """Notify about successful initialization"""
        self.webview_ready.emit({
            'phone': account.phone,
            'index': account_idx,
            'login_method': account.login_method
        })

    def _cleanup_drivers(self):
        """Clean up all WebDriver instances"""
        for driver in self._drivers:
            try:
                driver.quit()
            except Exception as e:
                logger.error(f"Error quitting driver: {str(e)}")

        self._drivers = []