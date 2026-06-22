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

- These features are deterministic.
- No external AI calls were added.
- No backend provider calls were added outside the existing AI Gateway paths.
- Backend persistence now covers runway snapshots, application records, proof assets, and interview sessions through authenticated CRUD APIs.
- Alembic migration `0004_workflow_records.py` adds these product workflow tables with `user_id` isolation, soft delete fields, and focused indexes.
- Browser-local state remains useful as an offline fallback in the web app, but the backend gap for product workflow persistence is closed.
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

- Wire the web pages from browser-local state to the authenticated workflow APIs.
- Add eval cases before AI generation is introduced for proof, interview, outreach, or campaign artifacts.
- Wire future generation only through AIGateway, RedactionService, ComplianceGuardAgent, audit logs, citations, and human approval.
- Persist per-user local model preferences through an authenticated settings API instead of process-local runtime settings.
