""""
Chatbot Query Generator
======================

Un chatbot intelligente per la generazione di query SQL
attraverso il processamento del linguaggio naturale.
"""

__version__ = "1.0.0"
__author__ = "Serge Guea"
__license__ = "MIT"

import logging
import json
import yaml
from pathlib import Path
from typing import Dict, Optional, Any, List
import sys
import os
from datetime import datetime, timedelta
import signal

# Configurazione base del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Percorsi importanti dell'applicazione
APP_DIR = Path(__file__).parent
ROOT_DIR = APP_DIR.parent
RESOURCES_DIR = ROOT_DIR / 'resources'
UI_DIR = ROOT_DIR / 'ui'
CONFIG_DIR = ROOT_DIR / 'config'
LOGS_DIR = ROOT_DIR / 'logs'
CACHE_DIR = ROOT_DIR / 'cache'
TEMP_DIR = ROOT_DIR / 'temp'

# Importazione delle classi principali
from .nlp import NLPProcessor
from .query_generator import QueryGenerator
from .database import DatabaseManager
from .error_correction import ErrorCorrector
from .grammar_analysis import GrammarAnalyzer
from .message_generator import MessageGenerator
from .math_solver import MathSolver
from .file_analyzer import FileAnalyzer

# Configurazioni predefinite estese
DEFAULT_CONFIG = {
    'database': {
        'path': 'database.db',
        'timeout': 30,
        'check_same_thread': False,
        'backup_interval': 3600,  # secondi
        'max_connections': 5
    },
    'nlp': {
        'model': 'it_core_news_sm',
        'batch_size': 1000,
        'cache_size': 1000,
        'timeout': 30
    },
    'ui': {
        'theme': 'light',
        'font_size': 12,
        'window_size': (800, 600),
        'auto_save': True,
        'language': 'it'
    },
    'security': {
        'enable_encryption': True,
        'key_file': 'security.key',
        'ssl_verify': True,
        'max_attempts': 3
    },
    'performance': {
        'cache_size': 1024,  # MB
        'max_threads': 4,
        'timeout': 30,
        'batch_size': 100
    },
    'logging': {
        'level': 'INFO',
        'file': 'app.log',
        'max_size': 10485760,  # 10MB
        'backup_count': 5
    }
}

class ConfigManager:
    """Gestore delle configurazioni dell'applicazione"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or str(CONFIG_DIR / 'config.yaml')
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Carica la configurazione da file"""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                return self._merge_configs(DEFAULT_CONFIG, config)
            return DEFAULT_CONFIG.copy()
        except Exception as e:
            logging.error(f"Errore nel caricamento della configurazione: {e}")
            return DEFAULT_CONFIG.copy()

    def _merge_configs(self, default: Dict, custom: Dict) -> Dict:
        """Unisce le configurazioni personalizzate con quelle predefinite"""
        result = default.copy()
        for key, value in custom.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def save_config(self) -> None:
        """Salva la configurazione su file"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f)
        except Exception as e:
            logging.error(f"Errore nel salvataggio della configurazione: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Ottiene un valore di configurazione"""
        try:
            keys = key.split('.')
            value = self.config
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """Imposta un valore di configurazione"""
        try:
            keys = key.split('.')
            config = self.config
            for k in keys[:-1]:
                config = config.setdefault(k, {})
            config[keys[-1]] = value
            self.save_config()
        except Exception as e:
            logging.error(f"Errore nell'impostazione della configurazione: {e}")

