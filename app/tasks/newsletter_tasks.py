from app.celery.config import celery_app
import logging
logger = logging.getLogger(__name__)

@celery_app.task(name="start_substack_analysis", bind=True)
def start_substack_analysis(self, search_result):
    from app.services import substack

    try:
        logger.info(f"Starting analysis for newsletter: {search_result['title']}")
        data = substack.get_substack_newsletter_archive(search_result)
        logger.info(f"Completed analysis for newsletter: {search_result['title']}")
        return data

    except Exception as e:
        logger.error(f"Error analyzing newsletter {search_result['title']}: {e}")
        raise self.retry(exc=e, countdown=10, max_retries=3)
