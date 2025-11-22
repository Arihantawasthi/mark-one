from typing import Union
from bs4 import BeautifulSoup
from bs4.element import NavigableString, PageElement, Tag
from fastapi import HTTPException
import requests

from app.db import queries
import logging
logger = logging.getLogger(__name__)


MAX_ISSUES = 5

def process_and_save_newsletters(analysis_run_id: int, search_result: dict) -> dict:
    newsletter_data = scrape_substack_newsletter(search_result)
    # queries.insert_issues(analysis_run_id, newsletter_data["title"], newsletter_data["issues"])
    return newsletter_data

def scrape_substack_newsletter(search_result: dict) -> dict:
    if "substack" not in search_result["link"]:
        return {}

    archive_link = f'{search_result["link"]}/api/v1/archive?sort=new&search=&offset=0&limit={MAX_ISSUES}'
    r = requests.get(archive_link, timeout=10)
    if r.status_code != 200:
        return {}

    issues = r.json()
    newsletter = {}
    newsletter["title"] = search_result["title"]
    newsletter["issues"] = []

    for issue in issues:
        issue_details = {}
        scrapped_data = scrape_issue_content(issue["canonical_url"])
        logger.error(f'Starting to scrape newsletter: {issue}')

        issue_details["title"] = issue["title"]
        issue_details["subtitle"] = issue["subtitle"]
        issue_details["link"] = issue["canonical_url"]
        issue_details["date"] = issue["post_date"]
        issue_details["author"] = extract_author(issue)

        issue_details["content"] = scrapped_data["content"]
        issue_details["like_count"] = scrapped_data["like_count"]
        issue_details["comment_count"] = scrapped_data["comment_count"]
        issue_details["image_count"] = scrapped_data["image_count"]
        issue_details["links"] = scrapped_data["links"]

        newsletter["issues"].append(issue_details)

    return newsletter

def extract_author(issue) -> str:
    bylines = issue.get("publishedBylines")

    if not isinstance(bylines, list) or len(bylines) == 0:
        return "Unknown"

    return bylines[0].get("name", "Unknown")


def scrape_issue_content(issue_url: str) -> dict:
    r = requests.get(issue_url, timeout=10)
    if r.status_code != 200:
        raise HTTPException(status_code=404, detail="Issue not found")

    soup = BeautifulSoup(r.text, "html.parser")
    article = soup.find("article")
    if not article:
        raise HTTPException(status_code=404, detail="Content not found")

    for widget in article.select("div.subscription-widget-wrap"):
        widget.decompose()

    issue = {}

    like_button_elem = article.find("div", class_="like-button-container").find("button")
    issue["like_count"] = get_engagement_count(like_button_elem)

    comment_button_elem = article.find("button", class_="post-ufi-comment-button")
    issue["comment_count"] = get_engagement_count(comment_button_elem)

    issue_content = article.find("div", class_="available-content")
    images = issue_content.find_all("img") + issue_content.find_all("figure")
    issue["image_count"] = len(images)

    links = {}
    for link in issue_content.find_all("a"):
        links["text"] = link.get_text().strip()
        links["url"] = link.get("href", "").strip()

    paras = [ p.get_text("\n\n").strip() for p in issue_content.find_all("p") ]
    issue["content"] = sanitize_content(paras)
    issue["links"] = links

    return issue

def get_engagement_count(button) -> int:
    if not button:
        return 0
    count_div = button.find("div")
    if not count_div:
        return 0
    try:
        return int(count_div.get_text().strip())
    except ValueError:
        return 0


def sanitize_content(paragraphs: list[str]) -> str:
    sanitized_paras = [ para for para in paragraphs if para ]
    content_str = "\n\n".join(sanitized_paras)
    return content_str
