# examples/nlp_examples.py
from app.nlp import NLPProcessor


def main():
    """Esempi di utilizzo del processore NLP"""

    # Inizializza il processore
    nlp = NLPProcessor()

    print("1. Analisi completa del testo")
    print("-" * 50)
    results = nlp.process_text("Il tuo testo qui")
    print("Risultati dell'analisi:")
    for key, value in results.items():
        print(f"{key}: {value}\n")

    print("\n2. Estrazione delle keywords")
    print("-" * 50)
    keywords = nlp.extract_keywords("Il tuo testo qui", top_n=5)
    print("Keywords estratte:")
    for keyword, score in keywords:
        print(f"- {keyword}: {score:.2f}")

    print("\n3. Analisi di similarità")
    print("-" * 50)
    text1 = "primo testo"
    text2 = "secondo testo"
    similarity = nlp.similarity_analysis(text1, text2)
    print(f"Similarità tra '{text1}' e '{text2}': {similarity:.2f}")

    print("\n4. Riconoscimento intento")
    print("-" * 50)
    query = "trova tutti i clienti di Roma"
    intent = nlp.get_query_intent(query)
    print(f"Query: {query}")
    print(f"Intento rilevato: {intent['primary_intent']}")
    print(f"Confidenza: {intent['confidence']}")


if __name__ == "__main__":
    main()