from datetime import datetime, timezone

from core.arXiv import arXiv
from core.clean_text import clean
from core.ingest import load_paper
from core.chunck import chunk_par_phrases
from core.embedding import OllamaEmbedder
from core.Qdrant import Qdrant


def run_ingest(max_results: int = 20) -> int:
    """Récupère les derniers papiers arXiv et les indexe dans Qdrant.

    Retourne le nombre de papiers traités.
    """
    embedder = OllamaEmbedder()
    qdrant = Qdrant()
    qdrant.create_collection()

    ar = arXiv()
    res = ar._get_research(max_results=max_results)

    for result in res:
        arxiv_id, version = result.get_short_id().split("v")
        docs, source_type, cleanup = load_paper(result)
        print(f"{result.get_short_id()} -> {source_type}, {len(docs)} doc(s)")

        for d in docs:
            texte = clean(d.page_content)
            chunks = chunk_par_phrases(texte, max_mots=100, overlap_phrases=2)
            if not chunks:
                continue

            vecteurs = embedder.embed_documents(chunks)
            metadatas = [
                {
                    "arxiv_id": arxiv_id,
                    "version": int(version),
                    "title": result.title,
                    "authors": [a.name for a in result.authors],
                    "categories": result.categories,
                    "published": result.published.isoformat(),
                    "updated": result.updated.isoformat(),
                    "indexed_at": datetime.now(timezone.utc).isoformat(),
                    "pdf_url": result.pdf_url,
                    "source_type": source_type,
                    "section": d.metadata.get("section"),
                    "chunk_index": i,
                    "chunk_count": len(chunks),
                }
                for i in range(len(chunks))
            ]

            qdrant.upsert_chunks(chunks, vecteurs, metadatas)
            print(f"  -> {len(chunks)} chunks indexés ({d.metadata.get('section', 'full_text')})")

        cleanup()

    return len(res)
