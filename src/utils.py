import re
import sqlite3
import os
import json
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_name):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """Inizializza il database se non esiste"""
        if not os.path.exists('data'):
            os.makedirs('data')

        self.conn = sqlite3.connect(f'data/{self.db_name}')
        self.cursor = self.conn.cursor()

    def execute(self, query, params=()):
        """Esegue una query SQL"""
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Errore nella query: {str(e)}")
            return False

    def fetch_all(self, query, params=()):
        """Esegue una query e ritorna tutti i risultati"""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"Errore nel fetch: {str(e)}")
            return []

    def close(self):
        """Chiude la connessione al database"""
        self.conn.close()


class CityDatabase:
    def __init__(self):
        self.load_cities()

    def load_cities(self):
        """Carica i dati dei comuni da file JSON"""
        try:
            with open('data/cities.json', 'r', encoding='utf-8') as f:
                self.cities = json.load(f)
        except FileNotFoundError:
            self.cities = self.get_default_cities()
            self.save_cities()

    def save_cities(self):
        """Salva i dati dei comuni in JSON"""
        if not os.path.exists('data'):
            os.makedirs('data')
        with open('data/cities.json', 'w', encoding='utf-8') as f:
            json.dump(self.cities, f, indent=4, ensure_ascii=False)

    def get_default_cities(self):
        """Ritorna un dizionario predefinito di città e codici"""
        return {
            "Roma": "H501", "Milano": "F205", "Napoli": "F839",
            "Torino": "L219", "Palermo": "G273", "Genova": "D969",
            "Bologna": "A944", "Firenze": "D612", "Bari": "A662",
            # Aggiungi altre città qui...
        }

    def get_cities(self):
        """Ritorna la lista delle città"""
        return list(self.cities.keys())

    def get_code(self, city):
        """Ritorna il codice di una città"""
        return self.cities.get(city)


class ConfigManager:
    def __init__(self):
        self.config_file = 'data/config.json'
        self.load_config()

    def load_config(self):
        """Carica la configurazione"""
        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = self.get_default_config()
            self.save_config()

    def save_config(self):
        """Salva la configurazione"""
        if not os.path.exists('data'):
            os.makedirs('data')
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def get_default_config(self):
        """Ritorna la configurazione predefinita"""
        return {
            'theme': 'clam',
            'language': 'it',
            'auto_backup': True,
            'backup_interval': 30,
            'last_backup': None
        }

    def get(self, key, default=None):
        """Ritorna un valore di configurazione"""
        return self.config.get(key, default)

    def set(self, key, value):
        """Imposta un valore di configurazione"""
        self.config[key] = value
        self.save_config()


class Logger:
    def __init__(self):
        self.log_dir = 'data/logs'
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def log(self, message, level='INFO'):
        """Registra un messaggio nel log"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {level}: {message}\n"

        log_file = os.path.join(
            self.log_dir,
            f"log_{datetime.now().strftime('%Y%m%d')}.txt"
        )

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_message)


class ValidationUtils:
    @staticmethod
    def validate_fiscal_code(code):
        """Valida un codice fiscale"""
        if not code or len(code) != 16:
            return False

        code = code.upper()
        return bool(re.match(r'^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$', code))

    @staticmethod
    def validate_date(date_str):
        """Valida una data nel formato DD/MM/YYYY"""
        try:
            day, month, year = map(int, date_str.split('/'))
            return bool(1 <= day <= 31 and 1 <= month <= 12 and 1900 <= year <= 2100)
        except:
            return False

    @staticmethod
    def validate_email(email):
        """Valida un indirizzo email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))