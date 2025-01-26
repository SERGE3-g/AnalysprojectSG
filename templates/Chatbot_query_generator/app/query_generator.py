import re
from typing import Dict, List, Optional, Union, Any
import logging
from datetime import datetime


class QueryGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Template base per le query SQL
        self.templates = {
            'select': "SELECT {columns} FROM {table} WHERE {conditions}",
            'insert': "INSERT INTO {table} ({columns}) VALUES ({values})",
            'update': "UPDATE {table} SET {set_values} WHERE {conditions}",
            'delete': "DELETE FROM {table} WHERE {conditions}",
            'join': "SELECT {columns} FROM {table1} JOIN {table2} ON {join_condition} WHERE {conditions}",
            'group_by': "SELECT {columns}, {aggregate_func}({aggregate_column}) FROM {table} WHERE {conditions} GROUP BY {group_columns}",
            'order_by': "SELECT {columns} FROM {table} WHERE {conditions} ORDER BY {order_columns} {order_direction}"
        }

        # Pattern per la validazione dei nomi delle tabelle e colonne
        self.identifier_pattern = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

        # Parole chiave SQL non permesse
        self.dangerous_patterns = [
            "--", ";--", ";", "/*", "*/", "@@", "@", "char", "nchar",
            "varchar", "nvarchar", "alter", "begin", "cast", "create",
            "cursor", "declare", "delete", "drop", "end", "exec",
            "execute", "fetch", "insert", "kill", "select", "sys",
            "sysobjects", "syscolumns", "table", "update"
        ]

    def generate_query(self, intent: str, params: Dict[str, Any]) -> str:
        """
        Genera una query SQL basata sull'intento e i parametri

        Args:
            intent (str): Tipo di query (select, insert, update, delete, etc.)
            params (Dict[str, Any]): Parametri per la query

        Returns:
            str: Query SQL generata

        Raises:
            ValueError: Se l'intent non è supportato o mancano parametri
        """
        try:
            # Validazione dell'intent
            if intent not in self.templates:
                raise ValueError(f"Intent non supportato: {intent}")

            # Validazione dei parametri
            self._validate_params(intent, params)

            # Preparazione dei parametri
            processed_params = self._process_params(intent, params)

            # Generazione della query
            query_template = self.templates[intent]
            query = query_template.format(**processed_params)

            # Validazione finale della query
            if not self.validate_query(query):
                raise ValueError("La query generata non è sicura")

            self.logger.info(f"Query generata con successo: {query}")
            return query

        except Exception as e:
            self.logger.error(f"Errore nella generazione della query: {str(e)}")
            raise

    def _validate_params(self, intent: str, params: Dict[str, Any]) -> None:
        """
        Valida i parametri della query

        Args:
            intent (str): Tipo di query
            params (Dict[str, Any]): Parametri da validare

        Raises:
            ValueError: Se i parametri non sono validi
        """
        required_params = {
            'select': ['columns', 'table', 'conditions'],
            'insert': ['table', 'columns', 'values'],
            'update': ['table', 'set_values', 'conditions'],
            'delete': ['table', 'conditions'],
            'join': ['columns', 'table1', 'table2', 'join_condition', 'conditions'],
            'group_by': ['columns', 'table', 'conditions', 'aggregate_func', 'aggregate_column', 'group_columns'],
            'order_by': ['columns', 'table', 'conditions', 'order_columns', 'order_direction']
        }

        # Verifica parametri richiesti
        for param in required_params[intent]:
            if param not in params:
                raise ValueError(f"Parametro mancante: {param}")

        # Valida nomi di tabelle e colonne
        if 'table' in params:
            if not self.identifier_pattern.match(params['table']):
                raise ValueError(f"Nome tabella non valido: {params['table']}")

    def _process_params(self, intent: str, params: Dict[str, Any]) -> Dict[str, str]:
        """
        Processa e formatta i parametri per la query

        Args:
            intent (str): Tipo di query
            params (Dict[str, Any]): Parametri da processare

        Returns:
            Dict[str, str]: Parametri processati
        """
        processed = params.copy()

        # Formattazione specifica per INSERT
        if intent == 'insert':
            if isinstance(processed['values'], (list, tuple)):
                processed['values'] = ', '.join(map(self._format_value, processed['values']))
            if isinstance(processed['columns'], (list, tuple)):
                processed['columns'] = ', '.join(processed['columns'])

        # Formattazione specifica per UPDATE
        elif intent == 'update':
            if isinstance(processed['set_values'], dict):
                processed['set_values'] = ', '.join(
                    f"{k} = {self._format_value(v)}"
                    for k, v in processed['set_values'].items()
                )

        return processed

    def _format_value(self, value: Any) -> str:
        """
        Formatta un valore per l'uso in una query SQL

        Args:
            value (Any): Valore da formattare

        Returns:
            str: Valore formattato
        """
        if isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, datetime):
            return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
        elif value is None:
            return 'NULL'
        return str(value)

    def validate_query(self, query: str) -> bool:
        """
        Validazione completa della query SQL

        Args:
            query (str): Query da validare

        Returns:
            bool: True se la query è valida, False altrimenti
        """
        query_lower = query.lower()

        # Controllo pattern pericolosi
        if any(pattern.lower() in query_lower for pattern in self.dangerous_patterns):
            return False

        # Controllo commenti
        if '--' in query or '/*' in query:
            return False

        # Controllo concatenazione query
        if ';' in query:
            return False

        # Controllo iniezioni UNION
        if 'union' in query_lower:
            return False

        return True

    def build_where_clause(self, conditions: Dict[str, Any]) -> str:
        """
        Costruisce la clausola WHERE della query

        Args:
            conditions (Dict[str, Any]): Condizioni per la clausola WHERE

        Returns:
            str: Clausola WHERE formattata
        """
        if not conditions:
            return "1=1"

        clauses = []
        for column, value in conditions.items():
            if isinstance(value, (list, tuple)):
                formatted_values = ', '.join(map(self._format_value, value))
                clauses.append(f"{column} IN ({formatted_values})")
            elif value is None:
                clauses.append(f"{column} IS NULL")
            else:
                clauses.append(f"{column} = {self._format_value(value)}")

        return ' AND '.join(clauses)

    def get_query_template(self, intent: str) -> Optional[str]:
        """
        Restituisce il template per un determinato tipo di query

        Args:
            intent (str): Tipo di query

        Returns:
            Optional[str]: Template della query o None se non trovato
        """
        return self.templates.get(intent)

    def add_query_template(self, intent: str, template: str) -> None:
        """
        Aggiunge un nuovo template per le query

        Args:
            intent (str): Tipo di query
            template (str): Template della query
        """
        if not isinstance(template, str):
            raise ValueError("Il template deve essere una stringa")

        self.templates[intent] = template
        self.logger.info(f"Aggiunto nuovo template per l'intent: {intent}")