# backend/app/models/__init__.py
# Import all SQLAlchemy models here so they register with Base.metadata
from app.models.query_log import QueryLog  # noqa: F401
from app.models.concept_embedding import ConceptEmbedding  # noqa: F401
from app.models.reasoning_chain_summary import ReasoningChainSummary  # noqa: F401