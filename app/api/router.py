import json
import logging
from fastapi import APIRouter, WebSocket
from app.core import settings
from app.db import queries
from app.services.beehiiv import BeehiivScraper
from app.services.newsletter import NewsletterService
from app.services.search import SearchService
from app.tasks.pipeline import scraping_stage
from app.tasks.newsletter_tasks import aggregate_issue_analysis
from app.services.pubsub import redis_client_async

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
    },
    {
        "position": 7,
        "title": "Joker Mag | Beehiiv",
        "link": "https://underdog.beehiiv.com/"
    }
]

search_results_b = [
    {
        "position": 7,
        "title": "The Sports Edit Newsletter | Beehiiv",
        "link": "https://newsletter.jokermag.com/"
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

    return { "status": "ok", "message": "Analysis triggered", "analysis_run_id": analysis_run_id }

@router.websocket("/status/{analysis_run_id}")
async def analysis_status(websocket: WebSocket, analysis_run_id: int):
    await websocket.accept()

    pubsub = redis_client_async.pubsub()
    await pubsub.subscribe(f"analysis_status:{analysis_run_id}")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await websocket.send_json(data)

    except Exception as e:
        logger.error(
            f"WebSocket error: {e}",
            extra={"analysis_run_id": analysis_run_id, "error": str(e)},
            exc_info=True
        )

    finally:
        await pubsub.unsubscribe(f"analysis_status:{analysis_run_id}")
        await websocket.close()


@router.post("/search")
async def search_newsletter_links(body: dict[str, list]):
    search_terms = body.get("queries", [])
    if not search_terms:
        return { "status": "error", "message": "No search terms provided" }

    search_service = SearchService(search_terms)
    results = await search_service.search()
    return { "status": "ok", "size": len(results), "data": results }


@router.get("/get-analysis")
async def get_analysis():
    analysis = queries.get_issue_analysis()
    return { "status": "ok", "message": "Analysis exported to analysis_export.csv", "data": analysis }


@router.get("/get-beehiiv")
def get_beehiiv():
    beehiv_scraper = BeehiivScraper(search_results_b[0])
    data = beehiv_scraper.scrape_newsletter()
    return { "status": "ok", "data": data }
