from __future__ import annotations

from packages.orchestration.run_pipeline import PipelineArtifacts


def build_markdown_report(artifacts: PipelineArtifacts) -> str:
    report = artifacts.report
    sources_by_id = {str(source.source_id): source for source in artifacts.sources}

    lines: list[str] =[
        "# Research Report",
        "",
        f"**Session ID:** `{artifacts.session.session_id}`",
        f"**Query:** {artifacts.session.query}",
        "",
        "## Execution Summary",
        report.executive_summary,
        "",
        "## Answer",
        report.answer,
        "",
        "## Key Findings",
    ]

    for finding in report.key_findings:
        lines.append(f"- {finding}")

    lines.extend(["", "## Limitations"])
    for limitation in report.limitations:
        lines.append(f"- {limitation}")

    lines.extend(["", "## Evidence Gaps"])
    for gap in report.evidence_gaps:
        lines.append(f"- {gap}")

    lines.extend(["", "## Sources"])
    for index, entry in enumerate(report.source_table, start=1):
        source_id = entry.get("source_id", "")
        title = entry.get("title", "Untitled")
        source = sources_by_id.get(source_id)
        source_url = source.url if source else ""

        citation = f"[S{index}]"
        if source_url:
            lines.append(f"- {citation} {title} ({source_url})")
        else:
            lines.append(f"- {citation} {title}")

    lines.extend(["", "## Trace", f"- Session trace reference: `{report.appendix_trace_ref}`", ""])
    return "\n".join(lines)
