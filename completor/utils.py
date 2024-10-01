"""Collection of commonly used utilities."""

from __future__ import annotations

import re
import sys
from typing import Any, Literal, NoReturn, overload

import numpy as np
import numpy.typing as npt
import pandas as pd

from completor.constants import Content, Headers, Keywords
from completor.logger import logger


def abort(message: str, status: int = 1) -> SystemExit:
    """Exit the program with a message and exit code (1 by default).

    Args:
        message: The message to be logged.
        status: Which system exit code to use. 0 indicates success.
        I.e. there were no errors, while 1 or above indicates that an error occurred. The default code is 1.

    Returns:
        SystemExit: Makes type checkers happy when using the ``raise`` keyword with this function. I.e.
            `>>> raise abort("Something when terribly wrong.")`
    """
    if status == 0:
        logger.info(message)
    else:
        logger.error(message)
    return sys.exit(status)


def sort_by_midpoint(
    df: pd.DataFrame, start_measured_depths: npt.NDArray[np.float64], end_measured_depths: npt.NDArray[np.float64]
) -> pd.DataFrame:
    """Sort DataFrame on midpoint calculated from the new start and end measured depths.

    Arguments:
        df: DataFrame to be sorted.
        start_measured_depths: Start measured depths.
        end_measured_depths: End measured depths.

    Returns:
        Sorted DataFrame.
    """
    _temp_column = "TEMPORARY_MIDPOINT"
    df[Headers.START_MEASURED_DEPTH] = start_measured_depths
    df[Headers.END_MEASURED_DEPTH] = end_measured_depths
    # Sort the data frame based on the mid-point.
    df[_temp_column] = df[[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH]].mean(axis=1)
    df = df.sort_values(by=[_temp_column])
    return df.drop([_temp_column], axis=1)


@overload
def log_and_raise_exception(message: str, kind: type = ..., throw: Literal[True] = ...) -> NoReturn: ...


@overload
def log_and_raise_exception(message: str, kind: type = ..., throw: Literal[False] = ...) -> BaseException: ...


def log_and_raise_exception(message: str, kind: type = ValueError, throw: bool = False) -> BaseException | None:
    """Log and throw an exception.

    Arguments:
        message: The message to be logged, and given to the exception.
        kind: The type of exception to be thrown.
        throw: Flag to toggle whether this function actually raises the exception or not.

    Raises:
        Exception: In general it can be any exception.
        ValueError: This is the default exception.
    """
    logger.error(message)
    if not isinstance(kind, (Exception, BaseException)):
        raise ValueError(f"The provided exception type ({kind}) does not inherit from Exception")
    if throw:
        raise kind(message)
    else:
        return kind(message)


def find_quote(string: str) -> re.Match | None:
    """Find single or double quotes in a string.

    Args:
        string: String to search through.

    Returns:
        Match of string if any.
    """
    quotes = "\"'"
    return re.search(rf"([{quotes}])(?:(?=(\\?))\2.)*?\1", string)


def clean_file_line(
    line: str, comment_prefix: str = "--", remove_quotation_marks: bool = False, replace_tabs: bool = True
) -> str:
    """Remove comments, tabs, newlines and consecutive spaces from a string.

    Also remove trailing '/' comments, but ignore lines containing a file path.

    Args:
        line: A string containing a single file line.
        comment_prefix: The prefix used to denote a comment in the file.
        remove_quotation_marks: Whether quotation marks should be removed from the line.
            Used for cleaning schedule files.
        replace_tabs: Whether tabs should be replaced with a space.

    Returns:
        A cleaned line. Returns an empty string in the case of a comment or empty line.
    """
    # Substitute string in quotes to avoid side effects when cleaning line e.g. `  '../some/path.file'`.
    match = find_quote(line)
    original_text = None
    if match is not None:
        i0, i1 = match.span()
        original_text = line[i0:i1]
        line = line[:i0] + "x" * (i1 - i0) + line[i1:]

    # Remove trailing comments
    line = line.split(comment_prefix)[0]
    # Skip cleaning process if the line was a comment
    if not line:
        return ""
    # Replace tabs with spaces, remove newlines and remove trailing spaces.
    if replace_tabs:
        line = line.replace("\t", " ").replace("\n", "")
    # Remove quotation marks if specified
    if remove_quotation_marks:
        line = line.replace("'", " ").replace('"', " ")

    # Find comments and replace with single '/'.
    line = re.sub(r"/[^/']*$", "/", line)

    if match is not None and original_text is not None:
        i0, i1 = match.span()
        line = line[:i0] + original_text + line[i1:]

    # Remove trailing whitespace
    line = line.strip(" ")
    if remove_quotation_marks:
        line = line.replace("'", " ").replace('"', " ")
    # Remove consecutive spaces
    line = " ".join(line.split())

    return line


