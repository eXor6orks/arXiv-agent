# core/embedding.py
import math
import os
from ollama import Client


class OllamaEmbedder:
    """Client pour interroger un modele d'embedding via l'API Ollama (Docker)."""

    def __init__(self, model="nomic-embed-text", base_url=None):
        base_url = base_url or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.model = model
        self.client = Client(host=base_url)

    def embed_query(self, text):
        return self.client.embed(model=self.model, input=text).embeddings[0]

    def embed_documents(self, texts):
        return self.client.embed(model=self.model, input=texts).embeddings


def similarite_cosinus(a: list[float], b: list[float]) -> float:
    """Mesure la proximité de deux vecteurs : 1 identique, 0 sans rapport."""
    produit = sum(x * y for x, y in zip(a, b))
    norme_a = math.sqrt(sum(x * x for x in a))
    norme_b = math.sqrt(sum(y * y for y in b))
    if norme_a == 0 or norme_b == 0:
        return 0.0
    return produit / (norme_a * norme_b)


def indexer(embedder: OllamaEmbedder, textes: list[str]) -> list[dict]:
    """Vectorise une liste de textes en documents prêts pour la recherche."""
    vecteurs = embedder.embed_documents(textes)
    return [{"texte": t, "vecteur": v} for t, v in zip(textes, vecteurs)]


def rechercher(embedder: OllamaEmbedder, question: str, corpus: list[dict], k: int = 3) -> list[dict]:
    """Classe les documents du corpus par similarité avec la question."""
    v_question = embedder.embed_query(question)
    classes = sorted(
        corpus,
        key=lambda doc: similarite_cosinus(v_question, doc["vecteur"]),
        reverse=True,
    )
    return classes[:k]
