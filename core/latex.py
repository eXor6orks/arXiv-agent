# core/latex.py
import os
import re
import glob
import shutil
import tarfile

import requests
from langchain_core.documents import Document
from pylatexenc.latex2text import LatexNodes2Text, MacroTextSpec, get_default_latex_context_db


def telecharger_source(result, dirpath="./sources"):
    """Télécharge l'archive source LaTeX (.tar.gz) d'un papier arXiv."""
    os.makedirs(dirpath, exist_ok=True)
    arxiv_id = result.get_short_id()
    url = f"https://arxiv.org/src/{arxiv_id}"
    filepath = os.path.join(dirpath, f"{arxiv_id}.tar.gz")

    resp = requests.get(url, headers={"User-Agent": "arxiv-agent/1.0"})
    if resp.status_code == 404:
        raise RuntimeError(f"Pas de source LaTeX disponible pour {arxiv_id}")
    resp.raise_for_status()

    # Certains papiers n'ont pas de source LaTeX : arXiv répond alors 200 avec le PDF
    # (au lieu d'un 404), donc on vérifie le type réel du contenu renvoyé.
    if resp.headers.get("Content-Type") != "application/gzip":
        raise RuntimeError(f"Pas de source LaTeX disponible pour {arxiv_id} (reçu {resp.headers.get('Content-Type')})")

    with open(filepath, "wb") as f:
        f.write(resp.content)
    return filepath


def _extraire(tarball_path):
    extract_dir = tarball_path.replace(".tar.gz", "")
    os.makedirs(extract_dir, exist_ok=True)
    with tarfile.open(tarball_path) as tar:
        tar.extractall(extract_dir)
    return extract_dir


def _trouver_fichier_principal(extract_dir):
    """Le .tex racine est celui qui contient \\documentclass."""
    tex_files = glob.glob(os.path.join(extract_dir, "**/*.tex"), recursive=True)
    for f in tex_files:
        contenu = open(f, encoding="utf-8", errors="ignore").read()
        if "\\documentclass" in contenu:
            return f
    return tex_files[0] if tex_files else None


_INPUT_RE = re.compile(r"\\(?:input|include|subfile)\{([^}]+)\}")


def _retirer_commentaires(contenu):
    """Supprime tout ce qui suit un % non échappé, ligne par ligne."""
    lignes = contenu.split("\n")
    return "\n".join(re.sub(r"(?<!\\)%.*", "", ligne) for ligne in lignes)


def _resoudre_includes(tex_path, root_dir=None, _vus=None):
    """
    Résout récursivement \\input{}, \\include{} et \\subfile{}.
    """
    if _vus is None:
        _vus = set()

    tex_path = os.path.abspath(tex_path)
    if root_dir is None:
        root_dir = os.path.dirname(tex_path)

    if tex_path in _vus or not os.path.exists(tex_path):
        return ""
    _vus.add(tex_path)

    contenu = open(tex_path, encoding="utf-8", errors="ignore").read()
    contenu = _retirer_commentaires(contenu)

    def _remplacer(match):
        nom = match.group(1)
        if not nom.endswith(".tex"):
            nom += ".tex"

        chemin = os.path.join(root_dir, nom)
        if not os.path.exists(chemin):
            chemin = os.path.join(os.path.dirname(tex_path), nom)

        return _resoudre_includes(chemin, root_dir=root_dir, _vus=_vus)

    return _INPUT_RE.sub(_remplacer, contenu)


_DOCUMENT_RE = re.compile(r"\\begin\{document\}(.*)\\end\{document\}", re.DOTALL)


def _isoler_corps_document(contenu):
    """Coupe tout ce qui précède \\begin{document} (titleformat, newcommand, options de classe...)."""
    m = _DOCUMENT_RE.search(contenu)
    return m.group(1) if m else contenu


# --- Appariement d'accolades, réutilisé pour les titres de section et les macros de lien ---

