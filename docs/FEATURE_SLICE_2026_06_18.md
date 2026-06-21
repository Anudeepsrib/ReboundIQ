# Feature Slice: Deterministic Career Workflows

Date: 2026-06-18

## Scope

This slice expands the web app from the initial Resume/JD vertical into a broader local-first ReboundIQ demo:

- Runway Planner at `/runway`
- Application Tracker at `/applications`
- Proof-of-Work Builder at `/proof`
- Interview Prep at `/interview`
- Campaign approval cockpit at `/campaigns`
- Dashboard and navigation updates for the full workflow set
- Local model picker at `/settings/ai-providers`

## Implementation Notes

- These features are client-side and deterministic.
- No external AI calls were added.
- No backend provider calls were added outside the existing AI Gateway paths.
- No database schema changes or Alembic migrations were required.
- Browser-local storage is used only for demo state on application, proof, and interview pages.
- Campaigns remain supervised workflow UI only; they do not run autonomous agents, auto-apply, auto-send, or auto-edit user artifacts.
- Local Ollama chat and embedding model choices can be changed at runtime for the API process.
- Suggested local model tags include Gemma-style and other Ollama models, and users can type any pulled local tag.

## Safety Notes

- Runway outputs are planning guidance and risk signals only.
- Proof drafts preserve missing evidence instead of inventing claims.
- Interview scores are local practice signals, not hiring predictions.
- Application actions remain manual.
- Campaign approval statuses are explicit human checkpoints.

## Follow-Up Work

- Replace browser-local state with authenticated API-backed CRUD using user_id isolation.
- Add Alembic migrations for applications, proof assets, interview attempts, runway snapshots, and approval requests.
- Add eval cases before AI generation is introduced for proof, interview, outreach, or campaign artifacts.
- Wire future generation only through AIGateway, RedactionService, ComplianceGuardAgent, audit logs, citations, and human approval.
- Persist per-user local model preferences through an authenticated settings API instead of process-local runtime settings.
