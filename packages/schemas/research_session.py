from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field


class ResearchSession(BaseModel):
    session_id: UUID
    query: str
    depth_mode: str = "standard"
    domain_mode: str = "mixed"
    status: Literal["created", "running", "completed", "failed"] = "created"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    provider: str = "placeholder"
    model: str = "placeholder"
    run_mode: str = "mvp_scaffold"
    comparison_group_id: str | None = None
