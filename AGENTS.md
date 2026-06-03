# ReboundIQ Agent Guidelines (for AI coding assistants)

This project must remain production-grade, privacy-first, and safety-compliant.

## Non-Negotiables (never violate)
- Local AI (Ollama) default. External AI disabled by default. Explicit user consent + PII redaction (RedactionService) before any external call. All AI via single AIGateway.
- Deterministic services are authoritative. Deep Agents (LangGraph CareerCampaignAgent + subagents) ONLY orchestrate; they delegate to services, use typed tools, request human approval for artifacts, never auto-apply, never auto-send messages, never fabricate metrics/claims/employer names.
- ComplianceGuardAgent + redaction + consent checks on every generation path. Memory (Hindsight or built-in) is evidence only — pre-use validation (freshness, consent, sensitivity, contradiction with current user input) + priority to explicit user data. Never overrides system prompts, disclaimers, or safety.
- No legal/immigration/financial/tax/medical advice. Phrase as "planning guidance" and "risk signals". Hard disclaimers in UI + prompts.
- Groundedness: RAG citations required for personal claims. If data missing, say so. Never hallucinate employment history, metrics, titles.
- User isolation: every query/service must filter by authenticated user_id. Row-level checks.
- Audit everything AI: ai_requests, agent_tool_calls, memory_* , action_audit_logs.
- Export + delete: full user data export and hard delete (with cascade where appropriate).
- No secrets in code or committed .env.

## Code Patterns
- Backend: FastAPI + SQLA 2.0 (Mapped) + Pydantic v2. Use async where possible. Alembic only for schema.
- AI: Never call provider directly in business code. Use gateway.chat / .structured / .embed. Pass request_id, user_id for audit.
- Agents: Use LangGraph StateGraph with Pydantic/ TypedDict state, PostgresSaver or Redis+DB checkpointer. Human checkpoints via interrupt or explicit approval_request table + UI.
- Frontend: Next 15 App Router. Server components + RSC where possible. Client only for interactive (forms, mock interview, kanban drag). All mutations via TanStack Query + server actions or route handlers. Zod + RHF for forms. shadcn/ui.
- Storage: Use the StorageService protocol. Never delete originals. User-isolated paths.
- Memory: Always go through MemoryProvider (default Postgres + pgvector). Hindsight only if explicitly enabled + consent per category.
- Tests/Evals: Golden cases in tests/evals/ and apps/api/app/evals/. Run via make eval. Include groundedness, citation, schema, safety (no forbidden claims), redaction, tool fidelity, compliance block rate.
- Docker: Named volumes. No host path binds in compose for Win compatibility. pgvector image. Ollama CPU model for dev.

## When Adding Features
1. Update design doc or note deviation.
2. Add Alembic migration (never edit models only).
3. Add to OpenAPI via Pydantic.
4. Add eval case if AI output.
5. Add to seed if demo data.
6. Update docs/ if user-facing.
7. Ensure redaction + compliance + human approval where external action or artifact.
8. Log with request_id / campaign_id / thread_id.

## Safety Review Checklist (for every PR touching generation)
- [ ] RedactionService called pre-external?
- [ ] ComplianceGuardAgent (or equivalent) ran and passed?
- [ ] Human approval checkpoint present for user-facing artifact?
- [ ] Citations / source inputs shown in UI?
- [ ] Disclaimers present?
- [ ] No auto external actions?
- [ ] User consent respected for memory / external AI / sensitive?
- [ ] Tests + eval cases updated?

Violations block merge.

See SECURITY.md, PRIVACY.md, EVALUATION.md, AI_PROVIDER_GUIDE.md.
