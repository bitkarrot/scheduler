# Migration Checklist: OS Crontab → APScheduler

## Pre-Migration

- [ ] Backup your LNBits database
- [ ] Note down all active scheduler jobs (via UI or API)
- [ ] Check current crontab entries: `crontab -l | grep scheduler`

## Installation Steps

### 1. Update Dependencies

```bash
# Using Poetry (recommended)
cd /path/to/lnbits
poetry install

# Or using pip
pip install -r extensions/scheduler/requirements.txt
```

### 2. Restart LNBits

```bash
# If using systemd
sudo systemctl restart lnbits

# Or if running manually
# Stop the current process and restart
poetry run lnbits
```

### 3. Verify Scheduler Started

Check logs for these messages:
```
[scheduler] APScheduler started
[scheduler] Loaded N active jobs from DB into scheduler
```

### 4. Test Job Execution

- Check that scheduled jobs run at expected times
- Use test endpoint: `GET /scheduler/api/v1/test_log/{job_id}`
- Verify log entries are created in database

### 5. Clean Up Old Crontab Entries (Optional)

```bash
# View current crontab
crontab -l

# Edit to remove scheduler entries
crontab -e
# Delete lines related to scheduler/run_cron_job.py

# Or remove all for current user
# crontab -r  # WARNING: removes ALL cron jobs
```

## Post-Migration Verification

- [ ] All jobs visible in UI
- [ ] Job status toggles work (pause/resume)
- [ ] New jobs can be created
- [ ] Jobs execute at scheduled times
- [ ] Execution logs appear in database
- [ ] No errors in application logs

## Troubleshooting

### Jobs show in UI but don't run

**Solution**: Toggle job status off then on
```bash
curl -X POST "http://localhost:5000/scheduler/api/v1/pause/{job_id}/false" \
  -H "X-Api-Key: your-admin-key"
curl -X POST "http://localhost:5000/scheduler/api/v1/pause/{job_id}/true" \
  -H "X-Api-Key: your-admin-key"
```

### APScheduler not starting

**Check**: Dependencies installed correctly
```bash
poetry show apscheduler httpx
# Should show version 3.10.x for apscheduler
```

**Check**: No import errors
```bash
poetry run python -c "from apscheduler.schedulers.asyncio import AsyncIOScheduler; print('OK')"
```

### Jobs run but fail with HTTP errors

**Check**: 
1. URL is accessible from LNBits server
2. Headers (especially auth) are correct
3. Body format matches API expectations
4. Check job execution logs: `GET /scheduler/api/v1/logentry/{job_id}`

## Rollback Plan (If Needed)

If you need to rollback to the old version:

```bash
# 1. Checkout previous version
git checkout <previous-commit>

# 2. Reinstall old dependencies
poetry install

# 3. Restart LNBits
sudo systemctl restart lnbits

# 4. Manually recreate crontab entries
# (You'll need to recreate jobs via UI/API)
```

## Key Differences

| Feature | Old (Crontab) | New (APScheduler) |
|---------|---------------|-------------------|
| Execution | Subprocess | In-process coroutine |
| State | Crontab + DB | Database only |
| Permissions | Needs crontab access | No special permissions |
| Docker | Requires cron daemon | Works out of the box |
| Performance | Cold start per job | Instant execution |
| Debugging | Check cron logs + app logs | App logs only |

## Support

If you encounter issues:

1. Check application logs: `tail -f data/logs/lnbits.log`
2. Check scheduler-specific logs: `tail -f extensions/scheduler/scheduler.log`
3. Enable debug logging in LNBits config
4. Open an issue on GitHub with logs and error messages

## Success Criteria

✅ Migration is successful when:
- APScheduler starts on application startup
- All existing jobs are loaded into APScheduler
- Jobs execute at their scheduled times
- New jobs can be created and scheduled
- Job status can be toggled (pause/resume)
- No crontab entries needed
- Works in Docker containers without modifications
