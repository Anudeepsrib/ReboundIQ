from app.services.llm_service import LLMService
from app.services.research_service import ResearchService
from app.schemas.job import RecruiterMessageRequest, JobResponse, CompanyResearch

class OrchestratorService:
    def __init__(self):
        self.llm = LLMService()
        self.researcher = ResearchService()

    async def process_recruiter_message(self, request: RecruiterMessageRequest) -> JobResponse:
        # 1. Parallel Execution would be better here, but sequential for MVP simplicity
        
        # Analyze Intent
        analysis = await self.llm.analyze_message_intent(request)
        
        # Research Company (if name provided)
        company_data = await self.researcher.research_company(request.company_name)
        
        # Generate Reply
        # Pass the research summary to the LLM
        research_summary = f"{company_data.name}: {company_data.summary}. Red Flags: {company_data.red_flags}"
        reply_draft = await self.llm.generate_reply(request, analysis, research_summary)
        
        # Estimate Salary (Optional/Future)
        salary_info = await self.llm.estimate_salary(request)

        return JobResponse(
            analysis=analysis,
            suggested_reply=reply_draft,
            company_info=company_data,
            salary_insights=salary_info
        )

orchestrator = OrchestratorService()
