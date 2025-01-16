# core/__init__.py
import logging
import sys

from core.base_page import BasePage
from core.webdriver import WebDriverFactory
from core.logger import Logger

__all__ = ['BasePage', 'WebDriverFactory', 'Logger']

from jinja2 import ext


# config/config.py
class Config:
    BASE_URL = "https://example.com"
    BROWSER = "chrome"
    IMPLICIT_WAIT = 10
    HEADLESS = False

    # Directory paths
    REPORTS_DIR = "reports"
    LOGS_DIR = "logs"
    SCREENSHOTS_DIR = "screenshots"


# config/logger_config.yaml
version: 1
formatters:
simple:
format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
handlers:
console:


class: logging.StreamHandler


level: logging.INFO
formatter: simple
stream: ext: // sys.stdout
file:


class: logging.FileHandler


level: logging.DEBUG
formatter: simple
filename: logs / test.log
root:
level: DEBUG
handlers: [console, file]

# tests/conftest.py
import pytest
from core.webdriver import WebDriverFactory
from core.logger import Logger
from config.config import Config


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """Setup logging configuration"""
    Logger.initialize('config/logger_config.yaml')
    return Logger.get_logger('TestFramework')


@pytest.fixture
def driver():
    """Setup WebDriver instance"""
    driver = WebDriverFactory.get_driver(
        browser=Config.BROWSER,
        options={
            'headless': Config.HEADLESS,
            'implicit_wait': Config.IMPLICIT_WAIT
        }
    )
    yield driver
    WebDriverFactory.quit_driver()


# tests/test_example.py
from core.base_page import BasePage
from selenium.webdriver.common.by import By


class LoginPage(BasePage):
    # Locators
    USERNAME_FIELD = (By.ID, "username")
    PASSWORD_FIELD = (By.ID, "password")
    LOGIN_BUTTON = (By.ID, "login")

    def __init__(self, driver):
        super().__init__(driver)
        self.url = "https://example.com/login"

    def login(self, username: str, password: str):
        self.input_text(self.USERNAME_FIELD, username)
        self.input_text(self.PASSWORD_FIELD, password)
        self.click(self.LOGIN_BUTTON)


def test_login(driver, setup_logging):
    logger = setup_logging
    logger.info("Starting login test")

    page = LoginPage(driver)
    page.login("testuser", "testpass")

    logger.info("Login test completed")

