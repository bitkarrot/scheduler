from crontab import CronTab

# make a bunch of cron methods for handling cron jobs

cron = CronTab(user='bitcarrot')
job = cron.new(command='echo hello_world')
job.minute.every(1)
cron.write()