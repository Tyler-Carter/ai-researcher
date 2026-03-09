from __future__ import annotations

from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field


class SourceEvaluation(BaseModel):
    evaluation_id: UUID
    source_id: UUID
    relevance_score: float
    credibility_score: float
    recency_score: float
    corroboration_score: float
    metadata_completeness_score: float
    overall_score: float
    reasoning: list[str] = Field(default_factory=list)
    decision: Literal["keep", "discard", "soft_keep"]
    flags: list[str] = Field(default_factory=list)
    provider: str = "placeholder"
    model: str = "placeholder"
    run_mode: str = "mvp_scaffold"
    latency_ms: int = 0
    token_usage: dict[str, int] = Field(default_factory=lambda: {"input": 0, "output": 0})
    estimated_cost_usd: float = 0.0
    schema_valid: bool = True
