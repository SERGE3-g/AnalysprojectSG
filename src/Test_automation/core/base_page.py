from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import *
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.select import Select
import os
import json
import time
from datetime import datetime
from typing import List, Tuple, Optional
from core.logger import Logger


class BasePage:
    """Enhanced base class for all page objects"""

    def __init__(self, driver):
        self.driver = driver
        self.timeout = 10
        self.wait = WebDriverWait(self.driver, self.timeout)
        self.logger = Logger.get_logger(self.__class__.__name__)

    def retry_on_exception(max_attempts: int = 3, delay: float = 1):
        """Decorator per ritentare operazioni in caso di errore"""

        def decorator(func):
            def wrapper(self, *args, **kwargs):
                last_exception = None
                for attempt in range(max_attempts):
                    try:
                        return func(self, *args, **kwargs)
                    except Exception as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            time.sleep(delay)
                            self.logger.warning(f"Retry attempt {attempt + 1} for {func.__name__}")
                raise last_exception

            return wrapper

        return decorator

    # Element Location Methods
    def find_element(self, by: By, value: str, timeout: Optional[int] = None) -> WebElement:
        """Find element with enhanced error handling and logging"""
        try:
            timeout = timeout or self.timeout
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            self.highlight_element(element)
            self.logger.debug(f"Element found: {by}={value}")
            return element
        except TimeoutException:
            self.logger.error(f"Element not found: {by}={value}")
            self.take_screenshot(f"element_not_found_{value}")
            raise
        except Exception as e:
            self.logger.error(f"Error finding element {by}={value}: {str(e)}")
            self.take_screenshot(f"error_finding_element_{value}")
            raise

    def find_elements(self, by: By, value: str, timeout: Optional[int] = None) -> List[WebElement]:
        """Find multiple elements with enhanced handling"""
        timeout = timeout or self.timeout
        try:
            elements = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located((by, value))
            )
            for element in elements:
                self.highlight_element(element)
            return elements
        except TimeoutException:
            self.logger.warning(f"No elements found: {by}={value}")
            return []

    def find_child_element(self, parent_element: WebElement, by: By, value: str) -> WebElement:
        """Find child element of a parent element"""
        return parent_element.find_element(by, value)

    # Enhanced Element Interaction Methods
    @retry_on_exception(max_attempts=3)
    def click(self, by: By, value: str, timeout: Optional[int] = None) -> None:
        """Enhanced click with multiple strategies"""
        element = self.find_element(by, value, timeout)
        try:
            self.wait_for_clickable((by, value))
            element.click()
        except ElementClickInterceptedException:
            self.logger.warning("Standard click failed, trying alternative methods")
            try:
                ActionChains(self.driver).move_to_element(element).click().perform()
            except:
                self.logger.warning("ActionChains click failed, trying JavaScript click")
                self.driver.execute_script("arguments[0].click();", element)

    def input_text(self, by: By, value: str, text: str, clear_first: bool = True,
                   click_first: bool = True) -> None:
        """Enhanced text input with options"""
        element = self.find_element(by, value)
        if click_first:
            element.click()
        if clear_first:
            element.clear()
            # Ensure the field is cleared
            if element.get_attribute("value"):
                element.send_keys(Keys.CONTROL + "a")
                element.send_keys(Keys.DELETE)
        element.send_keys(text)
        actual_value = element.get_attribute("value")
        if actual_value != text:
            self.logger.warning(f"Text verification failed. Expected: {text}, Got: {actual_value}")

    # Advanced Element State Methods
    def wait_for_condition(self, condition: callable, timeout: Optional[int] = None,
                           message: str = "") -> bool:
        """Wait for custom condition"""
        try:
            timeout = timeout or self.timeout
            WebDriverWait(self.driver, timeout).until(condition)
            return True
        except TimeoutException:
            self.logger.warning(f"Condition not met: {message}")
            return False

    def wait_for_page_load(self, timeout: Optional[int] = None) -> None:
        """Wait for page to completely load"""
        self.wait_for_condition(
            lambda driver: driver.execute_script("return document.readyState") == "complete",
            timeout,
            "Page load timeout"
        )

    def wait_for_ajax(self, timeout: Optional[int] = None) -> None:
        """Wait for all AJAX calls to complete"""
        self.wait_for_condition(
            lambda driver: driver.execute_script("return jQuery.active == 0"),
            timeout,
            "AJAX calls timeout"
        )

    # Enhanced Visual Helpers
    def highlight_element(self, element: WebElement, effect_time: float = 0.3) -> None:
        """Highlight element for visual debugging"""
        original_style = element.get_attribute("style")
        style = "border: 2px solid red; background: yellow;"
        self.driver.execute_script(
            "arguments[0].setAttribute('style', arguments[1]);",
            element, style
        )
        time.sleep(effect_time)
        self.driver.execute_script(
            "arguments[0].setAttribute('style', arguments[1]);",
            element, original_style
        )

    def take_element_screenshot(self, by: By, value: str, filename: str) -> None:
        """Take screenshot of specific element"""
        element = self.find_element(by, value)
        element.screenshot(filename)

    # Advanced Interaction Methods
    def press_key(self, by: By, value: str, key: str) -> None:
        """Press specific keyboard key on element"""
        element = self.find_element(by, value)
        element.send_keys(getattr(Keys, key.upper()))

    def get_element_attributes(self, by: By, value: str) -> dict:
        """Get all attributes of an element"""
        element = self.find_element(by, value)
        return self.driver.execute_script(
            'var items = {}; for (index = 0; index < arguments[0].attributes.length; ++index)'
            ' { items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value'
            ' }; return items;',
            element
        )

    # Enhanced JavaScript Methods
    def execute_script_with_retry(self, script: str, *args, max_attempts: int = 3) -> Any:
        """Execute JavaScript with retry logic"""
        for attempt in range(max_attempts):
            try:
                return self.driver.execute_script(script, *args)
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise
                time.sleep(1)

    def scroll_into_center(self, by: By, value: str) -> None:
        """Scroll element into center of viewport"""
        element = self.find_element(by, value)
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
            element
        )

    # Enhanced Validation Methods
    def verify_element_contains_text(self, by: By, value: str, text: str,
                                     case_sensitive: bool = False) -> bool:
        """Verify element contains specific text"""
        element_text = self.get_text(by, value)
        if not case_sensitive:
            return text.lower() in element_text.lower()
        return text in element_text

    def verify_element_attribute(self, by: By, value: str, attribute: str,
                                 expected_value: str) -> bool:
        """Verify element attribute value"""
        element = self.find_element(by, value)
        actual_value = element.get_attribute(attribute)
        return actual_value == expected_value

    # Enhanced File Operations
    def upload_file(self, by: By, value: str, file_path: str) -> None:
        """Upload file using send_keys"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        element = self.find_element(by, value)
        element.send_keys(os.path.abspath(file_path))

    def download_wait(self, directory: str, timeout: int = 30) -> bool:
        """Wait for download to complete"""
        seconds = 0
        dl_wait = True
        while dl_wait and seconds < timeout:
            time.sleep(1)
            dl_wait = False
            files = os.listdir(directory)
            for fname in files:
                if fname.endswith('.crdownload'):
                    dl_wait = True
            seconds += 1
        return seconds < timeout

    # Enhanced Cookie Management
    def get_all_cookies(self) -> List[dict]:
        """Get all cookies"""
        return self.driver.get_cookies()

    def add_cookie(self, cookie_dict: dict) -> None:
        """Add cookie to browser"""
        self.driver.add_cookie(cookie_dict)

    # Enhanced Network Methods
    def get_network_requests(self) -> List[dict]:
        """Get all network requests (requires Chrome DevTools Protocol)"""
        logs = self.driver.get_log('performance')
        return [json.loads(log['message'])['message'] for log in logs]

    # Enhanced Error Handling
    def safe_operation(self, operation: callable, default_value: Any = None) -> Any:
        """Safely execute operation with error handling"""
        try:
            return operation()
        except Exception as e:
            self.logger.error(f"Operation failed: {str(e)}")
            return default_value

    # Enhanced Assertions
    def assert_element_state(self, by: By, value: str,
                             state_check: callable,
                             message: str) -> None:
        """Assert element state with custom check"""
        element = self.find_element(by, value)
        assert state_check(element), message + " failed"

    def assert_element_text(self, by: By, value: str, expected_text: str) -> None:
        """Assert element text"""
        element = self.find_element(by, value)
        assert element.text == expected_text, f"Element text mismatch: {element.text} != {expected_text}"

    def assert_element_attribute(self, by: By, value: str, attribute: str, expected_value: str) -> None:
        """Assert element attribute value"""
        element = self.find_element(by, value)
        assert element.get_attribute(attribute) == expected_value, \
            f"Element attribute mismatch: {element.get_attribute(attribute)} != {expected_value}"

    def assert_element_visible(self, by: By, value: str) -> None:
        """Assert element is visible"""
        element = self.find_element(by, value)
        assert element.is_displayed(), f"Element not visible: {by}={value}"

    def assert_element_not_visible(self, by: By, value: str) -> None:
        """Assert element is not visible"""
        element = self.find_element(by, value)
        assert not element.is_displayed(), f"Element is visible: {by}={value}"