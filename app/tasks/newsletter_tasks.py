from app.celery.config import celery_app
import logging

from app.db import queries
from app.services.analysis import AnalysisService
from app.services.newsletter import NewsletterService
from app.services.pubsub import publish_status

logger = logging.getLogger(__name__)

@celery_app.task(name="process_and_save_newsletters_task", bind=True)
def process_and_save_newsletters_task(self, analysis_run_id, search_result):
    try:
        logger.info(
            f"[Scrape] Processing newsletter: {search_result['link']}",
            extra={ "analysis_run_id": analysis_run_id }
        )
        publish_status(
            analysis_run_id,
            "Scraping",
            "Processing Newsletters",
            f"Processing newsletter: {search_result['title']}",
            75
        )

        NewsletterService(analysis_run_id, search_result).process_and_save_issues()

        logger.info(
            f"[Scrape] Completed newsletter processing",
            extra={ "analysis_run_id": analysis_run_id }
        )
    except Exception as e:
        logger.error(
            f"[Scrape] Error processing newsletter: {search_result['link']}",
            extra={ "analysis_run_id": analysis_run_id, "error": str(e) },
            exc_info=True
        )
        raise e


@celery_app.task(name="analyze_issue_task", bind=True)
def analyze_issue_task(self, analysis_run_id, issue):
    try:
        logger.info(
            f"[Issue Analysis] Starting issue analysis for issue ID: {issue['id']}",
            extra={ "analysis_run_id": analysis_run_id, "issue_id": issue["id"] }
        )
        publish_status(
            analysis_run_id,
            "Issue Analysis",
            "Analyzing Newsletter Issues",
            f"Analyzing issue ID: {issue['id']}",
            90
        )

        AnalysisService(analysis_run_id, issue).analyze_issue()

        logger.info(
            f"[Issue Analysis] Completed issue analysis for issue ID: {issue['id']}",
            extra={ "analysis_run_id": analysis_run_id, "issue_id": issue["id"] }
        )
    except Exception as e:
        logger.error(
            f"[Issue Analysis] Error analyzing issue ID: {issue['id']}",
            extra={ "analysis_run_id": analysis_run_id, "issue_id": issue["id"], "error": str(e) },
            exc_info=True
        )
        raise e


@celery_app.task(name="test_task", bind=True)
def test_task(self):
    for _ in range(5):
        logger.error("TEST TASK EXECUTED")


@celery_app.task(name="aggregate_issue_analysis", bind=True)
def aggregate_issue_analysis(self, issue_ids, analysis_run_id):
    try:
        logger.info(
            f"[Aggregate Analysis] Starting aggregate analysis",
            extra={ "analysis_run_id": analysis_run_id, "issue_count": len(issue_ids),
                    "issue_ids": issue_ids }
        )

        AnalysisService(analysis_run_id, {}).aggregate_analysis(issue_ids)

        publish_status(
            analysis_run_id,
            "Aggregate Analysis",
            "Aggregating Issue Analyses",
            f"Aggregating analyses for {len(issue_ids)} issues.",
            100
        )

        logger.info(
            f"[Aggregate Analysis] Completed aggregation analysis",
            extra={ "analysis_run_id": analysis_run_id }
        )
    except Exception as e:
        logger.error(
            f"[Aggregate Analysis] Error during aggregate analysis",
            extra={ "analysis_run_id": analysis_run_id, "error": str(e) },
            exc_info=True
        )
        raise e


@celery_app.task(name="analyze_manual_issue_task", bind=True)
def analyze_manual_issue_task(self, analysis_run_id, search_results, issue_links):
    try:
        logger.info(
            f"[Manual Issue Analysis] Starting manual issue analysis",
            extra={ "analysis_run_id": analysis_run_id, "issue_links": issue_links }
        )
        publish_status(
            analysis_run_id,
            "Manual Issue Analysis",
            "Analyzing Manual Newsletter Issues",
            f"Starting manual issue analysis for {len(issue_links)} issues.",
            50
        )

        issues = NewsletterService(analysis_run_id, search_results[0]).process_and_save_manual_issues(issue_links)

        issue_ids = [ issue["id"] for issue in issues ]
        for issue in issues:
            AnalysisService(analysis_run_id, issue).analyze_issue()
            AnalysisService(analysis_run_id, {}).aggregate_analysis(issue_ids)

        logger.info(
            f"[Manual Issue Analysis] Completed manual issue analysis",
            extra={ "analysis_run_id": analysis_run_id }
        )
        publish_status(
            analysis_run_id,
            "Manual Issue Analysis",
            "Completed Manual Newsletter Issue Analysis",
            f"Completed manual issue analysis for {len(issue_links)} issues.",
            100
        )
    except Exception as e:
        logger.error(
            f"[Manual Issue Analysis] Error during manual issue analysis",
            extra={ "analysis_run_id": analysis_run_id, "error": str(e) },
            exc_info=True
        )
        raise e
