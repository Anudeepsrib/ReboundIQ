# ReboundIQ

**A local-first layoff-to-offer operating system for technical professionals.**

ReboundIQ helps laid-off or transitioning engineers, AI/data practitioners, PMs,
designers, analysts, and technical leads turn career recovery into a structured
workflow: runway planning, resume evidence, job targeting, proof-of-work,
applications, interview preparation, and supervised campaign planning.

The product is built around a simple rule: personal career data stays private by
default. Local Ollama AI is the default path, external AI is disabled until the
user opts in, and deterministic backend services remain authoritative.

## Product Promise

- **Local-first AI**: Ollama is the default provider. The app works without paid
  model APIs.
- **Privacy-first workflows**: every user-owned record is scoped by
  authenticated `user_id`; sensitive AI and memory paths require consent.
- **Evidence-based career artifacts**: resumes, proof stories, and campaign
  artifacts must be grounded in user-provided facts and citations.
- **Human control**: ReboundIQ never auto-applies, auto-sends outreach, or
  silently edits user-facing artifacts.
- **Planning guidance only**: runway, sponsorship, offer, and risk surfaces are
  guidance and risk signals, not legal, immigration, financial, tax, medical, or
  hiring advice.

## Available Now

- **Career dashboard** for the layoff-to-offer operating loop.
- **Runway planner** with persisted snapshots for expenses, savings, severance,
  unemployment assumptions, scenarios, and action items.
- **Application tracker** with authenticated records for company, role, stage,
  JD snapshot, next step, fit score, sponsorship signal, and resume version link.
- **Proof-of-work builder** with persisted STAR stories, case studies,
  architecture notes, GitHub README drafts, LinkedIn posts, citations, and
  application links.
- **Interview prep** with persisted sessions, focus areas, question logs,
  feedback, scores, scheduling, and application links.
- **Resume upload and parsing** with immutable original storage, parsed data,
  versions, private document chunks, and local embedding support.
- **JD analysis** through the AI Gateway with request IDs, user isolation, and
  groundedness/confidence signals.
- **AI provider settings** for local Ollama status, installed model discovery,
  suggested local tags, and runtime local model selection.
- **Supervised agent backend** for CareerCampaignAgent campaigns, typed tools,
  ComplianceGuard checks, tool-call audit logs, and human approval checkpoints.
- **Golden evals** for safety, groundedness, redaction, schema, tool fidelity,
  and campaign compliance behavior.

## Architecture

| Layer | Stack | Notes |
| --- | --- | --- |
| Web | Next.js 15 App Router, TypeScript, Tailwind | Product workflows live under `apps/web/app` with local-first fallbacks. |
| API | FastAPI, Pydantic v2, SQLAlchemy 2.0 async | Business logic lives in services; routes stay thin and authenticated. |
| Data | Postgres, pgvector, Alembic | Workflow tables, resumes, memory, audit, agents, approvals, and document chunks. |
| AI | `AIGateway`, Ollama, optional LiteLLM-compatible external providers | No business code calls providers directly. External AI requires consent and redaction. |
| Agents | LangGraph / Deep Agents patterns | Agents orchestrate deterministic typed tools and approval checkpoints. |
| Storage | `StorageService` protocol | Originals are preserved; user-isolated keys are required. |
| Evals | `make eval`, JSONL golden cases | Safety, citation, schema, redaction, groundedness, and compliance checks. |

## API Surface

Core authenticated backend routes include:

- `POST /api/v1/auth/register`, `POST /api/v1/auth/login`,
  `GET /api/v1/auth/me`
- `POST /api/v1/resumes/upload`,
  `POST /api/v1/resumes/{resume_id}/versions`, `GET /api/v1/resumes`
- `POST /api/v1/jobs/analyze`
- `GET /api/v1/ai/status`, `GET /api/v1/ai/local-models`,
  `POST /api/v1/ai/local-models/select`
- `GET|POST /api/v1/runway/snapshots`,
  `PATCH|DELETE /api/v1/runway/snapshots/{snapshot_id}`
- `GET|POST /api/v1/applications`,
  `PATCH|DELETE /api/v1/applications/{application_id}`
- `GET|POST /api/v1/proof/assets`,
  `PATCH|DELETE /api/v1/proof/assets/{asset_id}`
