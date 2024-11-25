"""Main module of Completor."""

from __future__ import annotations

import logging
import os
import re
import time

from tqdm import tqdm

from completor import create_output, parse, read_schedule, utils
from completor.constants import Keywords, ScheduleData
from completor.exceptions.clean_exceptions import CompletorError
from completor.get_version import get_version
from completor.launch_args_parser import get_parser
from completor.logger import handle_error_messages, logger
from completor.read_casefile import ReadCasefile
from completor.utils import (
    abort,
    clean_file_lines,
    clean_raw_data,
    find_keyword_data,
    find_well_keyword_data,
    replace_preprocessing_names,
)
from completor.wells import Well


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


def create(
    case_file: str, schedule: str, new_file: str, show_fig: bool = False, paths: tuple[str, str] | None = None
) -> tuple[ReadCasefile, Well | None]:
    """Create and write the advanced schedule file from input case- and schedule files.

    Args:
        case_file: Input case file.
        schedule: Input schedule file.
        new_file: Output schedule file.
        show_fig: Flag indicating if a figure is to be shown.
        paths: Optional additional paths.

    Returns:
        The case and schedule file, the well and output object.
    """
    case = ReadCasefile(case_file=case_file, schedule_file=schedule, output_file=new_file)
    active_wells = utils.get_active_wells(case.completion_table, case.gp_perf_devicelayer)

    figure_name = None
    if show_fig:
        figure_no = 1
        figure_name = f"Well_schematic_{figure_no:03d}.pdf"
        while os.path.isfile(figure_name):
            figure_no += 1
            figure_name = f"Well_schematic_{figure_no:03d}.pdf"

    err: Exception | None = None
    well = None
    # Add banner.
    schedule = create_output.metadata_banner(paths) + schedule
    # Strip trailing whitespace.
    schedule = re.sub(r"[^\S\r\n]+$", "", schedule, flags=re.MULTILINE)
    meaningful_data: ScheduleData = {}

    try:
        # Find the old data for each of the four main keywords.
        for chunk in find_keyword_data(Keywords.WELL_SPECIFICATION, schedule):
            clean_data = clean_raw_data(chunk, Keywords.WELL_SPECIFICATION)
            meaningful_data = read_schedule.set_welspecs(meaningful_data, clean_data)

        for chunk in find_keyword_data(Keywords.COMPLETION_DATA, schedule):
            clean_data = clean_raw_data(chunk, Keywords.COMPLETION_DATA)
            meaningful_data = read_schedule.set_compdat(meaningful_data, clean_data)

        for chunk in find_keyword_data(Keywords.WELL_SEGMENTS, schedule):
            clean_data = clean_raw_data(chunk, Keywords.WELL_SEGMENTS)
            meaningful_data = read_schedule.set_welsegs(meaningful_data, clean_data)

        for chunk in find_keyword_data(Keywords.COMPLETION_SEGMENTS, schedule):
            clean_data = clean_raw_data(chunk, Keywords.COMPLETION_SEGMENTS)
            meaningful_data = read_schedule.set_compsegs(meaningful_data, clean_data)

        for i, well_name in tqdm(enumerate(active_wells.tolist()), total=len(active_wells)):
            well = Well(well_name, i, case, meaningful_data[well_name])
            compdat, welsegs, compsegs, bonus = create_output.format_output(well, case, figure_name)

            for keyword in [Keywords.COMPLETION_SEGMENTS, Keywords.WELL_SEGMENTS, Keywords.COMPLETION_DATA]:
                old_data = find_well_keyword_data(well_name, keyword, schedule)
                if not old_data:
                    raise CompletorError(
                        "Could not find the unmodified data in original schedule file. Please contact the team!"
                    )
                try:
                    # Check that nothing is lost.
                    schedule.index(old_data)
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
        err = e_
    finally:
        # Make sure the output thus far is written, and figure files are closed.
        schedule = replace_preprocessing_names(schedule, case.mapper)
        with open(new_file, "w", encoding="utf-8") as file:
            file.write(schedule)

    if err is not None:
        raise err

    return case, well


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


if __name__ == "__main__":
    try:
        main()
    except CompletorError as e:
        raise abort(str(e)) from e
