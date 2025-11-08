from celery import Celery
import os

REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
REDIS_BROKER_DB = os.getenv('REDIS_BROKER_DB')

REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_BROKER_DB}'

celery_app = Celery(
    'mark-one',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.tasks.newsletter_tasks']
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
