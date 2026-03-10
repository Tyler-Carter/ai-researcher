import { useState } from 'react'
import type { ComponentProps } from 'react'
import './App.css'

type ResearchResponse = {
    session_id: string
    artifacts: {
        session: unknown
        plan: unknown
        sources: unknown[]
        evaluations: unknown[]
        summaries: unknown[]
        report: unknown
    }
    report_snapshot: string
}

type ExportFormat = 'markdown' | 'html'

type ExportResponse = {
    session_id: string
    export_format: ExportFormat
    file_path: string
    content: string
}

function App() {
    const [query, setQuery] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [result, setResult] = useState<ResearchResponse | null>(null)
    const [exportingFormat, setExportingFormat] = useState<ExportFormat | null>(null)
    const [exportStatus, setExportStatus] = useState<string | null>(null)


    const onSubmit: NonNullable<ComponentProps<'form'>['onSubmit']> = (event) => {
        event.preventDefault()
        if (!query.trim()) {
            return
        }

        setLoading(true)
        setError(null)

        void (async () => {
            try {
                const response = await fetch('http://localhost:8000/research/run', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query }),
                })

                if (!response.ok) {
                    throw new Error(`Request failed with status ${response.status}`)
                }

                const data = (await response.json()) as ResearchResponse
                setResult(data)
                setExportStatus(null)
            } catch (requestError) {
                setError(requestError instanceof Error ? requestError.message : 'Unknown request error')
            } finally {
                setLoading(false)
            }
        })()
    }

    const onExport = (format: ExportFormat) => {
        if (!result) {
            return
        }

        setExportingFormat(format)
        setError(null)
        setExportStatus(null)

        void (async () => {
            try {
                const response = await fetch(
                    `http://localhost:8000/research/${result.session_id}/export/${format}`,
                    { method: 'GET' },
                )

                if (!response.ok) {
                    throw new Error(`Export failed with status ${response.status}`)
                }

                const data = (await response.json()) as ExportResponse
                const fileExtension = format === 'markdown' ? 'md' : 'html'
                const blob = new Blob([data.content], {
                    type: format === 'markdown' ? 'text/markdown;charset=utf-8' : 'text/html;charset=utf-8',
                })
                const downloadUrl = URL.createObjectURL(blob)
                const anchor = document.createElement('a')
                anchor.href = downloadUrl
                anchor.download = `research-${data.session_id}.${fileExtension}`
                document.body.appendChild(anchor)
                anchor.click()
                anchor.remove()
                URL.revokeObjectURL(downloadUrl)

                setExportStatus(`Downloaded ${format} export.`)
            } catch (exportError) {
                setError(exportError instanceof Error ? exportError.message : 'Unknown export error')
            } finally {
                setExportingFormat(null)
            }
        })()
    }

    return (
      <main className="app-shell">
          <form onSubmit={onSubmit} className="form-wrapper cf">
              <input
                  type="text"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Enter a research question..."
              />
              <div className="button">
                  <button type="submit" disabled={loading}>
                      {loading ? 'Running...' : 'Run'}
                  </button>
              </div>
          </form>
          <div className="byline"><p>Export Options</p></div>
          <div className="button">
              <button
                  type="button"
                  onClick={() => onExport('html')}
                  disabled={exportingFormat !== null || result === null}
              >
                  {exportingFormat === 'html' ? 'Exporting HTML...' : 'HTML'}
              </button>
              <button
                  type="button"
                  onClick={() => onExport('markdown')}
                  disabled={exportingFormat !== null || result === null}
              >
                  {exportingFormat === 'markdown' ? 'Exporting Markdown...' : 'Markdown'}
              </button>
          </div>
          <div className="byline"><p>{exportStatus ? <p className="export-status">{exportStatus}</p> : null}</p>
          </div>

          {error ? <p className="error">{error}</p> : null}

          {result ? (
              <section className="results">
                  <h2>Session: {result.session_id}</h2>
                  <article>
                      <h3>Plan</h3>
                      <pre>{JSON.stringify(result.artifacts.plan, null, 2)}</pre>
                  </article>
                  <article>
                      <h3>Sources</h3>
                      <pre>{JSON.stringify(result.artifacts.sources, null, 2)}</pre>
                  </article>
                  <article>
                      <h3>Evaluations</h3>
                      <pre>{JSON.stringify(result.artifacts.evaluations, null, 2)}</pre>
                  </article>
                  <article>
                      <h3>Summaries</h3>
                      <pre>{JSON.stringify(result.artifacts.summaries, null, 2)}</pre>
                  </article>
                  <article>
                      <h3>Report</h3>
                      <pre>{JSON.stringify(result.artifacts.report, null, 2)}</pre>
                      <p>
                          <strong>Snapshot:</strong> {result.report_snapshot}
                      </p>
                  </article>
              </section>
          ) : null}
      </main>
  )
}

export default App
