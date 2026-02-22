from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


class QueryLogCreate(BaseModel):
    query_text: str = Field(..., min_length=1, max_length=4000)
    source: str = Field(..., min_length=1, max_length=200)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class QueryLogRead(BaseModel):
    id: str
    query_text: str
    source: str
    created_at: datetime
    metadata_json: dict