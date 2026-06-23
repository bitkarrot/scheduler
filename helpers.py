import json
import os

# .log path
dir_path = os.path.dirname(os.path.realpath(__file__))
log_path = os.path.join(dir_path, "scheduler.log")


async def convert_headers(headers: list) -> str:
    """Convert header items to JSON string."""
    allitems_as_dicts = [item.to_dict() for item in headers]
    headers_string = json.dumps(allitems_as_dicts)
    return headers_string


# log helpers
async def read_last_n_lines(file_path, n):
    with open(file_path) as file:
        lines = file.readlines()[-n:]
    return lines


async def get_complete_log() -> str:
    """
    return entire text log from disk, including other errors
    for now, only fetch the last 1000 lines,
    so that response does not get too large
    """
    if os.path.exists(log_path):
        content = ""
        last_1000_lines = await read_last_n_lines(log_path, 1000)
        for line in last_1000_lines:
            content += line
        return content
    else:
        return f"log file does not exist at location: {log_path}"


async def delete_complete_log() -> bool:
    """
    clear the contents of the text log on disk
    """
    # Check if the file exists before trying to delete it
    if os.path.exists(log_path):
        os.remove(log_path)
        return True
    else:
        return False
