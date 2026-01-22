"""A file handling class for the icv-control algorithm"""

from __future__ import annotations

import datetime
import re
from pathlib import Path

from completor import icv_functions
from completor.constants import ICVMethod
from completor.get_version import get_version
from completor.initialization import Initialization
from completor.logger import logger


class IcvFileHandling:
    """Create paths, directories, and output files."""

    def __init__(self, file_data: dict, initials: Initialization):
        self.initials = initials
        self.icv_functions = icv_functions.IcvFunctions(initials)
        self.current_working_directory = Path.cwd()
        self.output_file_name = Path(file_data["output_file_name"])
        self.output_directory = Path(file_data["output_directory"])
        self.input_case_file = Path(file_data["input_case_file"])
        self.create_ordered_filenames()
        self.create_include_files()
        self.create_main_schedule_file(Path(file_data["schedule_file_path"]))
        self.include_file_path = None
        self.schedule_include_file_path = None

    def create_ordered_filenames(self):
        """Create a dict with datetime keys and include file name values."""

        self.ordered_filenames = {}
        for icv_name in self.initials.icv_names:
            icv_date = self.initials.icv_dates[icv_name]
            if icv_date not in self.ordered_filenames:
                self.ordered_filenames[icv_date] = {}
            if icv_name not in self.ordered_filenames[icv_date]:
                self.ordered_filenames[icv_date][icv_name] = []

    def create_include_file_content(self, icv_name: str, file_type: ICVMethod, criteria: int | None = None) -> str:
        """Create include file content for icv functions.

        Args:
            icv_name: Icv name. One or two symbols, I.E: A or Z9.
            file_type: File type CHOKE_WAIT, OPEN_WAIT, CHOKE, OPEN.
            criteria: Integer value denoting the criteria.

        Returns:
            Content of the file_type include file.

        Raises:
            ValueError: If criteria is None for CHOKE or OPEN file type.

        """
        trigger_number_times = 10000
        file_content = ""
        actionx_repeater = self.initials.case.step_table[icv_name][0]
        if actionx_repeater > 9999 or len(str(actionx_repeater)) > 4:
            logger.warning(f"MAX 9999 steps:'{actionx_repeater}'steps on ICV '{icv_name}'")
        if file_type == ICVMethod.CHOKE_WAIT:
            trigger_minimum_interval = 10
            file_content += self.icv_functions.create_choke_wait(
                icv_name, trigger_number_times, trigger_minimum_interval, actionx_repeater, criteria
            )
            return file_content

        if file_type == ICVMethod.OPEN_WAIT:
            file_content += self.icv_functions.create_open_wait(icv_name, actionx_repeater, criteria)
            return file_content

        if file_type == ICVMethod.CHOKE:
            trigger_minimum_interval_str = ""
            file_content = self.icv_functions.create_choke_ready(
                icv_name, criteria, trigger_number_times, trigger_minimum_interval_str
            )
            file_content += self.icv_functions.create_choke_wait_stop(icv_name, criteria)
            file_content += self.icv_functions.create_choke_stop(
                icv_name, criteria, trigger_number_times, trigger_minimum_interval_str
            )
            trigger_number_times = 1
            file_content += self.icv_functions.create_choke(
                icv_name, criteria, trigger_number_times, trigger_minimum_interval_str, actionx_repeater
            )
            return file_content

        if file_type == ICVMethod.OPEN:
            trigger_minimum_interval_str = ""
            file_content += self.icv_functions.create_open_ready(
                icv_name, criteria, trigger_number_times, trigger_minimum_interval_str
            )
            file_content += self.icv_functions.create_open_wait_stop(icv_name, criteria)
            file_content += self.icv_functions.create_open_stop(
                icv_name, criteria, trigger_number_times, trigger_minimum_interval_str
            )
            trigger_number_times = 1
            file_content += self.icv_functions.create_open(
                icv_name, criteria, trigger_number_times, trigger_minimum_interval_str, actionx_repeater
            )
            return file_content

        raise ValueError(f"The file type '{file_type}' is not recognized.")

    def append_control_criteria_to_file(
        self, file_path: Path, well_name: str, icv_name: str, file_type: ICVMethod, icv_date: str, criteria: int | None
    ):
        """Append to the file.

        Args:
            file_path: Path to the file
            well_name: Well name.
            icv_name: Icv name, one or two symbols, I.E: A or Z9.
            file_type: Type of icv function file.
            icv_date: Date of Icv change.
            criteria: Integer value denoting the criteria.

        """
        self.ordered_filenames[icv_date][icv_name].append(file_path)
        content = self.create_include_file_content(icv_name, file_type, criteria)
        content = self.add_section_header(content, f"{well_name} {icv_name} {file_type}")
        self.append_content_to_file(file_path, content)

    def append_content_to_file(self, file_path: Path, content: str):
        """Append content to the file. Create the file if it does not exist.

        Args:
            file_path: Path to the file.
            content: Content to append to the file.

        """
        file_path.touch(exist_ok=True)

        if not content.endswith("\n\n"):
            content += "\n\n"

        with open(file_path, "a", encoding="utf-8") as file:
            file.write(content)

    def add_section_header(self, content: str, header: str) -> str:
        """Add a section header to the content.

        Args:
            content: Content to add the header to.
            header: Header to add to the content.

        Returns:
            Content with the header added.

        """
        if self.initials.case.python_dependent:
            return "" + content
        return f"--- {header} ---\n{content}"

    def create_include_files(self):
        """Create the include files for icv-control.

        The include files are as follows:
            - include.sch
                - icv-control tables
                - init
                - input
                - control critieria for each well and icv.
            - summary.sch
        """
        base_folder = Path(self.output_directory)
        fmu_path = Path("eclipse/include/")
        if str(fmu_path) in str(base_folder):
            base_include_path = Path("../include/schedule")
        else:
            base_include_path = Path("")

        base_folder.mkdir(parents=True, exist_ok=True)

        summary_file_path = Path(base_folder / "summary_icvc.sch")
        self.include_file_path = Path(base_folder / "include_icvc.sch")
        self.schedule_include_file_path = Path(base_include_path / "include_icvc.sch")
        # case_file_path = Path(base_folder / "case_icvc.case")

        summary_file_path.unlink(missing_ok=True)
        self.include_file_path.unlink(missing_ok=True)
        # case_file_path.unlink(missing_ok=True)

        content = self.add_section_header(self.initials.init_icvcontrol, "INIT")
        self.append_content_to_file(self.include_file_path, content)

        content = self.add_section_header(self.initials.input_icvcontrol, "INPUT")
        self.append_content_to_file(self.include_file_path, content)

        content = self.add_section_header(self.initials.summary, "SUMMARY")
        self.append_content_to_file(summary_file_path, content)
        logger.info(f"Created summary file: '{summary_file_path}'.")

        content = self.add_section_header(content, f"Completor version: {get_version()}")
        # self.append_content_to_file(case_file_path, content)

        for icv_name in self.initials.icv_names:
            well_name = self.initials.well_names[icv_name]
            icv_date = self.initials.icv_dates[icv_name]

            for file_type in [ICVMethod.CHOKE_WAIT, ICVMethod.CHOKE, ICVMethod.OPEN_WAIT, ICVMethod.OPEN]:
                if (
                    self.icv_functions.custom_conditions is not None
                    and file_type in self.icv_functions.custom_conditions
                    and icv_name in self.icv_functions.custom_conditions[file_type]
                ):
                    custom_criteria = self.icv_functions.custom_conditions[file_type][icv_name].keys()
                    for criteria in custom_criteria:
                        if criteria != "map":
                            self.append_control_criteria_to_file(
                                self.include_file_path, well_name, icv_name, file_type, icv_date, criteria
                            )
                else:
                    logger.warning(
                        f"No criteria found for well '{well_name}' icv '{icv_name}' " f"function '{file_type}'."
                    )
                    self.append_control_criteria_to_file(
                        self.include_file_path, well_name, icv_name, file_type, icv_date, None
                    )
        logger.info(f"Created include file: '{self.include_file_path}'.")

    def create_main_schedule_file(self, input_schedule: Path):
        """Creates the main output schedule file from the input schedule file.

        Args:
            input_schedule: Input schedule file name.

        """
        main_schedule_file = Path(self.output_directory / self.output_file_name)

        dates = [datetime.datetime.strptime(d, "%d %b %Y") for d in set(self.initials.icv_dates.values())]
        with open(input_schedule, encoding="utf-8") as fh:
            sch_files = fh.readlines()
        for index, line in enumerate(sch_files):
            line = " ".join(line.split())
            if "DATES" in line:
                sch_files[index] = line.replace("DATES\n", "DATES \n")

        sch_data = "".join(sch_files).split("DATES")
        sch_data_before_date = sch_data[0]
        sch_data_after_first_date, date_comment = format_date(sch_data[1:])
        for date in sch_data_after_first_date:
            try:
                dates.append(datetime.datetime.strptime(date, "%d %b %Y %H %M %S"))
            except ValueError:
                dates.append(datetime.datetime.strptime(date, "%d %b %Y"))
        sorted_dates = []
        # Sort dates chronologically and remove duplicate date entries.
        for date in sorted(set(dates)):
            # When the timestamp is zero, the timestamp is not written.
            if date.hour == 0 and date.minute == 0 and date.second == 0:
                sorted_dates.append(date.strftime("%d %b %Y").upper())
            else:
                sorted_dates.append(date.strftime("%d %b %Y %H:%M:%S").upper())

        lines_path_to_include = list(sch_data_before_date)
        lines_path = self.format_sch_file(sorted_dates, sch_data_after_first_date, date_comment)
        lines_path_to_include += lines_path
        main_schedule_lines = [line.replace("//", "/") for line in lines_path_to_include]

        with open(main_schedule_file, "w", encoding="utf-8") as file:
            file.write("".join(main_schedule_lines))
        logger.info(f"Created main schedule file: '{main_schedule_file}'.")

    def format_sch_file(
        self, sorted_dates: list[str], sch_data_after_first_date: dict[str, str], date_comment: dict[str, str]
    ) -> list[str]:
        """
        Formats the SCH file by including relevant paths and
        content based on sorted dates and SCH data.

        Args:
            sorted_dates: A list of sorted dates.
            sch_data_after_first_date: Containing SCH data after the first date.

        Returns:
            lines_path_to_include: Formatted paths to include in the SCH file.

        """
        lines_path_to_include = []
        base_include = "INCLUDE\n"

        for icvdate in sorted_dates:
            try:
                lines_path_to_include.append(f"DATES\n {icvdate} /{date_comment[icvdate]}\n/\n")
            except KeyError:
                lines_path_to_include.append(f"DATES\n {icvdate} /\n/\n")
            try:
                # Append content from SCH file after the first date.
                lines_path_to_include.append(sch_data_after_first_date[icvdate].strip() + "\n\n")
            except KeyError:
                # Skip if SCH data for the icvdate is not found.
                pass
            try:
                self.ordered_filenames[icvdate].keys()
            except KeyError:
                continue
            # The includes of 'init.udq' and 'input.udq' should be placed close to the
            # include 'well' statement.
            lines_path_to_include.append(f"{base_include} '{self.schedule_include_file_path}' /\n\n".replace("//", "/"))
        return lines_path_to_include


