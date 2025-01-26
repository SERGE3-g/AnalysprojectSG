from typing import Tuple, Optional


class QueryValidator:
    """Class for validating input text and generated queries."""

    @staticmethod
    def validate_input_text(text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate the input text from the user.

        Args:
            text (str): The input text to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not text:
            return False, "L'input non può essere vuoto."

        if len(text.strip()) < 10:
            return False, "L'input deve contenere almeno 10 caratteri."

        # Add more specific validation rules as needed

        return True, None

    @staticmethod
    def validate_query(query: str, db_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate the generated SQL query.

        Args:
            query (str): The SQL query to validate
            db_type (str): The type of database (PostgreSQL, Oracle, SQL)

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not query:
            return False, "La query generata è vuota."

        # Basic SQL injection prevention
        dangerous_keywords = ["DROP", "DELETE", "TRUNCATE", "ALTER", "--", ";", "/*"]
        for keyword in dangerous_keywords:
            if keyword in query.upper():
                return False, f"La query contiene parole chiave non consentite: {keyword}"

        # Database specific validations
        if db_type == "PostgreSQL":
            return QueryValidator._validate_postgresql_query(query)
        elif db_type == "Oracle":
            return QueryValidator._validate_oracle_query(query)
        else:  # Generic SQL
            return QueryValidator._validate_generic_sql_query(query)

    @staticmethod
    def _validate_postgresql_query(query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate PostgreSQL specific syntax.

        Args:
            query (str): The PostgreSQL query to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Add PostgreSQL specific validation rules
        return True, None

    @staticmethod
    def _validate_oracle_query(query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Oracle specific syntax.

        Args:
            query (str): The Oracle query to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Add Oracle specific validation rules
        return True, None

    @staticmethod
    def _validate_generic_sql_query(query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate generic SQL syntax.

        Args:
            query (str): The SQL query to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Add generic SQL validation rules
        return True, None


class FileValidator:
    """Class for validating input files."""

    @staticmethod
    def validate_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate the input file.

        Args:
            file_path (str): Path to the file to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            # Check if file exists
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if not content:
                return False, "Il file è vuoto."

            # Add more file validation rules as needed

            return True, None

        except FileNotFoundError:
            return False, "File non trovato."
        except PermissionError:
            return False, "Permesso negato per accedere al file."
        except Exception as e:
            return False, f"Errore durante la validazione del file: {str(e)}"