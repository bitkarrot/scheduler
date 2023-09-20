from crontab import CronTab, CronSlices

'''
CronHanlder class contains methods for handling cron jobs, create, edit, delete

see originaldocs for python-crontab package
https://pypi.org/project/python-crontab/
'''

import json

class CronHandler():
    def __init__(self, user:str):
        self._user = user
        self._cron = CronTab(user=self._user)

    def get_cron(self):
        return self._cron
    
    def set_cron(self, cron):
        self._cron = cron

    def get_user(self):
        return self._user
    
    def set_user(self, user):
        self._user = user  

    async def list_jobs(self) -> str:
        jobs = []
        for job in self._cron:
            jobs.append(str(job))
        return jobs

    async def pretty_print_jobs(self) -> None:
        print(f'==== Cron Jobs List: ====')
        jobs = await self.list_jobs()
        for i in jobs:
            print(i)

    async def new_job(self, command:str, frequency:str, comment:str):
        job = self._cron.new(command=command, comment=comment)        
        job.setall(frequency)
        if job.is_valid():
            self._cron.write_to_user(user=self._user)
            return f"job created: {command}, {self._user}, {frequency}"
        else: 
            return f"Error creating job: {command}, {self._user}, {frequency}"

    async def edit_job(self, command:str, frequency:str, comment:str): 
        iter = self._cron.find_comment(comment)
        for job in iter:
            ## assume job comment ID is unique
            job.command = command
            job.setall(frequency)
            if job.is_valid():
                self._cron.write_to_user(user=self._user)
                return f"job edited: {command}, {self._user}, {frequency}"
            else:
                return f"Error editing job: {command}, {self._user}, {frequency}"

    async def new_job_with_env(self, command:str, frequency:str, comment:str, env:json):
        job = self._cron.new(command=command, comment=comment)
        for key in env:
            job.env[key] = env[key]
        job.setall(frequency)
        if job.is_valid(): 
            self._cron.write_to_user(user=self._user)
            return f"job created: {command}, {self._user}, {frequency}"
        else: 
            return f"Error creating job: {command}, {self._user}, {frequency}"

    async def enable_job_by_comment(self, comment:str, bool:bool):
        print(f'enable_job_by_comment: {comment}, bool: {bool}')
        iter = self._cron.find_comment(comment)
        ## assume iter is only 1 long as using unique comment ID
        for job in iter:
            job.enable(bool)
            self._cron.write_to_user(user=self._user)
            return job.is_enabled()

    async def get_job_status(self, job_id: str) -> bool:
        iter = self._cron.find_comment(job_id)
        for job in iter:
            return job.is_enabled()


    async def remove_job(self, command=str):
        self._cron.remove_all(command=command)
        self._cron.write_to_user(user=self._user)


    async def clear_all_jobs(self):
        self._cron.remove_all()
        self._cron.write_to_user(user=self._user)

    async def remove_by_comment(self, comment):
        self._cron.remove_all(comment=comment)
        self._cron.write_to_user(user=self._user)

    async def remove_by_time(self, time):
        self._cron.remove_all(time=time)
        self._cron.write_to_user(user=self._user)


    async def set_global_env_vars(self, env:dict):
        for (name, value) in env.items():
            self._cron.env[name] = value
        self._cron.write_to_user(user=self._user)

    async def get_global_env_vars(self):
        output = ''    
        for (name, value) in self._cron.env.items():
            output += f'name: {name}, value: {value}'
        return output

    async def clear_global_env_vars(self):
        self._cron.env.clear()
        self._cron.write_to_user(user=self._user)

    async def validate_cron_string(self, timestring: str):
        is_valid = CronSlices.is_valid(timestring)
        return is_valid    
