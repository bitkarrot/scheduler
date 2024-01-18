import os
import logging
import logging.handlers

dir_path = os.path.dirname(os.path.realpath(__file__))
logname = os.path.join(dir_path, 'test_run_job.log')

logger = logging.getLogger('scheduler testlog')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=logname, encoding='utf-8', mode='a')
dt_fmt = '%Y-%m-%d %H:%M:%S'
formatter = logging.Formatter('[{asctime}] [{levelname}] {name}: {message}', dt_fmt, style='{')
handler.setFormatter(formatter)
logger.addHandler(handler)


async def test_job(job_id: str, adminkey: str) -> str:
    '''
        A clone of what is actually run when run_cron_job.py is executed
        This is used to execute the API call and log the result. 
    '''
    try:
        print("inside test cron")
        return "testjob 1234"
    except Exception as e:
        logger.error('[test_job]:Exception thrown in [test_job]: %s', e)


# jobid="f017227f71af4686a4a94339d2725624"
# admin="f0393874757f4824ad222e7557640963"
#asyncio.run(test_job(job_id=jobid, adminkey=admin))