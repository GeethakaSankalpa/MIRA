from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class ConceptCreate(BaseModel):
    name: str
    description: str
    domain: str

class Concept(BaseModel):
    concept_id: str
    name: str
    description: str
    domain: str
    version: int
    confidence: float
    created_at: datetime
    updated_at: datetime
    status: str
