import logging
import os
from cron_handler import CronHandler
from utils import get_env_data_as_dict
import asyncio

# This is a sample logging file, for Testing Purposes only
dir_path = os.path.dirname(os.path.realpath(__file__))
filename = os.path.join(dir_path, 'logfile.log')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(filename)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

async def main():

    logger.info(f"Path: {dir_path}")
    logger.info("sample test logger info")
    logger.error("sample error message")
    logger.warning("sample warning mesg")

    try:
        vars = get_env_data_as_dict(f'{dir_path}/.env')
        logger.info(vars)
        username = vars['SCHEDULER_USER']
        jobID = os.environ.get('ID')
        print(f'jobID: {jobID}')

        ch = CronHandler(username)
        status = await ch.get_job_status(jobID)
        logger.info(f'ID: {jobID}, Job Status: {status}')
        print(f'ID: {jobID}, Job Status: {status}')
    except Exception as e: 
        print(e)
        logger.error(f'Error: {e}')

asyncio.run(main())