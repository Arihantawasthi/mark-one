from celery import chord, group

from app.celery.config import celery_app
from .newsletter_tasks import process_and_save_newsletters_task, analyze_issue_task, test_task
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="scraping_stage", bind=True)
def scraping_stage(self, analysis_run_id, search_results):
    scraping_group = [
        process_and_save_newsletters_task.si(analysis_run_id, search_result)
        for search_result in search_results
    ]

    return chord(scraping_group, issue_analysis_stage.si(analysis_run_id))()



@celery_app.task(name="issue_analysis_stage", bind=True)
def issue_analysis_stage(self, analysis_run_id):
    logger.error("STARTED ISSUE ANALYSIS STAGE")
    # issues = queries.get_issues_by_analysis_run_id(analysis_run_id)
    analysis_group = group(
        analyze_issue_task.si(issue)
        for issue in range(10)
    )

    return chord(analysis_group, test_task.si())()
    # queries.update_analysis_run_issues_and_status(analysis_run_id, issue_count, "completed")
