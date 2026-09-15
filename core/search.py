from core.embedding import OllamaEmbedder
from core.Qdrant import Qdrant

_embedder = None
_qdrant = None


def _get_clients():
    global _embedder, _qdrant
    if _embedder is None:
        _embedder = OllamaEmbedder()
    if _qdrant is None:
        _qdrant = Qdrant()
    return _embedder, _qdrant


def search(question: str, top_k: int = 5, query_filter=None) -> list[dict]:
    """Recherche les chunks les plus pertinents pour une question dans Qdrant.

    Retourne une liste de dicts {score, arxiv_id, title, section, texte, ...}
    triés par pertinence décroissante.
    """
    embedder, qdrant = _get_clients()
    vecteur = embedder.embed_query(question)
    resultats = qdrant.search(vecteur, top_k=top_k, query_filter=query_filter)

    return [
        {
            "score": point.score,
            **point.payload,
        }
        for point in resultats.points
    ]
