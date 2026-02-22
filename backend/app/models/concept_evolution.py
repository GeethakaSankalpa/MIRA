from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal


class ConceptEvolveRequest(BaseModel):
    """
    When evolving, we allow updating the content.
    In M3 we keep it simple: name/description/domain can be updated.
    """
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    domain: str = Field(..., min_length=1, max_length=100)


class ConceptVersion(BaseModel):
    concept_id: str
    name: str
    description: str
    domain: str
    version: int
    confidence: float
    status: Literal["active", "deprecated"]
    created_at: datetime
    updated_at: datetime


class ConceptHistoryResponse(BaseModel):
    """
    Returns versions newest → oldest.
    """
    versions: list[ConceptVersion]