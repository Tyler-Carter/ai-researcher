# AGENTS.md

This file provides Codex operating guidance for the **Windows app environment** and is grounded in official OpenAI documentation.

## Scope

- Applies to Codex usage in this repository when running from the Codex Windows app.
- Prefer repository-local instructions here; use global defaults in `%USERPROFILE%\.codex\AGENTS.md` only for cross-repo behavior.

## Verified Codex Behavior (Windows App)

- Codex app on Windows runs with native Windows sandbox + PowerShell by default, and can be switched to WSL.
- The Windows app and native Windows Codex share the same Codex home: `%USERPROFILE%\.codex`.
- If using WSL and you want shared auth/config/session state, set `CODEX_HOME=/mnt/c/Users/<windows-user>/.codex` in WSL.
- Git must be installed on Windows for some app review/git features.

## AGENTS.md Discovery and Precedence

Codex instruction discovery order (highest-level to closest context):

1. Global scope in Codex home: `AGENTS.override.md` (if present), else `AGENTS.md`.
2. Project scope from project root to current working directory: per directory, `AGENTS.override.md` then `AGENTS.md` then configured fallback filenames.
3. Merge order is root to current directory; files closer to current directory win by being appended later.

## Repository Conventions for Codex

- Use `rg`/`rg --files` for search whenever available.
- Keep edits minimal and focused to the requested task.
- Do not run destructive git/file operations unless explicitly requested.
- After code changes, run the smallest relevant tests/lint first; expand only if needed.
- For substantial frontend/backend changes in this repo, run `npm run lint` before finalizing.
- Update `docs/progress_tracking.md` with any steps performed as part of an implementation / task.

## Project Parameters (from README.md)

- Product target: build a schema-constrained research orchestration system (`planner -> retrieval -> evaluation -> summarization -> report`) with traceability and citations.
- Contract-first rule: keep stage handoffs in typed schemas; validate model outputs against schema and server-side models before passing to the next stage.
- Retrieval scope target: web + scholarly connectors (OpenAlex, Crossref, Semantic Scholar, arXiv) with normalization and deduplication.
- Evaluation baseline: transparent scoring with deterministic heuristics first; keep/discard decisions must be auditable.
- Report requirements: citation-backed claims, contradictions/mixed-evidence handling, limitations, and evidence gaps.
- Provider instrumentation: persist provider/model/prompt/schema versions plus latency/token/cost metadata for each model-driven stage.
- Implementation sequencing: prioritize Layer 1 MVP flow end-to-end before iterative loops/domain packs/benchmark dashboard features.

## Common Commands (Current Repo)

- Install dependencies: `npm install`
- Start dev server: `npm run dev`
- Build: `npm run build`
- Lint: `npm run lint`
- Preview production build: `npm run preview`

## Current Implementation Reality

- The current checked-in app is frontend-first (`frontend/` + Vite scripts in root `package.json`).
- Treat `README.md` as target architecture/specification; do not assume all backend/services/modules listed there already exist.

## Windows Operational Notes

- If commands require elevation, run the Codex app as Administrator (agent inherits elevation).
- If PowerShell blocks scripts, use organizational policy guidance first; `RemoteSigned` is a common documented fix:
  `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned`

## Sources (Official / Verifiable)

- Codex AGENTS.md guide: https://developers.openai.com/codex/guides/agents-md
- Codex Windows app guide: https://developers.openai.com/codex/app/windows
- Codex docs index (navigation for App/Rules/AGENTS/Windows): https://developers.openai.com/codex
- OpenAI Help: Codex app available on Windows (March 4, 2026): https://help.openai.com/en/articles/6825453-chatgpt-release-notes
- OpenAI Help: Using Codex with your ChatGPT plan (includes Windows app availability): https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan
- OpenAI Codex GitHub README (`codex app`, ChatGPT sign-in flow): https://github.com/openai/codex
