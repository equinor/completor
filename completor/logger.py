from __future__ import annotations

import json
import logging
import sys
import time
from functools import wraps
from pathlib import Path


def getLogger(module_name="completor"):
    logger = logging.getLogger(module_name)

    formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.addFilter(lambda record: record.levelno < logging.ERROR)
    stdout_handler.setFormatter(formatter)

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.addFilter(lambda record: record.levelno >= logging.ERROR)
    stderr_handler.setFormatter(formatter)

    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)

    return logger


logger = getLogger(__name__)


def handle_error_messages(func):
    """
    Decorator to catch any exceptions it might throw
    (with some exceptions, such as KeyboardInterrupt)
    If there are any error messages from the exception, they are logged.
    If completor fails, the decorator will write a zip file to disk;
    Completor-<year><month><day>-<hour><minute><second>-<letter><5 numbers>.zip
    The last letter and numbers are chosen at random.
    The format is similar to Roxar's RMS' error files.

    The zip file contains

    * traceback.txt - a trace back
    * machine.txt - which machine it happened on
    * arguments.json - all input arguments
    * The content of any files passed
      For the main method of Completor, these are (if provided)
      * input_file.txt - The case file
      * schedule_file.txt  - The schedule file
      * new_file.txt - The output file
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
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
