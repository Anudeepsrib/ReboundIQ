# ReboundIQ Local-First Demo Release Checklist

Use this checklist before recording, demoing, or shipping the polished career
recovery demo.

## Data And Setup

- [ ] Run `make migrate` from the repo root and confirm Alembic reports one head.
- [ ] Run `make seed` and log in as `maya.patel.demo@reboundiq.local`.
- [ ] Confirm the seeded persona is synthetic and contains no real PII.
- [ ] Confirm `docs/demo/reboundiq_demo_persona.json` matches the demo script.
- [ ] Regenerate screenshots with `python docs/demo/generate_screenshot_assets.py` after changing workflow copy or KPIs.

## Product Journey

- [ ] Dashboard shows live readiness, reminders, weekly plan, safety posture, and no hard-coded progress.
- [ ] Runway planner shows planning guidance only and retains employment, immigration, tax, and financial disclaimers.
- [ ] Resume and JD match surfaces cite source inputs and mark missing metrics instead of inventing claims.
- [ ] Applications cover saved, recruiter, and technical stages with follow-up dates and no auto-apply action.
- [ ] Proof assets show citation requirements and approval state.
- [ ] Interview prep shows focus areas, practice history, and no hiring guarantee.
- [ ] Campaign cockpit has pending approval checkpoints and no auto-send behavior.
- [ ] Privacy settings can export JSON and require typing `DELETE` for hard deletion.

## AI Provider Switching

- [ ] `gemma3:4b` or another pulled Ollama tag can be selected for the demo user.
- [ ] A localhost-style Ollama base URL is accepted.
- [ ] A remote base URL is rejected with the local-provider bypass warning.
- [ ] External AI remains disabled unless both deployment config and user consent are enabled.
- [ ] Redaction and audit language is visible before any external consent is recorded.

## Verification

- [ ] `cd apps/api && python -m pytest tests -q`
- [ ] `cd apps/web && npm run build`
- [ ] `make eval`
- [ ] Browser smoke through `/dashboard`, `/runway`, `/resume`, `/jobs`, `/applications`, `/proof`, `/interview`, `/campaigns`, `/settings/ai-providers`, and `/settings/privacy`.
- [ ] Export/delete smoke with a throwaway seeded demo user.

## Release Narrative

- [ ] Outcome KPIs are framed as demo/product metrics, not guaranteed job outcomes.
- [ ] Competitive differentiation is against categories, not unverified competitor claims.
- [ ] Legal disclaimers remain visible for employment, immigration, tax, and financial decisions.
- [ ] README screenshot paths render in GitHub and local Markdown preview.
- [ ] No secrets, real resumes, real employer-confidential data, or committed `.env` files are present.
