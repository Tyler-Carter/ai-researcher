from __future__ import annotations

from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field


class Source(BaseModel):
    source_id: UUID
    session_id: UUID
    title: str
    url: str
    canonical_url: str
    authors: list[str] = Field(default_factory=list)
    publisher_or_venue: str = ""
    published_date: date | None = None
    source_type: str = "web"
    doi: str | None = None
    arxiv_id: str | None = None
    openalex_id: str | None = None
    semantic_scholar_id: str | None = None
    abstract: str | None = None
    retrieved_at: datetime = Field(default_factory=datetime.now)
    fulltext_available: bool = False
    raw_payload: dict = Field(default_factory=dict)