- `GET|POST /api/v1/interviews/sessions`,
  `PATCH|DELETE /api/v1/interviews/sessions/{session_id}`
- `POST /api/v1/agents/campaigns`,
  `POST /api/v1/agents/campaigns/{campaign_id}/run`,
  `GET /api/v1/agents/approvals`,
  `POST /api/v1/agents/approvals/{approval_id}/decide`

All workflow CRUD paths are deterministic and user-isolated. They do not invoke
AI, send messages, apply jobs, or generate user-facing artifacts.

## Quick Start

```powershell
git clone <your-fork-or-repo> ReboundIQ
cd ReboundIQ

Copy-Item .env.example .env

# Full local stack: Postgres + pgvector, Redis, Ollama, MinIO, API, web
make dev

# Apply schema and seed synthetic demo data
make migrate
make seed
```

Open:

- Web app: http://localhost:3000
- API docs: http://localhost:8000/docs
- API health: http://localhost:8000/health
- MinIO console: http://localhost:9001

First Ollama boot can take several minutes while local models are pulled. See
[docs/LOCAL_AI_SETUP.md](docs/LOCAL_AI_SETUP.md) for Windows, WSL2, Docker
Desktop, and CPU model notes.

## Local Development

```bash
make backend    # FastAPI only
make frontend   # Next.js only
make migrate    # Alembic upgrade head
make test       # Backend pytest + frontend check target
make lint       # Ruff, mypy, eslint, prettier
make eval       # Golden safety/eval suite
make down       # Stop and remove local compose volumes
```

Useful direct commands:

```bash
cd apps/api && python -m pytest tests -q
cd apps/api && alembic heads
cd apps/web && npm run build
```

## Safety Model

ReboundIQ treats career AI as a high-trust surface:

- external AI is off by default;
- redaction is required before any external call;
- all AI requests flow through `AIGateway`;
- ComplianceGuard runs on generation paths;
- user-facing artifacts require human approval checkpoints;
- personal claims require citations or explicit missing-data language;
- memory is evidence only and never overrides current user input or safety rules;
- every service query must filter by authenticated `user_id`;
- AI requests, agent tool calls, memory events, and actions are auditable.

See [AGENTS.md](AGENTS.md) and [docs/AGENT_BACKEND.md](docs/AGENT_BACKEND.md)
for the implementation rules that coding agents and contributors must preserve.

## Repository Map

```text
.
├── apps/
│   ├── api/                 # FastAPI backend
│   │   ├── app/
│   │   │   ├── ai/          # AIGateway, redaction, memory
│   │   │   ├── agents/      # supervised campaign orchestration
│   │   │   ├── api/v1/      # HTTP routes
│   │   │   ├── models/      # SQLAlchemy models
│   │   │   ├── schemas/     # Pydantic API contracts
│   │   │   └── services/    # deterministic business logic
│   │   ├── alembic/         # migrations
│   │   └── tests/           # backend tests
│   └── web/                 # Next.js frontend
├── docs/                    # product, setup, agent, and feature docs
├── infra/                   # Docker/Postgres initialization
├── tests/evals/goldens/     # safety and groundedness eval fixtures
├── docker-compose.yml
├── Makefile
└── AGENTS.md
```

## Documentation

- [User Guide](docs/USER_GUIDE.md)
- [Local AI Setup](docs/LOCAL_AI_SETUP.md)
- [Agent Backend](docs/AGENT_BACKEND.md)
- [Feature Slice Notes](docs/FEATURE_SLICE_2026_06_18.md)
- [Agent Guidelines](AGENTS.md)

## Roadmap

- Wire the web workflow pages to the authenticated workflow APIs.
- Add authenticated user export and hard-delete flows across all product tables.
- Persist per-user local AI preferences instead of process-local runtime
  selection.
- Expand proof, interview, outreach, and campaign generation only through
  `AIGateway`, redaction, ComplianceGuard, citations, eval cases, and human
  approval.
- Add production deployment hardening: rate limits, RLS policies, encryption for
  optional sensitive fields, backups, and operational dashboards.

## License

MIT. See [LICENSE](LICENSE).

**Review everything. Use AI as planning support, not as a substitute for human
judgment or professional advice.**
