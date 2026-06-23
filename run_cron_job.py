#!/usr/bin/env python3
"""Deprecated compatibility shim.

The scheduler extension now uses APScheduler + in-process async execution
(`job_runner.execute_job`) instead of spawning this script from OS crontab.
"""

import sys


def main() -> int:
    print(
        "run_cron_job.py is deprecated: scheduler jobs now run in-process via APScheduler.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
