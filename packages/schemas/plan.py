from __future__ import annotations

from uuid import UUID
from pydantic import BaseModel, Field


class SearchTask(BaseModel):
    task_id: UUID
    question: str
    target_sources: list[str]
    query_templates: list[str]
    inclusion_criteria: list[str] = Field(default_factory=list)
    exclusion_criteria: list[str] = Field(default_factory=list)
    priority: int = 1


class StoppingConditions(BaseModel):
    min_high_confidence_sourceS: int = 3
    max_iterations: int = 1
    stop_when_subquestions_covered_ratio: float = 0.5


class Plan(BaseModel):
    plan_id: UUID
    session_id: UUID
    objective: str
    sub_questions: list[str]
    search_tasks: list[SearchTask]
    stopping_conditions: StoppingConditions
    