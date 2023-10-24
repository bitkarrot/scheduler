# Scheduler extension

lnbits scheduler extension [previously: crontabs]

Notes: 

- This is a Draft: running on OSX only at the moment. 
- the user that runs LNBits needs access crontab -e permissions in order to read/write to crontab file.

- TODO: Docs, code cleanup, front end validation checks

## Usage

### Overview: 
Add, Edit, Delete and Monitor your scheduled Jobs from the Main Panel. 
  
<img width="908" alt="imgone" src="https://github.com/bitkarrot/scheduler/assets/73979971/75ebc47c-07be-444d-a167-31ae63c6e087">

### Create a job Dialog Box. 

Schedule a specific http call with a specific timed interval.

1. Create a new job by clicking "New Scheduled Job"
2. Fill the options for your new SCHEDULED JOB
    - Enter a Name for your Job
    - Select an action (GET/PUT/POST/DEL)
    - Enter the URL
    - Add any headers if required
    - Add body data if required
    - enter the scheduled time/day you want to run your job
3. Save your scheduled job and return to the main page to start the job (Green arrow)
4. All methods for controlling your job are on the main panel [Start/Stop, Edit, Delete, View Logs]

NOTE: Jobs do not run automatically on creation. You will need to start and stop the jobs on the main panel [see image above]. If you are unfamiliar with how the 5 slot scheduling works, visit this resource: https://crontab.guru

<img width="605" alt="imgtwo" src="https://github.com/bitkarrot/scheduler/assets/73979971/77f55660-52b6-459c-9ce2-d81e6fa7d1b5">

### There are two sets of logs:
- Individual Job Logs - these are viewable by clicking on the blue info icons on the main panel.
- Complete Extension Logs - This will show all errors and all events, these are viewable by clicking on the "View all logs" button, located the top of the main panel. 
