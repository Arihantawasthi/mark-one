import logging
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from fastapi import HTTPException
import requests

from app.core import settings

logger = logging.getLogger(__name__)


class SubstackScraper:
    def __init__(self, search_result):
        self.search_result = search_result
        self.acrhive_link = f"{search_result['link']}{settings.SUBSTACK_ARCHIVE_SUFFIX}{settings.MAX_ISSUES}"


    def scrape_newsletter(self) -> list[dict]:
        try:
            r = requests.get(self.acrhive_link, timeout=10)
            r.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch Substack archive: {e}")
            return []

        issues_data = r.json()
        scraped_issues = []

        for issue in issues_data:
            try:
                scraped_issue_details = {}
                content_data = self._scrape_issue_content(issue["canonical_url"])

                scraped_issue_details["title"] = issue["title"]
                scraped_issue_details["subtitle"] = issue["subtitle"]
                scraped_issue_details["link"] = issue["canonical_url"]
                scraped_issue_details["date"] = issue["post_date"]
                scraped_issue_details["author"] = self._extract_author(issue)
                scraped_issue_details["content"] = content_data["content"]
                scraped_issue_details["like_count"] = content_data["like_count"]
                scraped_issue_details["comment_count"] = content_data["comment_count"]
                scraped_issue_details["image_count"] = content_data["image_count"]
                scraped_issue_details["links"] = content_data["links"]
                scraped_issue_details["newsletter"] = self.search_result["title"]

                scraped_issues.append(scraped_issue_details)

            except HTTPException as e:
                logger.error(f"Failed to scrape issue content: {e.detail}")
                continue

        return scraped_issues


    def scrape_manual_issues(self, issue_urls: list[str]) -> list[dict]:
        scrapped_issues = []

        for issue_url in issue_urls:
            try:
                newsletter = ""
                parsed_url = urlparse(issue_url)
                if "www." in parsed_url.netloc:
                    newsletter = ""

                newsletter = parsed_url.netloc.split(".")[0]
                content_data = self._scrape_issue_content(issue_url)
                scrapped_issues.append({
                    "newsletter": newsletter,
                    "title": content_data["title"],
                    "subtitle": content_data["subtitle"],
                    "link": issue_url,
                    "date": None,
                    "author": "Unknown",
                    "content": content_data["content"],
                    "like_count": content_data["like_count"],
                    "comment_count": content_data["comment_count"],
                    "image_count": content_data["image_count"],
                    "links": content_data["links"]
                })
            except HTTPException as e:
                logger.error(f"Failed to scrape manual issue content: {e.detail}")
                continue

        return scrapped_issues


    def _scrape_issue_content(self, issue_url: str) -> dict:
        r = requests.get(issue_url, timeout=10)
        if r.status_code != 200:
            logger.error(f"Failed to fetch issue URL: {issue_url}")
            raise Exception("Issue not found")

        soup = BeautifulSoup(r.text, "html.parser")
        article = soup.find("article")

        if not article:
            logger.error(f"No article tag found in issue URL: {issue_url}")
            raise Exception("Content not found")

        for widget in article.select("div.subscription-widget-wrap"):
            widget.decompose()

        post_header = article.find("div", {"class": "post-header"})
        title = post_header.find("h1").get_text().strip()
        subtitle_elem = post_header.find("h3")
        subtitle = ""
        if subtitle_elem:
            subtitle = subtitle_elem.get_text().strip()

        like_elem_container = article.find("div", class_="like-button-container")
        if like_elem_container:
            like_elem = like_elem_container.find("button")
            like_count = self._get_engagement_count(like_elem)
        else:
            like_count = 0

        comment_elem = article.find("button", class_="post-ufi-comment-button")
        comment_count = self._get_engagement_count(comment_elem)

        issue_content = article.find("div", class_="available-content")
        images = issue_content.find_all("img") + issue_content.find_all("figure")
        image_count = len(images)

        links = []
        for link in issue_content.find_all("a"):
            links.append({
                "text": link.get_text().strip(),
                "url": link.get("href", "").strip()
            })
        paras = [ p.get_text(" ").strip() for p in issue_content.find_all("p") ]

        return {
            "title": title,
            "subtitle": subtitle,
            "content": paras,
            "like_count": like_count,
            "comment_count": comment_count,
            "image_count": image_count,
            "links": links
        }

    def _extract_author(self, issue) -> str:
        bylines = issue.get("publishedBylines")
        if not isinstance(bylines, list) or len(bylines) == 0:
            return "Unknown"

        return bylines[0].get("name", "Unknown")

    def _get_engagement_count(self, button) -> int:
        if not button:
            return 0
        count_div = button.find("div")
        if not count_div:
            return 0
        try:
            return int(count_div.get_text().strip())
        except ValueError:
            return 0
