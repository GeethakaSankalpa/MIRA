from __future__ import annotations

import logging
from functools import lru_cache
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """
    Loads the embedding model once per process.
    lru_cache prevents reloading on every request.
    """
    logger.info("Loading embedding model: %s", MODEL_NAME)
    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    """
    Convert text into a dense vector (embedding).
    This is used for semantic search.
    """
    model = _get_model()
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist()