from app.services import substack
from app.celery.config import celery_app
import logging

from app.db import queries

logger = logging.getLogger(__name__)

@celery_app.task(name="process_and_save_newsletters_task", bind=True)
def process_and_save_newsletters_task(self, analysis_run_id, search_result):
    logger.info(f"Starting analysis for newsletter: {search_result['title']}")
    substack.process_and_save_newsletters(analysis_run_id, search_result)
    logger.info(f"Completed analysis for newsletter: {search_result['title']}")


@celery_app.task(name="analyze_issue_task", bind=True)
def analyze_issue_task(self, issue):
    from app.llm import agent

    analysis = agent.analyze_newsletter_issue(issue)
    logger.error("Analyzing issue!!!!!")
    queries.insert_issue_analysis(issue["id"], analysis.additional_kwargs["parsed"])


@celery_app.task(name="test_task", bind=True)
def test_task(self):
    for i in range(5):
        logger.info(f"Test task iteration {i}")
