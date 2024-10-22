"""Main module of Completor."""

from __future__ import annotations

import logging
import os
import re
import time
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd
from tqdm import tqdm

from completor import create_output, parse, read_schedule, utils
from completor.constants import Keywords
from completor.create_output import format_header
from completor.exceptions import CompletorError
from completor.get_version import get_version
from completor.launch_args_parser import get_parser
from completor.logger import handle_error_messages, logger
from completor.read_casefile import ReadCasefile
from completor.utils import abort, clean_file_line, clean_file_lines
from completor.wells import Well


def _replace_preprocessing_names(text: str, mapper: Mapping[str, str] | None) -> str:
    """Expand start and end marker pairs for well pattern recognition as needed.

    Args:
        text: Text with pre-processor reservoir modelling well names.

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


def format_text(
    keyword: str | None, content: list[list[str]] | list[str] | str, chunk: bool = True, end_of_record: bool = False
) -> str:
    """Write the content of a keyword to the output file.

    Args:
        keyword: Reservoir simulator keyword.
        content: Text to be written.
        chunk: Flag for indicating this is a list of records.
        end_of_record: Flag for adding end-of-record ('/').

    Returns:
        Formatted text.
    """
    text = ""
    if keyword is None:
        return content  # type: ignore # it's really a formatted string

    text += f"{keyword:s}\n"
    if chunk:
        for recs in content:
            text += f" {' '.join(recs)} /\n"
    else:
        for line in content[1:]:
            if isinstance(line, list):
                logger.warning(
                    "Chunk is False, but content contains lists of lists, "
                    "instead of a list of strings the lines will be concatenated."
                )
                line = " ".join(line)
            text += line + "\n"
    if end_of_record:
        text += "/\n"

    return text


def get_content_and_path(case_content: str, file_path: str | None, keyword: str) -> tuple[str | None, str | None]:
    """Get the contents of a file from a path defined by user or case file.

    The method prioritizes paths given as input argument over the paths found in the case file.

    Args:
        case_content: The case file content.
        file_path: Path to file if given.
        keyword: Reservoir simulator keyword.

    Returns:
        File content, file path.

    Raises:
        CompletorError: If the keyword or file cannot be found.
    """
    if file_path is None:
        # Find the path/name of file from case file
        case_file_lines = clean_file_lines(case_content.splitlines())
        start_idx, end_idx = parse.locate_keyword(case_file_lines, keyword)
        # If the keyword is defined correctly
        if end_idx == start_idx + 2:
            # preprocess the text, remove leading/trailing whitespace and quotes
            file_path = " ".join(case_file_lines[start_idx + 1].strip("'").strip(" ").split())
            file_path = re.sub("[\"']+", "", file_path)

        else:
            # OUT_FILE is optional, if it's needed but not supplied the error is caught in ReadCasefile:check_pvt_file()
            if keyword == Keywords.OUT_FILE:
                return None, None
            raise CompletorError(f"The keyword {keyword} is not defined correctly in the casefile")
    if keyword != Keywords.OUT_FILE:
        try:
            with open(file_path, encoding="utf-8") as file:
                file_content = file.read()
        except FileNotFoundError as e:
            raise CompletorError(f"Could not find the file: '{file_path}'!") from e
        except (PermissionError, IsADirectoryError) as e:
            raise CompletorError(
                f"Could not read {Keywords.SCHEDULE_FILE}, this is likely because the path is missing quotes."
            ) from e
        return file_content, file_path
    return None, file_path


def process_content(line_number: int, clean_lines: dict[int, str]) -> tuple[list[list[str]], int]:
    """Process the contents

    Args:
        line_number: The current line number.
        clean_lines: Clean line to line number mapping.

    Returns:
        The formatted contents, and the new number of lines after processing.

    """
    content = ""
    # concatenate and look for 'end of records' => //
    while not re.search(r"/\s*/$", content):
        line_number += 1
        if line_number in clean_lines:
            content += clean_lines[line_number]
    content = _format_content(content)
    return content, line_number


def create(
    input_file: str, schedule_file: str, new_file: str, show_fig: bool = False, paths: tuple[str, str] | None = None
) -> tuple[ReadCasefile, Well | None, str] | tuple[ReadCasefile, Well | None]:
    """Create and write the advanced schedule file from input case- and schedule files.

    Args:
        input_file: Input case file.
        schedule_file: Input schedule file.
        new_file: Output schedule file.
        show_fig: Flag indicating if a figure is to be shown.
        paths: Optional additional paths.

    Returns:
        The case and schedule file, the well and output object.
    """
    output_text = ""
    output = None
    case = ReadCasefile(case_file=input_file, schedule_file=schedule_file, output_file=new_file)
    active_wells = utils.get_active_wells(case.completion_table, case.gp_perf_devicelayer)
    schedule_data: dict[str, dict[str, Any]] = {}
    schedule = schedule_file  # TODO: Refactor
    well = None

    figure_name = None
    if show_fig:
        figure_no = 1
        figure_name = f"Well_schematic_{figure_no:03d}.pdf"
        while os.path.isfile(figure_name):
            figure_no += 1
            figure_name = f"Well_schematic_{figure_no:03d}.pdf"

    lines = schedule_file.splitlines()
    clean_lines_map = {}
    for line_number, line in enumerate(lines):
        line = clean_file_line(line, remove_quotation_marks=True)
        if line:
            clean_lines_map[line_number] = line

    err: Exception | None = None

    line_number = 0
    prev_line_number = 0
    well_names = []
    # with tqdm(total=len(lines)) as progress_bar:
    #     while line_number < len(lines):
    #         progress_bar.update(line_number - prev_line_number)
    #         prev_line_number = line_number
    #         line = lines[line_number]
    #         keyword = line[:8].rstrip()
    #
    #         # Unrecognized (potential) keywords are written back untouched.
    #         if keyword not in Keywords.main_keywords:
    #             output_text += f"{line}\n"
    #             line_number += 1
    #             continue
    #
    #         # TODO(#164): Check that this works properly in multi-well environment.
    #         well_name = _get_well_name(clean_lines_map, line_number)
    #
    #         if keyword == Keywords.WELL_SPECIFICATION:
    #             if well_name not in list(active_wells):
    #                 output_text += format_text(keyword, "")
    #                 line_number += 1
    #                 continue  # not an active well
    #             chunk, after_content_line_number = process_content(line_number, clean_lines_map)
    #             schedule_data = read_schedule.set_welspecs(schedule_data, chunk)
    #             raw = lines[line_number:after_content_line_number]
    #             # Write it back 'untouched'.
    #             output_text += format_text(keyword, raw, chunk=False, end_of_record=True)
    #             line_number = after_content_line_number + 1
    #             continue
    #
    #         elif keyword == Keywords.COMPLETION_DATA:
    #             chunk, after_content_line_number = process_content(line_number, clean_lines_map)
    #             untouched_content = [rec for rec in chunk if rec[0] not in list(active_wells)]
    #             current_wells = {rec[0] for rec in chunk if rec[0]}
    #             current_active_wells = np.array(list(current_wells.intersection(active_wells)))
    #             if current_active_wells.size > 0:
    #                 schedule_data = read_schedule.set_compdat(schedule_data, chunk)
    #             if untouched_content:
    #                 # Write untouched wells back as-is.
    #                 output_text += format_text(keyword, untouched_content, end_of_record=True)
    #             line_number = after_content_line_number + 1
    #             continue
    #
    #         elif keyword == Keywords.WELL_SEGMENTS:
    #             if well_name not in list(active_wells):
    #                 output_text += format_text(keyword, "")
    #                 line_number += 1
    #                 continue  # not an active well
    #             chunk, after_content_line_number = process_content(line_number, clean_lines_map)
    #             schedule_data = read_schedule.set_welsegs(schedule_data, chunk)
    #             line_number = after_content_line_number + 1
    #             continue
    #
    #         elif keyword == Keywords.COMPLETION_SEGMENTS:
    #             if well_name not in list(active_wells):
    #                 output_text += format_text(keyword, "")
    #                 line_number += 1
    #                 continue  # not an active well
    #             chunk, after_content_line_number = process_content(line_number, clean_lines_map)
    #
    #             schedule_data = read_schedule.set_compsegs(schedule_data, chunk)
    #
    #             line_number = after_content_line_number + 1
    #             case.check_input(well_name, schedule_data)
    #
    #         well_names.append(well_name)
    #
    #     output_text += "\n" + format_header(paths)
    #     for i, well_name_ in tqdm(enumerate(well_names), total=len(well_names)):
    #         logger.debug("Writing new MSW info for well %s", well_name_)
    #         # well = Well(well_name_, i, case, schedule_data[well_name_])
    #         # output = create_output.format_output(well, case, figure_name, paths)
    #         # output_text += "\n" + output
    # line_number = 0
    # prev_line_number = 0
    # well_names = []
    # schedule = schedule_file  # TODO: Refactor
    # Add banner.
    schedule = create_output.metadata_banner(paths) + schedule
    # Strip trailing whitespace.
    schedule = re.sub(r"[^\S\r\n]+$", "", schedule, flags=re.MULTILINE)
    meaningful_data: dict[str, dict[str, pd.DataFrame | tuple[pd.DataFrame, pd.DataFrame]]] = {}

    try:
        # TODO(#ANDRE): Consider using update instead of returning and setting the whole dict.
        keyword = Keywords.WELL_SPECIFICATION
        chunks = find_keyword_data(keyword, schedule)
        for chunk in chunks:
            clean_data = clean_raw_data(chunk, keyword)
            meaningful_data = read_schedule.set_welspecs(meaningful_data, clean_data)

        keyword = Keywords.COMPLETION_DATA
        chunks = find_keyword_data(keyword, schedule)
        for chunk in chunks:
            clean_data = clean_raw_data(chunk, keyword)
            meaningful_data = read_schedule.set_compdat(meaningful_data, clean_data)

        keyword = Keywords.WELL_SEGMENTS
        chunks = find_keyword_data(keyword, schedule)
        for chunk in chunks:
            clean_data = clean_raw_data(chunk, keyword)
            meaningful_data = read_schedule.set_welsegs(meaningful_data, clean_data)

        keyword = Keywords.COMPLETION_SEGMENTS
        chunks = find_keyword_data(keyword, schedule)
        for chunk in chunks:
            clean_data = clean_raw_data(chunk, keyword)
            meaningful_data = read_schedule.set_compsegs(meaningful_data, clean_data)

        for i, well_name in enumerate(active_wells.tolist()):
            case.check_input(well_name, meaningful_data)  # TODO: This apparently have to be done first here!
            well = Well(well_name, i, case, meaningful_data[well_name])
            # well = Well(well_name_, i, case, schedule_data[well_name_])
            compdat, welsegs, compsegs, bonus, _ = create_output.format_output(well, case, figure_name, paths)

            # new_compdat = ""
            # new_compsegs = ""
            # new_welsegs = ""
            # bonus = ""
            # for lateral in well.active_laterals:
            # output_object = create_output.Output(well, None, case, figure_name)
            # output = create_output.format_output(well, case, figure_name, paths)

            # TODO: Maybe reformat WELSPECS not touched as well for a more consistent look?
            # TODO: Consider using update instead of returning and setting the whole str file.

            for keyword in [Keywords.COMPLETION_SEGMENTS, Keywords.WELL_SEGMENTS, Keywords.COMPLETION_DATA]:
                tmp_data = find_well_keyword_data(well_name, keyword, schedule)
                old_data = str("\n".join(tmp_data))
                try:
                    # Check that nothing is lost.
                    schedule.index(old_data)
                    if not old_data:
                        raise ValueError
                except ValueError:
                    raise CompletorError("Could not match the old data to schedule file. Please contact the team!")

                match keyword:
                    case Keywords.COMPLETION_DATA:
                        schedule = schedule.replace(old_data, compdat)
                    case Keywords.COMPLETION_SEGMENTS:
                        schedule = schedule.replace(old_data, compsegs + bonus)
                    case Keywords.WELL_SEGMENTS:
                        schedule = schedule.replace(old_data, welsegs)

    except Exception as e_:
        err = e_  # type: ignore
    finally:
        # Make sure the output thus far is written, and figure files are closed.
        schedule = _replace_preprocessing_names(schedule, case.mapper)
        with open(new_file, "w", encoding="utf-8") as file:
            file.write(schedule)

    if err is not None:
        raise err

    # if output is None:
    #     if len(active_wells) != 0:
    #         raise ValueError(
    #             "Inconsistent case and schedule files. Check well names, "
    #             "WELL_SPECIFICATION, COMPLETION_DATA, WELL_SEGMENTS, and COMPLETION_SEGMENTS."
    #         )
    #     return case, well
    return case, well  # , output


def main() -> None:
    """Generate a Completor output schedule file from the input given from user.

    Also set the correct loglevel based on user input. Defaults to WARNING if not set.

    Raises:
        CompletorError: If input schedule file is not defined as input or in case file.
    """
    parser = get_parser()
    inputs = parser.parse_args()

    if inputs.loglevel is not None:
        loglevel = inputs.loglevel
    else:
        loglevel = logging.WARNING
    # Loglevel NOTSET (0) gets overwritten by higher up loggers to WARNING, setting loglevel to 1 is a lazy workaround.
    loglevel = 1 if loglevel == 0 else loglevel

    logger.setLevel(loglevel)

    # Open the case file
    if inputs.inputfile is not None:
        with open(inputs.inputfile, encoding="utf-8") as file:
            case_file_content = file.read()

    schedule_file_content, inputs.schedulefile = get_content_and_path(
        case_file_content, inputs.schedulefile, Keywords.SCHEDULE_FILE
    )

    if isinstance(schedule_file_content, str):
        parse.read_schedule_keywords(clean_file_lines(schedule_file_content.splitlines()), Keywords.main_keywords)

    _, inputs.outputfile = get_content_and_path(case_file_content, inputs.outputfile, Keywords.OUT_FILE)

    if inputs.outputfile is None:
        if inputs.schedulefile is None:
            raise ValueError(
                "Could not find a path to schedule file. "
                f"It must be provided as a input argument or within the case files keyword '{Keywords.SCHEDULE_FILE}'."
            )
        inputs.outputfile = inputs.schedulefile.split(".")[0] + "_advanced.wells"

    paths_input_schedule = (inputs.inputfile, inputs.schedulefile)

    logger.info("Running Completor version %s. An advanced well modelling tool.", get_version())
    logger.debug("-" * 60)
    start_a = time.time()

    handle_error_messages(create)(
        case_file_content, schedule_file_content, inputs.outputfile, inputs.figure, paths=paths_input_schedule
    )

    logger.debug("Total runtime: %d", (time.time() - start_a))
    logger.debug("-" * 60)


def _get_well_name(schedule_lines: dict[int, str], i: int) -> str:
    """Get the well name from line number.

    Args:
        schedule_lines: Dictionary of lines in schedule file.
        i: Line index.

    Returns:
        Well name.
    """
    keys = np.array(sorted(list(schedule_lines.keys())))
    j = np.where(keys == i)[0][0]
    next_line = schedule_lines[int(keys[j + 1])]
    return next_line.split()[0]


def _format_content(text: str) -> list[list[str]]:
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
            clean_content.append(_format_content(clean_line)[0])
    return clean_content


def find_well_keyword_data(well: str, keyword: str, text: str) -> list[str]:
    """Find the data associated with keyword and well name, include leading comments.

    Args:
        well: Well name.
        keyword: Keyword to search for.
        text: Raw text to look for matches in.

    Returns:
        The correct match given keyword and well name.
    """
    matches = find_keyword_data(keyword, text)

    lines = []
    for match in matches:
        if re.search(well, match) is None:
            continue

        match = match.splitlines()
        once = False
        for i, line in enumerate(match):
            if not line:
                if once:
                    lines.append(line)
                continue

            if well in line.split()[0]:  # or f"'{well}'" == line.split()[0]: # TODO: This should be redundant.
                if keyword in [Keywords.WELL_SEGMENTS, Keywords.COMPLETION_SEGMENTS]:
                    # These keywords should just be the entire match as they never contain more than one well.
                    return match
                if not once:
                    once = True
                    # Remove contiguous comments above the first line by looking backwards,
                    # adding it to the replaceable text match.
                    for prev_line in match[i - 1 :: -1]:
                        if not prev_line.strip().startswith("--") or not prev_line:
                            break
                        lines.append(prev_line)
                    lines.reverse()

                    lines.append(line)
                else:
                    lines.append(line)
            elif not once:
                continue
            # All following comments inside data.
            elif line.strip().startswith("--"):
                lines.append(line)
            else:
                break

    return lines


if __name__ == "__main__":
    try:
        main()
    except CompletorError as e:
        raise abort(str(e)) from e