def _extraire_argument(s, debut):
    """
    Depuis une position pointant sur '{', retourne (contenu_entre_accolades, position_après_la_fermante),
    en gérant correctement l'imbrication (ex: \\rtwo{...} ou \\texorpdfstring{...}{...} imbriqués).
    """
    profondeur = 0
    for i in range(debut, len(s)):
        if s[i] == "{":
            profondeur += 1
        elif s[i] == "}":
            profondeur -= 1
            if profondeur == 0:
                return s[debut + 1 : i], i + 1
    return s[debut + 1 :], len(s)


# --- Simplification des liens : évite le bug de pylatexenc sur \href malformé ---

def _remplacer_macro_texte(contenu, nom_macro, index_arg_garde=-1):
    """
    Remplace \\nom_macro{...}{...}... par l'un de ses arguments (par défaut le dernier).
    Utilisé pour \\href / \\url, dont le handler par défaut de pylatexenc plante (IndexError)
    sur certaines formes malformées ou redéfinies par le papier.
    """
    pattern = re.compile(r"\\" + re.escape(nom_macro) + r"\*?")
    resultat, pos = [], 0
    while True:
        m = pattern.search(contenu, pos)
        if not m:
            resultat.append(contenu[pos:])
            break
        resultat.append(contenu[pos:m.start()])
        i = m.end()
        args = []
        while i < len(contenu) and contenu[i] == "{":
            arg, i = _extraire_argument(contenu, i)
            args.append(arg)
        resultat.append(args[index_arg_garde] if args else "")
        pos = i
    return "".join(resultat)


def _simplifier_liens(contenu):
    """\\href{url}{texte} -> texte, \\url{x} -> x."""
    contenu = _remplacer_macro_texte(contenu, "href", index_arg_garde=-1)
    contenu = _remplacer_macro_texte(contenu, "url", index_arg_garde=-1)
    return contenu


# --- Tables/figures -> légende seule, avant conversion texte ---

_CAPTION_RE = re.compile(r"\\caption\{((?:[^{}]|\{[^{}]*\})*)\}")
_TABLE_RE = re.compile(r"\\begin\{table\*?\}.*?\\end\{table\*?\}", re.DOTALL)
_FIGURE_RE = re.compile(r"\\begin\{figure\*?\}.*?\\end\{figure\*?\}", re.DOTALL)


def _simplifier_tables_figures(contenu):
    """Remplace tables/figures entières par leur seule légende (le contenu brut n'a pas de valeur sémantique)."""
    def _remplacer(nom):
        def _fn(m):
            leg = _CAPTION_RE.search(m.group(0))
            texte = leg.group(1).strip() if leg else ""
            return f"\n[{nom}: {texte}]\n" if texte else "\n"
        return _fn
    contenu = _TABLE_RE.sub(_remplacer("Tableau"), contenu)
    contenu = _FIGURE_RE.sub(_remplacer("Figure"), contenu)
    return contenu


def _nettoyer_latex(contenu):
    """Retire le contenu image, simplifie liens/tables/figures, retire la bibliographie."""
    contenu = re.sub(r"\\includegraphics(\[[^\]]*\])?\{[^}]*\}", "", contenu)
    contenu = _simplifier_liens(contenu)
    contenu = _simplifier_tables_figures(contenu)
    contenu = re.sub(r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}", "", contenu, flags=re.DOTALL)
    return contenu


# --- Découpage par section, avec appariement d'accolades (gère \rtwo{...}, \texorpdfstring{...}{...}) ---

_SECTION_START_RE = re.compile(r"\\((?:sub){0,2}section)\*?")


def _nettoyer_titre(titre_brut):
    """Retire les enrobages \\rtwo{...}, \\texorpdfstring{...}{...} autour du vrai titre."""
    titre_brut = re.sub(r"\\texorpdfstring\{((?:[^{}]|\{[^{}]*\})*)\}\{[^}]*\}", r"\1", titre_brut)
    titre_brut = re.sub(r"\\[a-zA-Z]+\{((?:[^{}]|\{[^{}]*\})*)\}", r"\1", titre_brut)
    return titre_brut.strip()


