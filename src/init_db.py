import sqlite3
import hashlib
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# === Creazione cartella per i log (UsersLog) ===
# Qui posizioniamo la cartella "UsersLog" allo stesso livello di init_db.py
LOG_DIR = Path(__file__).resolve().parent / 'UsersLog'
LOG_DIR.mkdir(exist_ok=True)  # Crea la cartella UsersLog se non esiste

# Configurazione del logging
LOG_FILE = LOG_DIR / 'database_init.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

try:
    # Ottieni il percorso della directory dove risiede init_db.py: (ad es. .../AnalysprojectSG/src)
    BASE_DIR = Path(__file__).resolve().parent

    # Puntiamo alla cartella data/ dentro src/
    DATA_DIR = BASE_DIR / 'data'
    DATA_DIR.mkdir(exist_ok=True)

    # Il nostro DB sarà .../src/data/users.db
    DB_FILE = DATA_DIR / 'users.db'

    logging.info(f"Directory base del progetto (src): {BASE_DIR}")
    logging.info(f"Directory data: {DATA_DIR}")
    logging.info(f"File database: {DB_FILE}")

except Exception as e:
    logging.error(f"Errore nella configurazione dei percorsi: {e}")
    sys.exit(1)


def initialize_database():
    """Inizializza il database con la struttura necessaria."""
    logging.info("Inizializzazione del database...")

    # Se vuoi sempre ricreare il database da zero, lo rimuoviamo se esiste
    if DB_FILE.exists():
        try:
            DB_FILE.unlink()
            logging.info("Database esistente eliminato (reinizializzazione forzata)")
        except Exception as e:
            logging.error(f"Errore nell'eliminazione del database esistente: {e}")
            return False

    # Connessione al database
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Creazione tabella users
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            reset_token TEXT,
            reset_token_expiry TIMESTAMP
        )
        ''')
        logging.info("Tabella 'users' creata (o già esistente).")

        # Creazione tabella access_logs
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        logging.info("Tabella 'access_logs' creata (o già esistente).")

        # Creazione tabella user_settings
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            theme TEXT DEFAULT 'light',
            language TEXT DEFAULT 'it',
            notifications INTEGER DEFAULT 1,
            last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        logging.info("Tabella 'user_settings' creata (o già esistente).")

        # Crea utente admin di default (password "admin123")
        admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute('''
        INSERT OR IGNORE INTO users (
            username, password, email, role, first_name, last_name
        ) VALUES (
            'admin',
            ?,
            'gueaserge2@gmail.com',
            'admin',
            'Serge',
            'Guea'
        )
        ''', (admin_password,))
        logging.info("Utente admin creato (se non già presente).")

        # Commit delle modifiche
        conn.commit()
        logging.info("Database inizializzato con successo!")
        return True

    except sqlite3.Error as e:
        logging.error(f"Errore SQLite durante l'inizializzazione: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    except Exception as e:
        logging.error(f"Errore generico durante l'inizializzazione: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


def test_database():
    """Verifica la struttura del database."""
    logging.info("Avvio test del database...")

    try:
        if not DB_FILE.exists():
            logging.error(f"Database non trovato in: {DB_FILE}")
            return False

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Verifica la struttura della tabella users
        logging.info("Verifica struttura tabella 'users':")
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        for col in columns:
            logging.info(f"Colonna: {col[1]}, Tipo: {col[2]}, NotNull: {col[3]}")

        # Verifica utenti presenti
        logging.info("Verifica utenti nel database:")
        cursor.execute('''
            SELECT username, email, role, first_name, last_name 
            FROM users
        ''')
        users = cursor.fetchall()

        if users:
            for user in users:
                logging.info("-" * 40)
                logging.info(f"Username: {user[0]}")
                logging.info(f"Email: {user[1]}")
                logging.info(f"Ruolo: {user[2]}")
                logging.info(f"Nome: {user[3]}")
                logging.info(f"Cognome: {user[4]}")
        else:
            logging.warning("Nessun utente trovato nel database.")

        # Verifica permessi file
        if not os.access(DB_FILE, os.R_OK | os.W_OK):
            logging.warning(f"Permessi insufficienti per il database: {DB_FILE}")
            os.chmod(DB_FILE, 0o666)
            logging.info("Permessi del database corretti a 666.")

        return True

    except sqlite3.Error as e:
        logging.error(f"Errore SQLite durante il test: {e}")
        return False
    except Exception as e:
        logging.error(f"Errore generico durante il test: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    try:
        logging.info("=== Inizializzazione Database ===")
        logging.info(f"Python versione: {sys.version}")
        logging.info(f"Sistema operativo: {os.name}")
        logging.info(f"Directory corrente: {os.getcwd()}")

        # Inizializzazione database
        if initialize_database():
            logging.info("Inizializzazione completata con successo")

            # Test database
            if test_database():
                logging.info("Test completato con successo")
                print("\nDatabase inizializzato e testato con successo!")
                sys.exit(0)
            else:
                logging.error("Test del database fallito")
                print("\nErrore durante il test del database")
                sys.exit(1)
        else:
            logging.error("Inizializzazione del database fallita")
            print("\nErrore durante l'inizializzazione del database")
            sys.exit(1)

    except Exception as e:
        logging.critical(f"Errore critico durante l'esecuzione: {e}")
        print(f"\nErrore critico: {e}")
        sys.exit(1)