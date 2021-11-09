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


def sort_by_midpoint(df: pd.DataFrame, end_md: np.ndarray, start_md: np.ndarray) -> pd.DataFrame:
    """
    Sort DataFrame on midpoint calculated from the new start and end measured depths.

    Arguments:
        df: DataFrame to be sorted
        end_md: End measured depth
        start_md: Start measured depth

    Returns:
        Sorted DataFrame
    """
    df["STARTMD"] = start_md
    df["ENDMD"] = end_md
    # sort the data frame based on the mid point
    df["MID"] = (df["STARTMD"] + df["ENDMD"]) * 0.5
    df.sort_values(by=["MID"], inplace=True)
    # drop the MID column
    df.drop(["MID"], axis=1, inplace=True)
    return df


def as_data_frame(args: dict[str, Any] | None = None, **kwargs) -> pd.DataFrame:
    """Helper function to create a data frame from a dictionary, or keywords."""
    if (args is None and kwargs is None) or (not args and not kwargs):
        raise ValueError("`as_data_frame` requires either a single dictionary, or keywords")

    if args:
        kwargs = args
    data = pd.DataFrame()
    for key, value in kwargs.items():
        data[key] = value

    return data
