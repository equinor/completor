"""Collection of commonly used utilities."""

from __future__ import annotations

import re
import sys
from collections.abc import Mapping
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd

from completor.constants import Content, Headers, Keywords
from completor.exceptions.clean_exceptions import CompletorError
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
                Content.DUAL_RATE_CONTROLLED_PRODUCTION,
                Content.DENSITY,
                Content.INJECTION_VALVE,
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


def check_width_lines(result: str, limit: int) -> list[tuple[int, str]]:
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
        # Well names can have slashes, therefore maxsplit must be 1.
        cleaned_line = lines[line_index].rsplit("/", maxsplit=1)[0] + "/"
        # Comment 'char' can be multiple and should not have maxsplit, nor the '--' added.
        cleaned_line = cleaned_line.rsplit("--")[0]

        if len(cleaned_line) > limit:
            too_long_lines.append((line_index, lines[line_index]))
    return too_long_lines


def format_default_values(text: str) -> list[list[str]]:
    """Format the data-records and resolve the repeat-mechanism.

    E.g. 3* == 1* 1* 1*, 3*250 == 250 250 250.

    Args:
        text: A chunk data-record.

    Returns:
        Expanded values.
    """
    chunk = re.split(r"\s+/", text)[:-1]
    expanded_data = []
    for line in chunk:
        new_record = ""
        for record in line.split():
            if not record[0].isdigit():
                new_record += record + " "
                continue
            if "*" not in record:
                new_record += record + " "
                continue

            # Handle repeats like 3* or 3*250.
            multiplier, number = record.split("*")
            new_record += f"{number if number else '1*'} " * int(multiplier)
        if new_record:
            expanded_data.append(new_record.split())
    return expanded_data


def find_keyword_data(keyword: str, text: str) -> list[str]:
    """Finds the common pattern for the four keywords thats needed.

    Args:
        keyword: Current keyword.
        text: The whole text to find matches in.

    Returns:
        The matches if any.

    """
    # Finds keyword followed by two slashes.
    # Matches any characters followed by a newline, non-greedily, to allow for comments within the data.
    # Matches new line followed by a single (can have leading whitespace) slash.
    pattern = rf"^{keyword}(?:.*\n)*?\s*\/"
    return re.findall(pattern, text, re.MULTILINE)


def clean_raw_data(raw_record: str, keyword: str) -> list[list[str]]:
    """Parse the record and clean its content.

    Args:
        raw_record: Raw data taken straight from schedule.
        keyword: The current keyword.

    Returns:
        The contents of the keyword, cleaned.
    """
    record = re.split(rf"{keyword}\n", raw_record)
    if len(record) != 2:
        raise CompletorError(f"Something went wrong when reading keyword '{keyword}' from schedule:\n{raw_record}")
    # Strip keyword and last line.
    raw_content = record[1].splitlines()
    if raw_content[-1].strip().startswith("/"):
        raw_content = raw_content[:-1]

    clean_content = []
    for line in raw_content:
        clean_line = clean_file_line(line, remove_quotation_marks=True)
        if clean_line:
            clean_content.append(format_default_values(clean_line)[0])
    return clean_content


def find_well_keyword_data(well: str, keyword: str, text: str) -> str:
    """Find the data associated with keyword and well name, include leading comments.

    Args:
        well: Well name.
        keyword: Keyword to search for.
        text: Raw text to look for matches in.

    Returns:
        The correct match given keyword and well name.
    """
    matches = find_keyword_data(keyword, text)

    lines: list[str] = []
    for match in matches:
        if re.search(well, match) is None:
            continue

        matchlines = match.splitlines()
        once = False
        for i, line in enumerate(matchlines):
            if not line:
                # Allow empty lines in the middle of a record.
                if once:
                    lines.append(line)
                continue
            if well == line.split()[0].replace("'", "").replace('"', ""):
                if keyword in [Keywords.WELL_SEGMENTS, Keywords.COMPLETION_SEGMENTS]:
                    # These keywords should just be the entire match as they never contain more than one well.
                    return match
                if not once:
                    once = True
                    # Remove contiguous comments above the first line by looking backwards,
                    # adding it to the replaceable text match.
                    comments: list[str] = []
                    for prev_line in matchlines[i - 1 :: -1]:
                        if not prev_line.strip().startswith("--") or not prev_line:
                            break
                        comments.append(prev_line)
                    lines += sorted(comments, reverse=True)
                lines.append(line)
            elif not once:
                continue
            # All following comments inside data.
            elif line.strip().startswith("--"):
                lines.append(line)
            else:
                break

    return str("\n".join(lines))


def replace_preprocessing_names(text: str, mapper: Mapping[str, str] | None) -> str:
    """Expand start and end marker pairs for well pattern recognition as needed.

    Args:
        text: Text with pre-processor reservoir modeling well names.
        mapper: Map of old to new names.

    Returns:
        Text with reservoir simulator well names.
    """
    if mapper is None:
        return text
    start_marks = ["'", " ", "\n", "\t"]
    end_marks = ["'", " ", " ", " "]
    for key, value in mapper.items():
        for start, end in zip(start_marks, end_marks):
            my_key = start + str(key) + start
            if my_key in text:
                my_value = start + str(value) + end
                text = text.replace(my_key, my_value)
    return text
