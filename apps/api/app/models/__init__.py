# SQLAlchemy models package
from .user import User, Base
from .profile import UserProfile
from .resume import Resume, ResumeVersion, DocumentChunk
from .ai_requests import AIRequest
from .agent_campaigns import AgentCampaign
from .agent_tool_calls import AgentToolCall
from .agent_approval_requests import AgentApprovalRequest
from .workflows import RunwaySnapshot, ApplicationRecord, ProofAsset, InterviewSession
from .action_audit_logs import ActionAuditLog
from .consent_records import ConsentRecord
from .memory_candidates import MemoryCandidate
from .memory_reflections import MemoryReflection

AIRequestLog = AIRequest

__all__ = [
    "User",
    "Base",
    "UserProfile",
    "Resume",
    "ResumeVersion",
    "AIRequestLog",
    "DocumentChunk",
    "AgentCampaign",
    "AgentToolCall",
    "AgentApprovalRequest",
    "RunwaySnapshot",
    "ApplicationRecord",
    "ProofAsset",
    "InterviewSession",
    "ActionAuditLog",
    "ConsentRecord",
    "MemoryCandidate",
    "MemoryReflection",
]
# job_application, document, agent_campaigns, memory_records etc added in later migrations / PRs
# ai_requests added in PR-4 for full audit of gateway calls (redacted + consent + full_audit_jsonb)
# document_chunks added in PR-7 for resume RAG (pgvector embeddings, grounded recall)
