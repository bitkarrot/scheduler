# Scheduler extension

lnbits scheduler extension [previously name crontabs]

Notes: 

- IMPORTANT: .env file set your system username that is running the LNBits instance.

  Example: if the user that is running the server is 'lnbits', you need to set SCHEDULER_USER=lnbits in the .env file

  The .env.example is the example file. 

- Additional Requirements: python-crontab==3.0.0
- This is a Draft: running on OSX only at the moment. 
- crontab needs access crontab -e permissions in order to work or else cannot read/write to crontab file. 
- .env.example contains the variable the user that has read/write crontab access at the system level 

- TODO list: clean up API, Docs, unit tests, other code cleanup, front end validation checks
