
import asyncio
import datetime as dt
import sys
sys.path.insert(0,'..')
from cron_handler import CronHandler
from utils import get_env_data_as_dict

## TODO make this a legit pytest
## UNIT TEST ALL THE THINGS!!

async def main(): 
    vars = get_env_data_as_dict('../.env')
    print(vars)
    username = vars['SCHEDULER_USER']
    print(f'Scheduler Username: {username}')

    print("testing CronHandler")
    # username = 'bitcarrot'
    env_vars = {'SHELL': '/usr/bin/bash', 'API_URL': 'http://localhost:8000'}
    
    # unique job id number to be placed in comment
    comment = "cron now ls"
    echo_comment = "cron now echo"

    now = dt.datetime.now()
    print(f'current datetime: {now}')
    
    ch = CronHandler(username)

    # regular cron job with comment
    response = await ch.new_job("ls", "* * * * *", comment=comment)
    print(response)

    # regular cron job with aliase
    response = await ch.new_job("ls", "@hourly", comment=comment)
    print(response)


    # cron job with env vars
    response = await ch.new_job_with_env("echo", "* * * * *", comment=echo_comment, env=env_vars)
    print(response)

    # enable job
    print("Enable Job by Comment")
    enable_status = await ch.enable_job_by_comment(comment=comment, bool=True)
    print(f'enabled status: {enable_status}')

    # disable job
    print("Disable Job by Comment")
    disable_status = await ch.enable_job_by_comment(comment=comment, bool=False)
    print(f'enabled status: {disable_status}')

    # pretty print jobs
    print("\npretty print jobs")
    await ch.pretty_print_jobs()

    # edit job - make this a method
    await ch.edit_job("ls", "*/8 * * * *", comment=comment)

    # validate cron string is valid
    cron_string = '10 * * * *'
    is_valid = await ch.validate_cron_string(cron_string)
    print(f'cron string {cron_string} is valid: {is_valid}')    

    # validate cron string is valid
    cron_string = 'hourly'
    is_valid = await ch.validate_cron_string(cron_string)
    print(f'cron string {cron_string} is valid: {is_valid}')    

    # validate cron string is valid
    cron_string = '@reboot'
    is_valid = await ch.validate_cron_string(cron_string)
    print(f'cron string {cron_string} is valid: {is_valid}')    


    # set env vars
    print("set env vars")
    await ch.set_env_vars(env_vars)

    # print environment variables
    print("get env vars")
    output = await ch.get_env_vars()
    print(output)

    # remove all jobs
    await ch.clear_all_jobs()



if __name__ == "__main__":
    asyncio.run(main())