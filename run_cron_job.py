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

LNBITS_BASE_URL = os.environ.get('LNBITS_BASE_URL') or 'http://localhost:5000'

async def save_job_execution(response: str, jobID: str, adminkey: str) -> None:
    '''
        Saves job execution to both db and to a logfile. 
        We can decide if we want to prioritize either later
        Note: We are logging everything to a single file for now, but
        individual rows in db.
    '''
    try:
        print(f' inside save_job_execution now ')
        if response.status_code == 200:
            logger.info(f"jobID: {jobID}, status_code: {response.status_code}")
            logger.info(f'jobID: {jobID}, response text: {response.text}')

            url = f'{LNBITS_BASE_URL}/scheduler/api/v1/logentry'

            # we have some difficulty saving response.text to db, unicode?
            data = {'job_id': jobID, 
                    'status': str(response.status_code), 
                    'response': 'sample text', # str(response.text),  
                    'timestamp': dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S') }

            logger.info(f' now pushing execution data to the database for jobID: {jobID}')
            logger.info(f'push db calling api : {url} with params: {data}')
           
            pushdb_response = httpx.post(
                url=url,
                headers={"X-Api-Key": adminkey},
                json=data
            )
            logger.info(f'pushdb status: {pushdb_response.status_code}')
            # logger.info(f'pushdb text: {pushdb_response.text}')

            if pushdb_response.status_code == 200:
                logger.info(f'success: saved results to db for jobID: {jobID}')
                return True
    except Exception as e:
        logger.error(f"error, saving to database for jobID: {jobID}")
        logger.error(e)
        return False


def call_api(method_name, url, headers, body):
    # assume body, headers is a string from the db
    # this method called from run_cron_job.py for job execution
    http_verbs = ['get', 'post', 'put', 'delete']

    print(f'body: {body} , type: {type(body)}')
    try:
        body_json = {}
        if body is not None:
            body_json = json.loads(body)
        print(f'body json: {body_json}')

        if method_name.lower() in http_verbs:
            method_to_call = getattr(httpx, method_name.lower())
            print(f'method_to_call: {method_to_call}')

            if method_name.lower() in ['get', 'delete'] and body_json is not None:
                response = method_to_call(url, headers=headers, params=body_json)
            elif method_name.lower() in ['post', 'put']:
                response = method_to_call(url, headers=headers, json=body_json)

            print("response from httpx call: ")
            print(response.status_code)
            # print(response.text)
            return response
        else:
            print(f'Invalid method name: {method_name}')

    except json.JSONDecodeError as e:
        print(f'body json decode error: {e}')
        raise e


async def get_job_by_id(jobID: str, adminkey: str):
    '''
        Gets job by jobID from API, as this script run by cron
        doesn't have access to entire lnbits environment
    '''
    try:

        print("get_job_by_id: \n")
        url = f'{LNBITS_BASE_URL}/scheduler/api/v1/jobs/{jobID}'

        response = httpx.get(
            url=url,
            headers={"X-Api-Key": adminkey}
        )
        print(f"response items in get_job_by_id: {response.text}\n")
        items = json.loads(response.text)
        return items
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
    # headers = [],  default value
    # body = None,  default value
    # example:[{"key":"X-Api-Key","value":"0b2569190e2f4b"},{"key":"Content-type","value":"application/json"}]
    try:
        jobID = os.environ.get('ID')
        adminkey = os.environ.get('adminkey')
        varinfo = f'run_cron_job jobID: {jobID}, adminkey: {adminkey}'
        print(varinfo)
        logger.info(varinfo)

        job = await get_job_by_id(jobID, adminkey)
        method_name = job['selectedverb']
        url = job['url']
        headers = job['headers']
        body = job['body']

        # print(f'type headers: {type(headers)}') 
        dbinfo = f'Database info jobID: {jobID}, method_name: {method_name}, url: {url}, headers: {headers}, body: {body}'    
        print(dbinfo)
        logger.info(dbinfo)

        json_headers = {}
        for h in headers: 
            json_headers.update({h['key']: h['value']})

        response = call_api(method_name, url, json_headers, body)

        print(f'response status from api call: {response.status_code}')
        # print(f'response text from api call: {response.text}')        
        #logger.info(f'response status from api call: {response.status_code}')
        #logger.info(f'response text from api call: {response.text}')

        # save_job_execution(response=response, jobID=jobID, adminkey=adminkey)

    except Exception as e:
        print(f'exception thrown in main() run_cron_job: {e}')
        logger.error(f'exception thrown in main() run_cron_job: {e}')


asyncio.run(main())


