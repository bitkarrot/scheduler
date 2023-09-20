import logging
import os
from cron_handler import CronHandler
from utils import get_env_data_as_dict
import asyncio

# This is a sample logging file
# For Testing Purposes only
dir_path = os.path.dirname(os.path.realpath(__file__))
filename = os.path.join(dir_path, 'logtest.log')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(filename)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

logger.info(f"Path: {dir_path}")
logger.info("this is test logger info")
logger.error("error message")
logger.warning("warning mesg")

async def main():
    vars = get_env_data_as_dict('../.env')
    print(vars)
    username = vars['SCHEDULER_USER']
    jobID = os.environ.get('ID')
    ch = CronHandler(username)
    status = await ch.get_job_status(jobID)
    print(f'ID: {jobID}, Job Status: {status}')



asyncio.run(main())