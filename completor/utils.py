"""Collection of commonly used utilities."""

from __future__ import annotations

import re
import sys
from typing import Any, overload

import numpy as np
import pandas as pd

import completor
from completor.logger import logger

try:
    from typing import Literal, NoReturn
except ImportError:
    pass


def abort(message: str, status: int = 1) -> SystemExit:
    """
    Exit the program with a message and exit code (1 by default).

    Args:
        message: The message to be logged.
        status: Which system exit code to use. 0 indicates success.
                I.e. there where no errors, while 1 or above indicates that
                an error occurred. By default the code is 1.

    Returns:
        SystemExit: Makes type checkers happy, when using the ``raise``
                    keyword with this function. I.e
                    >>> raise abort("Something when terribly wrong")
    Raises:
        SystemExit: The exception used by sys.exit
    """
    if status == 0:
        logger.info(message)
    else:
        logger.error(message)
    return sys.exit(status)
