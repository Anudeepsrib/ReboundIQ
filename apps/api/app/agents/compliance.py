from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.ai.redaction import redaction_service


Severity = Literal["low", "medium", "high"]


class ComplianceFinding(BaseModel):
    severity: Severity
    code: str
    message: str


class ComplianceReport(BaseModel):
    passed: bool
    findings: list[ComplianceFinding] = Field(default_factory=list)
    pii_counts: dict[str, int] = Field(default_factory=dict)
    disclaimers: list[str] = Field(default_factory=list)
    citations_required: bool = False


FORBIDDEN_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (
        re.compile(r"\b(guarantee|guaranteed)\b.*\b(job|offer|interview)\b", re.I),
        "forbidden_guarantee",
        "Do not guarantee interviews, offers, or outcomes.",
    ),
    (
        re.compile(r"\b(h-?1b|visa|immigration|green card)\b.*\b(safe|guaranteed)\b", re.I),
        "immigration_advice",
        "Do not provide legal or immigration advice; provide planning guidance only.",
    ),
    (
        re.compile(r"\b(tax|financial|medical|legal)\b.*\b(advice|should|must)\b", re.I),
        "regulated_advice",
        "Do not provide legal, financial, tax, medical, or similar regulated advice.",
    ),
    (
        re.compile(r"\b(auto[- ]?(apply|send)|send this for me|apply for me)\b", re.I),
        "auto_action",
        "Agents must never auto-apply or auto-send messages.",
    ),
    (
        re.compile(r"\b(fabricate|invent|make up|fake)\b", re.I),
        "fabrication_instruction",
        "Never fabricate employers, titles, metrics, skills, dates, or claims.",
    ),
]

PERSONAL_CLAIM_PATTERN = re.compile(
    r"\b(I|my|candidate|user)\b.*\b("
    r"built|led|owned|increased|decreased|reduced|saved|launched|managed|migrated|"
    r"\d+%|\$[0-9]"
    r")\b",
    re.I,
)

DISCLAIMER = (
    "Planning guidance only. Not legal, immigration, financial, tax, medical, "
    "or hiring-outcome advice. Review and edit all drafts before use."
)


def run_compliance_guard(
    *,
    artifact_type: str,
    content: dict[str, Any] | str,
    citations: list[str] | None = None,
    requires_human_approval: bool = True,
) -> ComplianceReport:
    """Deterministic ComplianceGuardAgent equivalent for generation paths."""
    text = _flatten_content(content)
    citations = citations or []
    findings: list[ComplianceFinding] = []
    _, pii_counts = redaction_service.redact_text(text)

    for pattern, code, message in FORBIDDEN_PATTERNS:
        if pattern.search(text):
            findings.append(
                ComplianceFinding(severity="high", code=code, message=message)
            )

    citations_required = bool(PERSONAL_CLAIM_PATTERN.search(text))
    if citations_required and not citations:
        findings.append(
            ComplianceFinding(
                severity="high",
                code="missing_citations",
                message="Personal claims require citations to user-provided evidence.",
            )
        )

    if artifact_type in {"outreach_email", "cover_letter", "resume_strategy"}:
        if not requires_human_approval:
            findings.append(
                ComplianceFinding(
                    severity="high",
                    code="approval_required",
                    message="User-facing artifacts require a human approval checkpoint.",
                )
            )

    if "send" in text.lower() and artifact_type == "outreach_email":
        findings.append(
            ComplianceFinding(
                severity="medium",
                code="manual_send_only",
                message="Outreach drafts must be manually reviewed and sent by the user.",
            )
        )

    passed = not any(f.severity == "high" for f in findings)
    return ComplianceReport(
        passed=passed,
        findings=findings,
        pii_counts=pii_counts,
        disclaimers=[DISCLAIMER],
        citations_required=citations_required,
    )


def merge_reports(reports: list[ComplianceReport]) -> ComplianceReport:
    findings: list[ComplianceFinding] = []
    pii_counts: dict[str, int] = {}
    citations_required = False
    for report in reports:
        findings.extend(report.findings)
        citations_required = citations_required or report.citations_required
        for key, value in report.pii_counts.items():
            pii_counts[key] = pii_counts.get(key, 0) + value
    passed = not any(f.severity == "high" for f in findings)
    return ComplianceReport(
        passed=passed,
        findings=findings,
        pii_counts=pii_counts,
        disclaimers=[DISCLAIMER],
        citations_required=citations_required,
    )


def _flatten_content(content: dict[str, Any] | str) -> str:
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for key, value in content.items():
        if isinstance(value, (dict, list)):
            parts.append(f"{key}: {value}")
        else:
            parts.append(f"{key}: {value}")
    return "\n".join(parts)

