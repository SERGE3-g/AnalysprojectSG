import os
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class QueryExporter:
    """Class for exporting generated queries in various formats."""

    def __init__(self, output_dir: str = "output"):
        """
        Initialize the QueryExporter.

        Args:
            output_dir (str): Directory where exported files will be saved
        """
        self.output_dir = output_dir
        self._ensure_output_dir_exists()

    def _ensure_output_dir_exists(self):
        """Create the output directory if it doesn't exist."""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, base_name: str, extension: str) -> str:
        """
        Generate a unique filename with timestamp.

        Args:
            base_name (str): Base name for the file
            extension (str): File extension

        Returns:
            str: Generated filename
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}.{extension}"

    def export_to_sql(self, query: str, db_type: str) -> Tuple[bool, Optional[str]]:
        """
        Export the query to a .sql file.

        Args:
            query (str): The SQL query to export
            db_type (str): The type of database

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        try:
            filename = self._generate_filename(f"query_{db_type.lower()}", "sql")
            filepath = os.path.join(self.output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"-- Generated query for {db_type}\n")
                f.write(f"-- Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(query)

            return True, filepath

        except Exception as e:
            return False, f"Errore durante l'esportazione SQL: {str(e)}"

    def export_to_json(self, query_data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Export query data to a JSON file.

        Args:
            query_data (Dict): Dictionary containing query information

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        try:
            filename = self._generate_filename("query_data", "json")
            filepath = os.path.join(self.output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(query_data, f, indent=4, ensure_ascii=False)

            return True, filepath

        except Exception as e:
            return False, f"Errore durante l'esportazione JSON: {str(e)}"

    def export_to_csv(self, queries: List[Dict]) -> Tuple[bool, Optional[str]]:
        """
        Export multiple queries to a CSV file.

        Args:
            queries (List[Dict]): List of dictionaries containing query information

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        try:
            filename = self._generate_filename("query_history", "csv")
            filepath = os.path.join(self.output_dir, filename)

            if not queries:
                return False, "Nessuna query da esportare."

            fieldnames = queries[0].keys()

            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(queries)

            return True, filepath

        except Exception as e:
            return False, f"Errore durante l'esportazione CSV: {str(e)}"

    def export_query_with_metadata(self,
                                   query: str,
                                   db_type: str,
                                   input_text: str,
                                   metadata: Dict = None) -> Tuple[bool, Optional[str]]:
        """
        Export query with associated metadata in JSON format.

        Args:
            query (str): The SQL query
            db_type (str): The type of database
            input_text (str): Original input text
            metadata (Dict): Additional metadata

        Returns:
            Tuple[bool, Optional[str]]: (success, error_message)
        """
        try:
            query_data = {
                "query": query,
                "database_type": db_type,
                "input_text": input_text,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }

            return self.export_to_json(query_data)

        except Exception as e:
            return False, f"Errore durante l'esportazione dei metadati: {str(e)}"