from __future__ import annotations

import json
from pathlib import Path

from packages.orchestration.run_pipeline import PipelineArtifacts

_STORE_DIR = Path("backend/data/sessions")


def save_pipeline_artifacts(artifacts: PipelineArtifacts) -> Path:
    _STORE_DIR.mkdir(parents=True, exist_ok=True)
    session_id = str(artifacts.session.session_id)
    path = _STORE_DIR / f"{session_id}.json"
    path.write_text(artifacts.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_pipeline_artifacts(session_id: str) -> PipelineArtifacts | None:
    path = _STORE_DIR / f"{session_id}.json"
    if not path.exists():
        return None

    payload = json.loads(path.read_text(encoding="utf-8"))
    return PipelineArtifacts.model_validate(payload)