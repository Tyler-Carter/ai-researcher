from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Any
from urllib.parse import quote_plus
from urllib.request import Request, urlopen
from xml.etree import ElementTree
from uuid import UUID, uuid4

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
    now = datetime.now(tz=None)
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
                target_sources=["web", "openalex", "crossref", "semantic_scholar", "arxiv"],
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
    query = first_task.question

    candidates: list[Source] = []
    candidates.extend(_search_web(query=query, session_id=session.session_id))
    candidates.extend(_search_openalex(query=query, session_id=session.session_id))
    candidates.extend(_search_crossref(query=query, session_id=session.session_id))
    candidates.extend(_search_semantic_scholar(query=query, session_id=session.session_id))
    candidates.extend(_search_arxiv(query=query, session_id=session.session_id))


    return _deduplicate_sources(candidates)


def _fetch_json(url: str, timeout_s: int = 12) -> dict[str, Any]:
    request = Request(url, headers={"User-Agent": "ai-researcher-mvp/0.1 (+retrieval-service)"})
    with urlopen(request, timeout=timeout_s) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None

    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            parsed = datetime.strptime(value, fmt)
            if fmt == "%Y-%m":
                return date(parsed.year, parsed.month, 1)
            if fmt == "%Y":
                return date(parsed.year, 1, 1)
            return parsed.date()
        except ValueError:
            continue
    return None


