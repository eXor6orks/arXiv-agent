# core/ingest.py
from core.latex import load_latex, remove_source
from core.pdf import telecharger_pdf, load_pdf, remove_pdf


def load_paper(result, sources_dir="./sources", pdf_dir="./papiers_ia"):
    """
    Essaie LaTeX en premier. Si aucune source n'est disponible, bascule sur le PDF.
    Retourne (docs, source_type, cleanup) où cleanup() supprime les fichiers temporaires.
    """
    try:
        docs, tarball_path, extract_dir = load_latex(result, sources_dir=sources_dir)
        cleanup = lambda: remove_source(tarball_path, extract_dir)
        return docs, "latex", cleanup

    except RuntimeError:
        pass  # pas de source LaTeX -> fallback PDF

    filepath = telecharger_pdf(result, dirpath=pdf_dir)
    docs = load_pdf(filepath)

    # métadonnées cohérentes avec la branche LaTeX
    metadata = {
        "arxiv_id": result.get_short_id(),
        "title": result.title,
        "authors": ", ".join(a.name for a in result.authors),
        "published": result.published.isoformat(),
        "url": result.entry_id,
        "source_type": "pdf",
    }
    for doc in docs:
        doc.metadata.update(metadata)

    cleanup = lambda: remove_pdf(filepath)
    return docs, "pdf", cleanup