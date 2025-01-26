import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui.main_window import MainWindow
import os
from datetime import datetime


def setup_logging():
    """Configura il sistema di logging"""
    # Crea la directory per i log se non esiste
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Nome del file di log con timestamp
    log_filename = f'logs/app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

    # Configurazione del logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename),
            logging.StreamHandler()
        ]
    )

    return logging.getLogger(__name__)


def check_dependencies():
    """Verifica che tutte le dipendenze necessarie siano installate"""
    required_packages = [
        'PyQt5',
        'spacy',
        'transformers',
        'torch',
        'sqlite3'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("Mancano le seguenti dipendenze:")
        for package in missing_packages:
            print(f"- {package}")
        print("\nInstallale usando:")
        print(f"pip install {' '.join(missing_packages)}")
        return False

    return True


def check_resources():
    """Verifica che tutte le risorse necessarie siano presenti"""
    required_directories = ['resources', 'logs', 'database']
    required_files = [
        'resources/icons/send.png',
        'resources/icons/save.png',
        'resources/icons/load.png',
        'resources/icons/clear.png'
    ]

    # Crea le directory mancanti
    for directory in required_directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.info(f"Creata directory: {directory}")

    # Verifica i file necessari
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        logging.warning("File mancanti:")
        for file in missing_files:
            logging.warning(f"- {file}")
        return False

    return True


def setup_environment():
    """Configura l'ambiente dell'applicazione"""
    # Imposta il percorso delle risorse
    os.environ['RESOURCE_PATH'] = os.path.join(os.path.dirname(__file__), 'resources')

    # Imposta il percorso del database
    os.environ['DATABASE_PATH'] = os.path.join(os.path.dirname(__file__), 'database')

    # Altre configurazioni ambientali se necessarie
    os.environ['PYTHONIOENCODING'] = 'utf-8'


def main():
    """Funzione principale dell'applicazione"""
    # Configura il logging
    logger = setup_logging()
    logger.info("Avvio dell'applicazione...")

    try:
        # Verifica le dipendenze
        if not check_dependencies():
            logger.error("Dipendenze mancanti. Installale prima di continuare.")
            sys.exit(1)

        # Verifica le risorse
        if not check_resources():
            logger.warning("Alcune risorse sono mancanti. L'applicazione potrebbe non funzionare correttamente.")

        # Configura l'ambiente
        setup_environment()

        # Crea l'applicazione Qt
        app = QApplication(sys.argv)

        # Imposta lo stile dell'applicazione
        app.setStyle('Fusion')

        # Carica il foglio di stile
        try:
            with open('ui/styles.qss', 'r') as f:
                app.setStyleSheet(f.read())
        except Exception as e:
            logger.warning(f"Impossibile caricare il foglio di stile: {e}")

        # Crea e mostra la finestra principale
        window = MainWindow()
        window.show()

        # Avvia il loop degli eventi
        sys.exit(app.exec_())

    except Exception as e:
        logger.error(f"Errore fatale nell'avvio dell'applicazione: {e}")
        sys.exit(1)
    finally:
        logger.info("Applicazione terminata")


if __name__ == '__main__':
    main()