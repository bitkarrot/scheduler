import asyncio
import httpx
import os
import json
from crud import create_log_entry, get_scheduler_job
import logging
import logging.handlers

filename = 'scheduler.log'

logger = logging.getLogger('scheduler')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=filename, encoding='utf-8', mode='a')
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

http_verbs = ['get', 'post', 'put', 'delete', 'head', 'options']

async def clear_log_file(logname: str) -> bool: 
    '''
        Clears the log file
    '''
    status = True
    try: 
        os.remove(logname)
        return status
    except Exception as e:
        logger.error(e)
        status = False
        return status

async def save_job_execution(response: str, jobID: str) -> None:
    '''
        Saves job execution to both db and to a logfile. 
        We can decide if we want to use either db or logfile or both later
        Note: We are logging everything to a single file for now.
    '''
    if response.status_code == 200:
        logger.info(f"jobID: {jobID}, status_code: {response.status_code}")
        logger.info(f'jobID: {jobID}, response text: {response.text}')
        create_log_entry(jobID, "success", response.text)
    else:
        logger.error(f"error, saving to database for jobID: {jobID}")
        create_log_entry(jobID, response.status_code, response.text)


async def main() -> None:
    '''
        The main method that is run when the run_cron_job.py is executed
        It will get jobID from the environment and query the DB 
        for the http verb, url, headers, and data. Then it will execute 
        the API call and log the result. 
    '''
    try:
        jobID = os.environ.get('ID')

        # TODO: test query DB for job and populate url, headers, data
        job = get_scheduler_job(jobID)
        method_name = job.selectedVerb
        url = job.url
        headers = json.loads(job.headers)
        data = json.loads(job.data)
        
        # Check if the method_name is valid for httpx
        if method_name.lower() in http_verbs:
            method_to_call = getattr(httpx, method_name.lower())
            response = method_to_call(url, headers=headers, params=data)
            await save_job_execution(response=response, jobID=jobID)
        else:
            logger.error(f'Invalid method name: {method_name}')
    except Exception as e:
        logger.error(f'exception thrown: {e}')


asyncio.run(main())


