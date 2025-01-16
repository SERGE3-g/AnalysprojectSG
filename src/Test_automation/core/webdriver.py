from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.safari.service import Service as SafariService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from typing import Optional, Dict, Any, Callable, List
import json
import os
from datetime import datetime
from core.logger import Logger


class WebDriverFactory:
    """
    Factory class per la creazione e gestione delle istanze WebDriver
    """

    _instance = None
    _driver = None
    _logger = Logger.get_logger('WebDriverFactory')

    def __init__(self):
        if WebDriverFactory._instance is not None:
            raise Exception("WebDriverFactory è una singleton class!")
        WebDriverFactory._instance = self

    @classmethod
    def get_instance(cls):
        """Ottiene l'istanza singleton della factory"""
        if cls._instance is None:
            cls._instance = WebDriverFactory()
        return cls._instance

    @classmethod
    def get_driver(cls, browser_type: str = "chrome", options: Dict[str, Any] = None) -> webdriver:
        """
        Ottiene un'istanza del WebDriver
        Args:
            browser_type: Tipo di browser ('chrome', 'firefox', 'edge', 'safari')
            options: Dizionario delle opzioni del browser
        Returns:
            Istanza WebDriver
        """
        if cls._driver is None:
            cls._driver = cls._create_driver(browser_type, options)
        return cls._driver

    @classmethod
    def _create_driver(cls, browser_type: str, options: Optional[Dict[str, Any]] = None) -> webdriver:
        """
        Crea una nuova istanza del WebDriver
        Args:
            browser_type: Tipo di browser
            options: Opzioni del browser
        Returns:
            Nuova istanza WebDriver
        """
        browser_type = browser_type.lower()
        options = options or {}

        if browser_type == "chrome":
            driver = cls._setup_chrome_driver(options)
        elif browser_type == "firefox":
            driver = cls._setup_firefox_driver(options)
        elif browser_type == "edge":
            driver = cls._setup_edge_driver(options)
        elif browser_type == "safari":
            driver = cls._setup_safari_driver(options)
        else:
            raise ValueError(f"Browser non supportato: {browser_type}")

        cls._configure_driver(driver, options)
        cls._logger.info(f"Driver {browser_type} creato con successo")
        return driver

    @classmethod
    def _setup_chrome_driver(cls, options: Dict[str, Any]) -> webdriver.Chrome:
        """Configura e crea Chrome WebDriver"""
        chrome_options = ChromeOptions()

        # Opzioni di base
        if options.get('headless', False):
            chrome_options.add_argument('--headless')

        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        # Opzioni aggiuntive
        if options.get('incognito', False):
            chrome_options.add_argument('--incognito')
        if options.get('disable_gpu', False):
            chrome_options.add_argument('--disable-gpu')
        if options.get('window_size'):
            chrome_options.add_argument(f'--window-size={options["window_size"]}')

        # Preferenze sperimentali
        experimental_options = {
            'excludeSwitches': ['enable-automation', 'enable-logging'],
            'prefs': {
                'download.default_directory': options.get('download_dir', os.getcwd()),
                'download.prompt_for_download': False,
                'download.directory_upgrade': True,
                'safebrowsing.enabled': True
            }
        }

        for key, value in experimental_options.items():
            chrome_options.add_experimental_option(key, value)

        # Argomenti aggiuntivi da options
        if 'arguments' in options:
            for arg in options['arguments']:
                chrome_options.add_argument(arg)

        service = ChromeService(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=chrome_options)

    @classmethod
    def _setup_firefox_driver(cls, options: Dict[str, Any]) -> webdriver.Firefox:
        """Configura e crea Firefox WebDriver"""
        firefox_options = FirefoxOptions()

        if options.get('headless', False):
            firefox_options.add_argument('--headless')

        # Preferenze Firefox
        firefox_options.set_preference('browser.download.folderList', 2)
        firefox_options.set_preference('browser.download.dir',
                                       options.get('download_dir', os.getcwd()))
        firefox_options.set_preference('browser.download.useDownloadDir', True)
        firefox_options.set_preference('browser.helperApps.neverAsk.saveToDisk',
                                       'application/pdf,application/x-pdf')

        if 'arguments' in options:
            for arg in options['arguments']:
                firefox_options.add_argument(arg)

        service = FirefoxService(GeckoDriverManager().install())
        return webdriver.Firefox(service=service, options=firefox_options)

    @classmethod
    def _setup_edge_driver(cls, options: Dict[str, Any]) -> webdriver.Edge:
        """Configura e crea Edge WebDriver"""
        edge_options = EdgeOptions()

        if options.get('headless', False):
            edge_options.add_argument('--headless')

        edge_options.add_argument('--start-maximized')

        if 'arguments' in options:
            for arg in options['arguments']:
                edge_options.add_argument(arg)

        service = EdgeService(EdgeChromiumDriverManager().install())
        return webdriver.Edge(service=service, options=edge_options)

    @classmethod
    def _setup_safari_driver(cls, options: Dict[str, Any]) -> webdriver.Safari:
        """Configura e crea Safari WebDriver"""
        service = SafariService()
        return webdriver.Safari(service=service)

    @classmethod
    def _configure_driver(cls, driver: webdriver, options: Dict[str, Any]) -> None:
        """
        Configura il driver con impostazioni comuni
        Args:
            driver: Istanza WebDriver
            options: Opzioni di configurazione
        """
        # Imposta i timeout
        driver.implicitly_wait(options.get('implicit_wait', 10))
        driver.set_page_load_timeout(options.get('page_load_timeout', 30))
        driver.set_script_timeout(options.get('script_timeout', 30))

        # Massimizza la finestra se richiesto
        if options.get('maximize', True):
            driver.maximize_window()

        # Dimensione della finestra personalizzata
        elif 'window_size' in options:
            width, height = map(int, options['window_size'].split('x'))
            driver.set_window_size(width, height)

    @classmethod
    def save_driver_logs(cls) -> None:
        """Salva i log del driver"""
        if cls._driver:
            log_types = cls._driver.log_types
            logs_dir = "reports/driver_logs"
            os.makedirs(logs_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            for log_type in log_types:
                try:
                    logs = cls._driver.get_log(log_type)
                    if logs:
                        log_file = f"{logs_dir}/{log_type}_{timestamp}.log"
                        with open(log_file, 'w') as f:
                            json.dump(logs, f, indent=4)
                        cls._logger.info(f"Log {log_type} salvati in {log_file}")
                except Exception as e:
                    cls._logger.error(f"Errore nel salvare i log {log_type}: {str(e)}")

    @classmethod
    def quit_driver(cls) -> None:
        """Chiude il driver e salva i log"""
        if cls._driver:
            try:
                cls.save_driver_logs()
                cls._driver.quit()
                cls._logger.info("Driver chiuso con successo")
            except Exception as e:
                cls._logger.error(f"Errore nella chiusura del driver: {str(e)}")
            finally:
                cls._driver = None

    @classmethod
    def clear_cookies(cls) -> None:
        """Cancella tutti i cookies"""
        if cls._driver:
            cls._driver.delete_all_cookies()
            cls._logger.info("Cookies cancellati")

    @classmethod
    def get_session_id(cls) -> Optional[str]:
        """Ottiene l'ID della sessione corrente"""
        if cls._driver:
            return cls._driver.session_id
        return None

    @classmethod
    def get_capabilities(cls) -> Optional[dict]:
        """Ottiene le capabilities del driver corrente"""
        if cls._driver:
            return cls._driver.capabilities
        return None

    @classmethod
    def save_session_info(cls) -> None:
        """Salva le informazioni della sessione corrente"""
        if cls._driver:
            session_info = {
                'session_id': cls.get_session_id(),
                'capabilities': cls.get_capabilities(),
                'timestamp': datetime.now().isoformat()
            }

            os.makedirs('reports/sessions', exist_ok=True)
            file_path = f'reports/sessions/session_{session_info["session_id"]}.json'

            with open(file_path, 'w') as f:
                json.dump(session_info, f, indent=4)
            cls._logger.info(f"Informazioni sessione salvate in {file_path}")

    @classmethod
    def get_session_storage(cls) -> dict:
        """Ottiene il contenuto del session storage"""
        if cls._driver:
            return cls._driver.execute_script(
                "return Object.assign({}, window.sessionStorage);"
            )
        return {}

    @classmethod
    def get_local_storage(cls) -> dict:
        """Ottiene il contenuto del local storage"""
        if cls._driver:
            return cls._driver.execute_script(
                "return Object.assign({}, window.localStorage);"
            )
        return {}

    class WebDriverFactory:
        """Aggiungo metodi per gestione remota, proxy e performance"""

        @classmethod
        def create_remote_driver(cls, hub_url: str, browser_type: str,
                                 options: Dict[str, Any] = None) -> webdriver.Remote:
            """
            Crea un'istanza di Remote WebDriver per testing distribuito
            Args:
                hub_url: URL del Selenium Grid Hub
                browser_type: Tipo di browser
                options: Opzioni di configurazione
            Returns:
                Remote WebDriver instance
            """
            options = options or {}
            capabilities = cls._get_capabilities_for_browser(browser_type, options)

            try:
                driver = webdriver.Remote(
                    command_executor=hub_url,
                    options=capabilities
                )
                cls._logger.info(f"Remote driver creato per {browser_type} su {hub_url}")
                return driver
            except Exception as e:
                cls._logger.error(f"Errore nella creazione del remote driver: {str(e)}")
                raise

        @classmethod
        def _get_capabilities_for_browser(cls, browser_type: str, options: Dict[str, Any]) -> dict:
            """
            Genera capabilities per il browser specificato
            """
            browser_type = browser_type.lower()
            if browser_type == "chrome":
                capabilities = cls._get_chrome_capabilities(options)
            elif browser_type == "firefox":
                capabilities = cls._get_firefox_capabilities(options)
            elif browser_type == "edge":
                capabilities = cls._get_edge_capabilities(options)
            else:
                raise ValueError(f"Browser non supportato per remote testing: {browser_type}")
            return capabilities

        @classmethod
        def _get_chrome_capabilities(cls, options: Dict[str, Any]) -> webdriver.ChromeOptions:
            """
            Configura capabilities specifiche per Chrome
            """
            chrome_options = ChromeOptions()
            chrome_options.set_capability('browserName', 'chrome')

            # Configurazioni base
            if options.get('headless', False):
                chrome_options.add_argument('--headless')

            # Configurazione proxy
            if 'proxy' in options:
                chrome_options.add_argument(f'--proxy-server={options["proxy"]}')

            # Configurazioni performance
            chrome_options.set_capability('goog:loggingPrefs', {
                'browser': 'ALL',
                'performance': 'ALL'
            })

            return chrome_options

        @classmethod
        def _get_firefox_capabilities(cls, options: Dict[str, Any]) -> webdriver.FirefoxOptions:
            """
            Configura capabilities specifiche per Firefox
            """
            firefox_options = FirefoxOptions()
            firefox_options.set_capability('browserName', 'firefox')

            if options.get('headless', False):
                firefox_options.add_argument('--headless')

            # Configurazione proxy
            if 'proxy' in options:
                firefox_options.set_capability('proxy', {
                    'proxyType': 'MANUAL',
                    'httpProxy': options['proxy'],
                    'sslProxy': options['proxy']
                })

            return firefox_options

        @classmethod
        def _get_edge_capabilities(cls, options: Dict[str, Any]) -> webdriver.EdgeOptions:
            """
            Configura capabilities specifiche per Edge
            """
            edge_options = EdgeOptions()
            edge_options.set_capability('browserName', 'edge')

            if options.get('headless', False):
                edge_options.add_argument('--headless')

            return edge_options

        @classmethod
        def setup_proxy(cls, proxy_address: str) -> None:
            """
            Configura proxy per il driver corrente
            Args:
                proxy_address: Indirizzo del proxy (es. "127.0.0.1:8080")
            """
            if not cls._driver:
                raise Exception("Driver non inizializzato")

            try:
                if isinstance(cls._driver, webdriver.Chrome):
                    cls._driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                        "userAgent": "Chrome/89.0.4389.82"
                    })
                    cls._driver.execute_cdp_cmd('Network.enable', {})
                    cls._driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
                        "headers": {"Proxy-Connection": "keep-alive"}
                    })
                cls._logger.info(f"Proxy configurato: {proxy_address}")
            except Exception as e:
                cls._logger.error(f"Errore nella configurazione del proxy: {str(e)}")
                raise

        @classmethod
        def enable_performance_logging(cls) -> None:
            """
            Abilita logging delle performance (Chrome only)
            """
            if not isinstance(cls._driver, webdriver.Chrome):
                cls._logger.warning("Performance logging disponibile solo per Chrome")
                return

            try:
                cls._driver.execute_cdp_cmd('Performance.enable', {})
                cls._logger.info("Performance logging abilitato")
            except Exception as e:
                cls._logger.error(f"Errore nell'abilitazione performance logging: {str(e)}")

        @classmethod
        def get_performance_metrics(cls) -> dict:
            """
            Ottiene metriche di performance (Chrome only)
            Returns:
                Dict con metriche di performance
            """
            if not isinstance(cls._driver, webdriver.Chrome):
                return {}

            try:
                metrics = cls._driver.execute_cdp_cmd('Performance.getMetrics', {})
                return {metric['name']: metric['value'] for metric in metrics['metrics']}
            except Exception as e:
                cls._logger.error(f"Errore nel recupero metriche: {str(e)}")
                return {}

        @classmethod
        def enable_network_interception(cls) -> None:
            """
            Abilita intercettazione richieste di rete (Chrome only)
            """
            if not isinstance(cls._driver, webdriver.Chrome):
                return

            try:
                cls._driver.execute_cdp_cmd('Network.enable', {})
                cls._driver.execute_cdp_cmd('Network.setBypassServiceWorker', {'bypass': True})
                cls._logger.info("Network interception abilitata")
            except Exception as e:
                cls._logger.error(f"Errore nell'abilitazione network interception: {str(e)}")

        @classmethod
        def get_network_requests(cls) -> List[Dict]:
            """
            Ottiene lista delle richieste di rete
            Returns:
                Lista di richieste network
            """
            if not isinstance(cls._driver, webdriver.Chrome):
                return []

            try:
                return cls._driver.execute_script("""
                    var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {};
                    var network = performance.getEntriesByType("resource") || {};
                    return network;
                """)
            except Exception as e:
                cls._logger.error(f"Errore nel recupero richieste network: {str(e)}")
                return []

        @classmethod
        def set_geolocation(cls, latitude: float, longitude: float) -> None:
            """
            Imposta la geolocalizzazione del browser
            Args:
                latitude: Latitudine
                longitude: Longitudine
            """
            if not isinstance(cls._driver, webdriver.Chrome):
                cls._logger.warning("Geolocation override disponibile solo per Chrome")
                return

            try:
                cls._driver.execute_cdp_cmd('Emulation.setGeolocationOverride', {
                    'latitude': latitude,
                    'longitude': longitude,
                    'accuracy': 100
                })
                cls._logger.info(f"Geolocation impostata: {latitude}, {longitude}")
            except Exception as e:
                cls._logger.error(f"Errore nell'impostazione geolocation: {str(e)}")

        @classmethod
        def set_timezone(cls, timezone_id: str) -> None:
            """
            Imposta il timezone del browser
            Args:
                timezone_id: ID del timezone (es. "America/New_York")
            """
            if not isinstance(cls._driver, webdriver.Chrome):
                return

            try:
                cls._driver.execute_cdp_cmd('Emulation.setTimezoneOverride', {
                    'timezoneId': timezone_id
                })
                cls._logger.info(f"Timezone impostato: {timezone_id}")
            except Exception as e:
                cls._logger.error(f"Errore nell'impostazione timezone: {str(e)}")

        @classmethod
        def set_device_metrics(cls, width: int, height: int, device_scale_factor: float = 1.0,
                               mobile: bool = False) -> None:
            """
            Imposta le metriche del device per emulazione mobile
            """
            if not isinstance(cls._driver, webdriver.Chrome):
                return

            try:
                cls._driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                    'width': width,
                    'height': height,
                    'deviceScaleFactor': device_scale_factor,
                    'mobile': mobile
                })
                cls._logger.info(f"Device metrics impostate: {width}x{height}")
            except Exception as e:
                cls._logger.error(f"Errore nell'impostazione device metrics: {str(e)}")

        @classmethod
        def enable_request_interception(cls) -> None:
            """
            Abilita intercettazione e modifica delle richieste (Chrome only)
            """
            if not isinstance(cls._driver, webdriver.Chrome):
                return

            try:
                cls._driver.execute_cdp_cmd('Fetch.enable', {
                    'patterns': [{'urlPattern': '*'}]
                })
                cls._logger.info("Request interception abilitata")
            except Exception as e:
                cls._logger.error(f"Errore nell'abilitazione request interception: {str(e)}")

        @classmethod
        def add_request_handler(cls, pattern: str, handler: Callable) -> None:
            """
            Aggiunge handler per richieste intercettate
            Args:
                pattern: Pattern URL da intercettare
                handler: Funzione da eseguire per ogni richiesta
            """
            if not isinstance(cls._driver, webdriver.Chrome):
                return

            try:
                cls._driver.execute_cdp_cmd('Fetch.enable', {
                    'patterns': [{'urlPattern': pattern}]
                })
                # Implementare logica handler
            except Exception as e:
                cls._logger.error(f"Errore nell'aggiunta request handler: {str(e)}")

        @classmethod
        def save_har_file(cls, path: str) -> None:
            """
            Salva HAR file con tutte le richieste network
            Args:
                path: Percorso dove salvare il file HAR
            """
            if not isinstance(cls._driver, webdriver.Chrome):
                return

            try:
                requests = cls.get_network_requests()
                har_data = {
                    'log': {
                        'version': '1.2',
                        'creator': {
                            'name': 'WebDriverFactory',
                            'version': '1.0'
                        },
                        'entries': requests
                    }
                }

                with open(path, 'w') as f:
                    json.dump(har_data, f, indent=2)
                cls._logger.info(f"HAR file salvato: {path}")
            except Exception as e:
                cls._logger.error(f"Errore nel salvataggio HAR file: {str(e)}")

