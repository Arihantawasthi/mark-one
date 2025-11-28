from celery import chord, group

from app.celery.config import celery_app
from app.db import queries
from app.tasks.newsletter_tasks import process_and_save_newsletters_task, analyze_issue_task, aggregate_issue_analysis, test_task
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
    issues = queries.get_issues_by_analysis_run_id(analysis_run_id)
    analysis_group = group(
        analyze_issue_task.si(analysis_run_id, issue)
        for issue in issues
    )

    queries.update_analysis_run_issues_and_status(analysis_run_id, len(issues), "completed")
    issue_ids = [ issue["id"] for issue in issues ]
    return chord(analysis_group, aggregate_issue_analysis.si(issue_ids, analysis_run_id))()
    # return chord(analysis_group, test_task.si())()
