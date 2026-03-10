# Progress Tracking

_Last updated: 2026-03-10._

## 1) README target vs current repository reality

The README describes a full research-orchestration platform with modular backend services, strict typed contracts, retrieval connectors, evaluation/summarization/reporting layers, persistent sessions, export formats, and benchmarking.

The current repository already includes:

- FastAPI API with `POST /research/run`, session fetch, and markdown/html export endpoints.
- A concrete orchestrator pipeline (`session -> plan -> retrieval -> evaluation -> summarization -> report`).
- Pydantic schema contracts for session, plan, source, evaluation, summary, and report artifacts.
- Live retrieval calls to web (Wikipedia), OpenAlex, Crossref, Semantic Scholar, and arXiv.
- Source deduplication, deterministic heuristic scoring, summary generation, and report synthesis.
- Local file-backed persistence for sessions and exports under `backend/data/*`.
- A React/Vite UI that runs research, renders artifacts, and downloads exports.

This means the project is **beyond a pure scaffold**, but still short of the full README target architecture and “portfolio-ready” requirements.

---

## 2) Remaining tasks to complete the project

Below are the highest-priority remaining tasks, ordered to align with the README roadmap (Layer 1 completion -> Layer 2 portfolio quality -> Layer 3 advanced autonomy).

1. **Persistence is local JSON storage**, not Postgres-backed repositories/migrations.
2. **Provider/model instrumentation fields** exist in schemas, but runtime values remain placeholders.
3. **Research planning** exists, but currently uses a static deterministic template (not model-generated planner output).

### A. Contract enforcement and model-stage reliability (finish Layer 1 quality bar)

1. Add explicit stage-boundary validation for every handoff (`Plan`, `Source[]`, `SourceEvaluation[]`, `SourceSummary[]`, `FinalReport`) before each downstream stage consumes input.
2. Introduce provider adapter boundaries for model-driven stages (planner/evaluator/summarizer/reporter) so runtime can capture provider/model/prompt/schema versions consistently.
3. Replace static/deterministic planner output with schema-constrained model output while preserving server-side validation.
4. Add structured error payloads for invalid stage outputs (schema failure, empty retrieval, connector timeout) and persist these as trace events.

### B. Retrieval/evaluation depth and evidence quality

1. Improve normalization and dedup logic across connectors (external ID precedence, canonical URL normalization, title fuzz matching fallback).
2. Expand scoring transparency with richer rationale fields (why keep/discard, confidence level, quality flags).
3. Add stronger contradiction + mixed-evidence analysis beyond cue-word heuristics (claim-level extraction and explicit supporting/contradicting linkage quality checks).
4. Add evidence-gap detection that is tied to plan/sub-question coverage rather than only report-level heuristics.

### C. Persistence and backend architecture hardening

1. Replace local JSON persistence with PostgreSQL-backed models and repositories.
2. Add migration tooling and initial schema for sessions, plans, sources, evaluations, summaries, reports, and event logs.
3. Add session history/list APIs for saved-session UX and replay.
4. Add background-job support (Redis + queue worker) only where long-running retrieval/report generation requires async execution.

### D. Frontend product requirements (README/UI target)

1. Evolve raw JSON rendering into dedicated views: plan trace, source table, evaluator rationale inspector, contradiction/evidence-gap panels.
2. Add session history and replay UX.
3. Add citation-aware report rendering (hover/source card behavior).
4. Add admin/debug views for stage event logs and raw connector payload inspection.

### E. Export and reporting completeness

1. Keep markdown/html exports and add production-grade formatting templates.
2. Add PDF export via HTML-to-PDF rendering with print stylesheet.
3. Ensure report sections always include: contradictions/mixed evidence, limitations, evidence gaps, and citation-linked claims.

### F. Benchmarking, evaluation harness, and observability (portfolio readiness)

1. Create benchmark dataset (25-50 prompts across required domains).
2. Implement scoring harness and metrics from README (coverage, citation linkage, corroboration, contradiction surfacing).
3. Add benchmark result storage and comparison API.
4. Add observability/event logging for each stage: input, normalized output, retrieval stats, dedup counts, rationale, failure mode classification.
5. Add benchmark/debug UI table for side-by-side run comparison.

### G. Layer 3 advanced capabilities (after Layers 1-2 are solid)

1. Implement iterative endpoint (`/research/run-iterative`) with planner evidence-review loop and stopping-condition checks.
2. Add depth/domain modes and domain packs.
3. Add answer/citation quality scoring dashboards.


---

## 3) Definition of done checklist (project completion)

The project can be considered complete when all are true:

### Task
- End-to-end orchestration uses schema-constrained model outputs with strict validation at every stage.
- Retrieval/evaluation/report outputs are auditable and citation-grounded with explicit contradiction/evidence-gap handling.
- Persistence is database-backed with reproducible saved sessions and full trace logs.
- UI supports traceability, source/rationale inspection, and session replay (not just raw JSON dumps).
- Export pipeline supports markdown, html, and pdf.
- Benchmark harness exists with tracked metrics and comparison views.

---

## 4) Work performed for this update


