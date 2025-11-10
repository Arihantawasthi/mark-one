from fastapi import APIRouter
from app.db import queries
from app.tasks.newsletter_tasks import process_newsletter_issues


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

@router.get("/")
def health_check():
    return { "status": "ok", "service": "scrapper" }

@router.get("/trigger-analysis")
def trigger_analysis():
    total_newsletters = len(search_results)
    niche = "Sports"
    search_terms = [ "top 10 newsletters on sports", "best sports newsletters", "popular sports newsletters" ]
    notion_doc_url = "https://www.notion.so/your-notion-doc-url"
    analysis_run_id = queries.insert_search_run(
        notion_doc_url,
        niche,
        search_terms,
        total_newsletters,
        0,
        "initiated"
    )

    process_newsletter_issues.delay(analysis_run_id, search_results)

    return { "status": "ok", "message": "Analysis triggered" }
