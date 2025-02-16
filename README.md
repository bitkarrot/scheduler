# Scheduler extension

lnbits scheduler extension [previously: crontabs]

IMPORTANT:

- **The user that runs LNBits server MUST have crontab -e permissions in order to read/write to crontab file.**
- This extension should be limited to admin account(s).
- min version 0.12.10

## Video Demo

https://github.com/bitkarrot/scheduler/assets/73979971/888d9e77-4edf-4573-85ee-8fc43c710120

### Overview:

Add, Edit, Delete and Monitor your scheduled Jobs from the Main Panel.

<img width="992" alt="Screenshot 2024-01-19 at 2 39 23 PM" src="https://github.com/bitkarrot/scheduler/assets/73979971/01656f95-bdde-4015-99c5-415ce9483ddb">
  
### Create a job Dialog Box.

Schedule a specific http call with a specific timed interval.

1. Create a new job by clicking "New Scheduled Job"
2. Fill the options for your new SCHEDULED JOB
   - Enter a Name for your Job
   - Select an action (GET/PUT/POST/DEL)
   - Enter the URL
   - Add any headers if required
   - Add body data if required, leave blank if there is no body (e.g. for DELETE)
   - enter the scheduled time/day you want to run your job. You can use [crontab.guru](https://crontab.guru) to help validate your cron schedules.
3. Save your scheduled job and return to the main page to test the job (Orange) or start the job (Green arrow)
4. All methods for controlling your job are on the main panel [Start/Stop, Edit, Test, View Logs and Delete]

NOTE: Jobs may not run automatically on creation depending on the release version. You will need to start and stop the jobs on the main panel [see image above]. If you are unfamiliar with how the 5 slot scheduling works, visit this resource: https://crontab.guru

<img width="605" alt="imgtwo" src="https://github.com/bitkarrot/scheduler/assets/73979971/77f55660-52b6-459c-9ce2-d81e6fa7d1b5">

### There are three sets of logs:

- Individual Job Logs - these are viewable by clicking on the blue info icons on the main panel.
- Test job Logs - this is for testing the job and the result is not recorded to the database only to the test log file.
- Complete Extension Logs - This will show all errors and all events, these are viewable by clicking on the "View all logs" button, located the top of the main panel.
