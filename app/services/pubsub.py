import json
import redis
import redis.asyncio as aioredis

from app.core import settings

redis_client_sync = redis.Redis.from_url(settings.REDIS_STATUS_URL)
redis_client_async = aioredis.Redis.from_url(settings.REDIS_STATUS_URL)

def publish_status(analysis_run_id: int, stage: str, title: str, detail: str, progress: int):
    status_message = {
        "analysis_run_id": analysis_run_id,
        "stage": stage,
        "title": title,
        "detail": detail,
        "progress": progress,
        "total_stages": 5
    }
    channel = f"analysis_status:{analysis_run_id}"
    redis_client_sync.publish(channel, json.dumps(status_message))
