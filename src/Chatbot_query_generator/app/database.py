import sqlite3
import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from pathlib import Path
import json
import threading
from datetime import datetime
import time
import queue
from contextlib import contextmanager


class DatabaseManager:
    """Gestore del database per l'applicazione"""

    def __init__(self, db_path: str, max_connections: int = 5):
        """
        Inizializza il gestore del database

        Args:
            db_path: Percorso del file database
            max_connections: Numero massimo di connessioni simultanee
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.max_connections = max_connections

        # Pool di connessioni
        self.connection_pool = queue.Queue(maxsize=max_connections)
        self.active_connections = 0
        self.lock = threading.Lock()

        # Statistiche e monitoraggio
        self.stats = {
            'queries_executed': 0,
            'last_query_time': None,
            'errors': 0,
            'connections_created': 0
        }

        # Inizializza il database e il pool di connessioni
        self._initialize_database()
        self._initialize_connection_pool()

    def _initialize_database(self) -> None:
        """Inizializza la struttura del database"""
        try:
            with self.get_connection() as conn:
                # Crea tabella per il tracciamento delle query
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS query_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        query TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        execution_time REAL,
                        success BOOLEAN,
                        error_message TEXT
                    )
                """)

                # Crea tabella per le statistiche
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS database_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        metric_name TEXT NOT NULL,
                        metric_value REAL,
                        details TEXT
                    )
                """)

                conn.commit()

        except Exception as e:
            self.logger.error(f"Errore nell'inizializzazione del database: {str(e)}")
            raise

    def _initialize_connection_pool(self) -> None:
        """Inizializza il pool di connessioni"""
        for _ in range(self.max_connections):
            try:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                self.connection_pool.put(conn)
                self.stats['connections_created'] += 1
            except Exception as e:
                self.logger.error(f"Errore nella creazione della connessione: {str(e)}")
                raise

    @contextmanager
    def get_connection(self) -> sqlite3.Connection:
        """
        Ottiene una connessione dal pool

        Yields:
            sqlite3.Connection: Connessione al database
        """
        connection = None
        try:
            connection = self.connection_pool.get(timeout=5)
            yield connection
        finally:
            if connection:
                self.connection_pool.put(connection)

    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """
        Esegue una query SQL e restituisce i risultati

        Args:
            query: Query SQL da eseguire
            params: Parametri per la query (opzionale)

        Returns:
            List[Dict]: Lista dei risultati
        """
        start_time = time.time()
        success = False
        error_message = None

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                results = [dict(row) for row in cursor.fetchall()]

                # Aggiorna le statistiche
                execution_time = time.time() - start_time
                self.stats['queries_executed'] += 1
                self.stats['last_query_time'] = execution_time
                success = True

                # Logga la query
                self._log_query(query, execution_time, success)

                return results

        except Exception as e:
            self.stats['errors'] += 1
            error_message = str(e)
            self._log_query(query, time.time() - start_time, False, error_message)
            self.logger.error(f"Errore nell'esecuzione della query: {str(e)}")
            raise

    def execute_transaction(self, queries: List[Tuple[str, tuple]]) -> None:
        """
        Esegue multiple query in una transazione

        Args:
            queries: Lista di tuple (query, params)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("BEGIN TRANSACTION")

                    for query, params in queries:
                        cursor.execute(query, params)

                    cursor.execute("COMMIT")
                except Exception as e:
                    cursor.execute("ROLLBACK")
                    raise e

        except Exception as e:
            self.logger.error(f"Errore nell'esecuzione della transazione: {str(e)}")
            raise

    def backup_database(self, backup_path: str) -> None:
        """
        Crea un backup del database

        Args:
            backup_path: Percorso dove salvare il backup
        """
        try:
            with self.get_connection() as src_conn:
                dst_conn = sqlite3.connect(backup_path)
                src_conn.backup(dst_conn)
                dst_conn.close()

            self.logger.info(f"Backup del database creato con successo: {backup_path}")

        except Exception as e:
            self.logger.error(f"Errore nella creazione del backup: {str(e)}")
            raise

    def get_table_schema(self, table_name: str) -> List[Dict]:
        """
        Ottiene lo schema di una tabella

        Args:
            table_name: Nome della tabella

        Returns:
            List[Dict]: Informazioni sulle colonne
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute(f"PRAGMA table_info({table_name})")
                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Errore nel recupero dello schema: {str(e)}")
            raise

    def get_database_size(self) -> int:
        """
        Ottiene la dimensione del database in bytes

        Returns:
            int: Dimensione del database
        """
        try:
            return Path(self.db_path).stat().st_size
        except Exception as e:
            self.logger.error(f"Errore nel recupero della dimensione: {str(e)}")
            raise

    def vacuum_database(self) -> None:
        """Ottimizza il database rimuovendo lo spazio non utilizzato"""
        try:
            with self.get_connection() as conn:
                conn.execute("VACUUM")
            self.logger.info("Database ottimizzato con successo")
        except Exception as e:
            self.logger.error(f"Errore nell'ottimizzazione del database: {str(e)}")
            raise

    def get_statistics(self) -> Dict:
        """
        Ottiene statistiche sul database

        Returns:
            Dict: Statistiche del database
        """
        stats = self.stats.copy()

        try:
            with self.get_connection() as conn:
                # Numero di tabelle
                cursor = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table'")
                stats['num_tables'] = cursor.fetchone()[0]

                # Dimensione totale
                stats['size_bytes'] = self.get_database_size()

                # Statistiche per tabella
                stats['tables'] = {}
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                for row in cursor.fetchall():
                    table_name = row[0]
                    cursor = conn.execute(f"SELECT count(*) FROM {table_name}")
                    stats['tables'][table_name] = {
                        'row_count': cursor.fetchone()[0],
                        'schema': self.get_table_schema(table_name)
                    }

            return stats

        except Exception as e:
            self.logger.error(f"Errore nel recupero delle statistiche: {str(e)}")
            raise

    def _log_query(self, query: str, execution_time: float, success: bool,
                   error_message: str = None) -> None:
        """
        Logga i dettagli di una query eseguita

        Args:
            query: Query eseguita
            execution_time: Tempo di esecuzione
            success: Se la query ha avuto successo
            error_message: Messaggio di errore (opzionale)
        """
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO query_log 
                    (query, execution_time, success, error_message)
                    VALUES (?, ?, ?, ?)
                """, (query, execution_time, success, error_message))
                conn.commit()
        except Exception as e:
            self.logger.error(f"Errore nel logging della query: {str(e)}")

    def optimize_query(self, query: str) -> str:
        """
        Analizza e ottimizza una query SQL

        Args:
            query: Query da ottimizzare

        Returns:
            str: Query ottimizzata
        """
        try:
            with self.get_connection() as conn:
                # Analizza il piano di esecuzione
                cursor = conn.execute(f"EXPLAIN QUERY PLAN {query}")
                plan = cursor.fetchall()

                # Analisi base del piano
                optimized_query = query

                # Suggerimenti per l'ottimizzazione
                suggestions = []

                # Verifica la presenza di indici
                if "SCAN TABLE" in str(plan):
                    suggestions.append("Considerare l'aggiunta di indici appropriati")

                # Verifica l'uso di DISTINCT non necessario
                if "DISTINCT" in query.upper() and "GROUP BY" in query.upper():
                    suggestions.append("DISTINCT potrebbe essere ridondante con GROUP BY")

                return {
                    'optimized_query': optimized_query,
                    'execution_plan': plan,
                    'suggestions': suggestions
                }

        except Exception as e:
            self.logger.error(f"Errore nell'ottimizzazione della query: {str(e)}")
            raise

    def close(self) -> None:
        """Chiude tutte le connessioni nel pool"""
        try:
            while not self.connection_pool.empty():
                conn = self.connection_pool.get_nowait()
                conn.close()
            self.logger.info("Tutte le connessioni sono state chiuse")
        except Exception as e:
            self.logger.error(f"Errore nella chiusura delle connessioni: {str(e)}")
            raise


# Esempio di utilizzo
if __name__ == "__main__":
    try:
        # Inizializza il database manager
        db = DatabaseManager("example.db")

        # Crea una tabella di esempio
        db.execute_query("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Inserisce alcuni dati di esempio
        users = [
            ("user1", "user1@example.com"),
            ("user2", "user2@example.com")
        ]

        for username, email in users:
            db.execute_query(
                "INSERT OR IGNORE INTO users (username, email) VALUES (?, ?)",
                (username, email)
            )

        # Recupera e stampa i dati
        results = db.execute_query("SELECT * FROM users")
        print("Utenti nel database:", results)

        # Stampa alcune statistiche
        stats = db.get_statistics()
        print("\nStatistiche del database:", json.dumps(stats, indent=2))

        # Chiude le connessioni
        db.close()

    except Exception as e:
        print(f"Errore nell'esecuzione dell'esempio: {str(e)}")