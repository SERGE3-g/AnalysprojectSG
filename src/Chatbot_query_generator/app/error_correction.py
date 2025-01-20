from typing import Dict, List, Tuple, Optional, Set, Any
import re
from difflib import get_close_matches, SequenceMatcher
import logging
from datetime import datetime
import json
import pickle
from collections import defaultdict
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class ErrorCorrector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._load_base_components()
        self._initialize_ml_components()
        self._load_error_patterns()
        self._setup_context_analyzer()

    def _load_base_components(self):
        """Carica i componenti base del correttore"""
        # Dizionario delle correzioni comuni
        self.common_corrections = {
            'seleziona': ['selezziona', 'selezionare', 'seleziona'],
            'dove': ['dovve', 'dove', 'dov'],
            'tabella': ['tavola', 'tabela', 'tabbella'],
            'inserisci': ['inserire', 'inserissce', 'inserisci'],
            'aggiorna': ['agiorna', 'aggiornare', 'agg'],
            'elimina': ['cancella', 'elimina', 'delete'],
        }

        # Pattern SQL avanzati
        self.sql_patterns = {
            'base_keywords': r'\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|AND|OR)\b',
            'advanced_keywords': r'\b(JOIN|GROUP BY|HAVING|ORDER BY|LIMIT|OFFSET)\b',
            'functions': r'\b(COUNT|SUM|AVG|MAX|MIN)\b',
            'operators': r'\b(LIKE|IN|BETWEEN|EXISTS|NOT|IS NULL|IS NOT NULL)\b',
            'table_name': r'\b[a-zA-Z_][a-zA-Z0-9_]*\b',
            'number': r'\b\d+\b',
            'operator': r'[=<>!]+',
            'string_literal': r"'[^']*'|\"[^\"]*\"",
            'comment': r'--.*$|/\*[\s\S]*?\*/',
        }

    def _initialize_ml_components(self):
        """Inizializza i componenti di machine learning"""
        self.vectorizer = TfidfVectorizer(
            analyzer='char',
            ngram_range=(2, 3),
            max_features=5000
        )

        # Carica il modello se esiste
        try:
            with open('error_correction_model.pkl', 'rb') as f:
                self.correction_model = pickle.load(f)
        except FileNotFoundError:
            self.correction_model = {}

        # Frequenza degli errori per l'apprendimento
        self.error_frequency = defaultdict(int)

        # Matrice di similarità per le parole
        self.word_similarities = {}

    def _load_error_patterns(self):
        """Carica i pattern di errori comuni"""
        self.error_patterns = {
            'typos': {
                'double_letters': r'([a-z])\1+',
                'common_swaps': [('ei', 'ie'), ('ou', 'uo')],
            },
            'sql_errors': {
                'missing_spaces': r'(WHERE|AND|OR)(\w)',
                'wrong_quotes': r'["""]',
                'unmatched_parentheses': r'\([^)]*$|\([^)]*\)',
            },
            'semantic_errors': {
                'wrong_join_syntax': r'JOIN\s+\w+\s+(?!ON)',
                'missing_group_by': r'(COUNT|SUM|AVG|MAX|MIN)\s*\([^)]*\).*(?!GROUP BY)',
            }
        }

    def _setup_context_analyzer(self):
        """Configura l'analizzatore di contesto"""
        self.context_rules = {
            'sql_context': {
                'select': {'required': ['from'], 'optional': ['where', 'group by', 'having', 'order by']},
                'insert': {'required': ['into', 'values'], 'optional': []},
                'update': {'required': ['set'], 'optional': ['where']},
                'delete': {'required': ['from'], 'optional': ['where']},
            },
            'semantic_context': {
                'aggregation': ['count', 'sum', 'avg', 'max', 'min'],
                'conditions': ['where', 'having'],
                'ordering': ['order by', 'asc', 'desc'],
            }
        }

    def learn_from_corrections(self, original: str, corrected: str) -> None:
        """
        Apprende dalle correzioni effettuate

        Args:
            original (str): Testo originale
            corrected (str): Testo corretto
        """
        try:
            # Aggiorna la frequenza degli errori
            diff = SequenceMatcher(None, original, corrected)
            for tag, i1, i2, j1, j2 in diff.get_opcodes():
                if tag in ('replace', 'delete'):
                    error = original[i1:i2]
                    correction = corrected[j1:j2]
                    self.error_frequency[(error, correction)] += 1

            # Aggiorna il modello
            if len(self.error_frequency) > 1000:
                self._update_correction_model()

        except Exception as e:
            self.logger.error(f"Errore nell'apprendimento dalle correzioni: {e}")

    def _update_correction_model(self) -> None:
        """Aggiorna il modello di correzione basato sulla frequenza degli errori"""
        try:
            # Converti le correzioni frequenti in features
            corrections = list(self.error_frequency.items())
            X = self.vectorizer.fit_transform([c[0][0] for c in corrections])

            # Aggiorna il modello
            for i, ((error, correction), freq) in enumerate(corrections):
                self.correction_model[error] = {
                    'correction': correction,
                    'frequency': freq,
                    'features': X[i].toarray()
                }

            # Salva il modello
            with open('error_correction_model.pkl', 'wb') as f:
                pickle.dump(self.correction_model, f)

        except Exception as e:
            self.logger.error(f"Errore nell'aggiornamento del modello: {e}")

    def analyze_query_context(self, query: str) -> Dict[str, Any]:
        """
        Analizza il contesto della query per identificare errori semantici

        Args:
            query (str): Query da analizzare

        Returns:
            Dict[str, Any]: Analisi del contesto
        """
        analysis = {
            'command_type': None,
            'missing_clauses': [],
            'semantic_errors': [],
            'suggestions': []
        }

        try:
            query_lower = query.lower()

            # Identifica il tipo di comando
            for command in ['select', 'insert', 'update', 'delete']:
                if query_lower.startswith(command):
                    analysis['command_type'] = command

                    # Verifica le clausole richieste
                    required = self.context_rules['sql_context'][command]['required']
                    for clause in required:
                        if clause not in query_lower:
                            analysis['missing_clauses'].append(clause)
                            analysis['suggestions'].append(f"Aggiungi la clausola {clause.upper()}")

                    break

            # Verifica errori semantici comuni
            if 'select' in query_lower:
                # Controlla JOIN senza ON
                if 'join' in query_lower and 'on' not in query_lower:
                    analysis['semantic_errors'].append("JOIN senza clausola ON")
                    analysis['suggestions'].append("Aggiungi la clausola ON dopo il JOIN")

                # Controlla funzioni di aggregazione senza GROUP BY
                if any(f in query_lower for f in self.context_rules['semantic_context']['aggregation']):
                    if 'group by' not in query_lower:
                        analysis['semantic_errors'].append("Funzione di aggregazione senza GROUP BY")
                        analysis['suggestions'].append("Aggiungi GROUP BY per le colonne non aggregate")

            return analysis

        except Exception as e:
            self.logger.error(f"Errore nell'analisi del contesto: {e}")
            return analysis

    def suggest_query_improvements(self, query: str) -> List[str]:
        """
        Suggerisce miglioramenti per la query

        Args:
            query (str): Query da analizzare

        Returns:
            List[str]: Lista di suggerimenti
        """
        suggestions = []
        try:
            query_lower = query.lower()

            # Suggerimenti per ottimizzazione
            if 'select *' in query_lower:
                suggestions.append("Specifica le colonne invece di usare SELECT *")

            if 'where' in query_lower and 'index' not in query_lower:
                suggestions.append("Considera l'uso di un indice per migliorare le performance")

            # Suggerimenti per leggibilità
            if len(query.split('\n')) == 1 and len(query) > 50:
                suggestions.append("Formatta la query su più righe per migliorare la leggibilità")

            if query.count('  ') > 0:
                suggestions.append("Standardizza la spaziatura usando un singolo spazio")

            return suggestions

        except Exception as e:
            self.logger.error(f"Errore nella generazione dei suggerimenti: {e}")
            return suggestions

    def analyze_error_patterns(self, text: str) -> Dict[str, List[str]]:
        """
        Analizza i pattern di errori nel testo

        Args:
            text (str): Testo da analizzare

        Returns:
            Dict[str, List[str]]: Errori trovati per categoria
        """
        errors = {
            'typos': [],
            'sql_errors': [],
            'semantic_errors': []
        }

        try:
            # Analizza errori di battitura
            for pattern_name, pattern in self.error_patterns['typos'].items():
                if isinstance(pattern, str):
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        errors['typos'].append(f"{pattern_name}: {match.group()}")
                else:
                    for old, new in pattern:
                        if old in text.lower():
                            errors['typos'].append(f"Possible swap: {old} -> {new}")

            # Analizza errori SQL
            for pattern_name, pattern in self.error_patterns['sql_errors'].items():
                matches = re.finditer(pattern, text)
                for match in matches:
                    errors['sql_errors'].append(f"{pattern_name}: {match.group()}")

            # Analizza errori semantici
            for pattern_name, pattern in self.error_patterns['semantic_errors'].items():
                if re.search(pattern, text, re.IGNORECASE):
                    errors['semantic_errors'].append(pattern_name)

            return errors

        except Exception as e:
            self.logger.error(f"Errore nell'analisi dei pattern: {e}")
            return errors

    def get_correction_confidence(self, original: str, corrected: str) -> float:
        """
        Calcola il livello di confidenza per una correzione

        Args:
            original (str): Testo originale
            corrected (str): Testo corretto

        Returns:
            float: Livello di confidenza (0-1)
        """
        try:
            # Calcola la similarità tra le stringhe
            base_similarity = SequenceMatcher(None, original, corrected).ratio()

            # Calcola la frequenza relativa della correzione
            freq = self.error_frequency.get((original, corrected), 0)
            max_freq = max(self.error_frequency.values()) if self.error_frequency else 1
            freq_factor = freq / max_freq

            # Combina i fattori
            confidence = (base_similarity * 0.7) + (freq_factor * 0.3)

            return min(1.0, confidence)

        except Exception as e:
            self.logger.error(f"Errore nel calcolo della confidenza: {e}")
            return 0.0

    def get_advanced_suggestions(self, query: str) -> Dict[str, Any]:
        """
        Fornisce suggerimenti avanzati per il miglioramento della query

        Args:
            query (str): Query da analizzare

        Returns:
            Dict[str, Any]: Suggerimenti avanzati
        """
        suggestions = {
            'optimization': [],
            'security': [],
            'style': [],
            'alternatives': []
        }

        try:
            # Suggerimenti per ottimizzazione
            if 'select *' in query.lower():
                suggestions['optimization'].append({
                    'issue': 'SELECT * usage',
                    'description': 'Specificare le colonne esplicitamente migliora le performance',
                    'example': query.replace('select *', 'SELECT column1, column2')
                })

            # Suggerimenti per sicurezza
            if re.search(r'--', query) or re.search(r'/\*.*\*/', query):
                suggestions['security'].append({
                    'issue': 'Comment in query',
                    'description': 'Evitare commenti nelle query di produzione',
                    'risk_level': 'medium'
                })

            # Suggerimenti di stile
            if not query.upper().startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE')):
                suggestions['style'].append({
                    'issue': 'Keyword case',
                    'description': 'Usa maiuscole per le keywords SQL',
                    'example': query.upper()
                })

            # Query alternative
            if 'where' in query.lower():
                suggestions['alternatives'].append({
                    'type': 'Index usage',
                    'description': 'Considera l\'uso di un indice',
                    'example': f"CREATE INDEX idx_name ON table_name (column_name)"
                })

            return suggestions

        except Exception as e:
            self.logger.error(f"Errore nella generazione dei suggerimenti avanzati: {e}")
            return suggestions