def _strip_html(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = re.sub(r"<[^>]+>", "", value)
    return " ".join(cleaned.split())


def _search_web(query: str, session_id: UUID) -> list[Source]:
    encoded = quote_plus(query)
    api_url = (
        "https://en.wikipedia.org/w/api.php?"
        f"action=query&list=search&srsearch={encoded}&utf8=1&format=json&srlimit=5"
    )

    try:
        payload = _fetch_json(api_url)
    except Exception:
        return []

    results: list[Source] = []
    for item in payload.get("query", {}).get("search", []):
        title = item.get("title")
        if not title:
            continue

        page_url = f"https://en.wikipedia.org/wiki/{quote_plus(title.replace(' ', '_'))}"
        results.append(
            Source(
                source_id=uuid4(),
                session_id=session_id,
                title=title,
                url=page_url,
                canonical_url=page_url,
                publisher_or_venue="Wikipedia",
                published_date=_parse_date(item.get("timestamp", "")[:10]),
                source_type="web",
                abstract=_strip_html(item.get("snippet")),
                raw_payload={"connector": "web", "item": item},
            )

        )
    return results


def _search_openalex(query: str, session_id: UUID) -> list[Source]:
    encoded = quote_plus(query)
    api_url = f"https://api.openalex.org/works?search={encoded}&per-page=5"

    try:
        payload = _fetch_json(api_url)
    except Exception:
        return []

    results: list[Source] = []
    for work in payload.get("results", []):
        authors = [author.get("author", {}).get("display_name", "") for author in work.get("authorships", [])]
        authors = [name for name in authors if name]

        primary_location = work.get("primary_location") or {}
        source = primary_location.get("source") or {}
        landing_page_url = primary_location.get("landing_page_url") or work.get("id")

        results.append(
            Source(
                source_id=uuid4(),
                session_id=session_id,
                title=work.get("display_name") or "Untitled",
                url=landing_page_url,
                canonical_url=landing_page_url,
                authors=authors,
                publisher_or_venue=source.get("display_name") or "OpenAlex",
                published_date=_parse_date(work.get("publication_date")),
                source_type="paper",
                doi=(work.get("doi") or "").replace("https://doi.org/", "") or None,
                openalex_id=work.get("id"),
                abstract=_strip_html(work.get("abstract")),
                raw_payload={"connector": "openalex", "work": work},
            )
        )

    return results


def _search_crossref(query: str, session_id: UUID) -> list[Source]:
    encoded = quote_plus(query)
    api_url = f"https://api.crossref.org/works?query={encoded}&rows=5"

    try:
        payload = _fetch_json(api_url)
    except Exception:
        return []

    items = payload.get("message", {}).get("items", [])
    results: list[Source] = []
    for item in items:
        title = (item.get("title") or ["Untitled"])[0]
        authors = []
        for author in item.get("author", []):
            given = author.get("given", "")
            family = author.get("family", "")
            full_name = f"{given} {family}".strip()
            if full_name:
                authors.append(full_name)

        doi = item.get("DOI")
        url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")
        issued = item.get("issued", {}).get("date-parts", [])
        published_date = None
        if issued and issued[0]:
            parts = issued[0]
            year = parts[0]
            month = parts[1] if len(parts) > 1 else 1
            day = parts[2] if len(parts) > 2 else 1
            try:
                published_date = date(year, month, day)
            except ValueError:
                published_date = None

        results.append(
            Source(
                source_id=uuid4(),
                session_id=session_id,
                title=title,
                url=url,
                canonical_url=url,
                authors=authors,
                publisher_or_venue=(item.get("container-title") or ["Crossref"])[0],
                published_date=published_date,
                source_type="paper",
                doi=doi,
                abstract=_strip_html(item.get("abstract")),
                raw_payload={"connector": "crossref", "item": item},
            )
        )

    return results


def _search_semantic_scholar(query: str, session_id: UUID) -> list[Source]:
    encoded = quote_plus(query)
    api_url = (
        "https://api.semanticscholar.org/graph/v1/paper/search?"
        f"query={encoded}&limit=5&fields=title,url,authors,venue,year,abstract,externalIds"
    )

    try:
        payload = _fetch_json(api_url)
    except Exception:
        return []

    results: list[Source] = []
    for paper in payload.get("data", []):
        authors = [author.get("name", "") for author in paper.get("authors", [])]
        authors = [name for name in authors if name]

        external_ids = paper.get("externalIds") or {}
        doi = external_ids.get("DOI")
        semantic_scholar_id = external_ids.get("CorpusId") or external_ids.get("ArXiv")
        paper_url = paper.get("url") or (f"https://doi.org/{doi}" if doi else "")

        published_date = None
        year = paper.get("year")
        if isinstance(year, int):
            try:
                published_date = date(year, 1, 1)
            except ValueError:
                published_date = None

        results.append(
            Source(
                source_id=uuid4(),
                session_id=session_id,
                title=paper.get("title") or "Untitled",
                url=paper_url,
                canonical_url=paper_url,
                authors=authors,
                publisher_or_venue=paper.get("venue") or "Semantic Scholar",
                published_date=published_date,
                source_type="paper",
                doi=doi,
                semantic_scholar_id=semantic_scholar_id,
                abstract=_strip_html(paper.get("abstract")),
                raw_payload={"connector": "semantic_scholar", "paper": paper},
            )
        )

    return results


def _search_arxiv(query: str, session_id: UUID) -> list[Source]:
    encoded = quote_plus(query)
    api_url = f"http://export.arxiv.org/api/query?search_query=all:{encoded}&start=0&max_results=5"

    try:
        request = Request(api_url, headers={"User-Agent": "ai-researcher-mvp/0.1 (+retrieval-service)"})
        with urlopen(request, timeout=12) as response:
            payload = response.read().decode("utf-8")
    except Exception:
        return []

    try:
        root = ElementTree.fromstring(payload)
    except ElementTree.ParseError:
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    results: list[Source] = []

    for entry in root.findall("atom:entry", ns):
        title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
        summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip()
        entry_id = (entry.findtext("atom:id", default="", namespaces=ns) or "").strip()
        published = (entry.findtext("atom:published", default="", namespaces=ns) or "").strip()

        authors = []
        for author_el in entry.findall("atom:author", ns):
            name = (author_el.findtext("atom:name", default="", namespaces=ns) or "").strip()
            if name:
                authors.append(name)

        published_date = _parse_date(published[:10])
        arxiv_id = entry_id.rsplit("/", 1)[-1] if entry_id else None

        results.append(
            Source(
                source_id=uuid4(),
                session_id=session_id,
                title=title or "Untitled",
                url=entry_id,
                canonical_url=entry_id,
                authors=authors,
                publisher_or_venue="arXiv",
                published_date=published_date,
                source_type="paper",
                arxiv_id=arxiv_id,
                abstract=_strip_html(summary),
                raw_payload={"connector": "arxiv", "entry_id": entry_id},
            )
        )

    return results


def _deduplicate_sources(candidates: list[Source]) -> list[Source]:
    seen: set[str] = set()
    deduped: list[Source] = []

    for source in candidates:
        doi_key = f"doi:{(source.doi or '').strip().lower()}" if source.doi else ""
        url_key = f"url:{source.canonical_url.strip().lower()}" if source.canonical_url else ""
        title_key = f"title:{source.title.strip().lower()}"

        key = doi_key or url_key or title_key
        if not key or key in seen:
            continue

        seen.add(key)
        deduped.append(source)

    return deduped



def _evaluate_sources(sources: list[Source]) -> list[SourceEvaluation]:
    evaluations: list[SourceEvaluation] = []
    for source in sources:
        relevance_score = 0.8
        credibility_score = 0.8 if source.source_type == "paper" else 0.65

        recency_score = 0.5
        if source.published_date:
            age_years = max(0, int((date.today() - source.published_date).days / 365))
            recency_score = max(0.3, min(1.0, 1 - (age_years / 10)))

        corroboration_score = 0.75 if source.doi else 0.6

        metadata_fields = [
            bool(source.title),
            bool(source.url),
            bool(source.authors),
            bool(source.publisher_or_venue),
            bool(source.published_date),
            bool(source.doi),
            bool(source.abstract),
        ]
        metadata_completeness_score = sum(metadata_fields) / len(metadata_fields)

        overall_score = (
                (relevance_score * 0.30)
                + (credibility_score * 0.25)
                + (recency_score * 0.15)
                + (corroboration_score * 0.10)
                + (metadata_completeness_score * 0.20)
        )
        decision = "keep" if overall_score >= 0.65 else "discard"
        flags = []
        if source.source_type == "web":
            flags.append("non_peer_reviewed")
        if not source.doi and source.source_type == "paper":
            flags.append("missing_doi")

        evaluations.append(
            SourceEvaluation(
                evaluation_id=uuid4(),
                source_id=source.source_id,
                relevance_score=round(relevance_score, 2),
                credibility_score=round(credibility_score, 2),
                recency_score=round(recency_score, 2),
                corroboration_score=round(corroboration_score, 2),
                metadata_completeness_score=round(metadata_completeness_score, 2),
                overall_score=round(overall_score, 2),
                reasoning=[
                    f"Source type: {source.source_type}",
                    f"DOI present: {'yes' if source.doi else 'no'}",
                    f"Metadata completeness: {round(metadata_completeness_score, 2)}",
                ],
                decision=decision,
                flags=flags,
                latency_ms=5,
            )
        )

    return evaluations


def _summarize_sources(sources: list[Source], evaluations: list[SourceEvaluation]) -> list[SourceSummary]:
    evaluation_by_source = {evaluation.source_id: evaluation for evaluation in evaluations}

    summaries: list[SourceSummary] = []
    for index, source in enumerate(sources, start=1):
        evaluation = evaluation_by_source.get(source.source_id)
        score = evaluation.overall_score if evaluation else 0.0
        source_label = source.publisher_or_venue or source.source_type

        summaries.append(
            SourceSummary(
                note_id=uuid4(),
                source_id=source.source_id,
                concise_summary=(
                    f"{source.title} is a {source.source_type} source from {source_label} "
                    f"with an overall evidence score of {score}."
                ),
                key_claims=[
                    source.abstract or f"{source.title} was retrieved for query coverage.",
                    ],
                methods=["Connector retrieval", "Schema normalization", "Deterministic scoring"],
                limitations=[
                    "Automated extraction may omit method details.",
                    "Scores are heuristic and not model-generated.",
                ],
                counterpoints=["Cross-source contradiction checks are not yet implemented."],
                evidence_snippets=[{"text": source.title, "location": "title"}],
                citation_anchor=f"[S{index}]",
            )
        )
    return summaries


def _generate_report(
    session: ResearchSession,
    summaries: list[SourceSummary],
    sources: list[Source],
) -> FinalReport:
    return FinalReport(
        report_id=uuid4(),
        session_id=session.session_id,
        executive_summary=(
            f"Retrieved {len(sources)} deduplicated sources from web and scholarly connectors "
            "for initial evidence mapping."
        ),
        answer=f"Initial evidence set assembled for query: {session.query}",
        key_findings=[summary.concise_summary for summary in summaries],
        competing_views=["Contradiction mining is pending implementation."],
        limitations=[
            "Current report is heuristic and connector-driven.",
            "No iterative planning loop has been applied.",
        ],
        evidence_gaps=["Need deeper extraction of methods, outcomes, and contradictions."],
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
