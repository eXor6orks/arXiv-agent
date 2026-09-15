import pysbd

_seg = pysbd.Segmenter(language="en", clean=False)

def segmenter_phrases(texte: str) -> list[str]:
    return [p.strip() for p in _seg.segment(texte) if p.strip()]

def chunk_par_phrases(texte, max_mots=200, overlap_phrases=2):
    phrases = segmenter_phrases(texte)
    chunks, courant, compte = [], [], 0
    for phrase in phrases:
        n = len(phrase.split())
        if courant and compte + n > max_mots:
            chunks.append(" ".join(courant))
            courant = courant[-overlap_phrases:]  # on reprend les dernières phrases
            compte = sum(len(p.split()) for p in courant)
        courant.append(phrase)
        compte += n
    if courant:
        chunks.append(" ".join(courant))
    return chunks