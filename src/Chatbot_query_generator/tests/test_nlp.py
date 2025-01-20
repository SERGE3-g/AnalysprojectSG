# tests/test_nlp.py
import unittest
from app.nlp import NLPProcessor


class TestNLPProcessor(unittest.TestCase):
    def setUp(self):
        """Inizializza il processore NLP prima di ogni test"""
        self.nlp = NLPProcessor()

    def test_process_text(self):
        """Testa l'elaborazione base del testo"""
        text = "Il tuo testo qui"
        results = self.nlp.process_text(text)

        self.assertIsInstance(results, dict)
        self.assertIn('entities', results)
        self.assertIn('tokens', results)
        self.assertIn('pos_tags', results)

    def test_keyword_extraction(self):
        """Testa l'estrazione delle keywords"""
        text = "Il tuo testo qui"
        keywords = self.nlp.extract_keywords(text, top_n=5)

        self.assertIsInstance(keywords, list)
        self.assertLessEqual(len(keywords), 5)
        for keyword in keywords:
            self.assertIsInstance(keyword, tuple)
            self.assertEqual(len(keyword), 2)

    def test_similarity_analysis(self):
        """Testa l'analisi di similarità"""
        text1 = "primo testo"
        text2 = "secondo testo"
        similarity = self.nlp.similarity_analysis(text1, text2)

        self.assertIsInstance(similarity, float)
        self.assertGreaterEqual(similarity, 0)
        self.assertLessEqual(similarity, 1)

    def test_query_intent(self):
        """Testa il riconoscimento dell'intento"""
        text = "trova tutti i clienti di Roma"
        intent = self.nlp.get_query_intent(text)

        self.assertIsInstance(intent, dict)
        self.assertIn('primary_intent', intent)
        self.assertIn('confidence', intent)


if __name__ == '__main__':
    unittest.main()