from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.services.embedding_service import embed_text
from app.services.concept_embedding_service import ConceptEmbeddingService
from app.services.similarity import cosine_similarity
from app.models.search_api import SearchResponse, SearchResult
from app.services.query_log_service import QueryLogService
from app.models.query_log_api import QueryLogCreate

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResponse)
def search(
    query: str = Query(..., min_length=1, max_length=2000),
    limit: int = Query(default=5, ge=1, le=50),
    db: Session = Depends(get_db),
):
    qvec = embed_text(query)

    rows = ConceptEmbeddingService(db).list_active()

    scored = []
    for r in rows:
        score = cosine_similarity(qvec, r.vector)
        scored.append((score, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:limit]

    results = [
        SearchResult(
            concept_id=r.concept_id,
            version=r.version,
            name=r.name,
            domain=r.domain,
            score=float(score),
        )
        for score, r in top
    ]

    # Log the search query (M4 integration)
    QueryLogService(db).log_query(
        QueryLogCreate(
            query_text=query,
            source="search",
            metadata_json={
                "limit": limit,
                "matches": [{"concept_id": x.concept_id, "score": x.score} for x in results],
            },
        )
    )

    return SearchResponse(query=query, results=results)