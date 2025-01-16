import os
from typing import Dict, Any
import json
import yaml
from datetime import datetime


class Config:
    """Classe per la gestione centralizzata delle configurazioni"""

    # Environment e configurazione base
    ENV = os.getenv('TEST_ENV', 'qa').lower()
    BROWSER = os.getenv('TEST_BROWSER', 'chrome').lower()
    HEADLESS = os.getenv('TEST_HEADLESS', 'false').lower() == 'true'

    # URLs per diversi ambienti
    URLS = {
        'qa': 'https://qa.example.com',
        'stage': 'https://staging.example.com',
        'prod': 'https://example.com'
    }

    # Timeouts
    IMPLICIT_WAIT = int(os.getenv('IMPLICIT_WAIT', '10'))
    EXPLICIT_WAIT = int(os.getenv('EXPLICIT_WAIT', '20'))
    PAGE_LOAD_TIMEOUT = int(os.getenv('PAGE_LOAD_TIMEOUT', '30'))

    # Directory paths
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    REPORTS_DIR = os.path.join(ROOT_DIR, 'reports')
    LOGS_DIR = os.path.join(ROOT_DIR, 'logs')
    SCREENSHOTS_DIR = os.path.join(ROOT_DIR, 'screenshots')
    DATA_DIR = os.path.join(ROOT_DIR, 'test_data')

    # Browser configurations
    BROWSER_CONFIGS = {
        'chrome': {
            'arguments': [
                '--start-maximized',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--disable-extensions'
            ],
            'experimental_options': {
                'excludeSwitches': ['enable-automation', 'enable-logging'],
                'prefs': {
                    'download.default_directory': os.path.join(ROOT_DIR, 'downloads'),
                    'download.prompt_for_download': False,
                    'download.directory_upgrade': True,
                    'safebrowsing.enabled': True
                }
            }
        },
        'firefox': {
            'arguments': ['-private'],
            'preferences': {
                'browser.download.folderList': 2,
                'browser.download.manager.showWhenStarting': False,
                'browser.download.dir': os.path.join(ROOT_DIR, 'downloads'),
                'browser.helperApps.neverAsk.saveToDisk': 'application/pdf,application/x-pdf'
            }
        },
        'edge': {
            'arguments': ['--start-maximized']
        }
    }

    # Test data
    TEST_DATA = {
        'users': {
            'admin': {
                'username': os.getenv('ADMIN_USER', 'admin'),
                'password': os.getenv('ADMIN_PASS', 'admin123')
            },
            'standard': {
                'username': os.getenv('STD_USER', 'user'),
                'password': os.getenv('STD_PASS', 'pass123')
            }
        }
    }

    # Reporting configuration
    REPORT_CONFIG = {
        'screenshot_on_failure': True,
        'html_report': True,
        'excel_report': True,
        'pdf_report': True,
        'junit_report': True
    }

    # Logging configuration
    LOG_CONFIG = {
        'file_logging': True,
        'console_logging': True,
        'log_level': 'DEBUG',
        'retention_days': 30,
        'external_logging': {
            'elasticsearch': {
                'enabled': False,
                'host': 'localhost',
                'port': 9200,
                'index': 'test_logs'
            },
            'splunk': {
                'enabled': False,
                'host': 'splunk.example.com',
                'port': 8089,
                'index': 'test_logs'
            }
        }
    }

    @classmethod
    def get_browser_options(cls) -> Dict[str, Any]:
        """Ottiene le opzioni del browser corrente"""
        browser_config = cls.BROWSER_CONFIGS.get(cls.BROWSER, {})
        if cls.HEADLESS:
            browser_config['arguments'] = browser_config.get('arguments', [])
            browser_config['arguments'].append('--headless')
        return browser_config

    @classmethod
    def get_base_url(cls) -> str:
        """Ottiene l'URL base per l'ambiente corrente"""
        return cls.URLS.get(cls.ENV, cls.URLS['qa'])

    @classmethod
    def load_test_data(cls, filename: str) -> Dict[str, Any]:
        """
        Carica dati di test da file JSON o YAML
        Args:
            filename: Nome del file da caricare
        Returns:
            Dati caricati dal file
        """
        file_path = os.path.join(cls.DATA_DIR, filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File non trovato: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if filename.endswith('.json'):
                    return json.load(f)
                elif filename.endswith('.yaml') or filename.endswith('.yml'):
                    return yaml.safe_load(f)
                else:
                    raise ValueError("Formato file non supportato")
        except Exception as e:
            raise Exception(f"Errore nel caricamento del file {filename}: {str(e)}")

    @classmethod
    def save_test_data(cls, data: Dict[str, Any], filename: str) -> None:
        """
        Salva dati di test su file
        Args:
            data: Dati da salvare
            filename: Nome del file
        """
        file_path = os.path.join(cls.DATA_DIR, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                if filename.endswith('.json'):
                    json.dump(data, f, indent=2)
                elif filename.endswith('.yaml') or filename.endswith('.yml'):
                    yaml.dump(data, f, default_flow_style=False)
                else:
                    raise ValueError("Formato file non supportato")
        except Exception as e:
            raise Exception(f"Errore nel salvataggio del file {filename}: {str(e)}")

    @classmethod
    def get_screenshot_path(cls, name: str) -> str:
        """
        Genera il path per uno screenshot
        Args:
            name: Nome dello screenshot
        Returns:
            Path completo del file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{name}_{timestamp}.png"
        path = os.path.join(cls.SCREENSHOTS_DIR, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    @classmethod
    def get_report_path(cls, name: str, extension: str) -> str:
        """
        Genera il path per un report
        Args:
            name: Nome del report
            extension: Estensione del file
        Returns:
            Path completo del file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{name}_{timestamp}.{extension}"
        path = os.path.join(cls.REPORTS_DIR, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    @classmethod
    def setup_directories(cls) -> None:
        """Crea tutte le directory necessarie"""
        directories = [
            cls.REPORTS_DIR,
            cls.LOGS_DIR,
            cls.SCREENSHOTS_DIR,
            cls.DATA_DIR,
            os.path.join(cls.ROOT_DIR, 'downloads')
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

    @classmethod
    def get_environment_config(cls) -> Dict[str, Any]:
        """
        Ottiene la configurazione completa dell'ambiente corrente
        Returns:
            Dictionary con tutte le configurazioni
        """
        return {
            'environment': cls.ENV,
            'browser': cls.BROWSER,
            'headless': cls.HEADLESS,
            'base_url': cls.get_base_url(),
            'timeouts': {
                'implicit': cls.IMPLICIT_WAIT,
                'explicit': cls.EXPLICIT_WAIT,
                'page_load': cls.PAGE_LOAD_TIMEOUT
            },
            'browser_config': cls.get_browser_options()
        }

    @classmethod
    def save_environment_config(cls) -> None:
        """Salva la configurazione dell'ambiente corrente"""
        config = cls.get_environment_config()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"env_config_{timestamp}.json"

        path = os.path.join(cls.REPORTS_DIR, 'configs', filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, 'w') as f:
            json.dump(config, f, indent=2)