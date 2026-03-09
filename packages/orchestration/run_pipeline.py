from __future__ import annotations

from datetime import date, datetime
from uuid import uuid4
from pydantic import BaseModel


from packages.schemas import (
    FinalReport,
    Plan,
    ResearchSession,
    SearchTask,
    Source,
    SourceEvaluation,
    SourceSummary,
    StoppingConditions,
)


class PipelineArtifacts(BaseModel):
    session: ResearchSession
    plan: Plan
    sources: list[Source]
    evaluations: list[SourceEvaluation]
    summaries: list[SourceSummary]
    report: FinalReport


def _build_session(query: str) -> ResearchSession:
    now = datetime.now(datetime.now(tz=None))
    return ResearchSession(
        session_id=uuid4(),
        query=query,
        status="running",
        created_at=now,
        updated_at=now,
    )


def _build_plan(session: ResearchSession) -> Plan:
    return Plan(
        plan_id=uuid4(),
        session_id=session.session_id,
        objective=f"Answer: {session.query}",
        sub_questions=["What is the current state of evidence?"],
        search_tasks=[
            SearchTask(
                task_id=uuid4(),
                question=session.query,
                target_sources=["web", "openalex", "crossref"],
                query_templates=[session.query],
                inclusion_criteria=["Directly relevant to query"],
                exclusion_criteria=["No citation metadata"],
                priority=1,
            )
        ],
        stopping_conditions=StoppingConditions(),
    )


def _retrieve_sources(session: ResearchSession, plan: Plan) -> list[Source]:
    first_task = plan.search_tasks[0]
    return [
        Source(
            source_id=uuid4(),
            session_id=session.session_id,
            title=f"Placeholder source for: {first_task.question}",
            url="https://example.org/source",
            canonical_url="https://example.org/source",
            authors=["AI Researcher"],
            publisher_or_venue="Example Journal",
            published_date=date.today(),
            source_type="paper",
            abstract="Placeholder abstract for MVP scaffold",
            raw_payload={"connector": "mock"},
        )
    ]


def _evaluate_sources(sources: list[Source]) -> list[SourceEvaluation]:
    return [
        SourceEvaluation(
            evaluation_id=uuid4(),
            source_id=source.source_id,
            relevance_score=0.8,
            credibility_score=0.75,
            recency_score=0.7,
            corroboration_score=0.65,
            metadata_completeness_score=0.9,
            overall_score=0.77,
            reasoning=["Placeholder deterministic scoring for scaffold."],
            decision="keep",
            flags=["placeholder"],
            latency_ms=5,
        )
        for source in sources
    ]


def _summarize_sources(sources: list[Source], _: list[SourceEvaluation]) -> list[SourceSummary]:
    return [
        SourceSummary(
            note_id=uuid4(),
            source_id=source.source_id,
            concise_summary="Placeholder summary generated from typed pipeline stage.",
            key_claims=["Pipeline contracts are functioning end-to-end."],
            methods=["Typed placeholder synthesis"],
            limitations=["No live connector calls in MVP scaffold."],
            counterpoints=["Requires real retrieval and scoring integration."],
            evidence_snippets=[{"text": source.title, "location": "title"}],
            citation_anchor="[S1]",
        )
        for source in sources
    ]


def _generate_report(
        session: ResearchSession,
        summaries: list[SourceSummary],
        sources: list[Source],
) -> FinalReport:
    return FinalReport(
        report_id=uuid4(),
        session_id=session.session_id,
        executive_summary="This is a typed placeholder report from the MVP pipeline.",
        answer=f"Preliminary placeholder answer for query: {session.query}",
        key_findings=[summary.concise_summary for summary in summaries],
        competing_views=["No competing views computed in placeholder mode."],
        limitations=["Connector, evaluator, and synthesis logic are stubs."],
        evidence_gaps=["Need multi-source corroboration and contradiction analysis."],
        source_table=[{"source_id": str(source.source_id), "title": source.title} for source in sources],
        appendix_trace_ref=str(session.session_id),
    )


def run_pipeline(query: str) -> PipelineArtifacts:
    session = _build_session(query)
    plan = _build_plan(session)
    sources = _retrieve_sources(session, plan)
    evaluations = _evaluate_sources(sources)
    summaries = _summarize_sources(sources, evaluations)
    report = _generate_report(session, summaries, sources)
    completed_session = session.model_copy(update={"status": "completed", "updated_at": datetime.now(tz=None)})

    return PipelineArtifacts(
        session=completed_session,
        plan=plan,
        sources=sources,
        evaluations=evaluations,
        summaries=summaries,
        report=report,
    )
