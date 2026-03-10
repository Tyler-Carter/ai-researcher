# Progress Tracking (as of last push)

_Last verified against commit `7dc24bd` on branch `work`._

## 1) README target vs current repository reality

The README describes a full research-orchestration platform with a modular backend, typed contracts, retrieval connectors, evaluation, summarization, reporting, session persistence, exports, and benchmarking.

Current repository state is an MVP slice with:

- A working FastAPI app exposing `GET /health` and `POST /research/run`.
- A typed end-to-end pipeline (`session -> plan -> retrieval -> evaluation -> summarization -> report`).
- Pydantic schemas for core artifacts (`ResearchSession`, `Plan`, `Source`, `SourceEvaluation`, `SourceSummary`, `FinalReport`).
- A simple React/Vite frontend that submits a query and renders pipeline artifacts.

### Implemented from README intent

1. **Contract-first core objects exist** via `packages/schemas/*`.
2. **Orchestration flow exists** in `run_pipeline(query)` and is invoked by API route `/research/run`.
3. **Retrieval includes web + scholarly connectors (subset):**
    - web (Wikipedia search)
    - OpenAlex
    - Crossref
4. **Deduplication exists** with DOI/URL/title fallback keys.
5. **Evaluation exists** with deterministic heuristic scoring and keep/discard decision.
6. **Summarization exists** as structured notes with citation anchors.
7. **Report generation exists** with findings, limitations, evidence gaps, and source table.
8. **Frontend exists** to execute runs and display stage outputs.

### Partially implemented (present but limited)

1. **Provider/model instrumentation fields** exist in schemas, but runtime values remain placeholders.
2. **Traceability** is present through returned artifacts and `appendix_trace_ref`, but there is no persistent storage layer yet.
3. **Research planning** exists, but currently uses a static, deterministic plan template (not model-generated planner output).

### Not yet implemented from README target architecture

1. **Most repo layout targets** under `packages/` are absent (agents/, retrieval module split, storage/, exports/, benchmarks/).
2. **Backend service decomposition** into separate services/modules is not present.
3. **Iterative orchestration endpoint** (`/research/run-iterative`) is not present.
4. **Remaining scholarly connectors** in README target are not present yet (Semantic Scholar, arXiv).
5. **Double validation with Structured Outputs + Pydantic** is not implemented; current pipeline is deterministic Python logic.
6. **Database persistence (PostgreSQL), Redis/job system, migrations, repositories** are not present.
7. **Export pipeline (markdown/html/pdf)** is not present.
8. **Benchmarking and comparison dashboard plumbing** is not present.
9. **Contradiction mining / mixed-evidence synthesis** is not implemented yet.

---

## 2) Current “done vs next” snapshot

### Done

- End-to-end MVP request path from frontend form to backend pipeline response.
- Typed schemas and typed response model.
- Deterministic retrieval/evaluation/summarization/report generation.

### Next high-impact steps

1. Add persistent session/source/artifact storage.
2. Split retrieval into connector modules and add Semantic Scholar + arXiv.
3. Introduce provider abstraction and real model-driven planner/summarizer/report stages with strict schema validation.
4. Add contradiction detection and stronger claim-level corroboration.
5. Add export and benchmarking layers from README target architecture.