def format_date(date_contents: list) -> tuple[dict, dict]:
    """
    This function takes a list of dates in the format "day/month/year time" or
    "day/month/year" and returns a dictionary of the formatted dates as keys and
    the corresponding schedule data as values.

    Args:
        sch_dates: List of strings representing dates and schedule data.

    Returns:
        sch_data: Dictionary with keys as formatted dates and values as schedule data.

    Raises:
        ValueError: if the input date string is not in the format of
            "day/month/year time" or "day/month/year".

    """
    formatted_data = {}
    date_comment = {}
    # iterate over the list of schedule dates
    for date_content in date_contents:
        if date_content:
            date_line, content = date_content.split("\n", 1)
            date, comment = date_line.split("/", 1)
            comment = comment.lstrip()
            date = date.strip()
            if comment:
                comment = " " + comment
            if content.lstrip().startswith("/"):
                content = content.replace("/", "", 1)
            # Remove special characters from the date string, replacing "JLY" with "JUL"
            date_formated = re.sub(r"[^a-zA-Z0-9]", " ", date).strip()
            date_formated = date_formated.replace("JLY", "JUL")
            try:
                # Try to parse the date using the expected format
                date = datetime.datetime.strptime(date_formated, "%d %b %Y %H %M %S")
            except ValueError:
                try:
                    date = datetime.datetime.strptime(date_formated, "%d %b %Y")
                except ValueError:
                    try:
                        date = datetime.datetime.strptime(date_formated, "%d%b%Y")
                    except ValueError:
                        logger.warning(
                            "Date format seems to be wrong in the schedule file.\n"
                            "Format: 1 JAN 2030. The day is an integer between 1-31.\n"
                            "The months are JAN, FEB, MAR, APR, MAY, JUN, JLY/JUL, "
                            "AUG, SEP, OCT, NOV or DEC.\nThe year is a 4 digit integer."
                            f" See line that states:'{date}'."
                        )
        try:
            if date.hour == 0 and date.minute == 0 and date.second == 0:
                date = date.strftime("%d %b %Y").upper()
            else:
                date = date.strftime("%d %b %Y %H %M %S").upper()
        except AttributeError:
            logger.warning(f"Something wrong in the date format in line: {date}")
        formatted_data[date] = content
        date_comment[date] = comment
    return formatted_data, date_comment
