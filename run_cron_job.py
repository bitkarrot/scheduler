import asyncio
import httpx
import os
import json
import logging
import logging.handlers
import datetime as dt

dir_path = os.path.dirname(os.path.realpath(__file__))
logname = os.path.join(dir_path, 'scheduler.log')

logger = logging.getLogger('scheduler')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=logname, encoding='utf-8', mode='a')
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

http_verbs = ['get', 'post', 'put', 'delete', 'head', 'options']
LNBITS_BASE_URL = os.environ.get('LNBITS_BASE_URL') or 'http://localhost:5000'

async def save_job_execution(response: str, jobID: str, adminkey: str) -> None:
    '''
        Saves job execution to both db and to a logfile. 
        We can decide if we want to prioritize either later
        Note: We are logging everything to a single file for now, but
        individual rows in db.
    '''
    try:
        if response.status_code == 200:
            logger.info(f"jobID: {jobID}, status_code: {response.status_code}")
            logger.info(f'jobID: {jobID}, response text: {response.text}')

            url = f'{LNBITS_BASE_URL}/scheduler/api/v1/logentry'
            # data = { 'jobid': jobID, 'status': str(response.status_code), 'response': response.text, 'timestamp': dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S') }
            data = { 'job_id': jobID, 'status': str(response.status_code), 'response': 'sample text', 'timestamp': dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S') }

            logger.info(f' now pushing execution data to the database for jobID: {jobID}')
            logger.info(f'push db calling api : {url} with params: {data}')
            print("pushdb_response: pushing now")
            print(url)
            print(data)

            pushdb_response = httpx.post(
                url=url,
                headers={"X-Api-Key": adminkey},
                json=data
            )

            print(f'pushdb status: {pushdb_response.status_code}')
            logger.info(f'pushdb status: {pushdb_response.status_code}')
            logger.info(f'pushdb text: {pushdb_response.text}')

            if pushdb_response.status_code == 200:
                logger.info(f'success: saved results to db for jobID: {jobID}')
                return True
    except Exception as e:
        logger.error(f"error, saving to database for jobID: {jobID}")
        logger.error(e)
        return False

async def get_job_by_id(jobID: str, adminkey: str):
    '''
        Gets job by jobID from API, as this script run by cron
        doesn't have access to entire lnbits environment
    '''
    try:

        print("get_job_by_id: \n")
        url = f'{LNBITS_BASE_URL}/scheduler/api/v1/jobs/{jobID}'
        headers = {"X-Api-Key": adminkey}

        print(f'url: {url}')
        print(f'headers: {headers}')

        logger.info(f'headers: {headers}')
        logger.info(f'api call: {url}')

        response = httpx.get(
            url=url,
            headers={"X-Api-Key": adminkey}
        )
        logger.info(response.status_code)
        print(f'response: {response.status_code}')
        print(f'type: {type(response.text)}')

        items = json.loads(response.text)
        print("response items in get_job_by_id: \n")
        print({items['id']}, {items['name']}, {items['status']}, {items['selectedverb']}, {items['url']}, {items['headers']}, {items['body']}, {items['extra']})
    
        return response.text
    except Exception as e:
        print(f'exception thrown: {e}')
        logger.error(f'Error trying to fetch data from db, check is LNBITS server running?: {e}')

async def clear_log_file(logname: str) -> bool: 
    '''
        Clears the log file by deleting the file on disk
    '''
    status = True
    try: 
        os.remove(logname)
        return status
    except Exception as e:
        logger.error(e)
        status = False
        return status

async def main() -> None:
    '''
        The main method that is run when the run_cron_job.py is executed
        It will get jobID from the environment and query the DB 
        for the http verb, url, headers, and data. Then it will execute 
        the API call and log the result. 
    '''
    try:
        jobID = os.environ.get('ID')
        adminkey = os.environ.get('adminkey')
        varinfo = f'run_cron_job jobID: {jobID}, adminkey: {adminkey}'
        print(varinfo)
        logger.info(varinfo)

        # TODO: test query DB for job and populate url, headers, data
        job_response = await get_job_by_id(jobID, adminkey)
        job = json.loads(job_response)

        method_name = job['selectedverb']
        url = job['url']
        headers = {}
        body = {}

        if job['headers'] is not None:
           headers = json.loads(job['headers'])
        if job['body'] is not None:
           body = json.loads(job['body'])

        dbinfo = f'Database info jobID: {jobID}, method_name: {method_name}, url: {url}, headers: {headers}, body: {body}'    
        print(dbinfo)
        logger.info(dbinfo)

        # Check if the method_name is valid for httpx
        if method_name.lower() in http_verbs:
            method_to_call = getattr(httpx, method_name.lower())
            response = method_to_call(url, headers=headers, params=body)        
            await save_job_execution(response=response, jobID=jobID, adminkey=adminkey)
        else:
            logger.error(f'Invalid method name: {method_name}')

    except Exception as e:
        print(f'exception thrown: {e}')
        logger.error(f'exception thrown: {e}')


asyncio.run(main())


