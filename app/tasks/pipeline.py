import asyncio
from celery import chord, group

from app.celery.config import celery_app
from app.db import queries
from app.services.pubsub import publish_status
from app.services.search import SearchService
from app.tasks.newsletter_tasks import process_and_save_newsletters_task, analyze_issue_task, aggregate_issue_analysis, test_task
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="search_stage", bind=True)
def search_stage(self, analysis_run_id, search_queries):
    logger.info(f"Running test task...", extra={"analysis_run_id": analysis_run_id})
    try:
        logger.info(
            "[Stage: Search] Started Search Stage",
            extra={"analysis_run_id": analysis_run_id, "queries": search_queries}
        )
        search_service = SearchService(search_queries)
        search_results = asyncio.run(search_service.search())

        publish_status(
            analysis_run_id,
            "Search",
            "Searching for newsletters",
            f"Found {len(search_results)} newsletters matching the search terms.",
            20
        )

        scraping_stage.delay(analysis_run_id, search_results)

        logger.info(
            "[Stage: Search] Completed Search Stage",
            extra={"analysis_run_id": analysis_run_id, "search_result_count": len(search_results)}
        )
        return None

    except Exception as e:
        logger.error(
            "[Stage: Search] FAILED",
            extra={"analysis_run_id": analysis_run_id, "error": str(e)},
            exc_info=True
        )
        raise e

@celery_app.task(name="scraping_stage", bind=True)
def scraping_stage(self, analysis_run_id, search_results):
    try:
        logger.info(
            "[Stage: Scrapping] Started Scraping Stage",
            extra={
                "analysis_run_id": analysis_run_id,
                "search_results": search_results,
                "search_result_count": len(search_results)
            }
        )
        publish_status(
            analysis_run_id,
            "Scraping",
            "Scraping newsletters",
            f"Starting to scrape {len(search_results) * 5} newsletters.",
            25
        )
        scraping_group = [
            process_and_save_newsletters_task.si(analysis_run_id, search_result)
            for search_result in search_results
        ]

        chord(scraping_group, issue_analysis_stage.si(analysis_run_id))()

        logger.info(
            "[Stage: Scrapping] Submitted scraping tasks",
            extra={"analysis_run_id": analysis_run_id}
        )
    except Exception as e:
        logger.error(
            "[Stage: Scrapping] FAILED",
            extra={"analysis_run_id": analysis_run_id, "error": str(e)},
            exc_info=True
        )
        raise e


@celery_app.task(name="issue_analysis_stage", bind=True)
def issue_analysis_stage(self, analysis_run_id):
    try:
        logger.info(
            "[Stage: Issue Analysis] Started Issue Analysis Stage",
            extra={"analysis_run_id": analysis_run_id}
        )
        issues = queries.get_issues_by_analysis_run_id(analysis_run_id)
        issue_ids = [ issue["id"] for issue in issues ]
        publish_status(
            analysis_run_id,
            "Issue Analysis",
            "Analyzing newsletter issues",
            f"Starting analysis of {len(issues)} newsletter issues.",
            50
        )
        logger.info(
            "[Stage: Issue Analysis] Found Issues",
            extra={ "analysis_run_id": analysis_run_id, "issue_count": len(issues) }
        )

        analysis_group = group(
            analyze_issue_task.si(analysis_run_id, issue)
            for issue in issues
        )

        chord(analysis_group, aggregate_issue_analysis.si(issue_ids, analysis_run_id))()
        logger.info(
            "[Stage: Issue Analysis] Issue analysis tasks submitted",
            extra={ "analysis_run_id": analysis_run_id },
        )
    except Exception as e:
        logger.error(
            "[Stage: Issue Analysis] FAILED",
            extra={"analysis_run_id": analysis_run_id, "error": str(e)},
            exc_info=True
        )
