from __future__ import annotations

from uuid import UUID
from pydantic import BaseModel, Field


class FinalReport(BaseModel):
    report_id: UUID
    session_id: UUID
    executive_summary: str
    answer: str
    key_findings: list[str] = Field(default_factory=list)
    competing_views: list[str] = Field(default_factory=list)
    contradiction_map: list[dict[str, str]] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    evidence_gaps: list[str] = Field(default_factory=list)
    source_table: list[dict] = Field(default_factory=list)
    appendix_trace_ref: str
    provider_summary: str = "placeholder"
    benchmark_summary: str = "mvp scaffold run"
    comparison_index: str = "n/a"
