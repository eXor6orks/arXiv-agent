from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SearchRequest(BaseModel):
    question: str
    top_k: int = 5


class SearchResultItem(BaseModel):
    score: float
    arxiv_id: str | None = None
    title: str | None = None
    section: str | None = None
    texte: str | None = None

    class Config:
        extra = "allow"


class IngestRequest(BaseModel):
    max_results: int = 20


class ConfigUpdateRequest(BaseModel):
    value: object


class UserCreateRequest(BaseModel):
    username: str
    password: str
    is_admin: bool = False


class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool
    created_at: str
