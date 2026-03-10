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

function App() {
    const [query, setQuery] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [result, setResult] = useState<ResearchResponse | null>(null)

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
            } catch (requestError) {
                setError(requestError instanceof Error ? requestError.message : 'Unknown request error')
            } finally {
                setLoading(false)
            }
        })()
    }



  return (
      <main className="app-shell">
          <h1>Run Research</h1>
          <form onSubmit={onSubmit} className="query-form">
              <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Enter a research question..."
              />
              <button type="submit" disabled={loading}>
                  {loading ? 'Running...' : 'Run'}
              </button>
          </form>

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
