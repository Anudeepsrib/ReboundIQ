# SQLAlchemy models package
<<<<<<< HEAD
# Base exported so alembic/env.py can do: from app.models import Base
from app.db.base import Base

from .user import User
from .profile import UserProfile
from .resume import Resume, ResumeVersion
from .agent_campaigns import AgentCampaign
from .memory_records import MemoryRecord
from .agent_tool_calls import AgentToolCall
from .agent_approval_requests import AgentApprovalRequest
from .memory_candidates import MemoryCandidate
from .memory_reflections import MemoryReflection
from .ai_requests import AIRequest
from .consent_records import ConsentRecord

__all__ = [
    "Base",
    "User",
    "UserProfile",
    "Resume",
    "ResumeVersion",
    "AgentCampaign",
    "MemoryRecord",
    "AgentToolCall",
    "AgentApprovalRequest",
    "MemoryCandidate",
    "MemoryReflection",
    "AIRequest",
    "ConsentRecord",
]
# Additional tables (jobs, applications, documents, action_audit_logs, etc) added in later PRs/migrations.
