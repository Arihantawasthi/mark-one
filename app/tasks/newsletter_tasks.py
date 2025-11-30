from app.celery.config import celery_app
import logging

from app.services.analysis import AnalysisService
from app.services.newsletter import NewsletterService

logger = logging.getLogger(__name__)

@celery_app.task(name="process_and_save_newsletters_task", bind=True)
def process_and_save_newsletters_task(self, analysis_run_id, search_result):
    try:
        logger.info(
            f"[Scrape] Processing newsletter: {search_result['link']}",
            extra={ "analysis_run_id": analysis_run_id }
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
