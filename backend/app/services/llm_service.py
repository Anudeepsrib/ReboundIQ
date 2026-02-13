import json
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.logging import logger
from app.schemas.job import RecruiterMessageRequest, ToneEnum

class LLMService:
    def __init__(self):
        self.client = None
        if settings.OPENAI_API_KEY:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            logger.warning("OPENAI_API_KEY not set. LLM features will fail or be mocked.")

    async def analyze_message_intent(self, message: RecruiterMessageRequest) -> str:
        """
        Analyzes the recruiter's message to determine intent and key points.
        """
        if not self.client:
            return "LLM Analysis Unavailable: No API Key."

        system_prompt = """You are an expert career coach. Analyze the recruiter's message.
        Identify:
        1. Is this a bulk blast or personalized?
        2. What is the core role/opportunity?
        3. Are there any immediate red flags or missing info (e.g. no salary range)?
        
        Keep it concise (2-3 sentences)."""

        user_prompt = f"""
        Sender: {message.sender_name or 'Unknown'}
        Company: {message.company_name or 'Unknown'}
        Message: "{message.message_text}"
        """

        try:
            response = await self.client.chat.completions.create(
                model=settings.DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM Error during analysis: {e}")
            return "Error analyzing message."

    async def generate_reply(self, message: RecruiterMessageRequest, analysis: str, company_research_summary: str) -> str:
        """
        Drafts a reply based on user context, tone, and the message analysis.
        """
        if not self.client:
            return "LLM Reply Unavailable: No API Key."

        system_prompt = f"""You are a Job Hunt Assistant. Draft a reply to a recruiter.
        Tone: {message.desired_tone.value}
        
        Rules:
        - Be professional but distinct.
        - If the user provided resume context, use it to highlight relevant skills.
        - If the company research revealed positive news, mention it casually.
        - If red flags were found, be cautious but polite (or ask clarifying questions).
        - Keep it under 150 words.
        """

        user_prompt = f"""
        Recruiter Message: "{message.message_text}"
        Analysis: {analysis}
        Company Research: {company_research_summary}
        User Context/Resume: {message.user_resume_context or "Not provided"}
        """

        try:
            response = await self.client.chat.completions.create(
                model=settings.DEFAULT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM Error during generation: {e}")
            return "Error generating reply."

    async def estimate_salary(self, message: RecruiterMessageRequest) -> str:
        """
        Estimates salary range based on role description and market knowledge.
        """
        if not self.client:
             return "Salary estimation unavailable."
             
        # ... logic similar to above ...
        return "Not implemented yet."

llm_service = LLMService()
