from datetime import datetime
import time
import logging

logger = logging.getLogger(__name__)


class StatsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        logger.info(f"request for {request.path} received at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')}")

        response = self.get_response(request)

        duration = time.time() - start_time

        # Add the header. Or do other things, my use case is to send a monitoring metric
        response["X-Page-Generation-Duration-ms"] = int(duration * 1000)

        logger.info(f"after {int(duration * 1000)}ms, response for {request.path} sent at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')}")
        return response
