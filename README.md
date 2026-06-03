# ReboundIQ — Layoff-to-Offer AI Copilot

> **From layoff shock to structured execution: runway, resume, proof, applications, interviews, and offer readiness.**

ReboundIQ is a **production-grade, local-first, privacy-first AI career recovery operating system** built for laid-off or transitioning technical professionals (software/AI/data engineers, PMs, designers, analysts, technical leads).

It supports H-1B / STEM OPT / sponsorship-sensitive candidates and senior professionals who need rigorous, evidence-based execution — not another job board or generic resume builder.

## Core Philosophy
- **Local AI by default** (Ollama / vLLM) — fully functional with zero paid API keys.
- **Provider-neutral AI Gateway** — switch seamlessly between local and any LiteLLM-compatible provider (OpenAI, Anthropic, Gemini, Groq, Together, Mistral, Azure, Bedrock, etc.).
- **External AI is opt-in only** — disabled by default + explicit consent + mandatory PII redaction + full audit.
- **Deterministic services + Deep Agent orchestration** (LangGraph) — agents coordinate; they never replace verified logic or fabricate data.
- **Hindsight Memory** — optional long-term learning layer that improves plans from real outcomes (callbacks, replies, interviews, rejections) while enforcing strict safety.
- **Zero tolerance for hallucination on personal facts** — every claim is grounded or explicitly states data is missing. Compliance Guard blocks unsafe output.
- **No legal / immigration / financial / tax / medical advice** — everything is framed as planning guidance and risk signals.

## Key Features (Full Spec Coverage)
1. **Layoff Recovery Dashboard** — 30/60/90-day plans, weekly goals, multi-dimensional risk indicators (runway, resume, portfolio, interview, visa sensitivity, etc.).
2. **Runway Planner** — expense/savings/severance modeling with conservative/moderate/aggressive scenarios + action checklists (with strong disclaimers).
3. **Resume Intelligence** — PDF/DOCX/TXT upload, structured parsing, ATS scoring, multiple role-targeted versions (AI Engineer, Backend, Data, Technical Lead, etc.). Never overwrites originals. Full version history.
4. **Job Description Analyzer** — deep extraction (skills, seniority, stacks, sponsorship clues, red flags) + evidence-based match score against your profile + rewrite strategy, recruiter message, cover letter drafts + citations.
5. **Proof-of-Work Builder** — STAR stories, case studies, architecture narratives, GitHub READMEs, LinkedIn posts — always cited to your real experience. No fabricated metrics or employers.
6. **Application Tracker** — full pipeline (Saved → Applied → Recruiter → Tech → System Design → Manager → Final → Offer/Rejected/Withdrawn). Scorecards, follow-up suggestions, JD snapshots, resume version linkage. No auto-apply.
7. **Networking & Outreach Copilot** — personalized messages (recruiters, hiring managers, referrals, alumni) with tone options. Manual send only. Tracking + learning from outcomes.
8. **Interview Prep Engine** — question banks (behavioral, system design, coding, AI/RAG, cloud, etc.) generated from your resume + JD + weak areas. Mock interview mode with evaluation + improvement tracking. Cheat sheets.
9. **Offer Readiness** — comp tracking (base/bonus/equity/benefits/immigration support), negotiation points, constraint comparison (disclaimers everywhere).
10. **Visa-Sensitive Career Mode** — optional encrypted fields (H-1B, OPT, GC stage, grace periods, sponsorship needs). Planning guidance only. Attorney-consult flags. Consent required.
11. **Private RAG Knowledge Base** — upload any docs (resumes, JDs, offers, notes, GitHub READMEs). pgvector + citations. Grounded generation only.
12. **Deep Agent Layer** — CareerCampaignAgent supervisor + 7 specialized subagents (ResumeDeep, JDDeep, ProofDeep, OutreachDeep, InterviewDeep, PlannerDeep, ComplianceGuardAgent). Typed tools, state, checkpoints, human approval for artifacts.
13. **Hindsight Memory Layer** — Postgres+pgvector (default) or optional external adapter. Categories, sensitivity levels, consent, reflection after real events. Memory is evidence, never overrides safety rules.
14. **Safety & Compliance** — Compliance Guard on every path. Redaction before external. No fabrication, no spam, full audit, data export + deletion.
15. **Observability & Evals** — structured logs, request IDs, AI usage/cost/latency tracking, golden test cases, hallucination/groundedness/citation/safety checks, `make eval`.
16. **Production Security** — JWT, RBAC-ready isolation, encrypted sensitive fields, rate limiting, secure uploads, consent records.

