# backend/app/tests/test_reasoning_chain_summary_model.py
from app.db.base import Base


def test_reasoning_chain_summary_table_registered():
    assert "reasoning_chain_summaries" in Base.metadata.tables