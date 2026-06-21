# SQLAlchemy models package
from .user import User, Base
from .profile import UserProfile
from .resume import Resume, ResumeVersion, DocumentChunk
from .ai_requests import AIRequest

AIRequestLog = AIRequest

__all__ = [
    "User",
    "Base",
    "UserProfile",
    "Resume",
    "ResumeVersion",
    "AIRequestLog",
    "DocumentChunk",
]
# job_application, document, agent_campaigns, memory_records etc added in later migrations / PRs
# ai_requests added in PR-4 for full audit of gateway calls (redacted + consent + full_audit_jsonb)
# document_chunks added in PR-7 for resume RAG (pgvector embeddings, grounded recall)
