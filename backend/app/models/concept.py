from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal


class ConceptCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    domain: str = Field(..., min_length=1, max_length=100)


class ConceptRead(BaseModel):
    concept_id: str
    name: str
    description: str
    domain: str
    version: int
    confidence: float
    status: Literal["active", "deprecated"]
    created_at: datetime
    updated_at: datetime