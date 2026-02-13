from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class ToneEnum(str, Enum):
    professional = "professional"
    casual = "casual"
    enthusiastic = "enthusiastic"
    assertive = "assertive"

class RecruiterMessageRequest(BaseModel):
    message_text: str = Field(..., description="The full text of the recruiter's message")
    sender_name: Optional[str] = Field(None, description="Name of the recruiter")
    company_name: Optional[str] = Field(None, description="Company they are recruiting for")
    user_resume_context: Optional[str] = Field(None, description="User's bio/resume summary to tailor the reply")
    desired_tone: ToneEnum = Field(ToneEnum.professional, description="Tone of the reply")

class CompanyResearch(BaseModel):
    name: str
    summary: str
    red_flags: List[str] = []
    positive_signals: List[str] = []
    funding_stage: Optional[str] = None

class JobResponse(BaseModel):
    analysis: str = Field(..., description="Brief analysis of the recruiter's intent")
    suggested_reply: str = Field(..., description="Drafted reply")
    company_info: Optional[CompanyResearch] = Field(None, description="Research about the company")
    salary_insights: Optional[str] = Field(None, description="Estimated salary range or negotiation tips")
