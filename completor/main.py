"""Main module of Completor."""

from __future__ import annotations
from tqdm import tqdm
from completor.create_output import Output, metadata_banner

from matplotlib.backends.backend_pdf import PdfPages  # type: ignore

import logging
import os
import re
import time
from collections.abc import Mapping
from typing import Any

import numpy as np

import completor
from completor import parse, read_schedule, utils
from completor.constants import Keywords
from completor.exceptions import CompletorError
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
    well = None

    figure_name = None
    if show_fig:
        figure_no = 1
        figure_name = f"Well_schematic_{figure_no:03d}.pdf"
        while os.path.isfile(figure_name):
            figure_no += 1
            figure_name = f"Well_schematic_{figure_no:03d}.pdf"

    # lines = schedule_file.splitlines()
    # clean_lines_map = {}
    # for line_number, line in enumerate(lines):
    #     line = clean_file_line(line, remove_quotation_marks=True)
    #     if line:
    #         clean_lines_map[line_number] = line

    err: Exception | None = None

    schedule = schedule_file
    meaningful_data = {}
    old = schedule
    schedule = metadata_banner(paths) + schedule
    schedule = re.sub(r"[^\S\r\n]+$", "", schedule, flags=re.MULTILINE)
    try:

        # TODO: Tqdm
        # TODO: Consider using update instead of returning and setting the whole dict.
        # TODO: Make this a method?
        # def read_meaningful_schedule_data(key, data) -> dict[str, dict[str, Any]]:
        #     = Keywords.COMPLETION_DATA
        #     chunks = find_keyword_data(keyword, schedule)
        #     for chunk in chunks:
        #         clean_data = format_data(chunk, keyword)
        #         meaningful_data = read_schedule.set_compdat(meaningful_data, clean_data)
        keyword = Keywords.WELL_SPECIFICATION
        chunks = find_keyword_data(keyword, schedule)
        for chunk in chunks:
            clean_data = format_data(chunk, keyword)
            meaningful_data = read_schedule.set_welspecs(meaningful_data, clean_data)

        keyword = Keywords.WELL_SEGMENTS
        chunks = find_keyword_data(keyword, schedule)
        for chunk in chunks:
            clean_data = format_data(chunk, keyword)
            meaningful_data = read_schedule.set_welsegs(meaningful_data, clean_data)

        keyword = Keywords.COMPLETION_SEGMENTS
        chunks = find_keyword_data(keyword, schedule)
        for chunk in chunks:
            clean_data = format_data(chunk, keyword)
            meaningful_data = read_schedule.set_compsegs(meaningful_data, clean_data)

        keyword = Keywords.COMPLETION_DATA
        chunks = find_keyword_data(keyword, schedule)
        for chunk in chunks:
            clean_data = format_data(chunk, keyword)
            meaningful_data = read_schedule.set_compdat(meaningful_data, clean_data)

        # TODO: Strip the single fnutts to have it get correct lol

        # TODO: Not the actual active well.
        # warn if under 4 len?
        # temp_active_wells = [key for key in meaningful_data.keys() if len(meaningful_data.get(key)) == 4]
        # temp_active_wells = [well for well in temp_active_wells if (well == case.completion_table["WELL"]).any()]

        for i, well_name in enumerate(active_wells):
            # TODO: Consider using update instead of returning and setting the whole str file.
            # schedule = replace_chunks(Keywords.WELL_SPECIFICATION, well, schedule, meaningful_data)
            well = Well(well_name, i, case, meaningful_data[well_name])

            output_object = Output(well, case, figure_name)

            print(well_name)
            # TODO: Maybe reformat WELSPECS not touched as well for a more consistent look?
            for keyword in Keywords.main_keywords:
                # TODO: Technically not needed to be calculated in WELSPECS case?
                old_data, format_header = find_well_keyword_data(well_name, keyword, schedule)
                if not old_data:
                    continue
                old_data = "\n".join(old_data)
                match keyword:
                    case Keywords.WELL_SPECIFICATION:
                        continue
                    case Keywords.COMPLETION_DATA:
                        # TODO: print_completion_data formatting looks wonky
                        #  Only formatting the one block, also adds headers to each lateral.
                        new_data = output_object.print_completion_data
                        schedule = schedule.replace(old_data, new_data)
                        # TODO: COMPDAT 'DERM2' looking a bit wonkey, maybe remove comments already there?
                        # TODO: Merge headers kanskje?
                        continue
                    case Keywords.COMPLETION_SEGMENTS:
                        new_data = output_object.print_completion_segments
                        new_data += output_object.bonus_data
                        schedule = schedule.replace(old_data, new_data)
                    case Keywords.WELL_SEGMENTS:
                        new_data = output_object.print_well_segments
                        schedule = schedule.replace(old_data, new_data)
                    case _:
                        print(keyword, "not handeled")
                        continue
                    # TODO: QUESTION MARK, what is what of VALV and WSEGICV??
                    # case Keywords.INFLOW_CONTROL_VALVE:
                    #     new_data = output_object.print_well_segments
                    # TODO: WSEGVALV headers blir ikke riktig formatert!
                    # case Keywords.WELL_SEGMENTS_VALVE:
                    #     new_data = output_object.print_well_segments

        print("bp")

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
    return case, well, output


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

    logger.info("Running Completor version %s. An advanced well modelling tool.", completor.__version__)
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
    # TODO: Docstrings
    pattern = rf"^{keyword}(?:\n--.*\n)?(?:.*\n)*?/"

    # Find matches
    return re.findall(pattern, text, re.MULTILINE)


def format_data(raw_record: str, keyword):
    # TODO: Parsing should not be in this file though, move it.
    # for record in raw_records:
    # record = raw_record.split(f"{keyword}\n")
    # record = raw_record.split(keyword)
    record = re.split(rf"{keyword}\n", raw_record)
    if len(record) != 2:
        # TODO: Fix it
        raise ValueError("Yoo, too many keywords in here yo")
    raw_content = record[1].splitlines()
    raw_content = raw_content[:-1]
    clean_content = []
    for line in raw_content:  # keepends=True?
        clean_line = clean_file_line(line, remove_quotation_marks=True)
        if clean_line:
            clean_content.append(_format_content(clean_line)[0])  # remove_quotation_marks=True?
    return clean_content


def find_well_keyword_data(well: str, keyword: str, text: str) -> tuple[list[str], bool]:
    matches = find_keyword_data(keyword, text)

    lines = []
    format_header = False
    # TODO: Place for big improvement by re.searching in matches strings as a preprocessing at least
    for match in matches:
        match = match.splitlines()
        once = True
        for i, line in enumerate(match):
            if well == line.split()[0] or f"'{well}'" in line.split()[0]:
                # TODO: This is not efficient
                if once:
                    # Remove contiguous comments above this line by looking backwards
                    for l in match[i - 1 :: -1]:
                        if l.strip().startswith("--"):
                            lines.append(l)
                        else:
                            break

                    once = False
                    lines.reverse()

                # if not format_header:
                #     is_first = all([l.startswith("--") for l in match[1:i]])
                #     if is_first:
                #         format_header = True
                if keyword in [Keywords.WELL_SEGMENTS, Keywords.COMPLETION_SEGMENTS]:
                    return match, True
                lines.append(line)

    return lines, format_header


if __name__ == "__main__":
    try:
        main()
    except CompletorError as e:
        raise abort(str(e)) from e
