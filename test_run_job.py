import asyncio
import httpx
import os
import json
import logging
import logging.handlers
import datetime as dt

from run_cron_job import check_logfile, get_job_by_id, call_api
# , save_job_execution

dir_path = os.path.dirname(os.path.realpath(__file__))
logname = os.path.join(dir_path, 'test_run_job.log')

logger = logging.getLogger('scheduler')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=logname, encoding='utf-8', mode='a')
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)


async def test_job(job_id: str, adminkey: str) -> None:
    '''
        A clone of what is actually run when run_cron_job.py is executed
        This is used to execute the API call and log the result. 
        
        headers = [],  default value
        body = None,  default value
        [{"key":"X-Api-Key","value":"0b2569190e2f4b"}]
    '''
    try:
        # print("inside test_job")
        await check_logfile(logname)
        job = await get_job_by_id(job_id, adminkey)
        method_name = job['selectedverb']
        url = job['url']
        headers = job['headers']
        body = job['body']

        json_headers = {}
        for h in headers: 
            json_headers.update({h['key']: h['value']})

        logger.info(f'[test_job]: {method_name}, {url}, {json_headers}, {body}')

        response = await call_api(method_name, url, json_headers, body)
        logger.info(f'[test_job]: response status from api call: {response.status_code}')
        logger.info(f'[test_job]: {response.text}')

    except json.JSONDecodeError as e:
        logger.info(f'[test_job]: body json decode error: {e}')
    except Exception as e:
        logger.error(f'exception thrown in [test_job]: {e}')


jobid="f017227f71af4686a4a94339d2725624"
admin="f0393874757f4824ad222e7557640963"

#asyncio.run(test_job(job_id=jobid, adminkey=admin))