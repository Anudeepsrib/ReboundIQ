from app.core.config import settings
from app.core.logging import logger
from app.schemas.job import CompanyResearch

# Optional: Import Tavily client if installed, or use HTTP requests
# from tavily import TavilyClient 

class ResearchService:
    def __init__(self):
        self.api_key = settings.TAVILY_API_KEY
    
    async def research_company(self, company_name: str) -> CompanyResearch:
        """
        Performs a search on the company to find recent news, funding, and reputation.
        """
        if not company_name:
            return CompanyResearch(name="Unknown", summary="No company name provided.")

        if self.api_key:
            # TODO: Implement real Tavily search
            # For now, we simulate a "Smart" search result
            return await self._mock_smart_search(company_name)
        else:
            return await self._mock_smart_search(company_name)

    async def _mock_smart_search(self, company_name: str) -> CompanyResearch:
        logger.info(f"Mocking research for {company_name}")
        # Return generic but plausible data for testing UI
        return CompanyResearch(
            name=company_name,
            summary=f"A technology company. (Mock Data: Real search requires Tavily Key).",
            red_flags=["Check Glassdoor for recent reviews", "Verify remote policy"],
            positive_signals=["Growing industry sector"],
            funding_stage="Series B (Estimated)"
        )

research_service = ResearchService()
