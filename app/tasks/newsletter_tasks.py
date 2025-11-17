from celery import chord
from app.celery.config import celery_app
import logging

from app.db import queries

logger = logging.getLogger(__name__)

@celery_app.task(name="start_substack_analysis_task", bind=True)
def start_substack_analysis(self, search_result, analysis_run_id):
    from app.services import substack

    try:
        logger.info(f"Starting analysis for newsletter: {search_result['title']}")
        substack.process_and_save_newsletters(search_result, analysis_run_id)
        logger.info(f"Completed analysis for newsletter: {search_result['title']}")

    except Exception as e:
        logger.error(f"Error analyzing newsletter {search_result['title']}: {e}")
        raise self.retry(exc=e, countdown=10, max_retries=3)


@celery_app.task(name="process_newsletter_issues", bind=True)
def process_newsletter_issues(self, analysis_run_id, search_results):
    scraping_tasks = []
    for search_result in search_results:
        scraping_tasks.append(start_substack_analysis.s(search_result, analysis_run_id))

    chord(scraping_tasks)(call_llm_analysis.s(analysis_run_id))


@celery_app.task(name="call_llm_analysis", bind=True)
def call_llm_analysis(self, analysis_run_id):

    queries.update_analysis_run_issues_and_status(analysis_run_id, issue_count, "completed")
