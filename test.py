import arxiv

from urllib.request import urlretrieve
import os

def telecharger_pdf(papier, dirpath="./papiers_ia"):
    os.makedirs(dirpath, exist_ok=True)
    arxiv_id = papier.entry_id.split("/")[-1]
    filepath = os.path.join(dirpath, f"{arxiv_id}.pdf")
    urlretrieve(papier.pdf_url, filepath)
    return filepath



def recuperer_derniers_papiers_ia(nombre_papiers=1):
    client = arxiv.Client()

    recherche = arxiv.Search(
        query="cat:cs.AI",  # catégorie officielle arXiv "Intelligence Artificielle"
        max_results=nombre_papiers,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    resultats = list(client.results(recherche))
    print(resultats)
    return resultats

def afficher_papiers(papiers):
    for i, papier in enumerate(papiers, start=1):
        print(f"\n{'='*80}")
        print(f"[{i}] {papier.title}")
        print(f"{'='*80}")
        print(f"Auteurs   : {', '.join(a.name for a in papier.authors)}")
        print(f"Date      : {papier.published.strftime('%d/%m/%Y')}")
        print(f"Catégories: {', '.join(papier.categories)}")
        print(f"PDF       : {papier.pdf_url}")
        print(f"Résumé    : {papier.summary[:250].replace(chr(10), ' ')}...")

if __name__ == "__main__":
    papiers = recuperer_derniers_papiers_ia(nombre_papiers=1)
    afficher_papiers(papiers)

    # Optionnel : télécharger tous les PDF dans un dossier local
    for papier in papiers:
        chemin = telecharger_pdf(papier)
        print(f"Téléchargé : {chemin}")