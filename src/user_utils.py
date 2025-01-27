import sqlite3
import hashlib
from datetime import datetime, timedelta
import secrets


class UserManager:
    def __init__(self, db_path='data/new_users.db'):
        self.db_path = db_path

    def create_user(self, username, password, email, first_name, last_name, role='user'):
        """Crea un nuovo utente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Verifica se username o email esistono già
            cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?',
                           (username, email))
            if cursor.fetchone():
                return False, "Username o email già registrati"

            # Hash della password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            # Inserisci il nuovo utente
            cursor.execute('''
                INSERT INTO users (
                    username, password, email, first_name, last_name,
                    role, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (username, hashed_password, email, first_name, last_name, role))

            # Crea le impostazioni predefinite
            user_id = cursor.lastrowid
            cursor.execute('''
                INSERT INTO user_settings (user_id)
                VALUES (?)
            ''', (user_id,))

            conn.commit()
            return True, "Utente creato con successo"

        except sqlite3.Error as e:
            return False, f"Errore database: {str(e)}"
        finally:
            conn.close()

    def update_user(self, user_id, **kwargs):
        """Aggiorna i dati di un utente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Costruisci la query di update
            update_fields = []
            values = []
            for key, value in kwargs.items():
                if key == 'password':
                    value = hashlib.sha256(value.encode()).hexdigest()
                update_fields.append(f"{key} = ?")
                values.append(value)

            if not update_fields:
                return False, "Nessun campo da aggiornare"

            values.append(user_id)
            query = f'''
                UPDATE users 
                SET {', '.join(update_fields)}
                WHERE id = ?
            '''

            cursor.execute(query, values)
            conn.commit()
            return True, "Dati utente aggiornati con successo"

        except sqlite3.Error as e:
            return False, f"Errore database: {str(e)}"
        finally:
            conn.close()

    def delete_user(self, user_id):
        """Disattiva un utente (soft delete)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                UPDATE users 
                SET is_active = 0 
                WHERE id = ?
            ''', (user_id,))

            conn.commit()
            return True, "Utente disattivato con successo"

        except sqlite3.Error as e:
            return False, f"Errore database: {str(e)}"
        finally:
            conn.close()

    def generate_reset_token(self, email):
        """Genera un token per il reset della password"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Verifica se l'email esiste
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            if not user:
                return False, "Email non trovata"

            # Genera token e data di scadenza
            token = secrets.token_urlsafe(32)
            expiry = datetime.now() + timedelta(hours=24)

            # Salva il token
            cursor.execute('''
                UPDATE users 
                SET reset_token = ?, reset_token_expiry = ? 
                WHERE id = ?
            ''', (token, expiry, user[0]))

            conn.commit()
            return True, token

        except sqlite3.Error as e:
            return False, f"Errore database: {str(e)}"
        finally:
            conn.close()

    def verify_reset_token(self, token):
        """Verifica la validità di un token di reset"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id 
                FROM users 
                WHERE reset_token = ? 
                AND reset_token_expiry > CURRENT_TIMESTAMP
            ''', (token,))

            result = cursor.fetchone()
            return bool(result), result[0] if result else None

        except sqlite3.Error as e:
            return False, None
        finally:
            conn.close()

    def get_user_settings(self, user_id):
        """Recupera le impostazioni di un utente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT theme, language, notifications
                FROM user_settings
                WHERE user_id = ?
            ''', (user_id,))

            result = cursor.fetchone()
            if result:
                return {
                    'theme': result[0],
                    'language': result[1],
                    'notifications': bool(result[2])
                }
            return None

        except sqlite3.Error as e:
            print(f"Errore nel recupero impostazioni: {e}")
            return None
        finally:
            conn.close()

    def update_user_settings(self, user_id, **settings):
        """Aggiorna le impostazioni di un utente"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            update_fields = []
            values = []
            for key, value in settings.items():
                update_fields.append(f"{key} = ?")
                values.append(value)

            if not update_fields:
                return False, "Nessuna impostazione da aggiornare"

            values.append(user_id)
            query = f'''
                UPDATE user_settings 
                SET {', '.join(update_fields)}, 
                    last_modified = CURRENT_TIMESTAMP
                WHERE user_id = ?
            '''

            cursor.execute(query, values)
            conn.commit()
            return True, "Impostazioni aggiornate con successo"

        except sqlite3.Error as e:
            return False, f"Errore database: {str(e)}"
        finally:
            conn.close()

    def get_access_logs(self, user_id=None, limit=50):
        """Recupera i log di accesso"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = '''
                SELECT u.username, al.action, al.timestamp, al.ip_address
                FROM access_logs al
                JOIN users u ON al.user_id = u.id
            '''
            params = []

            if user_id:
                query += ' WHERE al.user_id = ?'
                params.append(user_id)

            query += ' ORDER BY al.timestamp DESC LIMIT ?'
            params.append(limit)

            cursor.execute(query, params)
            return cursor.fetchall()

        except sqlite3.Error as e:
            print(f"Errore nel recupero log: {e}")
            return []
        finally:
            conn.close()