from fastapi import Request
import logging
import time
from app.core.logger import set_request_id

logger = logging.getLogger(__name__)

async def logging_middleware(request: Request, call_next):
    request_id = set_request_id()
    start_time = time.time()

    logger.info(
        f"Request Start: {request.method} {request.url.path}",
        extra={
            "extras": {
                "request_id": request_id,
                "method": request.method,
                "client_ip": request.client.host if request.client else "unknown",
            }
        }
    )

    try:
        response = await call_next(request)
        process_time = round((time.time() - start_time) * 100, 2)
        logger.info(
            f"Request Completed: {request.method} {request.url.path} completed in {process_time:.4f}ms",
            extra={
                "extras": {
                    "url": str(request.url),
                    "request_id": request_id,
                    "method": request.method,
                    "status_code": response.status_code,
                    "process_time_ms": process_time,
                }
            }
        )

        response.headers["X-Request-ID"] = request_id
        return response

    except Exception as e:
        process_time = round((time.time() - start_time) * 1000, 2)
        logger.error(
            f"Request Failed: {request.method} {request.url.path} failed in {process_time:.4f}ms",
            extra={
                "extras": {
                    "url": str(request.url),
                    "request_id": request_id,
                    "method": request.method,
                    "process_time_ms": process_time,
                    "error": str(e),
                }
            },
            exc_info=True
        )
        raise e
