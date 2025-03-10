import asyncio
import datetime as dt
import json
import logging
import logging.handlers
import os
from typing import Optional

import httpx

dir_path = os.path.dirname(os.path.realpath(__file__))
logname = os.path.join(dir_path, "scheduler.log")

logger = logging.getLogger("scheduler")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=logname, encoding="utf-8", mode="a")
dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(
    "[{asctime}] [{levelname}] {name}: {message}", dt_fmt, style="{"
)
handler.setFormatter(formatter)
logger.addHandler(handler)

LNBITS_BASE_URL = os.environ.get("BASE_URL") or "http://localhost:5000"


async def save_job_execution(
    response: httpx.Response, job_id: str, adminkey: str
) -> None:
    """
    Saves job execution to both db and to a logfile.
    We can decide if we want to prioritize either later
    Note: We are logging everything to a single file for now, but
    individual rows in db.
    """
    try:
        # print(f' inside save_job_execution now ')
        if response.status_code == 200:
            logger.info("job_id: %s, status_code: %s", job_id, response.status_code)
            # logger.info(f'job_id: %s, response text: %s', job_id, response.text)

            url = f"{LNBITS_BASE_URL}/scheduler/api/v1/logentry"

            logger.info("pushdb: response.status type: %s", type(response.status_code))
            logger.info("pushdb: response.text type: %s", type(response.text))
            # we have some difficulty saving response.text to db, unicode?
            data = {
                "id": os.urandom(16).hex(),  # Generate a unique ID for the log entry
                "job_id": job_id,
                "status": str(response.status_code),
                # 'response': 'sample text', # str(response.text),
                "response": response.text,
                "timestamp": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            logger.info(
                "pushdb: now pushing execution data to " "the database for job_id: %s",
                job_id,
            )
            logger.info("pushdb: calling api : %s with params: %s", url, data)

            pushdb_response = httpx.post(
                url=url, headers={"X-Api-Key": adminkey}, json=data
            )
            logger.info(
                "SaveJobExecution: pushdb status: %s", pushdb_response.status_code
            )
            # logger.info(f'SaveJobExecution: pushdb text: %s', pushdb_response.text)

            if pushdb_response.status_code == 200:
                logger.info("success: saved results to db for job_id: %s", job_id)
    except Exception as e:
        logger.error("error, saving to database for job_id: %s", job_id)
        logger.error(e)


async def process_json_body(request_body):
    try:
        json_data = json.loads(request_body)
        # Code to process the JSON data
        logger.info("Successfully parsed JSON: %s", json_data)
        return json_data
    except json.JSONDecodeError as e:
        # Code to handle the case where the body is not JSON
        logger.info("Error decoding JSON: %s", str(e))
        logger.info("The provided body is not in JSON format")
        return {}


async def call_api(method_name, url, headers, body) -> Optional[httpx.Response]:
    """
    Call API with parameters from database,
    assume body, headers is a string from the db
    this method called from run_cron_job.py for job execution
    """
    http_verbs = ["get", "post", "put", "delete"]

    try:
        body_json: dict = {}
        if body is None:
            body_json = {}
        elif len(body) > 0:
            body_json = await process_json_body(body)

        if method_name.lower() in http_verbs:
            method_to_call = getattr(httpx, method_name.lower())

            response = None
            if method_name.lower() in ["get", "delete"] and body_json is not None:
                response = method_to_call(url, headers=headers, params=body_json)
            elif method_name.lower() in ["post", "put"]:
                response = method_to_call(url, headers=headers, json=body_json)

            assert response, "response is None"
            logger.info(
                "[run_cron_job]: call_api response status: %s", response.status_code
            )
            logger.info("[run_cron_job]: call_api response text: %s", response.text)
            return response
        else:
            logger.info("Invalid method name: %s", method_name)

    except json.JSONDecodeError as exc:
        logger.info("body json decode error: %s", exc)
        raise exc
    return None


async def get_job_by_id(job_id: str, adminkey: str):
    """
    Gets job by job_id from API, as this script run by cron
    doesn't have access to entire lnbits environment
    """
    try:
        url = f"{LNBITS_BASE_URL}/scheduler/api/v1/jobs/{job_id}"

        response = httpx.get(url=url, headers={"X-Api-Key": adminkey})
        logger.info(
            "[get_job_by_id]: response items in get_job_by_id: %s\n", response.text
        )
        items = json.loads(response.text)
        return items
    except Exception as e:
        logger.error("[get_job_by_id]: exception thrown: %s", e)
        logger.error(
            "[get_job_by_id]: Error trying to fetch data from db, "
            "check is LNBITS server running?: %s",
            e,
        )


async def clear_log_file(logname: str) -> bool:
    """
    Clears the log file by deleting the file on disk
    """
    status = True
    try:
        os.remove(logname)
        return status
    except Exception as e:
        logger.error(e)
        status = False
        return status


async def check_logfile(logfile: str) -> None:
    # Check if the file exists
    if os.path.exists(logfile):
        logger.info("[check_logfile]: The file %s exists.", logfile)
    else:
        # Create the file
        with open(logfile, "w") as file:
            now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file.write(f"[{now}][check_logfile]: This is a new scheduler logfile.")


async def main() -> None:
    """
    The main method that is run when the run_cron_job.py is executed
    It will get job_id from the environment and query the DB
    for the http verb, url, headers, and data. Then it will execute
    the API call and log the result.

    example data:
    headers = [],  default value
    body = None,  default value
    [{"key":"X-Api-Key","value":"0b2569190e2f4b"}]
    """
    try:
        await check_logfile(logname)

        logger.info("[run_cron_job]: LNBITS_BASE_URL = %s", LNBITS_BASE_URL)
        job_id = os.environ.get("ID")
        assert job_id, "job_id not found in environment variables"
        adminkey = os.environ.get("adminkey")
        assert adminkey, "adminkey not found in environment variables"
        logger.info("[run_cron_job]: job_id: %s adminkey: %s", job_id, adminkey)

        job = await get_job_by_id(job_id, adminkey)
        assert job, "job not found in database"
        method_name = job["selectedverb"]
        url = job["url"]
        headers = job["headers"]
        body = job["body"]

        json_headers = {}
        for h in headers:
            json_headers.update({h["key"]: h["value"]})

        response = await call_api(method_name, url, json_headers, body)
        assert response, "response is None"
        logger.info(
            "[run_cron_job]: response status from api call: %s", response.status_code
        )
        logger.info("response text from api call: %s", response.text)

        await save_job_execution(response=response, job_id=job_id, adminkey=adminkey)

    except Exception as e:
        logger.error("exception thrown in main() run_cron_job: %s", e)


asyncio.run(main())
