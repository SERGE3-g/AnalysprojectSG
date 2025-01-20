from typing import Dict, List, Optional
import logging
from datetime import datetime
import random


class MessageGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Template per i messaggi
        self.templates = {
            'greeting': [
                "Ciao! Come posso aiutarti oggi?",
                "Benvenuto! Cosa posso fare per te?",
                "Salve! Sono qui per aiutarti con le tue query."
            ],
            'error': [
                "Mi dispiace, si è verificato un errore: {error}",
                "Ops! Qualcosa è andato storto: {error}",
                "C'è stato un problema: {error}"
            ],
            'success': [
                "Perfetto! Ho generato la query richiesta.",
                "Ecco la query che ho creato per te.",
                "Ho completato la generazione della query."
            ],
            'clarification': [
                "Potresti specificare meglio cosa intendi con '{term}'?",
                "Non sono sicuro di aver capito '{term}'. Puoi spiegare meglio?",
                "Mi serve più contesto per '{term}'. Puoi fornire più dettagli?"
            ],
            'confirmation': [
                "Vuoi procedere con questa query?",
                "Confermi di voler eseguire questa operazione?",
                "Sei sicuro di voler procedere?"
            ]
        }

        # Emoticon per rendere i messaggi più amichevoli
        self.emoticons = {
            'happy': ['😊', '😃', '👍'],
            'sad': ['😔', '😕', '😢'],
            'thinking': ['🤔', '💭', '💡'],
            'warning': ['⚠️', '❗', '⚡'],
            'success': ['✅', '🎉', '🌟']
        }

    def generate_response(self, intent: str, context: Dict = None) -> str:
        """
        Genera una risposta basata sull'intento e il contesto

        Args:
            intent (str): Tipo di risposta da generare
            context (Dict, optional): Contesto per la risposta

        Returns:
            str: Risposta generata
        """
        try:
            if intent not in self.templates:
                self.logger.warning(f"Template non trovato per l'intent: {intent}")
                return "Mi dispiace, non so come rispondere a questo."

            # Seleziona un template casuale per l'intent
            template = random.choice(self.templates[intent])

            # Aggiunge emoticon appropriate
            if intent == 'success':
                emoticon = random.choice(self.emoticons['happy'])
            elif intent == 'error':
                emoticon = random.choice(self.emoticons['sad'])
            else:
                emoticon = ''

            # Formatta il template con il contesto
            if context:
                response = template.format(**context)
            else:
                response = template

            return f"{emoticon} {response}".strip()

        except Exception as e:
            self.logger.error(f"Errore nella generazione della risposta: {str(e)}")
            return "Mi dispiace, si è verificato un errore nella generazione della risposta."

    def generate_query_explanation(self, query: str) -> str:
        """
        Genera una spiegazione in linguaggio naturale di una query SQL

        Args:
            query (str): Query da spiegare

        Returns:
            str: Spiegazione della query
        """
        try:
            parts = query.lower().split()
            explanation = "Questa query "

            if query.lower().startswith('select'):
                explanation += "seleziona "
                # Analizza le colonne
                from_index = parts.index('from')
                columns = ' '.join(parts[1:from_index])
                explanation += f"i dati ({columns}) "
                # Analizza la tabella
                where_index = parts.index('where') if 'where' in parts else len(parts)
                table = ' '.join(parts[from_index + 1:where_index])
                explanation += f"dalla tabella {table}"
                # Analizza le condizioni
                if 'where' in parts:
                    conditions = ' '.join(parts[where_index + 1:])
                    explanation += f" con le condizioni: {conditions}"

            return explanation

        except Exception as e:
            self.logger.error(f"Errore nella generazione della spiegazione: {str(e)}")
            return "Non riesco a spiegare questa query."

    def generate_error_message(self, error_type: str, details: Dict = None) -> str:
        """
        Genera un messaggio di errore user-friendly

        Args:
            error_type (str): Tipo di errore
            details (Dict, optional): Dettagli dell'errore

        Returns:
            str: Messaggio di errore
        """
        try:
            base_messages = {
                'syntax': "C'è un errore di sintassi nella query",
                'connection': "Non riesco a connettermi al database",
                'permission': "Non hai i permessi necessari",
                'not_found': "Non ho trovato quello che cercavi",
                'validation': "I dati inseriti non sono validi"
            }

            message = base_messages.get(error_type, "Si è verificato un errore")

            if details:
                if 'field' in details:
                    message += f" nel campo '{details['field']}'"
                if 'reason' in details:
                    message += f": {details['reason']}"

            return f"{random.choice(self.emoticons['sad'])} {message}"

        except Exception as e:
            self.logger.error(f"Errore nella generazione del messaggio di errore: {str(e)}")
            return "Si è verificato un errore imprevisto."

    def generate_help_message(self, topic: Optional[str] = None) -> str:
        """
        Genera un messaggio di aiuto

        Args:
            topic (Optional[str]): Argomento specifico per l'aiuto

        Returns:
            str: Messaggio di aiuto
        """
        try:
            if topic:
                help_messages = {
                    'query': """
                        Per creare una query, puoi:
                        1. Selezionare il tipo di query (SELECT, INSERT, etc.)
                        2. Descrivere cosa vuoi fare in linguaggio naturale
                        3. Specificare le condizioni se necessario
                    """,
                    'syntax': """
                        La sintassi base delle query è:
                        - SELECT: SELECT colonne FROM tabella WHERE condizioni
                        - INSERT: INSERT INTO tabella (colonne) VALUES (valori)
                        - UPDATE: UPDATE tabella SET campo = valore WHERE condizioni
                        - DELETE: DELETE FROM tabella WHERE condizioni
                    """,
                    'examples': """
                        Esempi di comandi:
                        - "Trova tutti gli utenti di Roma"
                        - "Inserisci un nuovo prodotto"
                        - "Aggiorna il prezzo del prodotto 1"
                        - "Elimina gli ordini vecchi"
                    """
                }
                return help_messages.get(topic, "Mi dispiace, non ho informazioni su questo argomento.")
            else:
                return """
                    💡 Posso aiutarti a:
                    - Generare query SQL
                    - Spiegare le query
                    - Correggere errori di sintassi

                    Usa 'help <argomento>' per maggiori dettagli su:
                    - query: Come creare query
                    - syntax: Sintassi SQL
                    - examples: Esempi di utilizzo
                """

        except Exception as e:
            self.logger.error(f"Errore nella generazione del messaggio di aiuto: {str(e)}")
            return "Non riesco a generare il messaggio di aiuto al momento."