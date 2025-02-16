import asyncio
import logging
import logging.handlers
import sys

import httpx

sys.path.insert(0, "..")

logfile = "test_scheduler.log"

logger = logging.getLogger("test_scheduler")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=logfile, encoding="utf-8", mode="a")
dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(
    "[{asctime}] [{levelname}] {name}: {message}", dt_fmt, style="{"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


async def main_test() -> None:
    http_verbs = ["get", "post", "put", "delete", "head", "options"]
    try:
        job_id = "12345test"
        method_name = "GET"  # HTTP verb determined by DB query
        url = "https://example.com"
        headers = {"X-Custom": "value"}
        data = {"key": "value"}

        # Check if the method_name is valid for httpx
        if method_name.lower() in http_verbs:
            method_to_call = getattr(httpx, method_name.lower())
            response = method_to_call(url, headers=headers, params=data)
            if response.status_code == 200:
                logger.info(f"job_id: {job_id}, status_code: {response.status_code}")
                logger.info(f"job_id: {job_id}, response text: {response.text}")
            else:
                logger.error(f"error, saving to database for job_id: {job_id}")
        else:
            logger.error(f"Invalid method name: {method_name}")

    except Exception as e:
        logger.error(f"exception thrown: {e}")


asyncio.run(main_test())
