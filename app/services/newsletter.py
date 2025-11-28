from toon_format import encode

from app.db import queries
from app.services.substack import SubstackScraper

class NewsletterService:
    def __init__(self, analysis_run_id: str, search_result: dict):
        self.analysis_run_id = analysis_run_id
        self.title = search_result["title"]
        self.scraper = None

        if "substack" in search_result["link"]:
            self.scraper = SubstackScraper(search_result)


    def process_and_save_issues(self):
        if not self.scraper:
            return

        scraped_data = self.scraper.scrape_newsletter()
        if not scraped_data or not scraped_data.get("issues"):
            return

        #try:
        issues_payload = []
        for issue in scraped_data["issues"]:
            toon_content = self._convert_to_toon(issue)
            issue["toon"] = toon_content
            issues_payload.append(issue)

        queries.insert_issues(self.analysis_run_id, self.title, issues_payload)
        return
        #except Exception as e:
        #    print(f"Error converting issues to toon format: {e}")
        #    return


    @staticmethod
    def _convert_to_toon(issue: dict) -> str:
        data = {
            "content": issue.get("content", ""),
            "like_count": issue.get("like_count", 0),
            "comment_count": issue.get("comment_count", 0),
            "image_count": issue.get("image_count", 0),
            "links": issue.get("links", [])
        }

        return encode(data)