def _decouper_par_section(contenu_latex: str):
    """Retourne une liste de (titre_section, latex_brut_de_la_section), sans la commande \\section{} en tête."""
    matches = list(_SECTION_START_RE.finditer(contenu_latex))
    if not matches:
        return [("full_text", contenu_latex)]

    segments = []
    if matches[0].start() > 0:
        segments.append(("preamble", contenu_latex[: matches[0].start()]))

    bornes = []
    for m in matches:
        titre_brut, fin_arg = _extraire_argument(contenu_latex, m.end())
        bornes.append((fin_arg, _nettoyer_titre(titre_brut)))

    for i, (fin_cmd, titre) in enumerate(bornes):
        fin_section = matches[i + 1].start() if i + 1 < len(matches) else len(contenu_latex)
        segments.append((titre, contenu_latex[fin_cmd:fin_section]))

    return segments


# --- Convertisseur configuré une seule fois (pas à chaque section) ---

def _contexte_sans_refs():
    db = get_default_latex_context_db()
    db.add_context_category(
        "refs_cites",
        prepend=True,
        macros=[
            MacroTextSpec("ref", simplify_repl=""),
            MacroTextSpec("eqref", simplify_repl=""),
            MacroTextSpec("cite", simplify_repl=""),
            MacroTextSpec("citep", simplify_repl=""),
            MacroTextSpec("citet", simplify_repl=""),
            MacroTextSpec("label", simplify_repl=""),
        ],
    )
    return db


_CONVERTISSEUR = LatexNodes2Text(latex_context=_contexte_sans_refs())


def _texte_de_secours(latex_section: str) -> str:
    """Fallback grossier si pylatexenc échoue malgré tout : retire les commandes LaTeX à la hache."""
    texte = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^{}]*\})*", " ", latex_section)
    return re.sub(r"[{}]", "", texte)


def load_latex(result, sources_dir="./sources"):
    """
    Télécharge + résout + nettoie + découpe par section + convertit en texte brut.
    Retourne (docs, tarball_path, extract_dir) — un Document par section.
    Une section dont la conversion échoue bascule sur un texte de secours plutôt que de faire échouer tout le papier.
    """
    arxiv_id = result.get_short_id()

    tarball_path = telecharger_source(result, dirpath=sources_dir)
    extract_dir = _extraire(tarball_path)

    main_tex = _trouver_fichier_principal(extract_dir)
    if main_tex is None:
        raise RuntimeError(f"Aucun .tex trouvé pour {arxiv_id}")

    contenu = _resoudre_includes(main_tex)
    contenu = _isoler_corps_document(contenu)
    contenu = _nettoyer_latex(contenu)

    meta_commune = {
        "arxiv_id": arxiv_id,
        "title": result.title,
        "authors": ", ".join(a.name for a in result.authors),
        "published": result.published.isoformat(),
        "url": result.entry_id,
        "source_type": "latex",
    }

    docs = []
    for titre, latex_section in _decouper_par_section(contenu):
        try:
            texte = _CONVERTISSEUR.latex_to_text(latex_section).strip()
        except Exception as e:
            print(f"[warn] conversion échouée pour {arxiv_id} / section '{titre}': {e}")
            texte = _texte_de_secours(latex_section).strip()

        if not texte:
            continue
        docs.append(Document(
            page_content=texte,
            metadata={**meta_commune, "section": titre},
        ))

    if not docs:
        raise RuntimeError(f"Conversion en texte vide pour {arxiv_id}")

    return docs, tarball_path, extract_dir


def remove_source(tarball_path, extract_dir=None):
    if os.path.exists(tarball_path):
        os.remove(tarball_path)
    if extract_dir and os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)