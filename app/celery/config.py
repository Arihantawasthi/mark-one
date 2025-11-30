from celery import Celery
from celery.app.base import signals
from app.core.logger import setup_logging
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
    enable_utc=True,
)

@signals.setup_logging.connect
def setup_celery_logging(**kwargs):
    setup_logging(log_level=settings.LOG_LEVEL, log_file=settings.LOG_FILE)

@signals.before_task_publish.connect
def add_request_id_header(headers=None, **kwargs):
    from app.core.logger import get_request_id
    if headers is not None:
        headers['request_id'] = get_request_id()


@signals.task_prerun.connect
def recover_request_id(sender=None, task=None, **kwargs):
    from app.core.logger import set_request_id
    req = getattr(task.request, 'headers', {})
    request_id = req.get('request_id')
    if request_id:
        set_request_id(request_id)
