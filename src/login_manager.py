import hashlib
import os
import socket
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests
from setuptools import logging


class LoginManager:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent
        self.data_dir = self.base_dir / 'data'
        self.db_path = self.data_dir / 'users.db'

        # Crea directory data se non esiste
        self.data_dir.mkdir(exist_ok=True)

        print(f"[DEBUG] LoginManager DB path: {self.db_path}")
        self.setup_database()

    def setup_database(self):
        """Verifica che il database esista, altrimenti lo inizializza."""
        if not os.path.exists(self.db_path):
            print("[DEBUG] Database non trovato, chiamo initialize_database()...")
            from init_db import initialize_database
            initialize_database()
        else:
            print("[DEBUG] Database già presente. Controllo struttura...")

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Controllo struttura
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            print(f"[DEBUG] Tabella 'users' -> colonne: {column_names}")

            if 'first_name' not in column_names or 'last_name' not in column_names:
                print("[ERRORE] La tabella 'users' non ha le colonne 'first_name'/'last_name'.")
                print("         Assicurati che init_db.py abbia creato la tabella correttamente.")

            # Controllo utenti esistenti
            cursor.execute("SELECT username, email, role FROM users")
            users = cursor.fetchall()
            print(f"[DEBUG] Utenti nel database: {users}")

        except sqlite3.Error as e:
            print(f"[ERRORE] Errore database in setup_database: {e}")
        finally:
            if 'conn' in locals():
                conn.close()

    def get_connection(self):
        """Ritorna una connessione aperta al database."""
        return sqlite3.connect(self.db_path)

    def hash_password(self, raw_password: str) -> str:
        """Restituisce l'hash SHA-256 di una password in chiaro."""
        return hashlib.sha256(raw_password.encode()).hexdigest()

    def get_system_info(self):
        """Ottiene informazioni di IP e sistema."""
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            public_ip = response.json()['ip'] if response.status_code == 200 else 'Unknown'

            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            os_info = f"OS: {os.name}, Platform: {sys.platform}, Host: {hostname}"

            return {
                'public_ip': public_ip,
                'local_ip': local_ip,
                'system_info': os_info
            }
        except Exception as e:
            print(f"Errore nel recupero informazioni sistema: {str(e)}")
            return {
                'public_ip': 'Unknown',
                'local_ip': 'Unknown',
                'system_info': 'Unknown'
            }

    def verify_login(self, username, password):
        """Verifica credenziali e stato attivo."""
        if not username or not password:
            logging.warning("Tentativo di login con credenziali vuote")
            return None

        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            hashed_password = self.hash_password(password)
            cursor.execute('''
                SELECT id, role
                FROM users
                WHERE username = ? 
                  AND password = ?
                  AND is_active = 1
            ''', (username, hashed_password))

            result = cursor.fetchone()
            if result:
                user_id, role = result
                system_info = self.get_system_info()

                # Aggiorna last_login e log dell'accesso
                cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
                cursor.execute('''
                    INSERT INTO access_logs (user_id, action, ip_address, user_agent)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, 'login_success', system_info['public_ip'], system_info['system_info']))
                conn.commit()
                return role
            else:
                # Tenta log fallito se l'utente esiste
                cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
                user_result = cursor.fetchone()
                if user_result:
                    system_info = self.get_system_info()
                    cursor.execute('''
                        INSERT INTO access_logs (user_id, action, ip_address, user_agent)
                        VALUES (?, ?, ?, ?)
                    ''', (user_result[0], 'login_failed', system_info['public_ip'], system_info['system_info']))
                    conn.commit()
                return None

        except sqlite3.Error as e:
            logging.error(f"Errore database: {e}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()


    def register_user(self, username, password, email, first_name, last_name):
        """Registra un nuovo utente."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Controlla username/email duplicati
            cursor.execute('SELECT id FROM users WHERE username=? OR email=?', (username, email))
            if cursor.fetchone():
                return False, "Username o email già registrati"

            hashed_password = self.hash_password(password)
            cursor.execute('''
                INSERT INTO users (
                    username, password, email, first_name, last_name,
                    role, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, 'user', 1, CURRENT_TIMESTAMP)
            ''', (username, hashed_password, email, first_name, last_name))

            user_id = cursor.lastrowid
            cursor.execute('''
                INSERT INTO user_settings (user_id, theme, language)
                VALUES (?, 'light', 'it')
            ''', (user_id,))

            conn.commit()
            return True, "Registrazione completata con successo"

        except sqlite3.Error as e:
            return False, f"Errore durante la registrazione: {str(e)}"
        finally:
            if 'conn' in locals():
                conn.close()

    def get_last_login_details(self, username):
        """Dettagli ultimo accesso di uno username."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT u.id, al.timestamp, al.ip_address, al.user_agent
                FROM users u
                LEFT JOIN access_logs al ON u.id = al.user_id
                WHERE u.username = ?
                  AND al.action = 'login_success'
                ORDER BY al.timestamp DESC
                LIMIT 1
            ''', (username,))

            result = cursor.fetchone()
            if result:
                return {
                    'user_id': result[0],
                    'last_login': result[1],
                    'ip_address': result[2],
                    'user_agent': result[3]
                }
            return None

        except sqlite3.Error as e:
            print(f"Errore nel recupero dettagli login: {str(e)}")
            return None
        finally:
            if 'conn' in locals():
                conn.close()

    def get_login_history(self, user_id, limit=10):
        """Cronologia degli accessi di user_id."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT timestamp, action, ip_address, user_agent
                FROM access_logs
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (user_id, limit))

            rows = cursor.fetchall()
            return [{
                'timestamp': r[0],
                'action': r[1],
                'ip_address': r[2],
                'user_agent': r[3]
            } for r in rows]

        except sqlite3.Error as e:
            print(f"Errore nel recupero cronologia: {str(e)}")
            return []
        finally:
            if 'conn' in locals():
                conn.close()

    def change_password(self, user_id, old_password, new_password):
        """Cambia password utente, previa verifica old_password."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            hashed_old = self.hash_password(old_password)
            cursor.execute('SELECT id FROM users WHERE id=? AND password=?', (user_id, hashed_old))
            if not cursor.fetchone():
                return False, "Password attuale non corretta"

            hashed_new = self.hash_password(new_password)
            cursor.execute('UPDATE users SET password=? WHERE id=?', (hashed_new, user_id))
            conn.commit()
            return True, "Password aggiornata con successo"

        except sqlite3.Error as e:
            return False, f"Errore cambio password: {str(e)}"
        finally:
            if 'conn' in locals():
                conn.close()

    def request_password_reset(self, email):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()

            if not user:
                return False, "Email non trovata"

            token = hashlib.sha256(os.urandom(32)).hexdigest()[:32]
            expiry = datetime.now() + timedelta(hours=24)

            cursor.execute('''
                UPDATE users 
                SET reset_token = ?, reset_token_expiry = ? 
                WHERE email = ?
            ''', (token, expiry, email))

            conn.commit()
            return True, token

        except sqlite3.Error as e:
            return False, f"Errore database: {str(e)}"
        finally:
            if 'conn' in locals():
                conn.close()

    def update_user_settings(self, user_id, **settings):
        """Aggiorna impostazioni dell'utente."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            fields = []
            values = []
            for key, value in settings.items():
                fields.append(f"{key} = ?")
                values.append(value)

            if not fields:
                return False, "Nessuna impostazione da aggiornare"

            values.append(user_id)
            query = f'''
                UPDATE user_settings
                SET {', '.join(fields)},
                    last_modified = CURRENT_TIMESTAMP
                WHERE user_id = ?
            '''

            cursor.execute(query, values)
            conn.commit()
            return True, "Impostazioni aggiornate con successo"

        except sqlite3.Error as e:
            return False, f"Errore update impostazioni: {str(e)}"
        finally:
            if 'conn' in locals():
                conn.close()


if __name__ == "__main__":
    # Esempio di test
    lm = LoginManager()
    print(f"[DEBUG] Usando DB: {lm.db_path}")

    # Esempio di reset password se un utente dimentica
    ok, msg = lm.reset_forgotten_password("test@example.com", "nuovaPassword123")
    print("Reset forgotten password:", msg)