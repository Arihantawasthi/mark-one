import logging
from toon_format import encode

from app.db import queries
from app.services.beehiiv import BeehiivScraper
from app.services.substack import SubstackScraper

logger = logging.getLogger(__name__)

class NewsletterService:
    def __init__(self, analysis_run_id: str, search_result: dict):
        self.analysis_run_id = analysis_run_id
        self.title = search_result.get("title", "Untitled")
        self.scraper = None
        self.platform = None

        if "substack" in search_result["link"]:
            self.scraper = SubstackScraper(search_result)
            self.platform = "substack"
        if "beehiiv" in search_result["link"]:
            self.scraper = BeehiivScraper(search_result)
            self.platform = "beehiiv"

    def process_and_save_issues(self):
        if not self.scraper:
            logger.info(
                f"[Scrape] Skipping unsupported platform",
                extra={ "analysis_run_id": self.analysis_run_id, "platform": self.platform, "newsletter_title": self.title }
            )
            return

        logger.info(
            f"[Scrape] Fetching and Scraping issues",
            extra={ "analysis_run_id": self.analysis_run_id, "platform": self.platform, "newsletter_title": self.title }
        )

        scraped_data = self.scraper.scrape_newsletter()
        if not scraped_data:
            logger.warning(
                f"[Scrape] No issues found",
                extra={ "analysis_run_id": self.analysis_run_id, "platform": self.platform, "newsletter_title": self.title }
            )
            return

        #try:
        issues_payload = []
        for issue in scraped_data:
            toon_content = self._convert_to_toon(issue)
            issue["toon"] = toon_content
            issue["platform"] = self.platform
            issues_payload.append(issue)

        queries.insert_issues(self.analysis_run_id, issues_payload)
        logger.info(
            f"[Scrape] Inserted {len(issues_payload)} issues into database",
            extra={ "analysis_run_id": self.analysis_run_id, "platform": self.platform, "newsletter_title": self.title }
        )
        #except Exception as e:
        #    print(f"Error converting issues to toon format: {e}")
        #    return

    def process_and_save_manual_issues(self, issue_urls: list[str]) -> list:
        if not self.scraper:
            logger.info(
                f"[Scrape] Skipping unsupported platform for manual issues",
                extra={ "analysis_run_id": self.analysis_run_id, "platform": self.platform, "newsletter_title": self.title }
            )
            return []

        logger.info(
            f"[Scrape] Fetching and Scraping manual issues",
            extra={ "analysis_run_id": self.analysis_run_id, "platform": self.platform, "newsletter_title": self.title }
        )

        scraped_data = self.scraper.scrape_manual_issues(issue_urls)
        if not scraped_data:
            logger.warning(
                f"[Scrape] No manual issues found",
                extra={ "analysis_run_id": self.analysis_run_id, "platform": self.platform, "newsletter_title": self.title }
            )
            return []

        issues_payload = []
        for issue in scraped_data:
            toon_content = self._convert_to_toon(issue)
            issue["toon"] = toon_content
            issue["platform"] = self.platform
            issues_payload.append(issue)

        issues = queries.insert_issues(self.analysis_run_id, issues_payload)
        logger.info(
            f"[Scrape] Inserted {len(issues_payload)} manual issues into database",
            extra={ "analysis_run_id": self.analysis_run_id, "platform": self.platform, "newsletter_title": self.title }
        )

        return issues


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
