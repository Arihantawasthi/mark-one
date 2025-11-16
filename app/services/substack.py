from bs4 import BeautifulSoup
from fastapi import HTTPException
import requests
from typing import Dict, List, Tuple

from app.db import queries


MAX_ISSUES = 5

def get_substack_newsletter_archive(search_result: Dict, analysis_run_id: int) -> Dict:
    if "substack" not in search_result["link"]:
        return {}

    archive_link = f"{search_result["link"]}/api/v1/archive?sort=new&search=&offset=0&limit={MAX_ISSUES}"
    r = requests.get(archive_link, timeout=10)
    if r.status_code != 200:
        return {}

    issues = r.json()
    newsletter = {}
    newsletter["title"] = search_result["title"]
    newsletter["issues"] = []

    for issue in issues:
        issue_details = {}
        issue_details["title"] = issue["title"]
        issue_details["subtitle"] = issue["subtitle"]
        issue_details["link"] = issue["canonical_url"]
        issue_details["date"] = issue["post_date"]
        issue_details["author"] = issue["publishedBylines"][0]["name"]
        issue_details["content"], issue_details["num_of_images"] = scrape_issue_content(issue["canonical_url"])

        newsletter["issues"].append(issue_details)

    queries.insert_issues(analysis_run_id, newsletter["title"], newsletter["issues"])

    return newsletter

def scrape_issue_content(issue_url: str) -> Tuple[str, int]:
    r = requests.get(issue_url, timeout=10)
    if r.status_code != 200:
        raise HTTPException(status_code=404, detail="Issue not found")

    soup = BeautifulSoup(r.text, "html.parser")
    article = soup.find("article")
    if not article:
        raise HTTPException(status_code=404, detail="Content not found")

    for widget in article.select("div.subscription-widget-wrap"):
        widget.decompose()

    issue_content = article.find("div", class_="available-content")
    paras = [p.text.strip() for p in issue_content.find_all("p")]
    num_of_images = len(issue_content.find_all("img"))

    sanitized_paras = sanitize_content(paras)

    return sanitized_paras, num_of_images

def sanitize_content(content: List[str]) -> str:
    sanitized_paras = [ paragraph for paragraph in content if paragraph ]
    content_str = "\n\n".join(sanitized_paras)
    return content_str
