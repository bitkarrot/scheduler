import json
import logging
import logging.handlers
import os

import httpx

from .crud import (
    get_scheduler_job,
)

dir_path = os.path.dirname(os.path.realpath(__file__))
logname = os.path.join(dir_path, "test_run_job.log")
logger = logging.getLogger("scheduler testlog")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=logname, encoding="utf-8", mode="a")
dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(
    "[{asctime}] [{levelname}] {name}: {message}", dt_fmt, style="{"
)
handler.setFormatter(formatter)
logger.addHandler(handler)


async def test_job(job_id: str) -> str:
    """
    A clone of what is actually run when run_cron_job.py is executed
    This is used to execute the API call and log the result.
    """
    try:
        # print(f'[test_run_job]: jobid: {job_id} adminkey: {adminkey}')
        jobinfo = await get_scheduler_job(job_id)
        assert jobinfo, "Job not found"
        # print(f'[test_run_job]: get scheduler job created: {jobinfo}')

        body_json: dict = {}
        json_headers = {}

        method_name = jobinfo.selectedverb
        url = jobinfo.url
        assert url, "No URL found"
        body = jobinfo.body
        headers = jobinfo.headers
        assert headers, "No headers found"

        if body is None:
            body_json = {}
        elif len(body) > 0:
            body_json = json.loads(body)
            # await process_json_body(body)
            # print(f' Length of body data {len(body)}')

        for h in headers:
            key = h.key
            value = h.value
            json_headers.update({key: value})
            # print(f'key: {key} value: {value}')

        # print(f'body_json: {body_json}')
        # print(f'headers_json: {json_headers}')

        logger.info(
            "[test_run_job]: url: %s headers: %s body: %s", url, json_headers, body_json
        )
        response = None
        # GET response
        if method_name == "GET":
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=json_headers, params=body_json)
                logger.info(
                    "[test_run_job]: response status from api call: %s",
                    response.status_code,
                )
                logger.info(
                    "[test_run_job]: response text from api call: %s", response.text
                )
        # POST response
        elif method_name == "POST":
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=json_headers, data=body_json)
                logger.info(
                    "[test_run_job]: response status from api call: "
                    f"{response.status_code}"
                )
                logger.info(
                    f"[test_run_job]: response text from api call: {response.text}"
                )
        # PUT response
        elif method_name == "PUT":
            async with httpx.AsyncClient() as client:
                response = await client.put(url, headers=json_headers, data=body_json)
                logger.info(
                    "[test_run_job]: response status from api call: "
                    f"{response.status_code}"
                )
                logger.info(
                    f"[test_run_job]: response text from api call: {response.text}"
                )
        # DELETE response
        elif method_name == "DELETE":
            async with httpx.AsyncClient() as client:
                response = await client.delete(url, headers=json_headers)
                logger.info(
                    "[test_run_job]: response status from api call: "
                    f"{response.status_code}"
                )
                logger.info(
                    f"[test_run_job]: response text from api call: {response.text}"
                )

        # return "testjob 1234"
        assert response, "No response from API call"
        return response.text

    except Exception as e:
        logger.error("[test_job]:Exception thrown in [test_job]: %s", e)
        return str(e)
