"""Class to import user data and initialize the icv-control algorithm"""

from __future__ import annotations

import datetime
import re

import pandas as pd

from completor.constants import ICVMethod
from completor.logger import logger
from completor.read_casefile import ICVReadCasefile
from completor.utils import insert_comment_custom_content, reduce_newlines, remove_duplicates

FUTSTP_INIT = 0
FUTO_INIT = 0
FUTC_INIT = 0
FUP_INIT = 2


class Initialization:
    """Initializes dicts for easy access. Creates the INPUT and UDQDEFINE files."""

    def __init__(self, case_object: ICVReadCasefile, schedule_content: str = ""):
        self.case = case_object
        self.schedule_content = schedule_content
        self.icv_control_table = case_object.icv_control_table

        self.custom_conditions = case_object.custom_conditions
        self.find_icv_names()
        self.find_well_names()
        self.find_segments()
        self.find_opening_init()
        self.find_areas()
        self.find_steps()
        self.find_frequency()
        self.find_icv_dates()
        self.check_dates_in_wells()
        self.find_icvs_per_well()
        self.create_init_icvcontrol()
        self.create_input_icvcontrol()
        self.create_summary_content()

    def get_props(self, icv_date: datetime, icv_name: str, property: str) -> str | int | float:
        """Get function for properties in the ICVCONTROL table.

        Args:
            icv_date: Date for an update in icv properties.
            icv_name: Icv name. A letter from A through Z.
            property: Property to be obtained from the ICVCONTROL table.

        Returns:
            An ICVCONTROL table property at a given date and for a given icv_name.
        """
        temp1 = self.icv_control_table[self.icv_control_table["ICVDATE"] == icv_date]
        temp2 = temp1[temp1["ICV"] == icv_name]
        return temp2[property].iloc[0]

    def find_icv_names(self):
        """Find unique icv names in the case file ICVCONTROL keyword."""
        self.icv_names = self.icv_control_table["ICV"].unique()

    def find_well_names(self):
        """Find unique active well names in the case file ICVCONTROL keyword."""

        self.well_names = {}
        for icv_name in self.icv_names:
            self.well_names[icv_name] = self.icv_control_table[self.icv_control_table["ICV"] == icv_name]["WELL"].iloc[
                0
            ]

        self.well_names_unique = list(set(self.well_names.values()))

    def find_icvs_per_well(self):
        """Find the number of unique valves pr well."""

        self.icvs_per_well = {}
        counted_icv_names = []
        icv_well_combo = {}
        for icv_name in self.icv_names:
            if self.well_names[icv_name] not in self.icvs_per_well.keys():
                self.icvs_per_well[self.well_names[icv_name]] = 1
                counted_icv_names.append(icv_name)
                icv_well_combo.update({icv_name: self.icvs_per_well[self.well_names[icv_name]]})
            if icv_name not in counted_icv_names:
                self.icvs_per_well[self.well_names[icv_name]] += 1
                counted_icv_names.append(icv_name)
                icv_well_combo.update({icv_name: self.icvs_per_well[self.well_names[icv_name]]})
        self.icv_well_combo = icv_well_combo

    def find_segments(self):
        """Find segment number associated with each icv."""

        self.segments = {}
        for icv_name in self.icv_names:
            self.segments[icv_name] = self.icv_control_table[self.icv_control_table["ICV"] == icv_name]["SEGMENT"].iloc[
                0
            ]

    def find_areas(self):
        """Find unique icv areas in the case file ICVCONTROL keyword."""
        self.areas = {}
        for icv_name in self.icv_names:
            self.areas[icv_name] = self.icv_control_table[self.icv_control_table["ICV"] == icv_name]["AC-TABLE"].iloc[0]

    def find_steps(self):
        """Find opersteps and waitsteps in the case file ICVCONTROL keyword."""

        self.operation_step = {}
        self.wait_step = {}
        for icv_name in self.icv_names:
            self.operation_step[icv_name] = self.icv_control_table[self.icv_control_table["ICV"] == icv_name][
                "OPERSTEP"
            ].iloc[0]
            self.wait_step[icv_name] = self.icv_control_table[self.icv_control_table["ICV"] == icv_name][
                "WAITSTEP"
            ].iloc[0]

    def find_opening_init(self):
        self.init_opening = {}
        # Add another column for table name`?`
        for icv_name in self.icv_names:
            self.init_opening[icv_name] = self.icv_control_table[self.icv_control_table["ICV"] == icv_name][
                "OPENING"
            ].iloc[0]

    def find_frequency(self):
        """Find unique icv frequency in the case file ICVCONTROL keyword."""

        self.frequency = {}
        for icv_name in self.icv_names:
            self.frequency[icv_name] = self.icv_control_table[self.icv_control_table["ICV"] == icv_name]["FREQ"].iloc[0]

    def find_icv_dates(self):
        """Find icv_dates in the case file ICVCONTROL keyword.

        Note that this approach reserves icv names such as A and A2 for the first and
        second appearance of icv A at dates number 1 and 2 in the ICVCONTROL table.
        Similarly, B, B2 and B3 are reserved for the first, second and third appearance
        of the icv B. All three appearances have distinct icv dates.
        """

        self.icv_dates = {}
        for icv_name in self.icv_names:
            # Get the ICVDATE for the current icv name
            tmp_date = self.icv_control_table[self.icv_control_table["ICV"] == icv_name]["ICVDATE"]
            # Convert the date string to a datetime object
            tmp = datetime.datetime.strptime(tmp_date.iloc[0], "%d.%b.%Y").date()
            # Format the datetime object as a string in the desired format: 01.JAN.1970
            tmp = tmp.strftime("%d %b %Y").upper()
            # Replace the first occurrence of the original date with the formatted date
            # It is replaced and not set to avoid pandas warnings.
            tmp_date = tmp_date.replace([0, tmp_date.iloc[0]], [0, tmp])
            if len(tmp_date) == 1:  # If there is only one date for the icv name
                self.icv_dates[icv_name] = tmp_date.iloc[0]
            else:  # If there are multiple dates for the icv name
                self.icv_dates[icv_name] = tmp_date.iloc[0]
                for idx in range(1, len(tmp_date)):
                    self.icv_dates[icv_name + str(idx + 1)] = tmp_date.iloc[idx]

    def check_dates_in_wells(self) -> None:
        """
        Check if different ICV dates have been entered for ICVs placed on the same well.

        This method iterates through the well names and ICV names in the
        `well_names` dictionary and checks if different ICV dates have been
        assigned to ICVs placed on the same well.
        """
        well_dates = {}
        for well in set(self.well_names.values()):
            well_dates[well] = {}
            for icv_name in self.well_names:
                if well == self.well_names[icv_name]:
                    well_dates[well][icv_name] = self.icv_dates[icv_name]
            if len(set(well_dates[well].values())) > 1:
                logger.warning(
                    "Different ICVDATE has been entered for ICVs placed on the same "
                    f"well. Well {well} got several dates. See {well_dates[well]}."
                )

    def number_of_icvs(self, icv_name: str) -> tuple[int, str | None]:
        """Finds the number of icvs in the well from an input icv_name.

        Args:
            icv_name: Letter from A through ZZ

        Returns:
            The number of icvs in the current well.

        """
        number_of_icvs = 0
        for icv in self.icv_names:
            if self.well_names[icv] == self.well_names[icv_name]:
                number_of_icvs += 1
        if number_of_icvs > 26:
            raise ValueError("Not more than twenty-six valves per well")
        return number_of_icvs

    def create_init_icvcontrol(self):
        """Create content of the init_icvcontrol.udq file.

        Returns:
            Content of the init_icvcontrol.udq icv-control file.

        """
        init_icvcontrol = "-- User input, specific for this input file\n\nUDQ\n\n" f"{60 * '-'}\n-- Time-stepping:\n\n"
        for icv_name in self.icv_names:
            table = {
                "FUD": self.icv_control_table[self.icv_control_table["ICV"] == icv_name]["FUD"].iloc[0],
                "FUH": self.icv_control_table[self.icv_control_table["ICV"] == icv_name]["FUH"].iloc[0],
                "FUL": self.icv_control_table[self.icv_control_table["ICV"] == icv_name]["FUL"].iloc[0],
            }
            for tstepping in ["FUD", "FUH", "FUL"]:
                init_icvcontrol += f"  ASSIGN {tstepping}_{icv_name} {table[tstepping]} /\n"

            init_icvcontrol += "\n"
        init_icvcontrol += f"\n{60 * '-'}\n-- Balance criteria\n\n"
        sub_table = {}
        for icv_name, icv_date in self.icv_dates.items():
            if "na" in icv_name.lower():
                raise ValueError("Python reads NA as NaN, thus ICV name cannot be NA!")
            if icv_date not in sub_table:
                sub_table[icv_date] = {}
            if icv_name not in sub_table[icv_date]:
                sub_table[icv_date][icv_name] = []
        for _ in sub_table:
            for icv_name in self.icv_names:
                init_icvcontrol += (
                    f"\n  ASSIGN FUTC_{icv_name} {FUTC_INIT} /\n"
                    f"  ASSIGN FUTO_{icv_name} {FUTO_INIT} /\n"
                    f"  ASSIGN FUP_{icv_name} {FUP_INIT} /\n"
                )
        init_icvcontrol += "/\n"

        if self.case.icv_table:
            init_icvcontrol += self.input_icv_opening_table(self.case.icv_table)
        else:
            logger.info("No ICVTABLES found, skipping writing table to init_icvcontrol.udq!")

        self.init_icvcontrol = init_icvcontrol

    def input_icv_opening_table(self, icv_tables: dict[str, pd.DataFrame]) -> str:
        """Create the opening position tables content for init_icvcontrol.udq for
        icv-control.

        Args:
            Icv opening tables.

        Returns:
            Updated contents of init_icvcontrol.udq.

        """
        icv_table_text = "\n\n" + 60 * "-" + "\n-- ICV opening position tables\n"
        for key, value in icv_tables.items():
            icv_table_text += "UDT\n-- ICV"
            for icv, table in self.areas.items():
                if key == table:
                    icv_table_text += f"  {icv}"
            icv_table_text += f"\n  'TU_{key}' 1 /\n"
            if len(key) > 5:
                logger.warning(
                    f"The table name '{key}' is longer than 5 characters. "
                    "This will create a UDT name longer than 8 characters which causes error in Eclipse."
                )

            position = " ".join(str(x) for x in value["POSITION"])
            icv_table_text += f"  'NV' {position} /\n"
            area = value["CV"] * value["AREA"]
            formatted_area = [
                f"{float(array_value):.3e}" for array_value in area
            ]  # put everything as scientific with 3 decimals
            icv_table_text += f"  {' '.join(formatted_area)} /\n  /\n/\n\n"
        return icv_table_text

    def create_input_icvcontrol(self):
        """Create the content of the input_icvcontrol.udq file for icv-control.

        Returns:
            Content of the input_icvcontrol.udq icv-control file.

        """

        futstp_init = 0
        udq_define = "UDQ\n\n-- Initialization\n\n"
        custom_fu_lines = "\n"
        input_lines = "\n"
        fufrq_lines = ""
        fut_lines = "\n"
        custom_content = None
        icv_function = ICVMethod.UDQ
        futstp_line = f"  ASSIGN FUTSTP {futstp_init} /\n"
        for icv_name in self.icv_names:
            try:
                fully_choked = self.case.min_table[icv_name][0]
                fully_opened = self.case.max_table[icv_name][0]
            except KeyError:
                fully_choked = self.case.min_table[icv_name].iloc[0][0]
                fully_opened = self.case.max_table[icv_name].iloc[0][0]
            input_lines += f"  ASSIGN FUCH_{icv_name} {fully_choked} /\n"
            input_lines += f"  ASSIGN FUOP_{icv_name} {fully_opened} /\n\n"
            fufrq_lines += f"  ASSIGN FUFRQ_{icv_name} {self.frequency[icv_name]} /\n"
            fut_lines += f"  ASSIGN FUT_{icv_name} {self.frequency[icv_name]} /\n"
            custom_assignments = self._find_and_assign(icv_name, icv_function)
            if custom_assignments:
                custom_fu_lines += custom_assignments + "\n"

            define_lines = "-- Definition of parameters,\n-- continuously updated:\n\n  DEFINE FUTSTP TIMESTEP /\n"
            for icv_name in self.icv_names:
                define_lines += f"  DEFINE FUT_{icv_name} FUT_{icv_name} + TIMESTEP /\n"
            define_lines += "\n"
            for icv_name in self.icv_names:
                custom_content = self.get_custom_content(icv_name, icv_function, 1, False)

                if custom_content is None:
                    define_lines += ""
                    logger.debug(f"No ICVALGORITHM given for icv {icv_name}.")
                else:
                    define_lines += custom_content
        if custom_content is not None:
            if self.custom_conditions.get(icv_function).get("UDQ") is not None:
                content = self.custom_conditions.get(icv_function).get("UDQ").get("1")
                content = [f"  {line.strip()}\n" for line in content.splitlines()]
                for index, line in enumerate(content):
                    content[index] = re.sub(r"[^\w\)]*$", "", line) + " /\n"
                content = "".join(content)
                define_lines += content
                if "ASSIGN" not in content:
                    logger.warning(
                        "When you define a custom UDQ without an ICV remember "
                        f"to assign every values. See ICVALGORITHM UDQ {content}"
                    )
        area_lines = "\n"
        if self.case.icv_table:
            fu_pos, fu_area = self.assign_fupos_from_opening_table()
            area_lines = fu_pos + fu_area

        for icv_name in self.icv_names:
            number = re.sub(r"[^A-Za-z_-]", "", self.areas[icv_name])
            if number in ["", "E", "E-", "E+"]:
                try:
                    init_opening_value = self.case.init_opening_table[icv_name][0]
                    if init_opening_value[0] == "T":
                        raise ValueError(
                            f"Table was reference in the case file for ICV {icv_name}, but no table was found."
                        )
                except KeyError:
                    pass
                if self.areas[icv_name] != "0":
                    area = self.areas[icv_name]
                else:
                    area = self.icv_control_table[self.icv_control_table["ICV"] == icv_name]["AREA"].iloc[0]
                area_lines += f"  ASSIGN FUARE_{icv_name} {area} /\n"
        udq_define += (
            fufrq_lines + fut_lines + input_lines + futstp_line + custom_fu_lines + define_lines + area_lines + "/"
        )
        udq_define = reduce_newlines(udq_define)

        self.input_icvcontrol = udq_define

    def assign_fupos_from_opening_table(self) -> tuple[str, str]:
        """Assign FUPOS_ICV to the max position of that ICV.

        Returns:

            Updated UDQDEFINE withst
            FUPOS_ICV,
            DEFINE _FUARE_ICV
        """
        fu_pos = "\n"
        fu_area = "\n"
        for icv, value in self.areas.items():
            table_name = re.sub(r"[^A-Za-z_-]", "", value)
            init_opening_value = self.init_opening[icv]
            if init_opening_value[0] == "T":
                position = re.sub("[^0-9]", "", init_opening_value)
            elif float(init_opening_value) == 0 and table_name not in ["", "E"]:
                position = self.case.icv_table[value]["POSITION"].max()
            elif float(init_opening_value) != 0 and table_name not in ["", "E"]:
                raise ValueError(
                    "Seems like you refer to a table, but have an opening value. "
                    f"See ICV '{icv}' with AC-Table '{table_name}' and opening "
                    f"value {init_opening_value}."
                )

            else:
                continue
            fu_pos += f"  DEFINE FUPOS_{icv} {position} /\n"
            fu_area += f"  DEFINE FUARE_{icv} TU_{value}[FUPOS_{icv}] /\n"
        return fu_pos, fu_area

    def create_summary_content(self):
        """Create the content of the summary file for icv-control.

        Returns:
            Content of the summary icv-control file.

        """
        fu_lines = ""
        fuarea_lines = ""
        fut_lines = ""

        for icv_name in self.icv_names:
            fus = ["FUP", "FUTC", "FUTO"]
            for fu in fus:
                fu_lines += f"{fu}_{icv_name}\n\n"
            fuarea_lines += f"FUARE_{icv_name}\n\n"
            fut_lines += f"FUT_{icv_name}\n\n"
        # Positive look-behind to check word is preceded by ASSIGN/DEFINE
        assigns = re.findall(r"(?<=ASSIGN\s)\w+", self.input_icvcontrol)
        defines = re.findall(r"(?<=DEFINE\s)\w+", self.input_icvcontrol)
        summary_values = assigns + defines + fu_lines.splitlines()
        summary_values = remove_duplicates(summary_values)
        summary = ""
        for value in summary_values:
            if len(value) > 8:
                raise ValueError(
                    f"The UDQ parameter '{value}' is longer than 8 characters. This will cause errors in Eclipse."
                )
            summary += value + "\n\n"
        sfopn_lines = "SFOPN\n"
        well_segment = ""
        for icv, well in self.well_names.items():
            well_segment += f"'{well}' {self.segments[icv]} /\n"
        well_segment += "/\n\n"
        sfopn_lines += well_segment
        self.summary = summary + sfopn_lines

    def parse_custom_content(self, current_icv: str, custom_data: dict, content: str, is_end_of_records=True) -> str:
        """Replace variables in custom content with their respective values.

        E.g.
            WELL(x)             ->  WellName
            FURATE_x > FURATE_y ->  FURATE_A > FURATE_B
            FU_x1, FU_x2, FU_z  ->  FU_E, FU_F, FU_G

        Args:
            current_icv: Letter denoting the current icv name.
            content: The content where unknowns
                should be replaced with correct info.
            is_end_of_records: If true add extra slash newline to
                end the records.

        Returns:
            The content with replaced icvs/wells/segments.

        """
        if content is None:
            return ""
        for criteria in custom_data[current_icv]["map"]:
            if criteria == "map":
                pass
            if isinstance(content, dict):
                content = custom_data[current_icv][criteria]
            if re.search(r"\d|\w", content) is None:
                raise ValueError("Missing content in CONTROL_CRITERIA keyword!")
            if current_icv != "UDQ":
                for x_value, icv in custom_data[current_icv]["map"][criteria].items():
                    content = re.sub(rf"WELL\({x_value}\)", f"'{self.well_names[icv]}'", content)
                    content = re.sub(rf"SEG\({x_value}\)", str(self.segments[icv]), content)
                    content = re.sub(rf"\_{x_value}\b", f"_{icv}", content)
            if current_icv != "UDQ":
                for x_value, icv in custom_data[current_icv]["map"][criteria].items():
                    content = re.sub(rf"WELL\({x_value}\)", f"'{self.well_names[icv]}'", content)
                    content = re.sub(rf"SEG\({x_value}\)", str(self.segments[icv]), content)
                    content = re.sub(rf"\_{x_value}\b", f"_{icv}", content)
            # Replace inconsistent end records and space with consistent version
            content = [f"  {line.strip()}\n" for line in content.splitlines()]
            for index, line in enumerate(content):
                if not line.isspace():
                    # Remove trailing non-word characters unless they are ) or ' at word boundary
                    content[index] = re.sub(r"(?:\B'|[^\w\)'])*$", "", line) + " /\n"
                else:
                    content[index] = ""
            content = "".join(content)
        content_variables = re.findall(r"[x]\d", content)
        if content_variables != []:
            logger.info(
                f"ICVALGORITHM ICV {current_icv} criteria {criteria} "
                f"contains an x value '{content_variables}' that did not "
                f"get translated into an ICV-name.\nCustom criteria is: {content}."
            )
        if is_end_of_records:
            return f"{insert_comment_custom_content()}{content}/\n"
        return f"{insert_comment_custom_content()}{content}"

    def get_custom_content(
        self, icv_name: str, icv_function: ICVMethod, criteria: int | str, is_end_of_records: bool = True
    ) -> tuple[str | None, list[int]]:
        """Helper method to get correct custom content.

        Args:
            icv_name: Current ICV.
            icv_function: The ICVMethod type calling this function.

        Returns:
            The custom content and criteria (if any), for the current ICV.

        """
        custom_content = None
        if self.custom_conditions is not None:
            custom_data = self.custom_conditions.get(icv_function)
            if custom_data is not None:
                if icv_function != ICVMethod.UDQ:
                    custom_content = ""
                    for icv in custom_data:
                        data = custom_data[icv].get(str(criteria))
                        if icv_name == icv.split()[0]:
                            custom_content += self.parse_custom_content(icv, custom_data, data, is_end_of_records)
                if icv_name in custom_data:
                    data = custom_data[icv_name].get(str(criteria))
                    if data is None:
                        return None
                    else:
                        custom_content = self.parse_custom_content(icv_name, custom_data, data, is_end_of_records)
                if icv_function == ICVMethod.UDQ:
                    custom_content = ""
                    for icv in custom_data:
                        if icv == "UDQ":
                            data = custom_data["UDQ"]
                        else:
                            data = custom_data[icv].get(str(criteria))
                        if icv_name == icv.split()[0]:
                            custom_content += self.parse_custom_content(icv, custom_data, data, is_end_of_records)
        return custom_content

    def _find_and_assign(self, icv_name: str, icv_function: ICVMethod = ICVMethod.UDQ) -> str | None:
        """Helper method to find all define statements in custom content to
        replace the 'DEFINE' statement with 'ASSIGN'.

        Args:
            icv_name: Current icv name.
            icv_function: The icv method (typically ICVMethod.UDQ).

        Returns:
            All statements that are defined processed into assign-statements.

        """
        custom_content = self.get_custom_content(icv_name, icv_function, 1, False)
        if custom_content is None:
            return None
        # Find all DEFINE some_word matches in text
        defines = [match for match, _ in re.findall(r"(\b(DEFINE)\s+\b\w+\b)", custom_content)]
        # Replace DEFINE with ASSIGN, and prepare format for writing to UDQDEFINE file.
        init_value = {}
        icvs_in_define = [line.split("_")[1] for line in defines]
        assigns = ""
        for current_icv in icvs_in_define:
            try:
                init_value[current_icv] = self.case.init_table[current_icv][0]
            except KeyError:
                init_value[current_icv] = self.case.init_table[current_icv].iloc[0][0]

        for match in defines:
            icv = icv_name
            if match[-1] in icvs_in_define:
                icv = match[-1]
            assigns += f"  {re.sub(r'(DEFINE)', 'ASSIGN', match)} {init_value[icv]} /\n"

        return assigns
