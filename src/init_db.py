import sqlite3
import hashlib
import os
from datetime import datetime


def initialize_database():
    """Inizializza il database per il sistema di gestione utenti"""

    # Crea la directory data se non esiste
    if not os.path.exists('data'):
        os.makedirs('data')

    # Connessione al database
    conn = sqlite3.connect('data/users.db')
    cursor = conn.cursor()

    # Elimina la tabella se esiste
    cursor.execute('DROP TABLE IF EXISTS users')
    cursor.execute('DROP TABLE IF EXISTS access_logs')

    # Crea la tabella degli utenti con la struttura corretta
    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        email TEXT,
        full_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        is_active INTEGER DEFAULT 1
    )
    ''')

    # Crea la tabella per i log di accesso
    cursor.execute('''
    CREATE TABLE access_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
        user_agent TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')

    # Crea indici per ottimizzare le query
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_username ON users(username)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_role ON users(role)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_email ON users(email)')

    # Inserisci l'utente admin di default
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        hashed_password = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute('''
        INSERT INTO users (username, password, role, email, full_name, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', ('admin', hashed_password, 'admin', 'gueaserge2@gmail.com', 'Administrator', 1))

    # Commit delle modifiche
    conn.commit()
    conn.close()

    print("Database inizializzato con successo!")


if __name__ == "__main__":
    print("Inizializzazione del database...")

    # Backup del database esistente se presente
    if os.path.exists('data/users.db'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f'data/users_backup_{timestamp}.db'

        # Crea una copia di backup
        import shutil

        shutil.copy2('data/users.db', backup_path)
        print(f"Backup del database esistente creato: {backup_path}")

        # Elimina il database esistente
        os.remove('data/users.db')
        print("Database esistente eliminato")

    # Inizializza il nuovo database
    initialize_database()