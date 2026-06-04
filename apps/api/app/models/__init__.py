# SQLAlchemy models package
from .user import User, Base
from .resume import Resume, ResumeVersion, DocumentChunk
from .ai_request import AIRequestLog

__all__ = ["User", "Base", "Resume", "ResumeVersion", "AIRequestLog", "DocumentChunk"]
# job_application, document, agent_campaigns, memory_records etc added in later migrations / PRs
# ai_requests added in PR-4 for full audit of gateway calls (redacted + consent + full_audit_jsonb)
# document_chunks added in PR-7 for resume RAG (pgvector embeddings, grounded recall)
