import asyncio
import os
# import httpx
# import json
# import datetime as dt

import logging
import logging.handlers

from cron_utils import save_job_execution, call_api, get_job_by_id, check_logfile

dir_path = os.path.dirname(os.path.realpath(__file__))
logname = os.path.join(dir_path, 'scheduler.log')

logger = logging.getLogger('scheduler')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=logname, encoding='utf-8', mode='a')
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

async def main() -> None:
    '''
        The main method that is run when the run_cron_job.py is executed
        It will get jobID from the environment and query the DB 
        for the http verb, url, headers, and data. Then it will execute 
        the API call and log the result. 
        
        example data:
        headers = [],  default value
        body = None,  default value
        [{"key":"X-Api-Key","value":"0b2569190e2f4b"}]
    '''
    try:
        await check_logfile(logname)

        jobID = os.environ.get('ID')
        adminkey = os.environ.get('adminkey')

        job = await get_job_by_id(jobID, adminkey)
        method_name = job['selectedverb']
        url = job['url']
        headers = job['headers']
        body = job['body']

        json_headers = {}
        for h in headers: 
            json_headers.update({h['key']: h['value']})

        response = await call_api(method_name, url, json_headers, body)
        logger.info('[run_cron_job]: response status from api call: %s', response.status_code)
        logger.info('response text from api call: %s', response.text)

        await save_job_execution(response=response, jobID=jobID, adminkey=adminkey)

    except Exception as e:
        logger.error('exception thrown in main() run_cron_job: %s', e)


asyncio.run(main())