## Quick Start (Recommended: Docker)

```powershell
# Windows (pwsh) or any OS with Docker + Compose
git clone <your-fork-or-repo> ReboundIQ
cd ReboundIQ

# Copy example env
Copy-Item .env.example .env

# Start full stack (Postgres + pgvector, Redis, Ollama, MinIO, API, Celery worker, Next.js web)
make dev
# or
docker compose up --build -d

# First boot: Ollama pulls a small CPU-friendly model (~1-2 GB). This can take 5-15 min on Windows/WSL2/CPU.
# Wait for health:
docker compose ps

# (Optional but recommended) Explicitly pull models
docker compose exec ollama ollama pull llama3.2:1b
docker compose exec ollama ollama pull nomic-embed-text

# Seed synthetic demo data (no real PII)
make seed

# Open
# Web:   http://localhost:3000
# API:   http://localhost:8000/docs
# MinIO: http://localhost:9001  (user: reboundiq / pass: reboundiqminio123)
```

See `LOCAL_AI_SETUP.md` for Windows/WSL2 specifics, model recommendations, and non-Docker dev setup.

## Makefile (One-Command Workflow)
```bash
make dev        # full local stack
make backend    # uvicorn only
make frontend   # next dev only
make migrate
make seed
make test
make lint
make eval       # AI evaluation suite
make down
```

## Project Structure (Monorepo)
```
reboundiq/
├── apps/
│   ├── api/                 # FastAPI (Python 3.11+)
│   │   ├── app/
│   │   │   ├── ai/          # AIGateway + providers (ollama, litellm)
│   │   │   ├── agents/      # LangGraph Deep Agents + ComplianceGuard
│   │   │   ├── rag/         # Document chunking + pgvector
│   │   │   ├── models/      # SQLAlchemy 2.0 (users, resumes, campaigns, memory_records, ...)
│   │   │   ├── services/    # Business logic (never calls providers directly)
│   │   │   └── evals/       # Golden tests + runner
│   │   └── tests/
│   └── web/                 # Next.js 15 + TypeScript + shadcn/ui
│       ├── app/             # (dashboard, resume, jobs, campaigns, settings, ...)
│       └── components/
├── packages/shared/
├── infra/
│   ├── docker/
│   ├── k8s/
│   └── terraform/ (optional)
├── docs/                    # ARCHITECTURE.md, SECURITY.md, AI_PROVIDER_GUIDE.md, ...
├── .design/                 # (gitignored) — design docs + PR plan from AI architect loop
├── docker-compose.yml
├── docker-compose.prod.yml
├── .pre-commit-config.yaml
├── .dockerignore (in apps/api/, apps/web/ for build contexts)
├── Makefile
└── README.md
```


## Important Disclaimers
**This software provides planning guidance and risk signals only.**  
It is not legal advice, immigration advice, financial advice, tax advice, or medical advice.  
All AI-generated content must be reviewed and edited by a human. Never use unedited output in real applications, messages, or official documents.

## Documentation
- `docs/LOCAL_AI_SETUP.md` (includes Windows/WSL2, Docker Desktop, Ollama CPU notes)
- Other guides (AI_PROVIDER_GUIDE.md, SECURITY.md, PRIVACY.md, EVALUATION.md, DEPLOYMENT.md, API.md, AI_PROVIDER_GUIDE.md) added in subsequent PRs per the plan in design.
- Full design + PR plan: `.design/design-doc-85a840fd.md` (internal, gitignored)
- See also: `.pre-commit-config.yaml`, `.dockerignore` (per-app), AGENTS.md, Makefile targets.

## License
MIT — see LICENSE.

**Review everything. Ground your own career decisions in reality, not AI output.**

## Contributing
See `CONTRIBUTING.md`. All contributions must preserve the strict safety, grounding, consent, and local-first principles.

---

*Built with the help of rigorous design-review loops (design-doc-writer + reviewer personas) and following a 20-step implementation order for a production, not demo, system.*
