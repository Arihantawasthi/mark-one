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
        search_query = f"site:beehiiv.com {query} newsletters"
        params = {
            "key": self.api_key,
            "cx": self.csx,
            "q": search_query,
            "num": 5,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            return response.json().get("items", [])


    async def search_substack(self, query: str) -> list[dict]:
        search_query = f"site:substack.com {query} newsletters"
        params = {
            "key": self.api_key,
            "cx": self.csx,
            "q": search_query,
            "num": 5,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(self.base_url, params=params)
            return response.json().get("items", [])


    def _collapse_issue_url_to_root(self, link: str) -> str:
        """
        Converts:
          https://example.substack.com/p/slug
          https://example.beehiiv.com/p/slug

        Into:
          https://example.substack.com
          https://example.beehiiv.com

        If not an issue URL, returns original link.
        """
        parsed = urlparse(link.strip())
        if not parsed.scheme or not parsed.netloc:
            return link
        path = parsed.path or ""
        if path.startswith("/p/") or path == "/p":
            return f"{parsed.scheme}://{parsed.netloc}"

        return link


    def _normalize_link(self, item: dict) -> dict | None:
        link = item.get("link", "")
        title = item.get("title", "")

        if not link or not title:
            return None

        try:
            collapsed_link = self._collapse_issue_url_to_root(link)
            parsed_url = urlparse(collapsed_link)

            if not parsed_url.scheme or not parsed_url.netloc:
                return None

            scheme = "https"
            host = parsed_url.netloc.lower()
            if host.startswith("www."):
                return None

            parts = host.split(".")

            if len(parts) != 3:
                return None

            _, domain, tld = parts
            parent_domain = f"{domain}.{tld}"

            if parent_domain not in ["substack.com", "beehiiv.com"]:
                return None

            if parsed_url.path not in ("", "/"):
                return None
            if parsed_url.query or parsed_url.fragment:
                return None

            normalized_link = f"{scheme}://{host}"

            return {
                "link": normalized_link,
                "title": title
            }
        except Exception:
            print(f"Error normalizing link: {link}")
            return None
