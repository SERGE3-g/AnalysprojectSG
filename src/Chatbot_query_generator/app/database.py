import sqlite3
from typing import List, Dict, Any, Optional, Union
import logging
from contextlib import contextmanager
from datetime import datetime
import json
import os


class DatabaseManager:
    def __init__(self, db_path: str):
        """
        Inizializza il DatabaseManager.

        Args:
            db_path (str): Percorso del file del database
        """
        self.db_path = db_path
        self.connection = None
        self.setup_logging()
        self.init_db()

    def setup_logging(self):
        """Configura il sistema di logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('database.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def init_db(self):
        """Inizializza il database con le tabelle necessarie"""
        try:
            with self.get_connection() as conn:
                # Tabella per il logging delle query
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS query_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT NOT NULL,
                        params TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        execution_time REAL,
                        status TEXT,
                        error_message TEXT
                    )
                """)

                # Tabella per le statistiche
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS db_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        table_name TEXT NOT NULL,
                        row_count INTEGER,
                        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Errore nell'inizializzazione del database: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Context manager per la gestione della connessione"""
        try:
            if not self.connection:
                self.connect()
            yield self.connection
        except sqlite3.Error as e:
            self.logger.error(f"Errore nella connessione al database: {e}")
            raise
        finally:
            if self.connection:
                self.connection.commit()

    def connect(self) -> bool:
        """
        Stabilisce una connessione al database

        Returns:
            bool: True se la connessione è stabilita con successo
        """
        try:
            if not os.path.exists(os.path.dirname(self.db_path)):
                os.makedirs(os.path.dirname(self.db_path))

            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row

            # Abilita il foreign key support
            self.connection.execute("PRAGMA foreign_keys = ON")
            # Configura timeout più lungo per le transazioni
            self.connection.execute("PRAGMA busy_timeout = 30000")

            return True
        except sqlite3.Error as e:
            self.logger.error(f"Errore di connessione al database: {e}")
            return False

    def execute_query(self, query: str, params: Optional[Union[tuple, dict]] = None) -> List[Dict[str, Any]]:
        """
        Esegue una query SQL e restituisce i risultati

        Args:
            query (str): Query SQL da eseguire
            params (Optional[Union[tuple, dict]]): Parametri per la query

        Returns:
            List[Dict[str, Any]]: Risultati della query
        """
        start_time = datetime.now()
        status = "success"
        error_message = None

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                if query.strip().upper().startswith('SELECT'):
                    results = [dict(row) for row in cursor.fetchall()]
                else:
                    conn.commit()
                    results = []

                execution_time = (datetime.now() - start_time).total_seconds()
                self._log_query(query, params, execution_time, status, error_message)

                return results

        except sqlite3.Error as e:
            status = "error"
            error_message = str(e)
            execution_time = (datetime.now() - start_time).total_seconds()
            self._log_query(query, params, execution_time, status, error_message)
            self.logger.error(f"Errore nell'esecuzione della query: {e}")
            raise

    def execute_many(self, query: str, params_list: List[Union[tuple, dict]]) -> None:
        """
        Esegue una query multiple volte con diversi parametri

        Args:
            query (str): Query SQL da eseguire
            params_list (List[Union[tuple, dict]]): Lista di parametri
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Errore nell'esecuzione multipla della query: {e}")
            raise

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Ottiene informazioni su una tabella

        Args:
            table_name (str): Nome della tabella

        Returns:
            List[Dict[str, Any]]: Informazioni sulla tabella
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA table_info({table_name})")
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            self.logger.error(f"Errore nel recupero delle informazioni della tabella: {e}")
            raise

    def _log_query(self, query: str, params: Any, execution_time: float, status: str,
                   error_message: Optional[str]) -> None:
        """
        Registra una query nel log

        Args:
            query (str): Query eseguita
            params (Any): Parametri della query
            execution_time (float): Tempo di esecuzione
            status (str): Stato dell'esecuzione
            error_message (Optional[str]): Messaggio di errore se presente
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO query_log (query, params, execution_time, status, error_message)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    query,
                    json.dumps(params) if params else None,
                    execution_time,
                    status,
                    error_message
                ))
                conn.commit()
        except sqlite3.Error as e:
            self.logger.error(f"Errore nel logging della query: {e}")

    def create_backup(self, backup_path: str) -> bool:
        """
        Crea un backup del database

        Args:
            backup_path (str): Percorso dove salvare il backup

        Returns:
            bool: True se il backup è stato creato con successo
        """
        try:
            with self.get_connection() as conn:
                backup_conn = sqlite3.connect(backup_path)
                conn.backup(backup_conn)
                backup_conn.close()
                self.logger.info(f"Backup creato con successo: {backup_path}")
                return True
        except sqlite3.Error as e:
            self.logger.error(f"Errore nella creazione del backup: {e}")
            return False

    def optimize_database(self) -> None:
        """Ottimizza il database"""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
                conn.execute("ANALYZE")
                self.logger.info("Database ottimizzato con successo")
        except sqlite3.Error as e:
            self.logger.error(f"Errore nell'ottimizzazione del database: {e}")
            raise

    def close(self) -> None:
        """Chiude la connessione al database"""
        if self.connection:
            try:
                self.connection.close()
                self.connection = None
                self.logger.info("Connessione al database chiusa")
            except sqlite3.Error as e:
                self.logger.error(f"Errore nella chiusura della connessione: {e}")
                raise

    def update_table_statistics(self, table_name: str) -> Dict[str, Any]:
        """
        Aggiorna e restituisce le statistiche di una tabella

        Args:
            table_name (str): Nome della tabella

        Returns:
            Dict[str, Any]: Statistiche aggiornate della tabella
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
                row_count = cursor.fetchone()['count']

                cursor.execute("""
                    INSERT OR REPLACE INTO db_stats (table_name, row_count, last_updated)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (table_name, row_count))

                return {
                    'table_name': table_name,
                    'row_count': row_count,
                    'last_updated': datetime.now()
                }
        except sqlite3.Error as e:
            self.logger.error(f"Errore nell'aggiornamento delle statistiche: {e}")
            raise