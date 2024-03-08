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


@overload
def log_and_raise_exception(message: str, kind: type = ..., throw: Literal[True] = ...) -> NoReturn: ...


@overload
def log_and_raise_exception(message: str, kind: type = ..., throw: Literal[False] = ...) -> BaseException: ...


def log_and_raise_exception(message: str, kind: type = ValueError, throw: bool = False) -> BaseException | None:
    """
    Log and throw an exception.

    Arguments:
        message: The message to be logged, and given to the exception
        kind: The type of exception to be thrown
        throw: Flag to toggle whether this function actually raises the exception or not

    Raises:
        Exception: In general it can be any exception
        ValueError: This is the default exception
    """
    logger.error(message)
    if not isinstance(kind, (Exception, BaseException)):
        raise ValueError(f"The provided exception type ({kind}) does not inherit from Exception")
    if throw:
        raise kind(message)
    else:
        return kind(message)


def clean_file_line(line: str, comment_prefix: str = "--", remove_quotation_marks: bool = False) -> str:
    """
    Remove comments, tabs, newlines and consecutive spaces from a string.

    Also remove trailing '/' comments, but ignore lines containing a file path.

    Args:
        line: A string containing a single file line
        comment_prefix: The prefix used to denote a comment in the file
        remove_quotation_marks: Whether quotation marks should be removed from the line
                                Used for cleaning schedule files

    Returns:
        A cleaned line. Returns an empty string in the case of a comment or empty line.
    """

    # Remove trailing comments
    line = line.split(comment_prefix)[0]
    # Skip cleaning process if the line was a comment
    if not line:
        return ""
    # Replace tabs with spaces, remove newlines and remove trailing spaces.
    line = line.replace("\t", " ").replace("\n", "")
    # Remove quotation marks if specified
    if remove_quotation_marks:
        line = line.replace("'", " ").replace('"', " ")
    # Remove trailing whitespace
    line = line.strip(" ")
    # Find comments and replace with single '/'.
    # Checks that the / is not part of a file path.
    line = re.sub(r"/[^/']*$", "/", line)
    # Remove consecutive spaces
    line = " ".join(line.split())

    return line


def clean_file_lines(lines: list[str], comment_prefix: str = "--") -> list[str]:
    """
    Remove comments, tabs, newlines and consecutive spaces from file lines.

    Args:
        lines: A list of file lines
        comment_prefix: The prefix used to denote a file comment

    Returns:
        A list with the cleaned lines
    """
    clean_lines = []
    for line in lines:
        cleaned_line = clean_file_line(line, comment_prefix=comment_prefix)
        # If clean_file_line returns "", don't process the line.
        if cleaned_line:
            clean_lines.append(cleaned_line)
    return clean_lines


def get_completor_version() -> str:
    """
    Get completor version from latest git tag.

    Returns:
        The version string in format 'v1.1.1'
    """
    # TODO: Add exception handling here!
