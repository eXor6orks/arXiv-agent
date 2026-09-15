import arxiv
import os
import re
import glob
import tarfile
from pylatexenc.latex2text import LatexNodes2Text

from config.config import get_config

class arXiv :
    def __init__(self):
        self.client = arxiv.Client()

    def _get_research(self, max_results=5):
        query = " OR ".join(get_config("ARXIV_RESEARCH_QUERY"))
        return list(
            self.client.results(
                arxiv.Search(
                    query=query,
                    max_results=max_results,
                    sort_by=arxiv.SortCriterion.SubmittedDate,
                    sort_order=arxiv.SortOrder.Descending,
                )
            )
        )
