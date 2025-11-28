from app.celery.config import celery_app
import logging

from app.services.analysis import AnalysisService
from app.services.newsletter import NewsletterService

logger = logging.getLogger(__name__)

@celery_app.task(name="process_and_save_newsletters_task", bind=True)
def process_and_save_newsletters_task(self, analysis_run_id, search_result):
    logger.info(f"Starting analysis for newsletter: {search_result['title']}")

    NewsletterService(analysis_run_id, search_result).process_and_save_issues()

    logger.info(f"Completed analysis for newsletter: {search_result['title']}")


@celery_app.task(name="analyze_issue_task", bind=True)
def analyze_issue_task(self, analysis_run_id, issue):
    AnalysisService(analysis_run_id, issue).analyze_issue()


@celery_app.task(name="test_task", bind=True)
def test_task(self):
    for _ in range(5):
        logger.error("TEST TASK EXECUTED")


@celery_app.task(name="aggregate_issue_analysis", bind=True)
def aggregate_issue_analysis(self, issue_ids, analysis_run_id):
    AnalysisService(analysis_run_id, {}).aggregate_analysis(issue_ids)
