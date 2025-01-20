"""
Chatbot Query Generator
======================

Un chatbot intelligente per la generazione di query SQL
attraverso il processamento del linguaggio naturale.
"""

__version__ = "1.0.0"
__author__ = "Serge Guea"
__license__ = "MIT"

import logging
from pathlib import Path

# Configurazione base del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Percorsi importanti dell'applicazione
APP_DIR = Path(__file__).parent
ROOT_DIR = APP_DIR.parent
RESOURCES_DIR = ROOT_DIR / 'resources'
UI_DIR = ROOT_DIR / 'ui'

# Verifica dell'esistenza delle cartelle necessarie
for directory in [RESOURCES_DIR, UI_DIR]:
    directory.mkdir(exist_ok=True)

# Importazione delle classi principali
from .nlp import NLPProcessor
from .query_generator import QueryGenerator
from .database import DatabaseManager
from .error_correction import ErrorCorrector
from .grammar_analysis import GrammarAnalyzer
from .message_generator import MessageGenerator
from .math_solver import MathSolver
from .file_analyzer import FileAnalyzer

# Dizionario delle configurazioni predefinite
DEFAULT_CONFIG = {
    'database': {
        'path': 'database.db',
        'timeout': 30,
        'check_same_thread': False
    },
    'nlp': {
        'model': 'it_core_news_sm',
        'batch_size': 1000
    },
    'ui': {
        'theme': 'light',
        'font_size': 12,
        'window_size': (800, 600)
    }
}


def initialize_app(config=None):
    """
    Inizializza l'applicazione con le configurazioni specificate

    Args:
        config (dict, optional): Configurazioni personalizzate.
                               Se None, usa le configurazioni predefinite.

    Returns:
        dict: Le configurazioni utilizzate per l'inizializzazione
    """
    if config is None:
        config = DEFAULT_CONFIG
    else:
        # Unisce le configurazioni personalizzate con quelle predefinite
        for key, default_value in DEFAULT_CONFIG.items():
            if key not in config:
                config[key] = default_value
            elif isinstance(default_value, dict):
                for sub_key, sub_value in default_value.items():
                    if sub_key not in config[key]:
                        config[key][sub_key] = sub_value

    # Inizializza il logger
    logger = logging.getLogger(__name__)
    logger.info("Inizializzazione dell'applicazione...")

    try:
        # Verifica e crea le directory necessarie
        for directory in [RESOURCES_DIR, UI_DIR]:
            if not directory.exists():
                directory.mkdir(parents=True)
                logger.info(f"Creata directory: {directory}")

        # Qui puoi aggiungere altre inizializzazioni necessarie
        logger.info("Applicazione inizializzata con successo")
        return config

    except Exception as e:
        logger.error(f"Errore durante l'inizializzazione: {str(e)}")
        raise


class AppContext:
    """
    Classe di contesto per gestire le risorse dell'applicazione
    """

    def __init__(self, config=None):
        self.config = initialize_app(config)
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
        # Chiudi tutte le risorse
        if hasattr(self, 'db_manager'):
            self.db_manager.close()