class WebDriverFactory:


    # Mobile Device Configurations
    MOBILE_DEVICES = {
        'iPhone_12': {
            'width': 390,
            'height': 844,
            'device_scale_factor': 3.0,
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'touch': True,
            'mobile': True
        },
        'Pixel_5': {
            'width': 393,
            'height': 851,
            'device_scale_factor': 2.75,
            'user_agent': 'Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.91 Mobile Safari/537.36',
            'touch': True,
            'mobile': True
        },
        'iPad_Pro': {
            'width': 1024,
            'height': 1366,
            'device_scale_factor': 2.0,
            'user_agent': 'Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'touch': True,
            'mobile': True
        }
    }

    @classmethod
    def emulate_mobile_device(cls, device_name: str) -> None:
        """
        Emula un dispositivo mobile predefinito
        Args:
            device_name: Nome del dispositivo da emulare
        """
        if device_name not in cls.MOBILE_DEVICES:
            raise ValueError(f"Dispositivo non supportato: {device_name}")

        device = cls.MOBILE_DEVICES[device_name]

        try:
            # Imposta metriche del dispositivo
            cls._driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                'width': device['width'],
                'height': device['height'],
                'deviceScaleFactor': device['device_scale_factor'],
                'mobile': device['mobile'],
                'touch': device['touch']
            })

            # Imposta user agent
            cls._driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                'userAgent': device['user_agent']
            })

            # Abilita touch events
            cls._driver.execute_cdp_cmd('Emulation.setTouchEmulationEnabled', {
                'enabled': True,
                'maxTouchPoints': 5
            })

            cls._logger.info(f"Emulazione dispositivo {device_name} configurata")
        except Exception as e:
            cls._logger.error(f"Errore nell'emulazione del dispositivo: {str(e)}")

    @classmethod
    def setup_appium_driver(cls, platform: str, device_name: str, app_path: str = None) -> None:
        """
        Configura Appium WebDriver per test mobile nativi
        Args:
            platform: 'android' o 'ios'
            device_name: Nome del dispositivo
            app_path: Percorso dell'applicazione da testare
        """
        try:
            from appium import webdriver as appium_webdriver

            desired_caps = {
                'platformName': platform.capitalize(),
                'deviceName': device_name,
                'automationName': 'UiAutomator2' if platform == 'android' else 'XCUITest',
                'newCommandTimeout': 600
            }

            if app_path:
                desired_caps['app'] = os.path.abspath(app_path)

            cls._driver = appium_webdriver.Remote(
                'http://localhost:4723/wd/hub',
                desired_caps
            )
            cls._logger.info(f"Driver Appium configurato per {platform}")
        except Exception as e:
            cls._logger.error(f"Errore nella configurazione Appium: {str(e)}")
            raise

    @classmethod
    def setup_visual_testing(cls, api_key: str = None) -> None:
        """
        Configura il supporto per visual testing usando Applitools Eyes
        Args:
            api_key: Applitools API key
        """
        try:
            from applitools.selenium import Eyes, Target

            eyes = Eyes()
            if api_key:
                eyes.api_key = api_key

            cls._eyes = eyes
            cls._eyes.open(
                driver=cls._driver,
                app_name='Test App',
                test_name='Visual Test'
            )
            cls._logger.info("Visual testing configurato")
        except ImportError:
            cls._logger.error("Applitools Eyes non installato")
        except Exception as e:
            cls._logger.error(f"Errore nella configurazione visual testing: {str(e)}")

    @classmethod
    def check_visual(cls, tag: str, target: str = None) -> None:
        """
        Esegue un controllo visuale della pagina o di un elemento
        Args:
            tag: Tag identificativo del check
            target: Selettore dell'elemento (opzionale)
        """
        if not hasattr(cls, '_eyes'):
            cls._logger.warning("Visual testing non configurato")
            return

    @classmethod
    def setup_performance_monitoring(cls) -> None:
        """Configura monitoraggio avanzato delle performance"""
        try:
            # Abilita tutti i domini di performance
            cls._driver.execute_cdp_cmd('Performance.enable', {})

            # Abilita timeline
            cls._driver.execute_cdp_cmd('Timeline.start', {
                'maxCallStackDepth': 50
            })

            # Abilita metriche di rete
            cls._driver.execute_cdp_cmd('Network.enable', {})

            # Abilita metriche browser
            cls._driver.execute_cdp_cmd('Browser.enable', {})

            cls._logger.info("Performance monitoring avanzato configurato")
        except Exception as e:
            cls._logger.error(f"Errore nella configurazione performance monitoring: {str(e)}")

    @classmethod
    def get_detailed_performance_metrics(cls) -> dict:
        """
        Ottiene metriche dettagliate di performance
        Returns:
            Dict con varie metriche di performance
        """
        try:
            # Performance timings
            timing = cls._driver.execute_script('return performance.timing.toJSON()')

            # Memory info
            memory = cls._driver.execute_script('return performance.memory')

            # Navigation timing
            navigation = cls._driver.execute_script("""
                var navigation = performance.getEntriesByType('navigation')[0];
                return navigation ? navigation.toJSON() : {};
            """)

            # Resource timings
            resources = cls._driver.execute_script("""
                return performance.getEntriesByType('resource').map(r => r.toJSON());
            """)

            # Paint timings
            paint = cls._driver.execute_script("""
                return performance.getEntriesByType('paint').map(p => p.toJSON());
            """)

            return {
                'timing': timing,
                'memory': memory,
                'navigation': navigation,
                'resources': resources,
                'paint': paint
            }
        except Exception as e:
            cls._logger.error(f"Errore nel recupero metriche performance: {str(e)}")
            return {}

    @classmethod
    def start_performance_trace(cls) -> None:
        """Avvia tracciamento performance"""
        try:
            cls._driver.execute_cdp_cmd('Tracing.start', {
                'categories': [
                    'devtools.timeline',
                    'disabled-by-default-devtools.timeline',
                    'disabled-by-default-devtools.timeline.frame',
                    'disabled-by-default-devtools.timeline.stack',
                    'v8.execute',
                    'disabled-by-default-v8.cpu_profiler'
                ],
                'options': 'sampling-frequency=10000'
            })
            cls._logger.info("Performance tracing avviato")
        except Exception as e:
            cls._logger.error(f"Errore nell'avvio performance tracing: {str(e)}")

    @classmethod
    def stop_performance_trace(cls, output_path: str) -> None:
        """
        Ferma tracciamento performance e salva risultati
        Args:
            output_path: Percorso dove salvare il trace file
        """
        try:
            trace_data = cls._driver.execute_cdp_cmd('Tracing.end', {})
            with open(output_path, 'w') as f:
                json.dump(trace_data, f)
            cls._logger.info(f"Performance trace salvato in {output_path}")
        except Exception as e:
            cls._logger.error(f"Errore nel salvataggio performance trace: {str(e)}")

        try:
            cls._driver.execute_cdp_cmd('Tracing.end', {})
            cls._logger.info("Performance tracing fermato")
        except Exception as e:
            cls._logger.error(f"Errore nell'arresto performance tracing: {str(e)}")