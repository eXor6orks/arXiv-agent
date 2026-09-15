from fastapi import APIRouter, Depends

from api.deps import get_current_user
from api.schemas import SearchRequest, SearchResultItem
from core.search import search

router = APIRouter(tags=["search"])


@router.post("/search", response_model=list[SearchResultItem])
def run_search(payload: SearchRequest, user: dict = Depends(get_current_user)):
    return search(payload.question, top_k=payload.top_k)
