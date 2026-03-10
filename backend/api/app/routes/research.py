from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from packages.exports import build_html_report, build_markdown_report
from packages.orchestration.run_pipeline import PipelineArtifacts, run_pipeline
from packages.storage import load_pipeline_artifacts, save_export_artifact, save_pipeline_artifacts

router = APIRouter(prefix="/research", tags=["research"])


class RunResearchRequest(BaseModel):
    query: str


class RunResearchResponse(BaseModel):
    session_id: str
    artifacts: PipelineArtifacts
    report_snapshot: str


class ExportResearchResponse(BaseModel):
    session_id: str
    export_format: str
    file_path: str
    content: str


@router.post("/run", response_model=RunResearchResponse)
def run_research(payload: RunResearchRequest) -> RunResearchResponse:
    artifacts = PipelineArtifacts.model_validate(run_pipeline(payload.query))
    save_pipeline_artifacts(artifacts)

    return RunResearchResponse.model_validate(
        {
            "session_id": str(artifacts.session.session_id),
            "artifacts": artifacts,
            "report_snapshot": artifacts.report.answer,
        }
    )


@router.get("/{session_id}", response_model=RunResearchResponse)
def get_research_session(session_id: str) -> RunResearchResponse:
    artifacts = load_pipeline_artifacts(session_id)
    if artifacts is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return RunResearchResponse.model_validate(
        {
            "session_id": session_id,
            "artifacts": artifacts,
            "report_snapshot": artifacts.report.answer,
        }
    )


@router.get("/{session_id}/export/{export_format}", response_model=ExportResearchResponse)
def export_research_session(session_id: str, export_format: str) -> ExportResearchResponse:
    artifacts = load_pipeline_artifacts(session_id)
    if artifacts is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if export_format == "markdown":
        content = build_markdown_report(artifacts)
    elif export_format == "html":
        content = build_html_report(artifacts)
    else:
        raise HTTPException(status_code=400, detail="Unsupported export format. Use markdown or html.")

    export_path = save_export_artifact(session_id=session_id, export_format=export_format, content=content)
    return ExportResearchResponse(
        session_id=session_id,
        export_format=export_format,
        file_path=str(export_path),
        content=content,
    )
