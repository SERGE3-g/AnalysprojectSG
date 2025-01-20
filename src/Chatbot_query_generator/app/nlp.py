from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqGeneration
import spacy
from typing import Dict, List, Tuple, Optional, Union
import logging
from spacy.tokens import Doc
from spacy.language import Language
import numpy as np
from collections import Counter
from langdetect import detect
from textblob import TextBlob
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from gensim.summarization import summarize
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
import nltk


class CustomSentencizer:
    def __init__(self):
        pass

    def __call__(self, doc: Doc) -> Doc:
        for sent in doc.sents:
            for token in sent:
                if token.text in ['.', '!', '?']:
                    doc[token.i].is_sent_start = True
        return doc


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
            # Carica i modelli per varie funzionalità
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="dbmdz/bert-base-italian-uncased-sentiment"
            )
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn"
            )
            self.translator = pipeline(
                "translation",
                model="Helsinki-NLP/opus-mt-it-en"
            )
            self.question_answerer = pipeline(
                "question-answering",
                model="deepset/roberta-base-squad2"
            )

            # Download necessari NLTK data
            try:
                nltk.data.find('tokenizers/punkt')
            except LookupError:
                nltk.download('punkt')
            try:
                nltk.data.find('corpora/stopwords')
            except LookupError:
                nltk.download('stopwords')

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
        """Elabora il testo utilizzando spaCy e estrae informazioni linguistiche."""
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
        """Analisi approfondita del sentimento con vari aspetti."""
        try:
            bert_result = self.sentiment_analyzer(text)[0]

            # Analisi aggiuntiva con TextBlob
            blob = TextBlob(text)

            return {
                'bert_sentiment': {
                    'label': bert_result['label'],
                    'score': bert_result['score'],
                    'confidence': self._calculate_confidence(bert_result['score'])
                },
                'textblob_sentiment': {
                    'polarity': blob.sentiment.polarity,
                    'subjectivity': blob.sentiment.subjectivity
                },
                'emotion_analysis': self._analyze_emotions(text),
                'aspect_based': self._analyze_aspect_based_sentiment(text)
            }
        except Exception as e:
            self.logger.error(f"Errore nell'analisi del sentimento: {str(e)}")
            raise

    def _analyze_emotions(self, text: str) -> Dict:
        """Analisi delle emozioni nel testo."""
        emotion_keywords = {
            'joy': ['felice', 'contento', 'gioioso', 'entusiasta'],
            'anger': ['arrabbiato', 'furioso', 'irritato'],
            'sadness': ['triste', 'malinconico', 'depresso'],
            'fear': ['spaventato', 'terrorizzato', 'ansioso'],
            'surprise': ['sorpreso', 'stupito', 'meravigliato']
        }

        text_lower = text.lower()
        emotions = {}
        for emotion, keywords in emotion_keywords.items():
            count = sum(1 for word in keywords if word in text_lower)
            emotions[emotion] = count / len(text.split())

        return emotions

    def _analyze_aspect_based_sentiment(self, text: str) -> List[Dict]:
        """Analisi del sentimento basata sugli aspetti."""
        try:
            doc = self.nlp(text)
            aspects = []

            for sent in doc.sents:
                for chunk in sent.noun_chunks:
                    # Analizza il sentimento intorno all'aspetto
                    context_start = max(0, chunk.start - 5)
                    context_end = min(len(doc), chunk.end + 5)
                    context = doc[context_start:context_end].text

                    sentiment = TextBlob(context).sentiment

                    aspects.append({
                        'aspect': chunk.text,
                        'sentiment': sentiment.polarity,
                        'context': context
                    })

            return aspects
        except Exception as e:
            self.logger.error(f"Errore nell'analisi del sentimento basata sugli aspetti: {str(e)}")
            return []

    def summarize_text(self, text: str, max_length: int = 130, min_length: int = 30) -> str:
        """Genera un riassunto del testo."""
        try:
            summary = self.summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
            return summary[0]['summary_text']
        except Exception as e:
            self.logger.error(f"Errore nella generazione del riassunto: {str(e)}")
            raise

    def answer_question(self, context: str, question: str) -> Dict:
        """Risponde a domande basate sul contesto."""
        try:
            result = self.question_answerer(question=question, context=context)
            return {
                'answer': result['answer'],
                'score': result['score'],
                'start': result['start'],
                'end': result['end']
            }
        except Exception as e:
            self.logger.error(f"Errore nella risposta alla domanda: {str(e)}")
            raise

    def detect_language(self, text: str) -> Dict:
        """Rileva la lingua del testo con confidenza."""
        try:
            lang = detect(text)
            # Calcola una confidenza approssimativa
            confidence = len(re.findall(r'\b\w+\b', text)) / 100.0
            confidence = min(max(confidence, 0.1), 0.99)

            return {
                'language': lang,
                'confidence': confidence,
                'is_reliable': confidence > 0.5
            }
        except Exception as e:
            self.logger.error(f"Errore nel rilevamento della lingua: {str(e)}")
            raise

    def translate_text(self, text: str, target_lang: str = "en") -> str:
        """Traduce il testo nella lingua specificata."""
        try:
            translation = self.translator(text, target_language=target_lang)
            return translation[0]['translation_text']
        except Exception as e:
            self.logger.error(f"Errore nella traduzione: {str(e)}")
            raise

    def extract_topics(self, text: str, num_topics: int = 5) -> List[Dict]:
        """Estrae i principali topic dal testo."""
        try:
            # Preprocessing
            doc = self.nlp(text)
            sentences = [sent.text for sent in doc.sents]

            # Calcola TF-IDF
            vectorizer = TfidfVectorizer(max_features=100, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(sentences)

            # Estrai i termini più importanti per topic
            feature_names = vectorizer.get_feature_names_out()
            scores = np.mean(tfidf_matrix.toarray(), axis=0)
            top_indices = np.argsort(scores)[-num_topics:]

            topics = []
            for idx in reversed(top_indices):
                topics.append({
                    'topic': feature_names[idx],
                    'score': float(scores[idx]),
                    'related_terms': self._find_related_terms(feature_names[idx], text)
                })

            return topics
        except Exception as e:
            self.logger.error(f"Errore nell'estrazione dei topic: {str(e)}")
            raise

    def _find_related_terms(self, term: str, text: str, num_terms: int = 3) -> List[str]:
        """Trova termini correlati a una parola chiave."""
        doc = self.nlp(text)
        term_token = self.nlp(term)[0]

        similarities = []
        for token in doc:
            if not token.is_stop and not token.is_punct and token.text.lower() != term.lower():
                similarities.append((token.text, token.similarity(term_token)))

        return [word for word, _ in sorted(similarities, key=lambda x: x[1], reverse=True)[:num_terms]]

    def analyze_readability(self, text: str) -> Dict:
        """Analizza la leggibilità del testo."""
        try:
            sentences = sent_tokenize(text)
            words = word_tokenize(text)

            # Calcola statistiche base
            num_sentences = len(sentences)
            num_words = len(words)
            num_chars = len(text)

            # Calcola indici di leggibilità
            avg_sentence_length = num_words / num_sentences if num_sentences > 0 else 0
            avg_word_length = num_chars / num_words if num_words > 0 else 0

            # Calcola indice Gulpease (specifico per l'italiano)
            gulpease = 89 + (300 * num_sentences - 10 * len(text)) / num_words if num_words > 0 else 0

            return {
                'statistics': {
                    'num_sentences': num_sentences,
                    'num_words': num_words,
                    'num_chars': num_chars,
                    'avg_sentence_length': round(avg_sentence_length, 2),
                    'avg_word_length': round(avg_word_length, 2)
                },
                'readability_scores': {
                    'gulpease_index': round(gulpease, 2),
                    'complexity_level': self._get_complexity_level(gulpease)
                },
                'text_structure': {
                    'paragraph_count': text.count('\n\n') + 1,
                    'sentence_types': self._analyze_sentence_types(sentences)
                }
            }
        except Exception as e:
            self.logger.error(f"Errore nell'analisi della leggibilità: {str(e)}")
            raise

    def _get_complexity_level(self, gulpease_score: float) -> str:
        """Determina il livello di complessità basato sull'indice Gulpease."""
        if gulpease_score >= 80:
            return "molto facile"
        elif gulpease_score >= 60:
            return "facile"
        elif gulpease_score >= 40:
            return "medio"
        else:
            return "difficile"

    def _analyze_sentence_types(self, sentences: List[str]) -> Dict:
        """Analizza i tipi di frasi nel testo."""
        types = {
            'dichiarative': 0,
            'interrogative': 0,
            'esclamative': 0,
            'imperative': 0
        }

        for sentence in sentences:
            if '?' in sentence:
                types['interrogative'] += 1
            elif '!' in sentence:
                types['esclamative'] += 1
            elif any(word in sentence.lower() for word in ['per favore', 'fai', 'vai', 'dimmi']):
                types['imperative'] += 1
            else:
                types['dichiarative'] += 1

        return types

    def extract_patterns(self, text: str) -> Dict:
        """Estrae pattern linguistici comuni dal testo."""
        try:
            doc = self.nlp(text)
            patterns = {
                'named_entities': self._categorize_entities(doc),
                'phrasal_patterns': self._extract_phrasal_patterns(doc),
                'syntax_patterns': self._analyze_syntax_patterns(doc)
            }
            return patterns
        except Exception as e:
            self.logger.error(f"Errore nell'estrazione dei pattern: {str(e)}")
            raise

    def _analyze_syntax_patterns(self, doc: Doc) -> Dict[str, List[str]]:
        """Analizza i pattern sintattici nel testo."""
        patterns = {
            'strutture_base': [],  # Strutture sintattiche di base
            'subordinate': [],  # Frasi subordinate
            'coordinate': [],  # Frasi coordinate
            'strutture_complesse': []  # Strutture sintattiche complesse
        }

        for sent in doc.sents:
            # Identifica la struttura base della frase
            root = [token for token in sent if token.dep_ == 'ROOT'][0]
            base_structure = self._get_base_structure(root)
            patterns['strutture_base'].append(base_structure)

            # Identifica subordinate
            for token in sent:
                if token.dep_ in ['advcl', 'acl', 'relcl']:
                    patterns['subordinate'].append(self._get_clause_text(token))

                # Identifica coordinate
                elif token.dep_ == 'conj' and token.head.pos_ == 'VERB':
                    patterns['coordinate'].append(f"{token.head.text} e {token.text}")

                # Identifica strutture complesse
                elif token.dep_ in ['ccomp', 'xcomp']:
                    patterns['strutture_complesse'].append(self._get_clause_text(token))

        return patterns

    def _get_base_structure(self, root_token: Token) -> str:
        """Estrae la struttura base di una frase partendo dal suo nodo radice."""
        subject = ""
        object = ""

        for child in root_token.children:
            if child.dep_ == 'nsubj':
                subject = child.text
            elif child.dep_ == 'obj':
                object = child.text

        return f"{subject} {root_token.text} {object}".strip()

    def _get_clause_text(self, token: Token) -> str:
        """Estrae il testo di una clausola partendo dal suo token principale."""
        clause_tokens = [token]
        for child in token.subtree:
            clause_tokens.append(child)

        clause_tokens.sort(key=lambda x: x.i)
        return ' '.join([t.text for t in clause_tokens])

    def _categorize_entities(self, doc: Doc) -> Dict[str, List[str]]:
        """Categorizza le entità nominate trovate nel testo."""
        entities = {
            'persone': [],
            'luoghi': [],
            'organizzazioni': [],
            'date': [],
            'altro': []
        }

        for ent in doc.ents:
            if ent.label_ in ['PERSON', 'PER']:
                entities['persone'].append(ent.text)
            elif ent.label_ in ['LOC', 'GPE']:
                entities['luoghi'].append(ent.text)
            elif ent.label_ in ['ORG']:
                entities['organizzazioni'].append(ent.text)
            elif ent.label_ in ['DATE']:
                entities['date'].append(ent.text)
            else:
                entities['altro'].append((ent.text, ent.label_))

        return entities

    def _extract_phrasal_patterns(self, doc: Doc) -> Dict[str, List[str]]:
        """Estrae pattern fraseologici comuni."""
        patterns = {
            'soggetto_verbo': [],
            'verbo_oggetto': [],
            'preposizionali': [],
            'modificatori': []
        }

        for token in doc:
            # Pattern soggetto-verbo
            if token.dep_ == 'nsubj' and token.head.pos_ == 'VERB':
                patterns['soggetto_verbo'].append(f"{token.text} {token.head.text}")

            # Pattern verbo-oggetto
            if token.dep_ == 'obj' and token.head.pos_ == 'VERB':
                patterns['verbo_oggetto'].append(f"{token.head.text} {token.text}")

            # Pattern preposizionali
            if token.dep_ == 'prep' and token.head.pos_ == 'VERB':
                pobj = next((child for child in token.children if child.dep_ == 'pobj'), None)
                if pobj:
                    patterns['preposizionali'].append(f"{token.head.text} {token.text} {pobj.text}")

            # Pattern con modificatori (aggettivi e avverbi)
            if token.dep_ == 'amod' or token.dep_ == 'advmod':
                patterns['modificatori'].append(f"{token.text} {token.head.text}")

        return patterns