# Progress Tracking (as of last push)

_Last verified against commit `f0f8d99` on branch `main`._

## 1) README target vs current repository reality

The README describes a full research-orchestration platform with modular backend services, strict typed contracts, retrieval connectors, evaluation/summarization/reporting layers, persistent sessions, export formats, and benchmarking.

Current repository state is an MVP slice with:

- A working FastAPI app exposing `GET /health` and `POST /research/run`.
- A typed end-to-end pipeline (`session -> plan -> retrieval -> evaluation -> summarization -> report`).
- Pydantic schemas for core artifacts (`ResearchSession`, `Plan`, `Source`, `SourceEvaluation`, `SourceSummary`, `FinalReport`).
- Local file-backed persistence for completed pipeline artifacts in `backend/data/sessions/*.json`.
- A React/Vite frontend that submits a query and renders pipeline artifacts.

### Implemented from README intent

1. **Contract-first core objects exist** via `packages/schemas/*`.
2. **Orchestration flow exists** in `run_pipeline(query)` and is invoked by API route `/research/run`.
3. **Retrieval includes web + scholarly connectors:** web (Wikipedia), OpenAlex, Crossref, Semantic Scholar, and arXiv.
4. **Deduplication exists** with DOI/URL/title fallback keys.
5. **Evaluation exists** with deterministic heuristic scoring and keep/discard decision.
6. **Summarization exists** as structured notes with citation anchors.
7. **Report generation exists** with findings, limitations, evidence gaps, and source table.
8. **Session artifact persistence now exists** via a storage module and session fetch route.
9. **Export artifact generation exists** for markdown/html via dedicated export endpoint and storage.

### Partially implemented (present but limited)

1. **Persistence is local JSON storage**, not Postgres-backed repositories/migrations.
2. **Provider/model instrumentation fields** exist in schemas, but runtime values remain placeholders.
3. **Research planning** exists, but currently uses a static deterministic template (not model-generated planner output).
4. **Exports are generated on-demand** and saved to local files, but no frontend export UX exists yet.

### Not yet implemented from README target architecture

1. **Most layout targets** under `packages/` are still absent or consolidated (agents/, retrieval module split, benchmarks/).
2. **Iterative orchestration endpoint** (`/research/run-iterative`) is not present.
3. **Structured Outputs + Pydantic double validation** is not implemented (current pipeline is deterministic Python logic).
4. **Database persistence (PostgreSQL), Redis/job system, migrations, repositories** are not present.
5. **PDF export pipeline** is not present.
6. **Benchmarking and comparison dashboard plumbing** is not present.
7. **Contradiction mining / mixed-evidence synthesis** is not implemented yet.

---

## 2) Current “done vs next” snapshot

### Done

- End-to-end MVP request path from frontend form to backend pipeline response.
- Typed schemas and typed response model.
- Deterministic retrieval/evaluation/summarization/report generation.
- Scholarly retrieval coverage (Semantic Scholar + arXiv) in retrieval stage.
- Local file-backed session/artifact persistence plus session retrieval endpoint.
- Markdown/HTML export generation endpoint and local export artifact persistence.

### Next high-impact steps

1. Add frontend export controls to request markdown/html artifacts and provide download UX from session results.

---

## 3) Task completed in this update

### Task
Implement the next roadmap step by adding persistent session/artifact storage for completed runs.

### Steps accomplished

1. Added `packages/exports/markdown.py` to generate a canonical markdown report from `PipelineArtifacts`.
2. Added `packages/exports/html.py` to generate a canonical HTML report from `PipelineArtifacts`.
3. Added `packages/storage/export_store.py` to persist generated exports under `backend/data/exports/`.
4. Extended `backend/api/app/routes/research.py` with `GET /research/{session_id}/export/{export_format}` to generate + persist markdown/html exports per session.
5. Kept planning/retrieval/evaluation/summarization/report orchestration logic unchanged to scope this task strictly to export artifacts.

