import logging
from fastapi import APIRouter
from app.db import queries
from app.tasks.pipeline import scraping_stage
from app.tasks.newsletter_tasks import aggregate_issue_analysis

logger = logging.getLogger(__name__)
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

search_results = [
    {
        "position": 3,
        "title": "About - MacGuffin or Meaning: Entertainment Newsletter",
        "link": "https://alisechaffins.substack.com/",
    },
    {
        "position": 4,
        "title": "About - We Have Notes",
        "link": "https://wehavenotes.substack.com/",
    },
    {
        "position": 5,
        "title": "Recommended by Aurelie Chazal - The Inclusive Screen",
        "link": "https://theinclusivescreen.substack.com/",
    },
    {
        "position": 6,
        "title": "TheFUSE — A Wichita Falls Arts & Entertainment newsletter",
        "link": "https://fallstownfuse.substack.com/",
    }
]


@router.get("")
async def health_check():
    logger.info("Health check endpoint called!")
    return { "status": "ok", "service": "scrapper" }

@router.get("/trigger-analysis")
def trigger_analysis():
    total_newsletters = len(search_results)
    niche = "entertainment"
    search_terms = [ "top 10 newsletters on sports", "best sports newsletters", "popular sports newsletters" ]
    notion_doc_url = "https://www.notion.so/your-notion-doc-url"
    analysis_run_id = queries.insert_analysis_run(
        notion_doc_url,
        niche,
        search_terms,
        total_newsletters,
        0,
        "initiated"
    )

    scraping_stage.delay(analysis_run_id, search_results)

    return { "status": "ok", "message": "Analysis triggered" }

@router.get("/get-analysis")
def get_analysis():
    analysis = queries.get_issue_analysis()
    return { "status": "ok", "message": "Analysis exported to analysis_export.csv", "data": analysis }

@router.get("/test-agg-analysis")
def test_agg_analysis():
    result = aggregate_issue_analysis(18)
    return { "status": "ok", "data": result }
