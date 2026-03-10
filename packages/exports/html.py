from __future__ import annotations

from html import escape

from packages.orchestration.run_pipeline import PipelineArtifacts


def build_html_report(artifacts: PipelineArtifacts) -> str:
    report = artifacts.report

    findings_html = "".join(f"<li>{escape(finding)}</li>" for finding in report.key_findings)
    limitations_html = "".join(f"<li>{escape(limitation)}</li>" for limitation in report.limitations)
    gaps_html = "".join(f"<li>{escape(gap)}</li>" for gap in report.evidence_gaps)

    source_rows: list[str] = []
    for index, entry in enumerate(report.source_table, start=1):
        title = escape(entry.get("title", "Untitled"))
        source_id = escape(entry.get("source_id", ""))
        source_rows.append(
            "<tr>"
            f"<td>[S{index}]</td>"
            f"<td>{title}</td>"
            f"<td><code>{source_id}</code></td>"
            "</tr>"
        )

    table_html = "".join(source_rows)

    return f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>Research Report</title>
  </head>
  <body>
    <h1>Research Report</h1>
    <p><strong>Session ID:</strong> <code>{escape(str(artifacts.session.session_id))}</code></p>
    <p><strong>Query:</strong> {escape(artifacts.session.query)}</p>

    <h2>Executive Summary</h2>
    <p>{escape(report.executive_summary)}</p>

    <h2>Answer</h2>
    <p>{escape(report.answer)}</p>

    <h2>Key Findings</h2>
    <ul>{findings_html}</ul>

    <h2>Limitations</h2>
    <ul>{limitations_html}</ul>

    <h2>Evidence Gaps</h2>
    <ul>{gaps_html}</ul>

    <h2>Sources</h2>
    <table border=\"1\" cellpadding=\"6\" cellspacing=\"0\">
      <thead>
        <tr><th>Citation</th><th>Title</th><th>Source ID</th></tr>
      </thead>
      <tbody>{table_html}</tbody>
    </table>

    <h2>Trace</h2>
    <p>Session trace reference: <code>{escape(report.appendix_trace_ref)}</code></p>
  </body>
</html>
"""