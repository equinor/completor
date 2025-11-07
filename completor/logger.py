from __future__ import annotations

import json
import logging
import sys
import time
from functools import wraps
from pathlib import Path

from completor.get_version import get_version


def get_logger(module_name="completor"):
    """Configure logger.

    Args:
        module_name: The name for logger.
    """
    logger_ = logging.getLogger(module_name)

    formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.addFilter(lambda record: record.levelno < logging.ERROR)
    stdout_handler.setFormatter(formatter)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.addFilter(lambda record: record.levelno >= logging.ERROR)
    stderr_handler.setFormatter(formatter)

    logger_.addHandler(stdout_handler)
    logger_.addHandler(stderr_handler)

    return logger_


logger = get_logger(__name__)


def handle_error_messages(func):
    """Decorator to catch any exceptions it might throw (with some exceptions, such as KeyboardInterrupt).

    If there are any error messages from the exception, they are logged.
    If completor fails, the decorator will write a zip file to disk;
    Completor-<year><month><day>-<hour><minute><second>-<letter><5 numbers>.zip
    The last letter and numbers are chosen at random.

    The zip file contains:
    * traceback.txt - a trace back.
    * machine.txt - which machine it happened on.
    * arguments.json - all input arguments.
    * The content of any files passed.
      For the main method of Completor, these are (if provided).
      * input_file.txt - The case file.
      * schedule_file.txt - The schedule file.
      * new_file.txt - The output file.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (Exception, SystemExit) as ex:
            # SystemExit does not inherit from Exception
            if isinstance(ex, SystemExit):
                exit_code = ex.code
            else:
                exit_code = 1
                logger.error(ex)
            if len(args) > 0:
                _kwargs = {}
                _kwargs["input_file"] = kwargs["paths"][0]
                _kwargs["schedule_file"] = kwargs["paths"][1]
                _kwargs["new_file"] = args[2]
                _kwargs["show_fig"] = args[3]
                kwargs = _kwargs

            dump_debug_information(**kwargs)
            exit(exit_code)

    return wrapper


def _convert_paths_to_strings(dict_) -> dict:
    kwargs = {}
    for key, value in dict_.items():
        if len(str(value).splitlines()) < 2:
            if isinstance(value, Path):
                value = str(value)
            kwargs[key] = value
    return kwargs


def dump_debug_information(**kwargs) -> None:
    """Helper method to create, and write all the files to a zip archive."""
    import random
    import socket
    import string
    import traceback
    from zipfile import ZIP_DEFLATED, ZipFile

    when = time.localtime()
    random_suffix = "".join(random.choices(string.ascii_letters) + random.choices(string.digits, k=5))
    name = (
        f"Completor-{when.tm_year}{when.tm_mon:02}{when.tm_mday:02}-"
        f"{when.tm_hour:02}{when.tm_min:02}{when.tm_sec:02}-{random_suffix}"
    )
    logger.error(
        "Completor failed. Writing debugging information to %s.zip. "
        "Please submit issue for questions and include said file.\n"
        "Do not submit internal or restricted files to the issue,"
        "please contact Equinor internal support to handle internal files.\n"
        "NOTE: the file includes all input you gave to Completor including the content of the input files",
        name,
    )
    logger.debug(traceback.format_exc())

    with ZipFile(name + ".zip", mode="x", compression=ZIP_DEFLATED) as zipfile:

        def dump(file_name: str, data: str | bytes, encoding: str = "UTF-8") -> None:
            path = Path(name) / file_name
            with zipfile.open(str(path), "w") as f:
                if isinstance(data, str):
                    data = data.encode(encoding)
                f.write(data)

        dump("traceback.txt", traceback.format_exc())
        dump("machine.txt", socket.getfqdn())
        dump("version.txt", get_version())
        dump("arguments.json", json.dumps(_convert_paths_to_strings(kwargs), indent=4))
        for key, value in kwargs.items():
            if isinstance(value, (Path, str)):
                try:
                    with open(value, encoding="utf-8") as f:
                        dump(f"{key}.txt", f.read())
                except Exception as ex:
                    dump(f"{key}.traceback.txt", traceback.format_exc())
                    dump(f"{key}.txt", ex.__repr__())
