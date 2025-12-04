import asyncio
import httpx
from app.core import settings


class SearchService:
    def __init__(self, queries):
        self.csx = settings.GOOGLE_CSE_ID
        self.api_key = settings.GOOGLE_API_KEY
        self.base_url = settings.BASE_SEARCH_URL or "https://www.googleapis.com/customsearch/v1"
        self.queries = queries


    async def search(self):
        results = []
        for query in self.queries:
            data: tuple = await asyncio.gather(
                self.search_beehiiv(query),
                self.search_substack(query)
            )
            results.extend(data[0])
            results.extend(data[1])

        return results


    async def search_beehiiv(self, query: str) -> list[dict]:
        search_query = f"site:beehiiv.com {query}"
        params = {
            "key": self.api_key,
            "cx": self.csx,
            "q": search_query,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            return response.json().get("items", [])


    async def search_substack(self, query: str) -> list[dict]:
        search_query = f"site:substack.com {query}"
        params = {
            "key": self.api_key,
            "cx": self.csx,
            "q": search_query,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            return response.json().get("items", [])
