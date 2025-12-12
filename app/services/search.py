import asyncio
from urllib.parse import urlparse
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
        unique_links = set()

        for query in self.queries:
            data: tuple = await asyncio.gather(
                self.search_beehiiv(query),
                self.search_substack(query)
            )
            raw_results = data[0] + data[1]

            for item in raw_results:
                normalized_item = self._normalize_link(item)

                if normalized_item:
                    link_key = normalized_item["link"]

                    if link_key not in unique_links:
                        unique_links.add(link_key)
                        results.append(normalized_item)

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


    def _normalize_link(self, item: dict) -> dict | None:
        link = item.get("link", "")
        title = item.get("title", "")

        if not link or not title:
            return None

        try:
            parsed_url = urlparse(link)
            if "www." in parsed_url.netloc:
                return None

            normalized_link = f"{parsed_url.scheme}://{parsed_url.netloc}/"
            if "substack.com" not in normalized_link and "beehiiv.com" not in normalized_link:
                return None

            return {
                "link": normalized_link,
                "title": title
            }
        except Exception:
            print(f"Error normalizing link: {link}")
            return None
