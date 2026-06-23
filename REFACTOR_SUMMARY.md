# Scheduler Extension Refactor Summary

## What Changed

This refactoring migrates the LNBits Scheduler extension from OS crontab to APScheduler 3.x, providing:

1. **No OS Dependencies**: No longer requires crontab permissions or daemon
2. **Docker/Container Friendly**: Works in any environment without cron daemon
3. **In-Process Execution**: Jobs run directly in the FastAPI event loop (no subprocess overhead)
4. **Single Source of Truth**: Database is the only persistent state (APScheduler is just runtime)

## Files Added

- `scheduler_handler.py` - APScheduler management
- `job_runner.py` - Async job execution logic
- `REFACTOR_SUMMARY.md` - This file

## Files Modified

- `__init__.py` - Added startup/shutdown hooks for APScheduler lifecycle
- `crud.py` - Replaced cron file operations with scheduler_handler functions
- `models.py` - Updated validation for APScheduler cron expressions
- `helpers.py` - Simplified helper surface
- `pyproject.toml` - Uses apscheduler + httpx
- `requirements.txt` - Updated dependencies

## Files Removed

- `cron_handler.py`
- `run_cron_job.py`
- `test_cron_handler_locally.py`

## Key Behavior Changes

### Job Creation
- **Before**: Created entry in OS crontab file + database
- **After**: Creates database entry + adds to in-process APScheduler

### Job Execution
- **Before**: Cron daemon spawns Python subprocess → cold start → HTTP call
- **After**: APScheduler directly calls async coroutine → immediate HTTP call

### Job Status
- **Before**: Database + crontab file (could drift)
- **After**: Database only (APScheduler rehydrated on startup)

### Startup Behavior
- **After**: On startup, all jobs with `status=True` are loaded from DB into APScheduler
- This means scheduler state survives restarts correctly

### Misfire Handling
- APScheduler configured with 60s grace time
- If app is down when job should fire, it runs immediately on startup (within 60s window)

## Migration Notes

### For Existing Installations

1. Stop LNBits
2. Update dependencies: `poetry install` or `pip install -r requirements.txt`
3. Start LNBits - existing jobs will be automatically migrated on startup
4. Old crontab entries from previous versions can be manually cleaned if present.

### For New Installations

- No crontab setup required
- No special permissions needed
- Works immediately in Docker/containers

## API Compatibility

All existing API endpoints remain unchanged:
- `GET /api/v1/jobs` - List jobs
- `POST /api/v1/jobs` - Create job
- `PUT /api/v1/jobs/{job_id}` - Update job
- `DELETE /api/v1/jobs/{job_id}` - Delete job
- `POST /api/v1/pause/{job_id}/{status}` - Toggle job status

## Testing

Test job execution:
```bash
# Via API test endpoint
curl -X GET "http://localhost:5000/scheduler/api/v1/test_log/{job_id}" \
  -H "X-Api-Key: your-admin-key"
```

Check APScheduler status in logs:
```
[scheduler] APScheduler started
[scheduler] Loaded N active jobs from DB into scheduler
[scheduler] Job added: {job_id} @ {cron_expression}
[scheduler] Job {job_id} executed: HTTP {status_code}
```

## Troubleshooting

### Jobs not running
1. Check database: `status` should be `true` (1)
2. Check logs for "APScheduler started" message
3. Check logs for "Loaded X active jobs" message
4. Verify cron expression with APScheduler validator

### Migration from old version
If you see jobs in database but not running:
1. Toggle job status off then on via API
2. This will re-register the job with APScheduler

## Dependencies

- **apscheduler** (>=3.10.0, <4.0) - Job scheduling engine
- **httpx** (>=0.27.0) - Async HTTP client for job execution

Note: APScheduler 4.x has breaking API changes - stick with 3.x for now.

### Why `python-crontab` may still appear in `poetry.lock`

This extension no longer imports or uses `python-crontab`.
If it appears in `poetry.lock`, it is currently pulled **transitively** by the
upstream `lnbits` package dependency tree (verified via `poetry show --tree lnbits`).

## Architecture

```
FastAPI App Startup
    ↓
APScheduler.start()
    ↓
Load active jobs from DB
    ↓
Register each with APScheduler
    ↓
[Runtime] APScheduler triggers jobs
    ↓
execute_job(job_id) async coroutine
    ↓
HTTP request via httpx
    ↓
Log result to database
```

## Performance Improvements

- **No subprocess overhead**: Jobs execute in same process
- **No cold start**: No Python interpreter startup per job
- **Connection pooling**: httpx reuses connections
- **Async execution**: Non-blocking job execution

## Configuration

APScheduler settings in `scheduler_handler.py`:
- `misfire_grace_time=60` - Jobs can run up to 60s late
- `replace_existing=True` - Job updates replace old schedule
- Scheduler runs in AsyncIO mode - native to FastAPI

## Logs

Job execution logs stored in database (`scheduler.logs` table):
- `job_id` - Job identifier
- `status` - HTTP status code (or "0" for errors)
- `response` - HTTP response body (truncated to 4000 chars)
- `timestamp` - Execution time

Complete application logs still available via `scheduler.log` file.
