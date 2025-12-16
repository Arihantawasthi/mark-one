import logging
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

from app.core import settings

logger = logging.getLogger(__name__)

class BeehiivScraper:
    def __init__(self, search_result):
        self.search_result = search_result
        self.base_link = search_result.get("link")
        self.archive_link = f"{search_result.get("link")}/archive"

    def scrape_newsletter(self) -> list[dict]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()

            archive_html = self._fetch_html(context, self.base_link)
            issue_links = self._extract_issues_links(archive_html)

            scraped_issues = []
            for issue_link in issue_links:
                issue_html = self._fetch_html(context, issue_link)
                issue_data = self._scrape_issue_content(issue_html)
                issue_data["link"] = issue_link
                issue_data["newsletter"] = self.search_result.get("title", "Untitled")
                scraped_issues.append(issue_data)

            browser.close()

        return scraped_issues

    def scrape_manual_issues(self, issue_urls: list[str]) -> list[dict]:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()

            scraped_issues = []
            for issue_url in issue_urls:
                issue_html = self._fetch_html(context, issue_url)
                issue_data = self._scrape_issue_content(issue_html)
                issue_data["link"] = issue_url
                issue_data["newsletter"] = self.search_result.get("title", "Untitled")
                scraped_issues.append(issue_data)

            browser.close()

        return scraped_issues

    def _extract_issues_links(self, archive_html: str) -> list[str]:
        issue_links = []
        seen_links = set()

        soup = BeautifulSoup(archive_html, "html.parser")

        for a in soup.find_all("a"):
            href = a.get("href", "")
            if "/p/" in href:
                if len(seen_links) > settings.MAX_ISSUES:
                    break
                if href not in seen_links:
                    seen_links.add(href)
                    issue_links.append(f"{self.base_link}{href}")

        return issue_links

    def _fetch_html(self, context, url: str) -> str:
        page = context.new_page()
        page.goto(url, timeout=90000, wait_until="load")
        html_content = page.content()
        page.close()
        return html_content

    def _scrape_issue_content(self, html: str) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        main = soup.find("main")

        if not main:
            logger.error(f"Failed to find main content for issue")
            raise Exception("Issue not found")

        engagement_section = main.find("div", {"class": "fixed bottom-0 left-0 top-auto z-20 w-full rounded bg-wt-background shadow-xl transition-all duration-300 ease-in-out md:bottom-auto md:z-auto md:!w-fit md:border-none md:shadow-none opacity-100 md:top-20"})
        like_elem = engagement_section.find("button", {"class": "group"})
        like_count = self._get_engagement_count(like_elem)
        comment_count = engagement_section.find("button", {"class": "group relative top-[1px] flex items-center outline-none md:pt-0"})
        comment_count = self._get_engagement_count(comment_count)

        for social_links in main.find_all("div", {"class": "bh__byline_social_wrapper"}):
            social_links.decompose()

        web_header = main.find("div", {"id": "web-header"})
        title = web_header.find("h1").get_text(strip=True) if web_header.find("h1") else ""
        subtitle = web_header.find("h2").get_text(strip=True) if web_header.find("h2") else ""
        author = self._extract_author(web_header)

        content_blocks = main.find("div", {"id": "content-blocks"})
        links = []
        for link in content_blocks.find_all("a"):
            links.append({
                "text": link.get_text().strip(),
                "url": link.get("href", "").strip()
            })
        paras = [ elem.get_text(" ").strip() for elem in content_blocks.find_all(["p", "h1", "h2", "h3", "h4"]) ]

        images = content_blocks.find_all("img") + content_blocks.find_all("figure")
        image_count = len(images)

        return {
            "title": title,
            "subtitle": subtitle,
            "date": None,
            "author": author,
            "content": paras,
            "like_count": like_count,
            "comment_count": comment_count,
            "image_count": image_count,
            "links": links
        }


    def _extract_author(self, web_header) -> str:
        author = "Unknown"
        link = web_header.find("a", "")
        href = ""
        if link:
            href = link.get("href", "")
        if "authors" in href:
            author = link.get_text(strip=True)

        return author


    def _get_engagement_count(self, button) -> int:
        if not button:
            return 0
        count_span = button.find("span")
        if not count_span:
            return 0
        try:
            count = int(count_span.get_text().strip())
            return count
        except ValueError:
            return 0

