from typing import Dict, List, Tuple, Optional
import re
import logging
from collections import Counter
import spacy
from spacy.tokens import Doc, Token
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import wordnet
from nltk.tag import pos_tag


class GrammarAnalyzer:
    def __init__(self, language: str = 'it'):
        """
        Inizializza l'analizzatore grammaticale

        Args:
            language (str): Lingua da analizzare ('it' per italiano, 'en' per inglese)
        """
        self.logger = logging.getLogger(__name__)
        self.language = language

        # Carica il modello linguistico appropriato
        try:
            if language == 'it':
                self.nlp = spacy.load('it_core_news_sm')
            else:
                self.nlp = spacy.load('en_core_web_sm')
        except Exception as e:
            self.logger.error(f"Errore nel caricamento del modello linguistico: {str(e)}")
            raise ValueError(f"Modello linguistico non disponibile per {language}")

        # Regole grammaticali comuni
        self.common_errors = {
            'it': {
                'gli': r'\bgli\b(?!\s+[aeiou])',  # 'gli' seguito da consonante
                'un': r'\bun\b(?=\s+[aeiou])',  # 'un' seguito da vocale
                'hanno': r'\ba\b(?=\s+[aeiou])',  # 'a' seguito da vocale
            },
            'en': {
                'their': r'\btheir\b(?=\s+is\b|\s+are\b)',  # 'their' seguito da verbo
                'its': r'\bits\b(?=\s+[A-Z])',  # 'its' seguito da maiuscola
                'your': r'\byour\b(?=\s+are\b)',  # 'your' seguito da 'are'
            }
        }

    def analyze_text(self, text: str) -> Dict:
        """
        Analizza un testo fornendo statistiche e informazioni grammaticali

        Args:
            text (str): Testo da analizzare

        Returns:
            Dict: Dizionario contenente varie statistiche e analisi
        """
        try:
            # Preprocessamento del testo
            text = text.strip()
            if not text:
                raise ValueError("Il testo è vuoto")

            # Analisi base con spaCy
            doc = self.nlp(text)

            # Raccolta statistiche
            stats = {
                'num_sentences': len(list(doc.sents)),
                'num_words': len(doc),
                'num_chars': len(text),
                'avg_word_length': sum(len(token.text) for token in doc) / len(doc) if len(doc) > 0 else 0,
                'parts_of_speech': Counter(token.pos_ for token in doc),
                'named_entities': [(ent.text, ent.label_) for ent in doc.ents],
                'common_words': Counter(token.text.lower() for token in doc if not token.is_stop).most_common(10)
            }

            return stats

        except Exception as e:
            self.logger.error(f"Errore nell'analisi del testo: {str(e)}")
            raise ValueError("Errore nell'analisi del testo")

    def check_grammar(self, text: str) -> List[Dict]:
        """
        Controlla la grammatica del testo e identifica possibili errori

        Args:
            text (str): Testo da controllare

        Returns:
            List[Dict]: Lista di errori grammaticali trovati
        """
        try:
            errors = []
            doc = self.nlp(text)

            # Controllo regole specifiche per la lingua
            for error_type, pattern in self.common_errors[self.language].items():
                matches = re.finditer(pattern, text)
                for match in matches:
                    errors.append({
                        'type': error_type,
                        'position': match.start(),
                        'text': match.group(),
                        'context': text[max(0, match.start() - 20):min(len(text), match.end() + 20)]
                    })

            # Controllo accordi soggetto-verbo
            for sent in doc.sents:
                subject = None
                verb = None

                for token in sent:
                    if token.dep_ == 'nsubj':
                        subject = token
                    elif token.pos_ == 'VERB':
                        verb = token

                    if subject and verb:
                        if not self._check_agreement(subject, verb):
                            errors.append({
                                'type': 'subject_verb_agreement',
                                'position': verb.idx,
                                'text': f"{subject.text} {verb.text}",
                                'context': sent.text
                            })
                        subject = None
                        verb = None

            return errors

        except Exception as e:
            self.logger.error(f"Errore nel controllo grammaticale: {str(e)}")
            raise ValueError("Errore nel controllo grammaticale")

    def _check_agreement(self, subject: Token, verb: Token) -> bool:
        """
        Controlla l'accordo tra soggetto e verbo

        Args:
            subject (Token): Token del soggetto
            verb (Token): Token del verbo

        Returns:
            bool: True se l'accordo è corretto, False altrimenti
        """
        try:
            if self.language == 'it':
                # Regole per l'italiano
                if subject.morph.get('Number') and verb.morph.get('Number'):
                    return subject.morph.get('Number')[0] == verb.morph.get('Number')[0]
            else:
                # Regole per l'inglese
                if subject.morph.get('Number') and verb.morph.get('Number'):
                    return subject.morph.get('Number')[0] == verb.morph.get('Number')[0]
            return True

        except Exception:
            return True  # In caso di dubbio, considera l'accordo corretto

    def suggest_corrections(self, text: str) -> List[Dict]:
        """
        Suggerisce correzioni per gli errori trovati nel testo

        Args:
            text (str): Testo da correggere

        Returns:
            List[Dict]: Lista di suggerimenti di correzione
        """
        try:
            corrections = []
            errors = self.check_grammar(text)

            for error in errors:
                suggestion = {
                    'original': error['text'],
                    'position': error['position'],
                    'suggestions': []
                }

                if error['type'] == 'subject_verb_agreement':
                    # Trova la forma corretta del verbo
                    subject, verb = error['text'].split()
                    doc = self.nlp(f"{subject} {verb}")
                    corrected_verb = self._get_corrected_verb(doc[0], doc[1])
                    if corrected_verb:
                        suggestion['suggestions'].append(corrected_verb)

                elif error['type'] in self.common_errors[self.language]:
                    # Suggerimenti per errori comuni
                    if self.language == 'it':
                        if error['type'] == 'gli':
                            suggestion['suggestions'].append('il')
                            suggestion['suggestions'].append('lo')
                        elif error['type'] == 'un':
                            suggestion['suggestions'].append("un'")
                    else:  # inglese
                        if error['type'] == 'their':
                            suggestion['suggestions'].append("there")
                            suggestion['suggestions'].append("they're")
                        elif error['type'] == 'its':
                            suggestion['suggestions'].append("it's")

                if suggestion['suggestions']:
                    corrections.append(suggestion)

            return corrections

        except Exception as e:
            self.logger.error(f"Errore nella generazione dei suggerimenti: {str(e)}")
            raise ValueError("Errore nella generazione dei suggerimenti")

    def _get_corrected_verb(self, subject: Token, verb: Token) -> Optional[str]:
        """
        Ottiene la forma corretta del verbo in base al soggetto

        Args:
            subject (Token): Token del soggetto
            verb (Token): Token del verbo

        Returns:
            Optional[str]: Forma corretta del verbo, se trovata
        """
        try:
            if self.language == 'it':
                # Implementazione base per l'italiano
                # Qui andrebbero aggiunte più regole di coniugazione
                return None
            else:
                # Regole base per l'inglese
                subj_num = subject.morph.get('Number')[0] if subject.morph.get('Number') else 'Sing'
                if verb.lemma_ == 'be':
                    if subj_num == 'Sing':
                        return 'is'
                    return 'are'
                elif subj_num == 'Sing':
                    return verb.lemma_ + 's'
                return verb.lemma_

        except Exception:
            return None

    def analyze_complexity(self, text: str) -> Dict:
        """
        Analizza la complessità del testo

        Args:
            text (str): Testo da analizzare

        Returns:
            Dict: Metriche di complessità
        """
        try:
            doc = self.nlp(text)
            sentences = list(doc.sents)

            # Calcolo metriche
            num_sentences = len(sentences)
            num_words = len([token for token in doc if not token.is_punct])
            num_complex_words = len([token for token in doc if len(token.text) > 6])

            # Indice di leggibilità
            if num_sentences > 0:
                avg_sentence_length = num_words / num_sentences
                percent_complex_words = (num_complex_words / num_words) * 100 if num_words > 0 else 0
                readability = 0.4 * (avg_sentence_length + percent_complex_words)
            else:
                readability = 0

            return {
                'avg_sentence_length': round(num_words / num_sentences, 2) if num_sentences > 0 else 0,
                'percent_complex_words': round((num_complex_words / num_words) * 100, 2) if num_words > 0 else 0,
                'readability_index': round(readability, 2),
                'vocabulary_richness': len(
                    set(token.text.lower() for token in doc if not token.is_punct)) / num_words if num_words > 0 else 0,
                'sentence_complexity': {
                    'simple': len([s for s in sentences if len(list(s)) < 10]),
                    'medium': len([s for s in sentences if 10 <= len(list(s)) <= 20]),
                    'complex': len([s for s in sentences if len(list(s)) > 20])
                }
            }

        except Exception as e:
            self.logger.error(f"Errore nell'analisi della complessità: {str(e)}")
            raise ValueError("Errore nell'analisi della complessità del testo")

    def find_synonyms(self, word: str) -> List[str]:
        """
        Trova i sinonimi di una parola

        Args:
            word (str): Parola di cui trovare i sinonimi

        Returns:
            List[str]: Lista di sinonimi
        """
        try:
            synonyms = set()

            if self.language == 'it':
                # Per l'italiano, usa il modello spaCy
                doc = self.nlp(word)
                for token in doc:
                    for lexeme in token.vocab.vectors:
                        if lexeme.is_lower == token.is_lower and lexeme.prob >= -15:
                            synonyms.add(lexeme.text)
            else:
                # Per l'inglese, usa WordNet
                for syn in wordnet.synsets(word):
                    for lemma in syn.lemmas():
                        if lemma.name() != word:
                            synonyms.add(lemma.name())

            return list(synonyms)[:10]  # Limita a 10 sinonimi

        except Exception as e:
            self.logger.error(f"Errore nella ricerca dei sinonimi: {str(e)}")
            raise ValueError("Errore nella ricerca dei sinonimi")


# Esempio di utilizzo
if __name__ == "__main__":
    # Inizializza l'analizzatore
    analyzer = GrammarAnalyzer(language='it')

    # Testo di esempio
    text = """
    Il gatto nero corre velocemente nel giardino.
    Gli alberi sono alti e verdi.
    Un automobile è parcheggiata davanti a casa.
    """

    try:
        # Analisi del testo
        print("=== Analisi del testo ===")
        stats = analyzer.analyze_text(text)
        print(f"Numero di frasi: {stats['num_sentences']}")
        print(f"Numero di parole: {stats['num_words']}")
        print(f"Parti del discorso più comuni: {dict(stats['parts_of_speech'])}")

        # Controllo grammaticale
        print("\n=== Errori grammaticali ===")
        errors = analyzer.check_grammar(text)
        for error in errors:
            print(f"Errore trovato: {error['type']} in '{error['text']}'")

        # Analisi della complessità
        print("\n=== Complessità del testo ===")
        complexity = analyzer.analyze_complexity(text)
        print(f"Indice di leggibilità: {complexity['readability_index']}")
        print(f"Distribuzione complessità frasi: {complexity['sentence_complexity']}")

    except Exception as e:
        print(f"Si è verificato un errore: {str(e)}")