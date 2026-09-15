from core.db import get_config_value

DEFAULTS = {
    "ENVIRONMENT": 0,
    "DOWNLOAD_PDF": False,
    "ARXIV_RESEARCH_QUERY": ["cat:cs.AI"],
    "EMBEDDING_MODEL": "nomic-embed-text",
    "EMBEDDING_DIMENSION": {
        "nomic-embed-text": 768
    },
    "COLLECTION": "documentation",
}


def get_config(key: str):
    """Lit une valeur de config depuis la DB, avec repli sur DEFAULTS si absente/DB indisponible."""
    try:
        value = get_config_value(key)
    except Exception:
        value = None
    if value is None:
        return DEFAULTS.get(key)
    return value
