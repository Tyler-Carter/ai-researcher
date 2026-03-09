from __future__ import annotations

from uuid import UUID
from pydantic import BaseModel, Field


class SourceSummary(BaseModel):
    note_id: UUID
    source_id: UUID
    concise_summary: str
    key_claims: list[str] = Field(default_factory=list)
    methods: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    counterpoints: list[str] = Field(default_factory=list)
    evidence_snippets: list[dict[str, str]] = Field(default_factory=list)
    citation_anchor: str
    