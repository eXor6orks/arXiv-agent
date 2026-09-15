import os
from urllib.request import urlretrieve
from langchain_community.document_loaders import PyMuPDFLoader

def telecharger_pdf(papier, dirpath="./papiers_ia"):
    os.makedirs(dirpath, exist_ok=True)
    arxiv_id = papier.entry_id.split("/")[-1]
    filepath = os.path.join(dirpath, f"{arxiv_id}.pdf")
    urlretrieve(papier.pdf_url, filepath)
    return filepath

def load_pdf(filepath):
    loader = PyMuPDFLoader(filepath, mode="single")
    pages = loader.load()

    return pages

def remove_pdf(filepath):
    if os.path.exists(filepath):
        os.remove(filepath)