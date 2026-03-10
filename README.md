## 1. Build target

**Research orchestration system**

Core product flow:

1. User submits a research question.
2. Planner converts it into a structured plan.
3. Retrieval pulls evidence from web + scholarly APIs.
4. Evaluator scores and filters sources.
5. Summarizer produces structured notes per source.
6. Synthesizer/report generator produces a citation-backed report.
7. UI exposes the trace, source table, contradictions, and exports.

Using **schema-constrained outputs** is the right backbone here because OpenAI Structured Outputs are specifically designed to make model responses conform to a JSON Schema, which is exactly what you want for agent handoff reliability. FastAPI also maps cleanly onto Pydantic response models and JSON-schema generation, which makes the contracts enforceable at the API boundary. ([developers.openai.com](https://developers.openai.com/api/docs/guides/structured-outputs/?utm_source=chatgpt.com))

---

## 2. Recommended implementation shape

### Backend
Uses a modular monorepo and keeps execution centralized.

**Stack**
- Python 3.12
- FastAPI
- Pydantic v2
- httpx for async API calls
- PostgreSQL
- Redis only when you need background jobs
- Celery or Dramatiq later, not in v1

**Why**
- FastAPI + Pydantic provides a typed request/response models, validation, and OpenAPI generation out of the box. ([fastapi.tiangolo.com](https://fastapi.tiangolo.com/tutorial/response-model/?utm_source=chatgpt.com))
- PostgreSQL to enable relational storage for sessions, sources, claims, and reports, while still benefiting from `jsonb` for trace/event payloads and native full-text search support. ([postgresql.org](https://www.postgresql.org/docs/current/datatype-json.html?utm_source=chatgpt.com))

### Frontend
- React
- TypeScript
- TanStack Query
- Zustand or Redux Toolkit for local UI state
- Tailwind or MUI
- Markdown renderer + citation hover cards

### Deployment
- API: Render/Fly.io/Railway
- DB: Neon or managed Postgres
- Frontend: Vercel
- Object storage for exports: S3-compatible bucket

---

## 3. System architecture

Use an **explicit orchestrator**, not autonomous agent-to-agent free form messaging.

### Core services
- `planner_service`
- `retrieval_service`
- `evaluation_service`
- `summarization_service`
- `report_service`
- `session_service`
- `export_service`
- `benchmark_service`

### Orchestrator Rules
* The planner, evaluator, summarizer, and report generator will never call a vendor SDK directly.
* Every agent calls the provider adapter
* Every session stores `provider`, `model`, `prompt_version`, `schema_version`, `latency_ms`, `token_usage`, and `estimated_cost_usd`

### Execution model
The orchestrator owns the workflow.

```text
POST /research/run
  -> create session
  -> planner.generate_plan()
  -> retrieval.execute_tasks()
  -> evaluation.score_sources()
  -> summarization.create_notes()
  -> report.generate()
  -> persist all artifacts
  -> return session_id + report snapshot
```

For version 2.0:

```text
POST /research/run-iterative
  -> planner.generate_plan()
  -> retrieval/evaluation/summarization
  -> planner.review_evidence_state()
  -> decide continue/stop
  -> repeat until stopping condition met
```

Ensure downstream agents do not create their own schemas. Every stage reads and writes typed objects.

---

## 4. Package and repo layout

```text
ai-researcher/
  backend/
    api/
      app/
        main.py
        routes/
        dependencies/
        config/
    frontend/
      src/
        pages/
        components/
        features/
  packages/
    schemas/
      research_session.py
      plan.py
      source.py
      evaluation.py
      summary.py
      report.py
    agents/
      planner/
      evaluator/
      summarizer/
      reporter/
    retrieval/
      base.py
      web_search.py
      openalex.py
      crossref.py
      semantic_scholar.py
      arxiv.py
      normalize.py
      dedup.py
    orchestration/
      run_pipeline.py
      iterative_pipeline.py
    storage/
      models/
      repositories/
      migrations/
    exports/
      markdown.py
      html.py
      pdf.py
    benchmarks/
      datasets/
      scorers/
  docs/
    architecture.md
    scoring-rubric.md
    connector-notes.md
  tests/
    unit/
    integration/
    eval/
```

---

## 5. Canonical data model

System's contract layer.

### ResearchSession
```json
{
  "session_id": "uuid",
  "query": "string",
  "depth_mode": "standard",
  "domain_mode": "mixed",
  "status": "completed",
  "created_at": "datetime",
  "updated_at": "datetime",
  "provider": "ollama",
  "model": "qwen3:8b",
  "run_mode": "local_free",
  "comparison_group_id": "str | None = None"
}
```

### Plan
```json
{
  "plan_id": "uuid",
  "session_id": "uuid",
  "objective": "string",
  "sub_questions": ["string"],
  "search_tasks": [
    {
      "task_id": "uuid",
      "question": "string",
      "target_sources": ["web", "openalex", "crossref"],
      "query_templates": ["string"],
      "inclusion_criteria": ["string"],
      "exclusion_criteria": ["string"],
      "priority": 1
    }
  ],
  "stopping_conditions": {
    "min_high_confidence_sources": 6,
    "max_iterations": 3,
    "stop_when_subquestions_covered_ratio": 0.8
  }
}
```

### Source
External IDs are included because these APIs expose overlapping but different metadata models: 
* OpenAlex covers works/authors/sources
* Crossref is strong for DOI-centered metadata
* Semantic Scholar exposes paper/author/citation graph data
* arXiv provides preprint metadata through its API. ([developers.openalex.org](https://developers.openalex.org/api-reference/introduction?utm_source=chatgpt.com))

```json
{
  "source_id": "uuid",
  "session_id": "uuid",
  "title": "string",
  "url": "string",
  "canonical_url": "string",
  "authors": ["string"],
  "publisher_or_venue": "string",
  "published_date": "date",
  "source_type": "paper",
  "doi": "string|null",
  "arxiv_id": "string|null",
  "openalex_id": "string|null",
  "semantic_scholar_id": "string|null",
  "abstract": "string|null",
  "retrieved_at": "datetime",
  "fulltext_available": false,
  "raw_payload": {}
}
```

### SourceEvaluation
```json
{
  "evaluation_id": "uuid",
  "source_id": "uuid",
  "relevance_score": 0.86,
  "credibility_score": 0.78,
  "recency_score": 0.92,
  "corroboration_score": 0.64,
  "metadata_completeness_score": 0.88,
  "overall_score": 0.81,
  "reasoning": [
    "Directly addresses sub-question 2",
    "DOI present",
    "Venue metadata present",
    "Recent source for fast-moving topic"
  ],
  "decision": "keep",
  "flags": ["preprint", "limited_methods_detail"],
  "provider": "ollama",
  "model": "qwen3:8b",
  "run_mode": "local_free",
  "latency_ms": 1840,
  "token_usage": {
    "input": 4200,
	"output": 1100
  },
  "estimated_cost_usd": 0.0,
  "schema_valid": true
}
```

### Claim
```json
{
  "claim_id": "uuid",
  "claim_text": "string",
  "supporting_source_ids": ["uuid"],
  "counter_evidence_source_ids": ["uuid"],
  "confidence": 0.74,
  "status": "supported"
}
```

### SummaryNote
```json
{
  "note_id": "uuid",
  "source_id": "uuid",
  "concise_summary": "string",
  "key_claims": ["string"],
  "methods": ["string"],
  "limitations": ["string"],
  "counterpoints": ["string"],
  "evidence_snippets": [
    {
      "text": "string",
      "location": "abstract"
    }
  ],
  "citation_anchor": "[S12]"
}
```

### Report
```json
{
  "report_id": "uuid",
  "session_id": "uuid",
  "executive_summary": "string",
  "answer": "string",
  "key_findings": ["string"],
  "competing_views": ["string"],
  "limitations": ["string"],
  "evidence_gaps": ["string"],
  "source_table": [],
  "appendix_trace_ref": "uuid",
  "provider_summary": "string",
  "benchmark_summary": "string",
  "comparison_index": "string"
}
```

### Provider Abstraction layer
Responsibility:
* route planner/ evaluator / summarizer / report tasks to a configured model provider
* normalize tool-calling and structured-output behavior across providers
* track provider-level metrics
* support A/B comparison runs

#### Example Python interface
```python
class LLMProvider(Protocol):
	async def generate_structured(
		self,
		system_prompt: str,
		user_prompt: str,
		json_schema: dict,
		tools: list[dict] | None = None,
		temperature: float = 0.0,
	) -> dict: ...
	
	async def generate_text(
		self,
		system_prompt: str,
		user_prompt: str,
		temperature: float = 0.2,
	) -> str: ...
```

#### Providers
* Ollama + Qwen 3 8B (free local)
* Gemini free tier (optional hosted free mode)
* OpenAI GPT and Claude as comparison targets

---

## 6. Agent contract design

### Planner output contract
Use Structured Outputs and reject invalid outputs server-side.

Fields:
- objective
- sub_questions
- search_tasks
- inclusion_criteria
- exclusion_criteria
- stopping_conditions
- recommended_depth_adjustment
- adapter contract
- run metadata schema
- benchmark result scehma

### Evaluator output contract
Fields:
- normalized source record
- relevance score
- credibility score
- rationale
- flags
- keep/discard
- Add provider-independent deterministic heuristics first (so the evaluator is not overly model-dependent)
- by-provider comparison
- by-model comparison
- local-vs-hosted comparison

### Summarizer output contract
Fields:
- concise summary
- claims
- evidence
- limitations
- citation anchor
- strict_structured=True
- retry with lower-temperature fallback
- deterministic repair pass for malformed local-model JSON

### Report output contract
Fields:
- answer
- findings
- disagreements
- gaps
- caveats
- citations
- provider comparison appendix
- cost/latency section
- “why this provider was chosen” block

Implementation rule:
- every model output is validated twice:
    1. by OpenAI Structured Outputs against the schema
    2. by Pydantic after receipt

That double validation materially reduces brittle agent chaining. ([developers.openai.com](https://developers.openai.com/api/docs/guides/structured-outputs/?utm_source=chatgpt.com))

---

## 7. Retrieval layer blueprint

Implement retrieval as connectors plus one normalization layer.

### Connector interface
```python
class RetrievalConnector(Protocol):
    async def search(self, query: str, limit: int = 10) -> list[RawResult]: ...
    async def hydrate(self, raw_result: RawResult) -> dict: ...
```

### Connectors
- `web_search_connector`
- `openalex_connector`
- `crossref_connector`
- `semantic_scholar_connector`
- `arxiv_connector`

### Why this set works
- **OpenAlex**: broad scholarly entity coverage across works, authors, institutions, and related entities. ([docs.openalex.org](https://docs.openalex.org/?utm_source=chatgpt.com))
- **Crossref**: DOI-centric metadata retrieval with filters and structured JSON responses. ([crossref.org](https://www.crossref.org/documentation/retrieve-metadata/rest-api/?utm_source=chatgpt.com))
- **Semantic Scholar**: paper, author, citation, and venue-oriented graph data. ([semanticscholar.org](https://www.semanticscholar.org/product/api?utm_source=chatgpt.com))
- **arXiv**: preprint retrieval via its API, with Atom/XML metadata responses and separate bulk/OAI options if you expand later. ([info.arxiv.org](https://info.arxiv.org/help/api/index.html?utm_source=chatgpt.com))

### Retrieval pipeline
For each planner task:
1. Generate 2–4 queries.
2. Fan out to connectors asynchronously.
3. Normalize raw results to `Source`.
4. Deduplicate.
5. Return top `N` candidates.

### Dedup order
1. DOI exact match
2. arXiv ID exact match
3. Canonical URL exact match
4. Title normalization + fuzzy match
5. Semantic Scholar / OpenAlex cross-id match

### Normalization rules
- Canonicalize URLs
- Normalize author arrays
- Parse dates to UTC date
- Mark `source_type`
- Store raw payload for auditability

---

## 8. Source evaluation rubric

Keep this transparent and deterministic-first.

### Score formula
```text
overall_score =
  0.30 * relevance +
  0.25 * authority +
  0.10 * recency +
  0.10 * metadata_completeness +
  0.15 * corroboration +
  0.10 * directness
```

### Authority defaults
- official vendor/government/institution docs: 0.9–1.0
- peer-reviewed paper with DOI + venue: 0.8–0.95
- preprint: 0.6–0.8
- reputable journalism: 0.6–0.8
- personal blog: 0.2–0.5

### Metadata completeness signals
- DOI present
- author names present
- published date present
- venue/publisher present
- abstract present
- canonical URL present

### Recency weighting
Make recency topic-aware:
- current events / tooling / market research: high recency weight
- historical / foundational science: low recency weight

### Corroboration logic
Claim-level corroboration, not source-level only:
- source gets a boost if at least one major claim is supported by 2+ independent sources

### Keep/discard rule
- keep if `overall_score >= 0.65`
- soft keep if `relevance >= 0.8` but `authority < 0.5`
- discard if duplicate or off-topic
- flag if preprint or weak metadata

---

## 9. Summarization layer blueprint

The summarizer should not produce prose first. It should produce a **structured note** first, then optional prose.

### Summarization flow
1. Read source metadata + abstract/snippets.
2. Produce `SummaryNote`.
3. Extract claims into `ClaimCandidate`.
4. Link claims to other sources.

### Per-source summary prompt objective
Return:
- what the source says
- what evidence it offers
- what method it used
- what limitations are visible
- what it does **not** establish

### Good v1 rule
Do not summarize more than the top 8–10 sources in detail.
For the rest, keep metadata-only evaluation.

---

## 10. Contradiction detection

Do this in two layers.

### Layer A: heuristic contradiction flags
Compare claims by entity + predicate polarity.

Example:
- Source A: “Tool X reduces latency by 40%.”
- Source B: “Tool X showed no significant latency improvement.”

Normalize into:
- entity: Tool X
- predicate: impact on latency
- stance: positive / null / negative

### Layer B: model-assisted contradiction clustering
Input:
- list of claim triplets
- source IDs
- confidence levels

Output:
- agreement clusters
- disagreement clusters
- unresolved conflicts

### UI output
Show:
- “agreement”
- “mixed evidence”
- “active contradiction”
- “insufficient evidence”

---

## 11. Evidence gaps section

Generate gaps from:
- uncovered sub-questions
- claims with only one weak source
- lack of recent evidence for fast-moving questions
- inaccessible full text
- overreliance on preprints or blogs

Simple rule:
if a sub-question has fewer than 2 credible supporting sources, add it to `evidence_gaps`.

---

## 12. Iterative research loop for Layer 3

Required to use bounded iterations.

### Loop state
```json
{
  "iteration": 2,
  "subquestion_coverage": 0.71,
  "high_confidence_claims": 5,
  "open_conflicts": 2,
  "remaining_gaps": 3
}
```

### Continue criteria
Continue if any are true:
- coverage < threshold
- unresolved contradiction on a high-priority question
- fewer than `min_high_confidence_sources`
- important domain pack requires source diversity threshold

### Stop criteria
Stop when:
- max iterations reached
- marginal gain < threshold
- all critical sub-questions sufficiently covered

This gives you agentic behavior without turning the system into uncontrolled looping.

---

## 13. Domain packs

To be implemented as config bundles, not separate codebases.

### DomainPack interface
```python
class DomainPack(BaseModel):
    name: str
    preferred_connectors: list[str]
    authority_weights: dict[str, float]
    recency_half_life_days: int
    required_metadata_fields: list[str]
    query_templates: list[str]
```

### Examples
**Tech**
- prefer docs, GitHub, vendor blogs, arXiv, Semantic Scholar
- high recency sensitivity

**Legal**
- prefer statutes, court opinions, official guidance, law review
- very high authority sensitivity
- citations must preserve jurisdiction

**Biomedical**
- prefer PubMed-like expansion later, peer-reviewed journals, preprints flagged
- require method transparency
- stronger caution language

**Market research**
- prefer filings, investor relations, official statistics, reputable business reporting
- high recency and source provenance sensitivity

---

## 14. API surface

### Core endpoints
- `POST /research/run`
- `POST /research/run-iterative`
- `GET /research/{session_id}`
- `GET /research/{session_id}/trace`
- `GET /research/{session_id}/sources`
- `GET /research/{session_id}/report`
- `POST /research/{session_id}/export/markdown`
- `POST /research/{session_id}/export/html`
- `POST /research/{session_id}/export/pdf`

### Benchmark endpoints
- `POST /benchmarks/run`
- `GET /benchmarks/{run_id}`
- `GET /benchmarks/{run_id}/results`

### Internal service endpoints
Optional later:
- `POST /planner/plan`
- `POST /retrieval/search`
- `POST /evaluation/score`
- `POST /summary/generate`
- `POST /report/generate`

For v1, keep these as Python services, not separate deployables.

---

## 15. Database design

### Tables
- `research_sessions`
- `plans`
- `research_tasks`
- `sources`
- `source_external_ids`
- `source_evaluations`
- `claims`
- `claim_source_links`
- `summary_notes`
- `reports`
- `research_events`
- `exports`
- `benchmark_runs`
- `benchmark_cases`
- `benchmark_results`

### Use `jsonb` for
- raw API payloads
- event logs
- prompt/response snapshots
- planner/evaluator rationale payloads

### Add FTS indices
Use PostgreSQL text search for:
- report search
- session history search
- source title/abstract search ([postgresql.org](https://www.postgresql.org/docs/current/textsearch.html?utm_source=chatgpt.com))

---

## 15. LLM Strategy and provider comparison
Supports two deployment modes:

### Free / local mode
Ollama + Qwen 3

Used for local only processing as the free option.

### Hosted frontier mode
OpenAI / Gemini / Claude

Less local hardware dependency.

---

## 16. Frontend blueprint

Use a 4-pane product layout from the start.

### Pane 1: Query + controls
- research question input
- depth mode: quick / standard / deep
- domain mode: general / academic / tech / legal / biomedical / market
- run button

### Pane 2: Research trace
- planner output
- retrieval events
- scoring events
- iteration history
- stop/continue rationale

### Pane 3: Source table
Columns:
- title
- type
- authority
- relevance
- recency
- overall
- status
- why kept/discarded

### Pane 4: Final report
Sections:
- executive summary
- answer
- key findings
- competing views
- evidence gaps
- limitations
- citations
- export actions

### Saved sessions view
- query
- created date
- domain mode
- report confidence
- reopen / replay

---

## 17. Export design

### Markdown
Primary canonical export.

### HTML
Rendered report with citation links and source cards.

### PDF
Generate from HTML, not from markdown directly.
Use a print stylesheet and headless browser rendering.

Include:
- title page
- query metadata
- final answer
- citations
- source appendix
- research trace appendix for portfolio demos

---

## 18. Evaluation harness

Requirements for being "production ready":

### Benchmark dataset
Create 25–50 prompts across:
- technical research
- scientific/literature synthesis
- product/tool comparison
- historical research
- current-events-with-citations
- mixed-evidence topics

### Evaluation dimensions
- plan completeness
- source precision@k
- citation coverage
- unsupported claim rate
- contradiction detection accuracy
- evidence-gap detection quality
- report usefulness

### Concrete metrics
- `% subquestions with >= 2 credible sources`
- `% report claims linked to at least one source`
- `% high-confidence claims with corroboration`
- `% contradictions surfaced when present`
- average source score for cited vs uncited sources

### Human eval rubric
Use 1–5 scales for:
- usefulness
- trustworthiness
- coverage
- clarity
- citation quality

---

## 19. Observability and debugging

Requirement to start the project.

### Log every stage
For each session persist:
- input
- normalized planner output
- retrieval queries per connector
- raw result count
- dedup count
- source evaluation rationale
- summaries
- final report generation inputs

### Track failure modes
- invalid schema output
- connector timeout
- empty retrieval
- excessive duplicates
- report generated with weak evidence

### Minimum admin/debug screens
- session event log
- raw source payload viewer
- evaluator rationale inspector
- benchmark comparison table

---

## 20. Implementation roadmap by layer

## Layer 1: MVP
Goal: one strong end-to-end research run.

Build:
- query input
- planner with 3–7 sub-questions
- retrieval from web + OpenAlex + Crossref + Semantic Scholar + arXiv
- dedup
- heuristic evaluator
- top-10 summaries
- markdown/HTML report with citations
- basic trace panel

Do **not** add:
- iterative loop
- domain packs
- benchmarking UI
- PDF export if time is tight

### Success criterion
A user can run one research question and inspect:
- plan
- sources
- scores
- final answer with citations

---

## Layer 2: Strong portfolio version
This is the featured-project tier.

Add:
- saved sessions
- research trace replay
- contradiction map
- evidence gaps
- entity normalization
- PDF export
- source rationale panel
- session history UI
- benchmark harness v1

### Success criterion
A reviewer can see that the system is:
- auditable
- reproducible
- explainable
- citation-aware

---

## Layer 3: Advanced version
Add controlled autonomy.

Add:
- iterative evidence loop
- planner evidence review pass
- depth modes
- domain packs
- benchmark dashboard
- answer quality scoring
- citation quality scoring

### Success criterion
The system can justify when it searched more and why it stopped.

---

## 21. First 6-week execution plan

### Week 1
- define schemas
- scaffold FastAPI + React app
- create DB schema
- implement planner contract + fixtures

### Week 2
- implement retrieval connectors
- normalize results
- implement dedup
- persist sources

### Week 3
- implement evaluator
- score table
- build source review API + UI

### Week 4
- implement summarizer + claim extraction
- generate markdown/HTML report
- wire report pane

### Week 5
- build trace view
- add saved sessions
- implement evidence gaps + contradiction heuristic

### Week 6
- add export
- build benchmark dataset
- record demo
- write architecture and case study docs

---

## Engineering risks

### 1. Retrieval inconsistency
Different APIs return different metadata shapes and coverage. 
OpenAlex, Crossref, Semantic Scholar, and arXiv all expose different retrieval styles and metadata granularity.
Heterogeneity should be assumed by design. ([developers.openalex.org](https://developers.openalex.org/api-reference/introduction?utm_source=chatgpt.com))

### 2. Weak citation grounding
Fix by requiring every report claim to reference one or more `source_id`s.

### 3. Duplicate-heavy scholarly results
Fix by strong external-ID-first dedup.

### 4. Overconfident synthesis
Fix by forcing limitations and evidence gaps into the report schema.

### 5. Scope sprawl
Fix by shipping Layer 1 before touching iterative research.

---

## Requirements for being "portfolio ready":

The following are emphasized in the case study:
- schema-constrained multi-agent orchestration
- heterogeneous scholarly API integration
- credibility scoring with transparent rationale
- contradiction-aware synthesis
- reproducible research sessions
- benchmarked report quality
- audit-friendly UX

## Phase 1 MVP

- one query input
- planner returns 5 sub-questions
- retrieval hits web + OpenAlex + Crossref + Semantic Scholar + arXiv
- dedup to top 25 results
- evaluator scores all 25
- summarizer writes notes for top 8
- report generator writes markdown with citations
- frontend shows trace, source table, report, session save

---

## MVP scaffold run guide (current state)

### Run frontend + backend

1. Install frontend deps:
  - `npm install`
2. Run backend API (from repo root):
  - `uvicorn backend.api.app.main:app --reload --port 8000`
3. Run frontend dev server:
  - `npm run dev`
4. Open the Vite URL and use the **Run Research** form to call `POST /research/run`.

### Current MVP scope

- End-to-end orchestration path is implemented as typed placeholders.
- Pipeline stages return schema-valid scaffold objects for planning, retrieval, evaluation, summarization, and report generation.
- Live connectors (OpenAlex/Crossref/Semantic Scholar/arXiv), persistence, and iterative loops are not yet implemented.

### Contract + orchestration locations

- Schema contracts: `packages/schemas/`
- Orchestration entrypoint: `packages/orchestration/run_pipeline.py`
- API route for execution: `backend/api/app/routes/research.py`