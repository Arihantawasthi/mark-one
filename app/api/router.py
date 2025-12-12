import json
import logging
from fastapi import APIRouter, Path, WebSocket
from app.core import settings
from app.db import queries
from app.services.beehiiv import BeehiivScraper
from app.services.newsletter import NewsletterService
from app.services.search import SearchService
from app.tasks.pipeline import scraping_stage, search_stage
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

@router.post("/start-query-analysis")
def start_query_analysis(body: dict[str, list]):
    search_queries = body.get("queries", [])
    if not search_queries:
        return { "requestStatus": 0, "message": "No search terms provided" }

    display_title = f'Market Scout Analysis - "{search_queries[0]}"'
    if len(search_queries) > 1:
        display_title += f' (+{len(search_queries)-1})'

    analysis_run_id = queries.insert_analysis_run(
        display_title,
        "",
        "general",
        search_queries,
        0,
        0,
        "initiated"
    )
    search_stage.delay(analysis_run_id, search_queries)

    return { "requestStatus": 1, "message": "Analysis started", "analysis_id": analysis_run_id }


@router.post("/start-links-analysis")
def start_links_analysis(body: dict[str, list]):
    links = body.get("links", [])
    if not links:
        return { "requestStatus": 0, "message": "No links provided" }

    display_title = f'Custom Links Analysis - "{links[0]}"'
    if len(links) > 1:
        display_title += f' (+{len(links)-1})'

    analysis_run_id = queries.insert_analysis_run(
        display_title,
        "",
        "general",
        [],
        0,
        0,
        "initiated"
    )
    search_results = [ { "link": link, "title": "Custom" } for link in links ]
    scraping_stage.delay(analysis_run_id, search_results)

    return { "requestStatus": 1, "message": "Analysis started", "analysis_id": analysis_run_id }


@router.websocket("/ws/status/{analysis_run_id}")
async def ws_analysis_status(websocket: WebSocket, analysis_run_id: int):
    await websocket.accept()

    pubsub = redis_client_async.pubsub()
    await pubsub.subscribe(f"analysis_status:{analysis_run_id}")

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                await websocket.send_json(data)
                queries.put_progress_statuses(analysis_run_id, data)

    except Exception as e:
        logger.error(
            f"WebSocket error: {e}",
            extra={"analysis_run_id": analysis_run_id, "error": str(e)},
            exc_info=True
        )

    finally:
        await pubsub.unsubscribe(f"analysis_status:{analysis_run_id}")
        await websocket.close()


@router.websocket("/ws/test-status")
async def ws_test_status(websocket: WebSocket):
    await websocket.accept()
    mock_progress = [
        { "stage": "Search", "title": "Searching for newsletters", "detail": "Searching...", "progress": 20 },
        { "stage": "Scraping", "title": "Scraping newsletters", "detail": "Scraping...", "progress": 40 },
        { "stage": "Issue Analysis", "title": "Analyzing newsletter issues", "detail": "Analyzing...", "progress": 60 },
        { "stage": "Aggregation", "title": "Aggregating analysis", "detail": "Aggregating...", "progress": 80 },
        { "stage": "Completed", "title": "Analysis completed", "detail": "Done!", "progress": 100 }
    ]

    for progress in mock_progress:
        import asyncio
        await websocket.send_json(progress)
        await asyncio.sleep(5)


@router.post("/search")
async def search_newsletter_links(body: dict[str, list]):
    search_terms = body.get("queries", [])
    if not search_terms:
        return { "status": "error", "message": "No search terms provided" }

    search_service = SearchService(search_terms)
    results = await search_service.search()
    return { "status": "ok", "size": len(results), "data": results }


@router.get("/analysis-status/{analysis_run_id}")
def analysis_status(analysis_run_id: int):
    status = queries.get_analysis_status(analysis_run_id)
    return {
        "requestStatus": 1,
        "message": "Successfully fetched analysis status",
        "data": {
            "analysis_id": analysis_run_id,
            "status": status,
        }
    }

@router.get("/analysis/{analysis_run_id}")
def get_analysis(analysis_run_id: int):
    issue_analysis = queries.get_issue_analyses_by_analysis_run_id(analysis_run_id)
    agg_analysis = queries.get_agg_issue_analysis_by_run_id(analysis_run_id)
    return {
        "requestStatus": 1,
        "message": "Successfully fetched analysis",
            "data": { "analysis_run_id": analysis_run_id, "issue_analyses": issue_analysis, "agg_analysis": agg_analysis }
    }

@router.get("/analysis/process-status/{analysis_run_id}")
def get_analysis_process_status(analysis_run_id: int):
    process_status = queries.get_analysis_progress_status(analysis_run_id)
    return {
        "requestStatus": 1,
        "message": "Successfully fetched analysis process status",
        "data": { "analysis_run_id": analysis_run_id, "process_status": process_status }
    }

@router.get("/analyses/list")
def list_analyses():
    analyses = queries.get_all_analyses()
    return {
        "requestStatus": 1,
        "message": "Successfully fetched analyses",
        "data": analyses
    }


@router.get("/get-beehiiv")
def get_beehiiv():
    beehiv_scraper = BeehiivScraper(search_results_b[0])
    data = beehiv_scraper.scrape_newsletter()
    return { "status": "ok", "data": data }
