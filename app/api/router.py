from fastapi import APIRouter, HTTPException
import requests
from typing import List
from bs4 import BeautifulSoup

router = APIRouter(tags=["newsletter"])

search_results = [
    {
      "title": "Soccer Analytics Newsletter | Richard Whittall | Substack",
      "link": "https://socceranalytics.substack.com/",
      "snippet": "A newsletter about soccer analytics (well, about everything really). Click to read Soccer Analytics Newsletter, by Richard Whittall, a Substack publication ...",
      "position": 1
    },
    {
      "title": "Optimum Sports Consulting Newsletter | Substack",
      "link": "https://optimumsportsconsulting.substack.com/",
      "snippet": "Welcome to the NIL Newsletter by Optimum Sports Consulting - providing valuable, actionable NIL resources for athletes, administrators, agencies and...",
      "position": 2
    },
    {
      "title": "Olympics Everywhere Newsletter | Sydney Bauer | Substack",
      "link": "https://olympicseverywhere.substack.com/",
      "snippet": "The Olympics are so big they touch every aspect of a country's society; I'm here to unpack that. Click to read Olympics Everywhere Newsletter, by Sydney ...",
      "position": 3
    }
]

MAX_ISSUES = 5

@router.get("/")
def health_check():
    return { "status": "ok", "service": "scrapper" }

@router.get("/scrape")
def scrape():
    links = []
    for result in search_results:
        if "substack" in result["link"]:
            archive_link = f"{result["link"]}archive?sort=new"
            r = requests.get(archive_link, timeout=10)
            if r.status_code != 200:
                return []
            html = r.text

            soup = BeautifulSoup(html, "html.parser")
            newsletter_title_container = soup.find("div", attrs={"data-testid": "navbar"})
            newsletter_title = newsletter_title_container.find("h1").find("a").text.strip()
            if newsletter_title == "":
                newsletter_title = newsletter_title_container.find("h1").find("img")["alt"].strip()

            issue_list_container = soup.find("div", class_="portable-archive-list")
            issue_links = [
                a["href"] for a in issue_list_container.find_all("a", attrs={"data-testid": 'post-preview-title'})[:MAX_ISSUES]
                if result["link"] in a["href"]
            ]
            newsletter_info = {
                "title": newsletter_title,
                "links": issue_links
            }
            links.append(newsletter_info)

    return { "newsletter_info": links }
