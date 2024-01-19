import os
import logging
import logging.handlers
import httpx

from .crud import (
    get_scheduler_job,
)

dir_path = os.path.dirname(os.path.realpath(__file__))
logname = os.path.join(dir_path, 'test_run_job.log')
logger = logging.getLogger('scheduler testlog')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=logname, encoding='utf-8', mode='a')
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)

# async def call_api(method_name, url, headers, body):
#     '''
#         Call API with parameters from database, 
#         assume body, headers is a string from the db
#         this method called from run_cron_job.py for job execution    
#     '''
#     http_verbs = ['get', 'post', 'put', 'delete']

#     try:
#         body_json = {}
#         if len(body) > 0:
#             body_json = await process_json_body(body)

#         if method_name.lower() in http_verbs:
#             method_to_call = getattr(httpx, method_name.lower())

#             if method_name.lower() in ['get', 'delete'] and body_json is not None:
#                 response = method_to_call(url, headers=headers, params=body_json)
#             elif method_name.lower() in ['post', 'put']:
#                 response = method_to_call(url, headers=headers, json=body_json)

#             logger.info(f'[run_cron_job]: call_api response status: {response.status_code}')
#             logger.info(f'[run_cron_job]: call_api response text: {response.text}')
#             return response
#         else:
#             logger.info(f'Invalid method name: {method_name}')

#     except json.JSONDecodeError as e:
#         logger.info(f'body json decode error: {e}')
#         raise e

async def process_json_body(request_body):
    try:
        json_data = json.loads(request_body)
        # Code to process the JSON data
        logger.info("Successfully parsed JSON:", json_data)
        return json_data
    except json.JSONDecodeError as e:
        # Code to handle the case where the body is not JSON
        logger.info("Error decoding JSON:", str(e))
        logger.info("The provided body is not in JSON format")
        return {}

async def test_job(job_id: str, adminkey: str) -> str:
    '''
        A clone of what is actually run when run_cron_job.py is executed
        This is used to execute the API call and log the result. 
    '''
    try:
        print("inside test cron")
        print(f'jobid: {job_id} adminkey: {adminkey}')
        os.environ['ID'] = job_id
        os.environ['adminkey'] = adminkey

        jobinfo = await get_scheduler_job(job_id)
        print(f'Scheduler job created: {jobinfo}')
        #print(f' type of job info: {type(jobinfo)}')

        body_json = {}
        json_headers = {}
 
        method_name = jobinfo.selectedverb
        url = jobinfo.url
        body = jobinfo.body
        headers = jobinfo.headers

        print(f'method_name: {method_name}')
        print(f'url: {url}')
        print(f'body: {body_json}')
        print(f'header: {headers}')

        print(f' Length of body data {len(body)}')

        print("\n\n\n\n")

        if len(body) > 0:
            body_json = body # await process_json_body(body)
        
        for h in headers:
            key = h.key
            value = h.value
            print(f'key: {key} value: {value}')
            json_headers.update({key: value})

        print(f'body_json: {body_json}')
        print(f'headers_json: {json_headers}')

    # curl http://localhost:5000/api/v1/wallet -H "X-Api-Key: 0b3f9b8f35d64da2a8026a851fd9fd21" 
    #        jobinfo.url = 'http://localhost:5000/api/v1/wallet'


        ## GET response
        if method_name == 'GET':
            async with httpx.AsyncClient() as client:
                response = await client.get(jobinfo.url, headers=json_headers, params=body_json)
                print(f'response: {response}')
                logger.info('[run_cron_job]: response status from api call: %s', response.status_code)
                logger.info('response text from api call: %s', response.text)

        # # ## POST response
        if method_name == 'POST':
            async with httpx.AsyncClient() as client:
                response = await client.post(jobinfo.url, headers=json_headers, data=body_json)
                print(f'response: {response}')
                print(f'response status from api call: {response.status_code}')
                print(f'response text from api call: {response.text}')

        # return "testjob 1234"
        return response.text
    
    except Exception as e:
        logger.error('[test_job]:Exception thrown in [test_job]: %s', e)


# jobid="f017227f71af4686a4a94339d2725624"
# admin="f0393874757f4824ad222e7557640963"
#asyncio.run(test_job(job_id=jobid, adminkey=admin))