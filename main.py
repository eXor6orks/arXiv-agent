import argparse

from dotenv import load_dotenv

load_dotenv()

from config.config import DEFAULTS
from core.auth import hash_password
from core.db import create_user, get_user, init_db
from core.pipeline import run_ingest
from core.search import search


def cmd_ingest(args):
    n = run_ingest(max_results=args.max_results)
    print(f"{n} papier(s) traité(s).")


def cmd_search(args):
    resultats = search(args.question, top_k=args.top_k)
    for r in resultats:
        print(f"[{r['score']:.4f}] {r['arxiv_id']} - {r['title']} ({r.get('section')})")
        print(f"    {r['texte'][:200]}...")


def cmd_create_user(args):
    if get_user(args.username) is not None:
        print(f"L'utilisateur '{args.username}' existe déjà.")
        return
    create_user(args.username, hash_password(args.password), is_admin=args.admin)
    role = "admin" if args.admin else "standard"
    print(f"Utilisateur '{args.username}' créé ({role}).")


def build_parser():
    parser = argparse.ArgumentParser(description="arXiv agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_ingest = subparsers.add_parser("ingest", help="Récupère et indexe des papiers arXiv dans Qdrant")
    p_ingest.add_argument("--max-results", type=int, default=20)
    p_ingest.set_defaults(func=cmd_ingest)

    p_search = subparsers.add_parser("search", help="Recherche dans la base vectorielle")
    p_search.add_argument("question", help="Question à rechercher")
    p_search.add_argument("--top-k", type=int, default=5)
    p_search.set_defaults(func=cmd_search)

    p_user = subparsers.add_parser("create-user", help="Crée un utilisateur pour l'API (portail de gestion)")
    p_user.add_argument("username")
    p_user.add_argument("password")
    p_user.add_argument("--admin", action="store_true", help="Donne les droits d'administration")
    p_user.set_defaults(func=cmd_create_user)

    return parser


if __name__ == "__main__":
    init_db(DEFAULTS)
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
