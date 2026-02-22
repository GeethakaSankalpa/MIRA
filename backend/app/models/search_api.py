from pydantic import BaseModel


class SearchResult(BaseModel):
    concept_id: str
    version: int
    name: str
    domain: str
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]