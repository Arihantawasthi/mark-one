import json
import logging
from fastapi import APIRouter, Depends, WebSocket
from app.db import queries
from app.services.beehiiv import BeehiivScraper
from app.services.search import SearchService
from app.tasks.pipeline import scraping_stage, search_stage
from app.tasks.newsletter_tasks import analyze_manual_issue_task
from app.services.pubsub import redis_client_async
from app.core.helpers import TokenException, hash_password, verify_password, generate_access_token, verify_token

logger = logging.getLogger(__name__)
router = APIRouter(tags=["newsletter"])


@router.get("")
async def health_check():
    logger.info("Health check endpoint called!")
    return { "status": "ok", "service": "scrapper" }

@router.post("/create-client")
async def create_client(body: dict):
    username = body.get("username", "")
    password = body.get("password", "")
    max_usage = body.get("max_usage", 1000)
    max_token_usage = body.get("max_token_usage", 100_000)

    password = hash_password(password)

    if not username or not password or not max_usage or not max_token_usage:
        return { "requestStatus": 0, "message": "Missing required fields" }

    client_id = queries.insert_client(username, password, max_usage, max_token_usage)
    return { "requestStatus": 1, "message": "Client created successfully", "id": client_id }


@router.post("/login")
async def login(body: dict):
    username = body.get("username", "")
    password = body.get("password", "")

    if not username or not password:
        return { "requestStatus": 0, "message": "Missing required fields" }

    client = queries.get_client_by_username(username)
    if not client:
        return { "requestStatus": 0, "message": "Invalid username or password" }

    stored_password_hash = client["password"]
    if not verify_password(password, stored_password_hash):
        return { "requestStatus": 0, "message": "Invalid username or password" }

    token = generate_access_token(client)
    data = {
        "client_id": client["id"],
        "username" : client["username"],
        "token": token,
        "usage": client["current_usage"],
        "token_usage": client["current_token_usage"]
    }
    return { "requestStatus": 1, "message": "Login successful", "data": data }


@router.post("/test-route")
def test_route(token_data: dict = Depends(verify_token)):
    if token_data.get("requestStatus") == 0:
        return token_data
    try:
        return { "requestStatus": 1, "message": "Token is valid", "data": token_data }
    except Exception as e:
        logger.error(
            f"Error in test route: {e}",
            extra={"error": str(e)},
            exc_info=True
        )
        return { "requestStatus": 0, "message": "Invalid token" }


@router.post("/start-query-analysis")
def start_query_analysis(body: dict[str, list], token_data: dict = Depends(verify_token)):
    if not token_data:
        return { "requestStatus": 0, "message": "User is not authorized!" }

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
        "initiated",
        token_data.get("sub_id")
    )

    search_stage.delay(analysis_run_id, search_queries)
    return { "requestStatus": 1, "message": "Analysis started", "analysis_id": analysis_run_id }


@router.post("/start-links-analysis")
def start_links_analysis(body: dict[str, list], token_data: dict = Depends(verify_token)):
    if not token_data:
        return { "requestStatus": 0, "message": "user is not authorized!" }

    links = body.get("links", [])
    if not links:
        return { "requestStatus": 0, "message": "no links provided" }

    display_title = f'custom links analysis - "{links[0]}"'
    if len(links) > 1:
        display_title += f' (+{len(links)-1})'

    analysis_run_id = queries.insert_analysis_run(
        display_title,
        "",
        "general",
        [],
        0,
        0,
        "initiated",
        token_data.get("sub_id")
    )

    search_results = [ { "link": link, "title": "custom" } for link in links ]
    scraping_stage.delay(analysis_run_id, search_results)
    return { "requestStatus": 1, "message": "analysis started", "analysis_id": analysis_run_id }


@router.post("/start-manual-issues-analysis")
def start_manual_issues_analysis(body: dict, token_data: dict = Depends(verify_token)):
    if not token_data:
        return { "requestStatus": 0, "message": "User is not authorized!" }

    links = body.get("issue_urls", [])
    analysis_run_id = body.get("analysis_id", None)
    if not links or not analysis_run_id:
        return { "requestStatus": 0, "message": "No links provided or Analysis Id not found" }

    search_results = [ { "link": link, "title": "Custom" } for link in links ]
    analyze_manual_issue_task.delay(analysis_run_id, search_results, links)
    return { "requestStatus": 1, "message": "Manual issues analysis started", "analysis_id": analysis_run_id }


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


@router.get("/analysis-status/{analysis_run_id}")
def analysis_status(analysis_run_id: int, token_data: dict = Depends(verify_token)):
    if not token_data:
        return { "requestStatus": 0, "message": "User is not authorized!" }

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
def get_analysis(analysis_run_id: int, token_data: dict = Depends(verify_token)):
    if not token_data:
        return { "requestStatus": 0, "message": "User is not authorized!" }

    issue_analysis = queries.get_issue_analyses_by_analysis_run_id(analysis_run_id)
    agg_analysis = queries.get_agg_issue_analysis_by_run_id(analysis_run_id)
    return {
        "requestStatus": 1,
        "message": "Successfully fetched analysis",
            "data": { "analysis_run_id": analysis_run_id, "issue_analyses": issue_analysis, "agg_analysis": agg_analysis }
    }

@router.get("/analysis/process-status/{analysis_run_id}")
def get_analysis_process_status(analysis_run_id: int, token_data: dict = Depends(verify_token)):
    if not token_data:
        return { "requestStatus": 0, "message": "User is not authorized!" }

    process_status = queries.get_analysis_progress_status(analysis_run_id)
    return {
        "requestStatus": 1,
        "message": "Successfully fetched analysis process status",
        "data": { "analysis_run_id": analysis_run_id, "process_status": process_status }
    }


@router.get("/analyses/list")
def list_analyses(token_data: dict = Depends(verify_token)):
    if not token_data:
        return { "requestStatus": 0, "message": "User is not authorized!" }

    analyses = queries.get_all_analyses(token_data.get("sub_id"))
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