def clean_file_lines(lines: list[str], comment_prefix: str = "--") -> list[str]:
    """Remove comments, tabs, newlines and consecutive spaces from file lines.

    Args:
        lines: A list of file lines.
        comment_prefix: The prefix used to denote a file comment.

    Returns:
        A list with the cleaned lines.
    """
    clean_lines = []
    for line in lines:
        cleaned_line = clean_file_line(line, comment_prefix=comment_prefix)
        # If clean_file_line returns "", don't process the line.
        if cleaned_line:
            clean_lines.append(cleaned_line)
    return clean_lines


def shift_array(array: npt.NDArray[Any], shift_by: int, fill_value: Any = np.nan) -> npt.NDArray[Any]:
    """Shift an array to the left or right, similar to Pandas' shift.

    Note: By chrisaycock https://stackoverflow.com/a/42642326.

    Args:
        array: Array to shift.
        shift_by: The amount and direction (positive/negative) to shift by.
        fill_value: The value to fill out of range values with. Defaults to np.nan.

    Returns:
        Shifted Numpy array.

    """
    result = np.empty_like(array)
    if shift_by > 0:
        result[:shift_by] = fill_value
        result[shift_by:] = array[:-shift_by]
    elif shift_by < 0:
        result[shift_by:] = fill_value
        result[:shift_by] = array[-shift_by:]
    else:
        result[:] = array
    return result


def get_active_wells(completion_table: pd.DataFrame, gp_perf_devicelayer: bool) -> npt.NDArray[np.str_]:
    """Get a list of active wells specified by users.

    Notes:
        No device layer will be added for perforated wells with gravel-packed annulus.
        Completor does nothing to gravel-packed perforated wells by default.
        This behavior can be changed by setting the GRAVEL_PACKED_PERFORATED_DEVICELAYER keyword in the case file to true.

    Args:
        completion_table: Completion information.
        gp_perf_devicelayer: Keyword denoting if the user wants a device layer for this type of completion.

    Returns:
        The active wells found.
    """
    # Need to check completion of all wells in the completion table to remove GP-PERF type wells
    # If the user wants a device layer for this type of completion.
    if not gp_perf_devicelayer:
        gp_check = completion_table[Headers.ANNULUS] == Content.OPEN_ANNULUS
        perf_check = completion_table[Headers.DEVICE_TYPE].isin(
            [
                Content.AUTONOMOUS_INFLOW_CONTROL_DEVICE,
                Content.AUTONOMOUS_INFLOW_CONTROL_VALVE,
                Content.DENSITY_ACTIVATED_RECOVERY,
                Content.INFLOW_CONTROL_DEVICE,
                Content.VALVE,
                Content.INFLOW_CONTROL_VALVE,
            ]
        )
        # Where annuli is "OA" or perforation is in the list above.
        mask = gp_check | perf_check
        if not mask.any():
            logger.warning(
                "There are no active wells for Completor to work on. E.g. all wells are defined with Gravel Pack "
                "(GP) and valve type PERF. "
                f"If you want these wells to be active set {Keywords.GRAVEL_PACKED_PERFORATED_DEVICELAYER} to TRUE."
            )
        return np.array(completion_table[Headers.WELL][mask].unique())
    return np.array(completion_table[Headers.WELL].unique())


def check_width_lines(result: str, limit: int = 132) -> list[tuple[int, str]]:
    """Check the width of each line versus limit.

    Disregarding all content after '/' and '--' characters.

    Args:
        result: Raw text.
        limit: The character width limit.

    Raises:
        ValueError: If there exists any data that is too long.
    """
    lines = result.splitlines()
    lengths = np.char.str_len(lines)
    lines_to_check = np.nonzero(lengths >= limit)[0]
    too_long_lines = []
    for line_index in lines_to_check:
        cleaned_line = lines[line_index].rsplit("/")[0] + "/"
        cleaned_line = cleaned_line.rsplit("--")[0] + "--"

        if len(cleaned_line) > limit:
            too_long_lines.append((line_index, lines[line_index]))
    return too_long_lines
