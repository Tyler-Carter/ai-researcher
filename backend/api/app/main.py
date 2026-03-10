from __future__ import annotations

from fastapi import FastAPI

from .routes.research import router as research_router

app = FastAPI(title="AI Researcher API", version="0.1.0")
app.include_router(research_router)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}