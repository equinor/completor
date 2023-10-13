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
