from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from packages.orchestration.run_pipeline import PipelineArtifacts, run_pipeline

router = APIRouter(prefix="/research", tags=["research"])


class RunResearchRequest(BaseModel):
    query: str


class RunResearchResponse(BaseModel):
    session_id: str
    artifacts: PipelineArtifacts
    report_snapshot: str


@router.post("/run", response_model=RunResearchResponse)
def run_research(payload: RunResearchRequest) -> RunResearchResponse:
    artifacts = PipelineArtifacts.model_validate(run_pipeline(payload.query))
    return RunResearchResponse.model_validate(
        {
            "session_id": str(artifacts.session.session_id),
            "artifacts": artifacts,
            "report_snapshot": artifacts.report.answer,
        }
    )