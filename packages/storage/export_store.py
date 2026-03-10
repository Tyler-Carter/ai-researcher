from __future__ import annotations

from pathlib import Path

_EXPORT_DIR = Path("backend/data/exports")


def save_export_artifact(session_id: str, export_format: str, content: str) -> Path:
    _EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = "md" if export_format == "markdown" else "html"
    path = _EXPORT_DIR / f"{session_id}.{suffix}"
    path.write_text(content, encoding="utf-8")
    return path