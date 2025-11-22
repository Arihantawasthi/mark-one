from celery import Celery
import app.core.settings as settings

celery_app = Celery(
    'mark-one',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.tasks.newsletter_tasks', 'app.tasks.pipeline']
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    result_expires=3600,
    worker_concurrency=4,
    broker_connection_retry_on_startup=True,
    timezone="UTC",
)
