import logging
import logging.handlers
import os

# Get the directory where this file is located
dir_path = os.path.dirname(os.path.realpath(__file__))
logname = os.path.join(dir_path, "scheduler.log")

# Create log directory if it doesn't exist
os.makedirs(os.path.dirname(logname), exist_ok=True)

# Touch the log file if it doesn't exist
if not os.path.exists(logname):
    open(logname, "a").close()
    os.chmod(logname, 0o666)  # Make it readable/writable by all

# Configure logger
logger = logging.getLogger("scheduler")
logger.setLevel(logging.DEBUG)

# Prevent duplicate handlers
if not logger.handlers:
    handler = logging.FileHandler(filename=logname, encoding="utf-8", mode="a")
    dt_fmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(
        "[{asctime}] [{levelname}] {name}: {message}", dt_fmt, style="{"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
