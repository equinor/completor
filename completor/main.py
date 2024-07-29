"""Main module of Completor."""

from __future__ import annotations

import logging
import os
import re
import time
from collections.abc import Mapping

import numpy as np
from tqdm import tqdm

import completor
from completor import completion, create_wells, parse
from completor.completion import WellSchedule
from completor.constants import Keywords
from completor.create_output import CreateOutput
from completor.create_wells import CreateWells
from completor.exceptions import CompletorError
from completor.launch_args_parser import get_parser
from completor.logger import handle_error_messages, logger
from completor.read_casefile import ReadCasefile
from completor.utils import abort, clean_file_line, clean_file_lines
from completor.visualization import close_figure, create_pdfpages


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
        for line in content:
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
            # OUTFILE is optional, if it's needed but not supplied the error is caught in ReadCasefile:check_pvt_file()
            if keyword == "OUTFILE":
                return None, None
            raise CompletorError(f"The keyword {keyword} is not defined correctly in the casefile")
    if keyword != "OUTFILE":
        try:
            with open(file_path, encoding="utf-8") as file:
                file_content = file.read()
        except FileNotFoundError as e:
            raise CompletorError(f"Could not find the file: '{file_path}'!") from e
        except (PermissionError, IsADirectoryError) as e:
            raise CompletorError("Could not read SCHFILE, this is likely because the path is missing quotes.") from e
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
) -> tuple[ReadCasefile, WellSchedule, CreateWells, CreateOutput] | tuple[ReadCasefile, WellSchedule, CreateWells]:
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
    written_wells = set()  # Keep track of which wells has been written.
    case = ReadCasefile(case_file=input_file, schedule_file=schedule_file, output_file=new_file)
    wells = CreateWells(case)
    active_wells = create_wells.get_active_wells(case.completion_table, case.gp_perf_devicelayer)
    schedule = WellSchedule(active_wells)  # container for MSW-data

    pdf_file = None
    if show_fig:
        figure_no = 1
        figure_name = f"Well_schematic_{figure_no:03d}.pdf"
        while os.path.isfile(figure_name):
            figure_no += 1
            figure_name = f"Well_schematic_{figure_no:03d}.pdf"
        pdf_file = create_pdfpages(figure_name)

    lines = schedule_file.splitlines()
    clean_lines_map = {}
    for line_number, line in enumerate(lines):
        line = clean_file_line(line, remove_quotation_marks=True)
        if line:
            clean_lines_map[line_number] = line

    err: Exception | None = None

    line_number = 0
    prev_line_number = 0
    try:
        with tqdm(total=len(lines)) as progress_bar:
            while line_number < len(lines):
                progress_bar.update(line_number - prev_line_number)
                prev_line_number = line_number
                line = lines[line_number]
                keyword = line[:8].rstrip()

                # Unrecognized (potential) keywords are written back untouched.
                if keyword not in Keywords.main_keywords:
                    output_text += format_text(None, f"{line}\n")
                    line_number += 1
                    continue

                well_name = _get_well_name(clean_lines_map, line_number)

                if keyword == Keywords.WELSPECS:
                    chunk, after_content_line_number = process_content(line_number, clean_lines_map)
                    schedule.set_welspecs(chunk)
                    raw = lines[line_number:after_content_line_number]
                    output_text += format_text(keyword, raw, chunk=False)  # Write it back 'untouched'.
                    line_number = after_content_line_number + 1
                    continue

                elif keyword == Keywords.COMPDAT:
                    chunk, after_content_line_number = process_content(line_number, clean_lines_map)
                    remains = schedule.handle_compdat(chunk)
                    if remains:
                        output_text += format_text(keyword, remains, end_of_record=True)  # Write non-active wells.
                    line_number = after_content_line_number + 1
                    continue

                elif keyword == Keywords.WELSEGS:
                    if well_name not in list(schedule.active_wells):
                        output_text += format_text(keyword, "")
                        line_number += 1
                        continue  # not an active well
                    chunk, after_content_line_number = process_content(line_number, clean_lines_map)
                    schedule.set_welsegs(chunk)  # update with new data
                    line_number = after_content_line_number + 1
                    continue

                elif keyword == Keywords.COMPSEGS:
                    if well_name not in list(schedule.active_wells):
                        output_text += format_text(keyword, "")
                        line_number += 1
                        continue  # not an active well
                    chunk, after_content_line_number = process_content(line_number, clean_lines_map)
                    schedule.set_compsegs(chunk)
                    line_number = after_content_line_number + 1

                    case.check_input(well_name, schedule)

                    if well_name not in written_wells:
                        write_welsegs = True  # will only write WELSEGS once
                        written_wells.add(well_name)
                    else:
                        write_welsegs = False
                    logger.debug("Writing new MSW info for well %s", well_name)
                    wells.update(well_name, schedule)
                    well_number = completion.get_well_number(well_name, active_wells)
                    output = CreateOutput(
                        case, schedule, wells, well_name, well_number, show_fig, pdf_file, write_welsegs, paths
                    )
                    output_text += format_text(None, output.finalprint)
                    continue
                raise CompletorError(
                    f"Unrecognized content at line number {line_number} with content:\n{line}\n"
                    "If you encounter this, please contact the team as this might be a mistake with the software."
                )
            else:
                progress_bar.update(len(lines) - prev_line_number)

    except Exception as e_:
        err = e_  # type: ignore
    finally:
        # Make sure the output thus far is written, and figure files are closed.
        output_text = _replace_preprocessing_names(output_text, case.mapper)
        with open(new_file, "w", encoding="utf-8") as file:
            file.write(output_text)

        close_figure()
        if pdf_file is not None:
            pdf_file.close()

    if err is not None:
        raise err

    if output is None:
        if len(schedule.active_wells) != 0:
            raise ValueError(
                "Inconsistent case and schedule files. Check well names, WELSPECS, COMPDAT, WELSEGS, and COMPSEGS."
            )
        return case, schedule, wells
    return case, schedule, wells, output


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
    else:
        raise CompletorError("Need input case file to run Completor")

    schedule_file_content, inputs.schedulefile = get_content_and_path(
        case_file_content, inputs.schedulefile, Keywords.SCHFILE
    )

    if isinstance(schedule_file_content, str):
        parse.read_schedule_keywords(clean_file_lines(schedule_file_content.splitlines()), Keywords.main_keywords)

    _, inputs.outputfile = get_content_and_path(case_file_content, inputs.outputfile, Keywords.OUTFILE)

    if inputs.outputfile is None:
        if inputs.schedulefile is None:
            raise ValueError(
                "Could not find a path to schedule file. "
                "It must be provided as a input argument or within the case files keyword 'SCHFILE'."
            )
        inputs.outputfile = inputs.schedulefile.split(".")[0] + "_advanced.wells"

    paths_input_schedule = (inputs.inputfile, inputs.schedulefile)

    logger.debug("Running Completor %s. An advanced well modelling tool.", completor.__version__)
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


if __name__ == "__main__":
    try:
        main()
    except CompletorError as e:
        raise abort(str(e)) from e