class ResourceManager:
    """Gestore delle risorse dell'applicazione"""

    def __init__(self):
        self.directories = {
            'resources': RESOURCES_DIR,
            'ui': UI_DIR,
            'config': CONFIG_DIR,
            'logs': LOGS_DIR,
            'cache': CACHE_DIR,
            'temp': TEMP_DIR
        }
        self._initialize_directories()

    def _initialize_directories(self) -> None:
        """Inizializza le directory necessarie"""
        for directory in self.directories.values():
            directory.mkdir(parents=True, exist_ok=True)

    def get_path(self, resource_type: str, filename: str) -> Path:
        """Ottiene il percorso completo di una risorsa"""
        if resource_type not in self.directories:
            raise ValueError(f"Tipo di risorsa non valido: {resource_type}")
        return self.directories[resource_type] / filename

    def ensure_resource(self, resource_type: str, filename: str) -> Path:
        """Assicura l'esistenza di una risorsa"""
        path = self.get_path(resource_type, filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def list_resources(self, resource_type: str) -> List[str]:
        """Lista tutte le risorse di un tipo specifico"""
        if resource_type not in self.directories:
            raise ValueError(f"Tipo di risorsa non valido: {resource_type}")
        directory = self.directories[resource_type]
        return [f.name for f in directory.iterdir() if f.is_file()]

class CacheManager:
    """Gestore della cache dell'applicazione"""

    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get(self, key: str) -> Optional[Any]:
        """Recupera un valore dalla cache"""
        try:
            cache_file = self.cache_dir / f"{key}.cache"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                if datetime.fromisoformat(data['expires']) > datetime.now():
                    return data['value']
            return None
        except Exception as e:
            logging.error(f"Errore nel recupero dalla cache: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Imposta un valore nella cache"""
        try:
            cache_file = self.cache_dir / f"{key}.cache"
            data = {
                'value': value,
                'expires': (datetime.now().replace(microsecond=0) +
                          timedelta(seconds=ttl)).isoformat()
            }
            with open(cache_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logging.error(f"Errore nell'impostazione della cache: {e}")

    def clear(self) -> None:
        """Pulisce la cache"""
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
        except Exception as e:
            logging.error(f"Errore nella pulizia della cache: {e}")

def initialize_app(config: Optional[Dict] = None) -> Dict:
    """Inizializza l'applicazione con le configurazioni specificate"""
    logger = logging.getLogger(__name__)
    logger.info("Inizializzazione dell'applicazione...")

    try:
        # Inizializza il gestore delle configurazioni
        config_manager = ConfigManager()
        if config:
            for key, value in config.items():
                config_manager.set(key, value)

        # Inizializza il gestore delle risorse
        resource_manager = ResourceManager()

        # Inizializza il gestore della cache
        cache_manager = CacheManager()

        # Configura il logging avanzato
        setup_logging(config_manager.get('logging'))

        # Registra gli handler per la terminazione graceful
        setup_signal_handlers()

        logger.info("Applicazione inizializzata con successo")
        return config_manager.config

    except Exception as e:
        logger.error(f"Errore durante l'inizializzazione: {str(e)}")
        raise

def setup_logging(config: Dict) -> None:
    """Configura il sistema di logging"""
    logging.basicConfig(
        level=getattr(logging, config['level']),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config['file']),
            logging.StreamHandler(sys.stdout)
        ]
    )

def setup_signal_handlers() -> None:
    """Configura gli handler per i segnali di sistema"""
    def signal_handler(signum, frame):
        logging.info(f"Ricevuto segnale {signum}. Terminazione in corso...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

class AppContext:
    """Classe di contesto per gestire le risorse dell'applicazione"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = initialize_app(config)
        self.config_manager = ConfigManager()
        self.resource_manager = ResourceManager()
        self.cache_manager = CacheManager()

        # Inizializza i componenti principali
        self.nlp = NLPProcessor()
        self.query_generator = QueryGenerator()
        self.db_manager = DatabaseManager(self.config['database']['path'])
        self.error_corrector = ErrorCorrector()
        self.grammar_analyzer = GrammarAnalyzer()
        self.message_generator = MessageGenerator()
        self.math_solver = MathSolver()
        self.file_analyzer = FileAnalyzer()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def cleanup(self) -> None:
        """Pulisce e chiude tutte le risorse"""
        try:
            # Chiudi la connessione al database
            if hasattr(self, 'db_manager'):
                self.db_manager.close()

            # Pulisci la cache temporanea
            if hasattr(self, 'cache_manager'):
                self.cache_manager.clear()

            # Salva le configurazioni
            if hasattr(self, 'config_manager'):
                self.config_manager.save_config()

            logging.info("Pulizia delle risorse completata con successo")
        except Exception as e:
            logging.error(f"Errore durante la pulizia delle risorse: {str(e)}")

    def reload_config(self) -> None:
        """Ricarica le configurazioni"""
        self.config = self.config_manager._load_config()

    def get_resource_path(self, resource_type: str, filename: str) -> Path:
        """Ottiene il percorso di una risorsa"""
        return self.resource_manager.get_path(resource_type, filename)

if __name__ == "__main__":
    try:
        with AppContext() as app:
            # Esempio di utilizzo
            logging.info("Applicazione avviata con successo")

            # Test delle funzionalità
            app.config_manager.set('ui.theme', 'dark')
            app.cache_manager.set('test_key', 'test_value')

            # Lista delle risorse disponibili
            resources = app.resource_manager.list_resources('resources')
            logging.info(f"Risorse disponibili: {resources}")

    except Exception as e:
        logging.error(f"Errore durante l'esecuzione: {str(e)}")
        sys.exit(1)