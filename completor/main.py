"""Main module of Completor."""

from __future__ import annotations

import logging
import os
import re
import sys
import time
from pathlib import Path

from matplotlib.backends.backend_pdf import PdfPages  # type: ignore
from tqdm import tqdm

from completor import create_output, parse, read_schedule, utils
from completor.constants import Keywords, ScheduleData
from completor.exceptions.clean_exceptions import CompletorError
from completor.get_version import get_version
from completor.icv_file_handling import IcvFileHandling
from completor.initialization import Initialization
from completor.initialization_pyaction import InitializationPyaction
from completor.launch_args_parser import get_parser
from completor.logger import handle_error_messages, logger
from completor.read_casefile import ICVReadCasefile, ReadCasefile
from completor.utils import (
    clean_file_lines,
    clean_raw_data,
    completion_keyword_in_file,
    find_keyword_data,
    find_well_keyword_data,
    icvc_keyword_in_file,
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
) -> tuple[ReadCasefile, Well | None, list[tuple[str, int]]]:
    """Create and write the advanced schedule file from input case- and schedule files.

    Args:
        case_file: Input case file.
        schedule: Input schedule file.
        new_file: Output schedule file.
        show_fig: Flag indicating if a figure is to be shown.
        paths: Optional additional paths.

    Returns:
        - ReadCasefile object.
        - Well object or None if no well was found.
        - Well segment list or None if no update of segment list.
    """
    case = ReadCasefile(case_file=case_file, schedule_file=schedule, output_file=new_file)
    active_wells = utils.get_active_wells(case.completion_table, case.gp_perf_devicelayer)
    well_segment_list: list[tuple[str, int]] = []
    pdf = None
    figure_name = None
    if show_fig:
        figure_no = 1
        figure_name = f"Well_schematic_{figure_no:03d}.pdf"
        while os.path.isfile(figure_name):
            figure_no += 1
            figure_name = f"Well_schematic_{figure_no:03d}.pdf"
        pdf = PdfPages(figure_name)

    err: Exception | None = None
    well = None
    # Add banner.
    schedule = create_output.metadata_banner(paths) + schedule
    # Strip trailing whitespace.
    schedule = re.sub(r"[^\S\r\n]+$", "", schedule, flags=re.MULTILINE)
    meaningful_data: ScheduleData = {}

    well_segment_list = []
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
        for i, well_name in tqdm(enumerate(active_wells.tolist()), total=len(active_wells), file=sys.stdout):
            try:
                well = Well(well_name, i, case, meaningful_data[well_name])
            except KeyError:
                logger.warning(f"Well '{well_name}' is written in case file but does not exist in schedule file.")
                continue
            compdat, welsegs, compsegs, bonus, df_icv = create_output.format_output(well, case, pdf)
            if len(df_icv) > 0:
                get_icv_segment(well_segment_list, df_icv)
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
        if pdf is not None:
            pdf.close()

    if err is not None:
        raise err

    return case, well, well_segment_list


def get_icv_segment(well_segment_list, icv_dataframe):
    for row in range(len(icv_dataframe)):
        well_name = icv_dataframe.iloc[row]["WELL"]
        segment_number = int(icv_dataframe.iloc[row]["START_SEGMENT_NUMBER"])
        well_segment_list.append((well_name, segment_number))


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
    # If ICVC exists, it should not be mandatory to have whole schedule files
    # Check on both schedule and case files first
    if completion_keyword_in_file(inputs.inputfile) and not icvc_keyword_in_file(inputs.inputfile):
        if isinstance(schedule_file_content, str):
            parse.read_schedule_keywords(clean_file_lines(schedule_file_content.splitlines()), Keywords.main_keywords)

    _, inputs.outputfile = get_content_and_path(case_file_content, inputs.outputfile, Keywords.OUT_FILE)

    if inputs.outputfile is None:
        if inputs.schedulefile is None:
            raise ValueError("Could not find a path to schedule file. It must be provided as a input argument.")
        inputs.outputfile = inputs.schedulefile.split(".")[0] + "_advanced.wells"

    paths_input_schedule = (inputs.inputfile, inputs.schedulefile)

    logger.info("Running Completor version %s. An advanced well modelling tool.", get_version())
    logger.debug("-" * 60)
    start_a = time.time()

    case, well, well_start_segments = handle_error_messages(create)(
        case_file_content, schedule_file_content, inputs.outputfile, inputs.figure, paths=paths_input_schedule
    )
    if icvc_keyword_in_file(inputs.inputfile):
        # start running ICV Control
        # the input schedule file to second run of ICV Control is the output file from Completor
        # therefore

        inputs.schedulefile = inputs.outputfile
        inputs.schedulefile = os.path.abspath(inputs.schedulefile)

        if inputs.outputfile is not None:

            schedule_content, inputs.schedulefile = get_content_and_path(
                case_file_content, inputs.schedulefile, Keywords.SCHEDULE_FILE
            )
            inputs.outputfile, inputs.outputdirectory = get_output_filename_and_directory(inputs)

            if inputs.inputfile is not None:
                create_icvc(case_file_content, schedule_content, inputs, well_start_segments)

    logger.debug("Total runtime: %d", (time.time() - start_a))
    logger.debug("-" * 60)


def get_output_filename_and_directory(inputs) -> tuple[str, str]:
    """Get the output filename and directory from the user input.

    Args:
        arguments: Arguments from the command line.

    Returns:
        output_filename: The output filename.
        output_directory: The output directory.
    """
    if inputs.outputfile:
        output_path = Path(inputs.outputfile)
        output_filename = f"{output_path.name}"
    else:
        output_path = Path(inputs.schedulefile)
        output_filename = f"{output_path.stem}.sch"

    # use cwd as output directory if the output_path is just a filename. e.g. output.sch
    output_directory = str(Path.cwd() if output_path.parent == Path(".") else output_path.parent)
    return output_filename, output_directory


def create_icvc(case_content: str, schedule_content: str | None, inputs, new_segments: str):
    """
    Create ICV-control schedule- and include files from input case- and schedule files.

    Args:
        input_case_content: Input case file.
        schedule_content: Input schedule file.
        arguments: Arguments from the command line.
    """

    case = ICVReadCasefile(case_content, schedule_content, new_segments)
    initials = Initialization(case, schedule_content)
    initials_pyaction = InitializationPyaction(case, schedule_content)
    file_data = {
        "output_file_name": inputs.outputfile,
        "output_directory": inputs.outputdirectory,
        "schedule_file_path": inputs.schedulefile,
        "input_case_file": inputs.inputfile,
    }
    IcvFileHandling(file_data, initials, initials_pyaction)
