import sqlite3
import hashlib
import os
from datetime import datetime


def initialize_database():
    """Inizializza il database con la struttura necessaria"""
    # Assicurati che la directory data esista
    if not os.path.exists('data'):
        os.makedirs('data')

    # Connessione al database
    conn = sqlite3.connect('data/users.db')
    cursor = conn.cursor()

    try:
        # Creazione tabella utenti
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            first_name TEXT,
            last_name TEXT,
            role TEXT NOT NULL DEFAULT 'user',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            reset_token TEXT,
            reset_token_expiry TIMESTAMP
        )
        ''')

        # Creazione tabella log accessi
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

        # Creazione tabella impostazioni utente
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

        # Crea utente admin di default se non esiste
        admin_password = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute('''
        INSERT OR IGNORE INTO users (
            username, password, email, role, first_name, last_name
        ) VALUES (
            'admin',
            ?,
            'gueaserge2@gmail.com',
            'admin',
            'Admin',
            'User'
        )
        ''', (admin_password,))

        # Commit delle modifiche
        conn.commit()
        print("Database inizializzato con successo!")

    except sqlite3.Error as e:
        print(f"Errore durante l'inizializzazione del database: {e}")
        conn.rollback()

    finally:
        conn.close()


def update_database():
    """Aggiorna la struttura del database esistente"""
    conn = sqlite3.connect('data/users.db')
    cursor = conn.cursor()

    try:
        # Lista delle colonne esistenti nella tabella users
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = {column[1] for column in cursor.fetchall()}

        # Aggiungi nuove colonne se non esistono
        new_columns = {
            'email': 'TEXT UNIQUE',
            'first_name': 'TEXT',
            'last_name': 'TEXT',
            'reset_token': 'TEXT',
            'reset_token_expiry': 'TIMESTAMP'
        }

        for column, data_type in new_columns.items():
            if column not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {column} {data_type}")
                    print(f"Colonna {column} aggiunta con successo")
                except sqlite3.Error as e:
                    print(f"Errore nell'aggiunta della colonna {column}: {e}")

        # Verifica e crea la tabella user_settings se non esiste
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

        # Commit delle modifiche
        conn.commit()
        print("Database aggiornato con successo!")

    except sqlite3.Error as e:
        print(f"Errore durante l'aggiornamento del database: {e}")
        conn.rollback()

    finally:
        conn.close()


if __name__ == "__main__":
    # Se il database non esiste, inizializzalo
    if not os.path.exists('data/users.db'):
        initialize_database()
    else:
        # Se esiste, aggiorna la struttura
        update_database()
