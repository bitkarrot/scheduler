import asyncio
import httpx
import os
from crud import create_log_entry, get_scheduler_job
import json

http_verbs = ['get', 'post', 'put', 'delete', 'head', 'options']

async def save_job_execution(response: str, jobID: str) -> bool:
    if response.status_code == 200:
        print(f"success, saving to database for jobID: {jobID}") 
        print(f'status_code: {response.status_code}')
        # print(f'response: {response.text}')
        # TODO: save result to database w/job ID as reference and timestamp?
        create_log_entry(jobID, "success", response.text)
    else:
        print(f"error, saving to database for jobID: {jobID}")
        create_log_entry(jobID, response.status_code, response.text)
    return True


async def main() -> None:
    try:
        jobID = os.environ.get('ID')
        print(f'jobID: {jobID}')

        # TODO: test query DB for job and populate url, headers, data
        job = get_scheduler_job(jobID)
        method_name = job.selectedVerb
        url = job.url
        headers = json.loads(job.headers)
        data = json.loads(job.data)

        # method_name = 'GET'  # HTTP verb determined by DB query    
        # url = 'https://example.com'
        # headers = {'X-Custom': 'value'}
        # data = {'key': 'value'}
        
        # Check if the method_name is valid for httpx
        if method_name.lower() in http_verbs:
            method_to_call = getattr(httpx, method_name.lower())
            response = method_to_call(url, headers=headers, params=data)
            await save_job_execution(response=response, jobID=jobID)
        else:
            print(f'Invalid method name: {method_name}')
    except Exception as e:
        print(f'exception thrown: {e}')
        # TODO: log the error properly


asyncio.run(main())




