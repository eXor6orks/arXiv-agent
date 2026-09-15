"""Initialise la base (config + admin) au démarrage du conteneur.

Idempotent : peut être exécuté à chaque démarrage sans effet de bord si
la base existe déjà.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from config.config import DEFAULTS
from core.auth import hash_password
from core.db import create_user, get_user, init_db


def main():
    init_db(DEFAULTS)
    print("Base de données initialisée (config par défaut chargée si absente).")

    admin_username = os.environ.get("ADMIN_USERNAME")
    admin_password = os.environ.get("ADMIN_PASSWORD")

    if not admin_username or not admin_password:
        print("ADMIN_USERNAME / ADMIN_PASSWORD non définis : aucun admin créé.")
        return

    if get_user(admin_username) is not None:
        print(f"Admin '{admin_username}' déjà présent, rien à faire.")
        return

    create_user(admin_username, hash_password(admin_password), is_admin=True)
    print(f"Admin '{admin_username}' créé.")


if __name__ == "__main__":
    main()
