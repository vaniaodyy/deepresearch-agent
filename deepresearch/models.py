"""
Shared models for DeepResearch Agent.
"""

from datetime import datetime
from pydantic import BaseModel


class Source(BaseModel):
    """A research source."""
    url: str
    title: str
    snippet: str
    content: str | None = None
    source_type: str  # web, arxiv, reddit, github, news
    confidence: float = 0.0
    retrieved_at: datetime = datetime.now()
