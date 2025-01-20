from transformers import pipeline
import spacy
from typing import Dict, List, Tuple, Optional
import logging
from spacy.tokens import Doc
from spacy.language import Language
import numpy as np
from collections import Counter


class NLPProcessor:
    def __init__(self, model_name: str = "it_core_news_sm"):
        """
        Inizializza il processore NLP con modelli specifici.

        Args:
            model_name (str): Nome del modello spaCy da caricare
        """
        self.logger = logging.getLogger(__name__)
        try:
            self.nlp = spacy.load(model_name)
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="dbmdz/bert-base-italian-uncased-sentiment"
            )
            self._setup_custom_components()
        except Exception as e:
            self.logger.error(f"Errore nell'inizializzazione di NLPProcessor: {str(e)}")
            raise

    def _setup_custom_components(self):
        """Configura componenti personalizzati per la pipeline spaCy"""
        if not Language.has_factory("custom_sentencizer"):
            @Language.factory("custom_sentencizer")
            def create_custom_sentencizer(nlp, name):
                return CustomSentencizer()

        if "custom_sentencizer" not in self.nlp.pipe_names:
            self.nlp.add_pipe("custom_sentencizer", before="parser")

    def process_text(self, text: str) -> Dict:
        """
        Elabora il testo utilizzando spaCy e estrae informazioni linguistiche.

        Args:
            text (str): Testo da analizzare

        Returns:
            Dict: Dizionario contenente le analisi linguistiche
        """
        try:
            doc = self.nlp(text)
            return {
                'entities': [(ent.text, ent.label_) for ent in doc.ents],
                'tokens': [token.text for token in doc],
                'pos_tags': [(token.text, token.pos_) for token in doc],
                'sentences': [str(sent) for sent in doc.sents],
                'noun_chunks': [chunk.text for chunk in doc.noun_chunks],
                'dependencies': [(token.text, token.dep_, token.head.text) for token in doc],
                'lemmas': [(token.text, token.lemma_) for token in doc]
            }
        except Exception as e:
            self.logger.error(f"Errore nell'elaborazione del testo: {str(e)}")
            raise

    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analizza il sentimento del testo utilizzando il modello BERT.

        Args:
            text (str): Testo da analizzare

        Returns:
            Dict: Risultato dell'analisi del sentimento
        """
        try:
            result = self.sentiment_analyzer(text)[0]
            return {
                'sentiment': result['label'],
                'score': result['score'],
                'confidence': self._calculate_confidence(result['score'])
            }
        except Exception as e:
            self.logger.error(f"Errore nell'analisi del sentimento: {str(e)}")
            raise

    def extract_keywords(self, text: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Estrae le parole chiave dal testo utilizzando TF-IDF.

        Args:
            text (str): Testo da analizzare
            top_n (int): Numero di parole chiave da estrarre

        Returns:
            List[Tuple[str, float]]: Lista di tuple (parola, score)
        """
        try:
            doc = self.nlp(text)
            words = [token.text for token in doc if not token.is_stop and not token.is_punct]
            word_freq = Counter(words)

            # Calcolo semplificato del TF-IDF
            max_freq = max(word_freq.values())
            word_scores = {
                word: (freq / max_freq) * (1 / (1 + words.count(word)))
                for word, freq in word_freq.items()
            }

            return sorted(word_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        except Exception as e:
            self.logger.error(f"Errore nell'estrazione delle keywords: {str(e)}")
            raise

    def similarity_analysis(self, text1: str, text2: str) -> float:
        """
        Calcola la similarità semantica tra due testi.

        Args:
            text1 (str): Primo testo
            text2 (str): Secondo testo

        Returns:
            float: Score di similarità (0-1)
        """
        try:
            doc1 = self.nlp(text1)
            doc2 = self.nlp(text2)
            return doc1.similarity(doc2)
        except Exception as e:
            self.logger.error(f"Errore nel calcolo della similarità: {str(e)}")
            raise

    def _calculate_confidence(self, score: float) -> str:
        """
        Calcola il livello di confidenza basato sullo score.

        Args:
            score (float): Score di confidenza

        Returns:
            str: Livello di confidenza (alto, medio, basso)
        """
        if score > 0.8:
            return "alto"
        elif score > 0.6:
            return "medio"
        else:
            return "basso"

    def get_query_intent(self, text: str) -> Dict:
        """
        Determina l'intento della query dell'utente.

        Args:
            text (str): Testo della query

        Returns:
            Dict: Informazioni sull'intento della query
        """
        try:
            doc = self.nlp(text.lower())

            # Parole chiave per ogni tipo di query
            intent_keywords = {
                'select': ['mostra', 'trova', 'cerca', 'visualizza', 'seleziona'],
                'insert': ['inserisci', 'aggiungi', 'crea', 'nuovo'],
                'update': ['aggiorna', 'modifica', 'cambia', 'sostituisci'],
                'delete': ['elimina', 'cancella', 'rimuovi', 'togli']
            }

            # Trova le corrispondenze
            matches = {
                intent: any(keyword in text.lower() for keyword in keywords)
                for intent, keywords in intent_keywords.items()
            }

            # Determina l'intento pr incipale
            primary_intent = max(matches.items(), key=lambda x: x[1])[0]

            return {
                'primary_intent': primary_intent,
                'confidence': self._calculate_confidence(0.7),  # Esempio di confidence
                'detected_actions': [k for k, v in matches.items() if v]
            }
        except Exception as e:
            self.logger.error(f"Errore nell'analisi dell'intento: {str(e)}")
            raise


class CustomSentencizer:
    """Componente personalizzato per la segmentazione delle frasi"""

    def __call__(self, doc: Doc) -> Doc:
        for i, token in enumerate(doc[:-1]):
            if token.text in [".", "!", "?"]:
                doc[i].is_sent_start = True
                if i + 1 < len(doc):
                    doc[i + 1].is_sent_start = True
        return doc
