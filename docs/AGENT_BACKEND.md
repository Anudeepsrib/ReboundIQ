# Agent Backend

ReboundIQ's backend exposes a supervised CareerCampaignAgent under `/api/v1/agents`.

## Safety Model

- Local AI remains the default through `AIGateway`.
- LangChain/LangGraph/Deep Agents use `GatewayChatModel`, which delegates model calls back to `AIGateway`.
- Agent nodes orchestrate deterministic typed tools; they do not auto-apply resumes, auto-send outreach, or fabricate claims.
- ComplianceGuard runs before approval. High-severity findings block the checkpoint.
- User-facing artifacts require human approval in `agent_approval_requests`.
- All campaign tools log to `agent_tool_calls`; AI calls log structured events and best-effort `ai_requests` rows.

## Endpoints

- `POST /api/v1/agents/campaigns` creates a campaign and optionally runs it.
- `GET /api/v1/agents/campaigns` lists the authenticated user's campaigns.
- `GET /api/v1/agents/campaigns/{campaign_id}` reads one user-owned campaign.
- `POST /api/v1/agents/campaigns/{campaign_id}/run` runs or reruns the graph.
- `GET /api/v1/agents/campaigns/{campaign_id}/approvals` lists campaign approvals.
- `GET /api/v1/agents/approvals` lists approvals for the authenticated user.
- `POST /api/v1/agents/approvals/{approval_id}/decide` approves or rejects a checkpoint.

## Observability

Set `LANGSMITH_TRACING=true`, `LANGSMITH_PROJECT`, and `LANGSMITH_API_KEY` to trace LangGraph/LangChain runs in LangSmith. `LANGGRAPH_CHECKPOINT_BACKEND=postgres` enables the async Postgres checkpointer; local development defaults to memory checkpoints while persisting final state in `agent_campaigns.metadata_json`.

