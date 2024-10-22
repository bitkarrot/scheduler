import logging
import logging.handlers
import os

dir_path = os.path.dirname(os.path.realpath(__file__))
logname = os.path.join(dir_path, "scheduler.log")

logger = logging.getLogger("scheduler")
logger.setLevel(logging.DEBUG)

handler = logging.FileHandler(filename=logname, encoding="utf-8", mode="a")
dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(
    "[{asctime}] [{levelname}] {name}: {message}", dt_fmt, style="{"
)
handler.setFormatter(formatter)
logger.addHandler(handler)
