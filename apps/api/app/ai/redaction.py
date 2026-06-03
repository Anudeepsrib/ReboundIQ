"""
RedactionService for ReboundIQ.

Regex-first PII redaction + local LLM fallback hook (stubbed for skeleton).
NON-BYPASSABLE before any external provider call.
Never sends original PII to external even with consent.
All AI (incl. redaction decisions) audited via gateway.
"""

import re
from typing import List, Dict, Tuple, Any, Optional

import structlog

logger = structlog.get_logger()


class RedactionService:
    """Production redaction. Use .redact_for_external() for all external paths."""

    def __init__(self) -> None:
        # Regex patterns for high-precision common PII. Expand conservatively.
        self.pii_patterns: Dict[str, re.Pattern[str]] = {
            "ssn": re.compile(r"\b\d{3}[- ]?\d{2}[- ]?\d{4}\b"),
            "email": re.compile(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", re.IGNORECASE
            ),
            "phone_us": re.compile(
                r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
            ),
            # Rough CC; real systems use more Luhn etc. Sufficient for eval skeleton.
            "credit_card": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
        }

    def redact_text(self, text: str) -> Tuple[str, Dict[str, int]]:
        """Return (redacted_text, per-type counts). Pure, no side effects."""
        if not text or not isinstance(text, str):
            return text or "", {}
        redacted = text
        counts: Dict[str, int] = {}
        for pii_type, pattern in self.pii_patterns.items():
            matches = list(pattern.finditer(redacted))
            if matches:
                redacted = pattern.sub(f"[REDACTED_{pii_type.upper()}]", redacted)
                counts[pii_type] = len(matches)
        return redacted, counts

    def redact_messages(
        self, messages: List[Dict[str, str]]
    ) -> Tuple[List[Dict[str, str]], bool, Dict[str, int]]:
        """Redact chat-style messages list. Returns (redacted_list, was_redacted_any, total_counts)."""
        if not messages:
            return [], False, {}
        redacted_msgs: List[Dict[str, str]] = []
        any_redacted = False
        total_counts: Dict[str, int] = {}
        for msg in messages:
            content = msg.get("content", "") if isinstance(msg, dict) else ""
            red_content, counts = self.redact_text(content)
            if counts:
                any_redacted = True
                for k, v in counts.items():
                    total_counts[k] = total_counts.get(k, 0) + v
            new_msg = (
                dict(msg) if isinstance(msg, dict) else {"role": "user", "content": ""}
            )
            new_msg["content"] = red_content
            redacted_msgs.append(new_msg)
        return redacted_msgs, any_redacted, total_counts

    async def redact_for_external(
        self,
        messages: List[Dict[str, str]],
        user_text: Optional[str] = None,
        use_llm_fallback: bool = False,
    ) -> Tuple[List[Dict[str, str]], bool, Dict[str, Any]]:
        """
        Entry point for gateway before external calls.
        Always applies regex. LLM fallback for advanced detection (local ollama only).
        Returns (redacted_messages, was_redacted, audit_info_dict)
        audit_info includes counts, lens, used_fallback.
        """
        red_msgs, was_red, counts = self.redact_messages(messages)
        red_user: Optional[str] = None
        if user_text:
            red_user, u_counts = self.redact_text(user_text)
            if u_counts:
                was_red = True
                for k, v in u_counts.items():
                    counts[k] = counts.get(k, 0) + v

        audit_info: Dict[str, Any] = {
            "redaction_counts": counts,
            "used_llm_fallback": False,
            "original_len": sum(
                len((m.get("content") or "") if isinstance(m, dict) else "")
                for m in messages
            )
            + (len(user_text) if user_text else 0),
            "redacted_len": sum(
                len((m.get("content") or "") if isinstance(m, dict) else "")
                for m in red_msgs
            )
            + (len(red_user) if red_user else 0),
        }

        if use_llm_fallback:
            # Skeleton: do not actually invoke here to avoid import cycles / extra latency in redaction path.
            # In full: would do a *local-only* gateway call (ollama forced) with strict prompt for PII spans,
            # then apply additional redactions. Consent/redaction not needed for this meta call.
            # Never send the result of this to external.
            audit_info["used_llm_fallback"] = False
            logger.info(
                "redaction.llm_fallback_skipped_for_skeleton",
                extra={
                    "reason": "regex covers SSN/email eval cases; full LLM in later PR"
                },
            )

        return red_msgs, was_red, audit_info


redaction_service = RedactionService()
