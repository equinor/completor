"""Class to import user data and initialize the icv-control algorithm"""

from __future__ import annotations

import re
from datetime import datetime

import pandas as pd

from completor.constants import ICVMethod
from completor.logger import logger
from completor.read_casefile import ICVReadCasefile
from completor.utils import insert_comment_custom_content, reduce_newlines, remove_duplicates

FUTSTP_INIT = 0
FUTO_INIT = 0
FUTC_INIT = 0
FUP_INIT = 2


class InitializationPyaction:
    """Initializes dicts for easy access. Creates the INPUT and UDQDEFINE files."""

    def __init__(self, case_object: ICVReadCasefile, schedule_content: str | None = None):
        self.case = case_object

        if schedule_content is None:
            schedule_content = ""

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
            tmp = datetime.strptime(tmp_date.iloc[0], "%d.%b.%Y").date()
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
        well_dates: dict[str, dict[str, str]] = {}
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

    def number_of_icvs(self, icv_name: str) -> int:
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
            Content of the init.py icv-control file.

        """
        init_icvcontrol_pyaction = """
#
# OPM Flow PYACTION Module Script
#

import pandas as pd

import opm_embedded

ecl_state = opm_embedded.current_ecl_state
schedule = opm_embedded.current_schedule
report_step = opm_embedded.current_report_step
summary_state = opm_embedded.current_summary_state

if (not 'setup_done' in locals()):
    executed = False
    setup_done = True

# Time-stepping:

"""
        for icv_name in self.icv_names:
            table = {
                "FUD": self.icv_control_table[self.icv_control_table["ICV"] == icv_name]["FUD"].iloc[0],
                "FUH": self.icv_control_table[self.icv_control_table["ICV"] == icv_name]["FUH"].iloc[0],
                "FUL": self.icv_control_table[self.icv_control_table["ICV"] == icv_name]["FUL"].iloc[0],
            }
            for tstepping in ["FUD", "FUH", "FUL"]:
                init_icvcontrol_pyaction += f"summary_state['{tstepping}_{icv_name}'] = {table[tstepping]}\n"

            init_icvcontrol_pyaction += "\n"
        init_icvcontrol_pyaction += "# Balance criteria\n\n"
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
                init_icvcontrol_pyaction += (
                    f"summary_state['FUTC_{icv_name}'] = {FUTC_INIT}\n"
                    f"summary_state['FUTO_{icv_name}'] = {FUTO_INIT}\n"
                    f"summary_state['FUP_{icv_name}'] = {FUP_INIT}\n"
                )
        init_icvcontrol_pyaction += "\n\n"
        for icv_name in self.icv_names:
            try:
                fully_choked = self.case.min_table[icv_name][0]
                fully_opened = self.case.max_table[icv_name][0]
            except KeyError:
                fully_choked = self.case.min_table[icv_name].iloc[0][0]
                fully_opened = self.case.max_table[icv_name].iloc[0][0]

            init_icvcontrol_pyaction += f"summary_state['FUCH_{icv_name}'] = {fully_choked}\n"
            init_icvcontrol_pyaction += f"summary_state['FUOP_{icv_name}'] = {fully_opened}\n\n"
            init_icvcontrol_pyaction += f"summary_state['FUFRQ_{icv_name}'] = {self.frequency[icv_name]}\n"
            init_icvcontrol_pyaction += f"summary_state['FUT_{icv_name}'] = {self.frequency[icv_name]}\n"
        if self.case.icv_table:
            fu_pos, fu_area = self.assign_fupos_from_opening_table()
            init_icvcontrol_pyaction += fu_pos + "\n"
        else:
            logger.info("No ICVTABLES found, skipping writing table to init_icvcontrol.udq!")
        self.init_icvcontrol = init_icvcontrol_pyaction

    def input_icv_opening_table(self, icv_tables: dict[str, pd.DataFrame]) -> str:
        """Create the opening position tables content for init_icvcontrol.udq for
        icv-control.

        Args:
            Icv opening tables.

        Returns:
            Updated contents of include.py.

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

    def input_icv_opening_table_pyaction(self, icv_tables: dict[str, pd.DataFrame]) -> str:
        """Create the opening position tables content for init_icvcontrol.udq for
        icv-control.

        Args:
            Icv opening tables.

        Returns:
            Updated contents of init_icvcontrol with table for pyaction.

        """
        icv_table_text_pyaction = "# ICV opening position tables as dataframe\n"
        for key, value in icv_tables.items():
            icv_table_text_pyaction += f"# Table {key} for ICV"
            for icv, table in self.areas.items():
                if key == table:
                    icv_table_text_pyaction += f"  {icv}"
            icv_table_text_pyaction += "\n"
            position = value["POSITION"]
            area = value["CV"] * value["AREA"]
            # Create flow_trim list with formatted area values
            flow_trim = []
            for pos, ar in zip(position, area):
                flow_trim.append([pos, 1, f"{float(ar):.3e}"])

            # Format flow_trim as text output
            flow_trim_text = ""
            for row in flow_trim:
                flow_trim_text += f"    [{row[0]}, {row[1]}, {row[2]}],\n"
            icv_table_text_pyaction += f"flow_trim_{key} = [\n{flow_trim_text}]\n"
        return icv_table_text_pyaction

    def create_input_icvcontrol(self):
        """Create the content of the input_icvcontrol.udq file for icv-control.

        Returns:
            Content of the include.py icv-control file.

        """

        custom_fu_lines = "\n"
        custom_content = None
        icv_function = ICVMethod.UDQ
        udq_define_pyaction = "# Input for ICV Control in summary state\n\n"
        udq_define_pyaction += """
#
# OPM Flow PYACTION Module Script
#

import pandas as pd

import opm_embedded

ecl_state = opm_embedded.current_ecl_state
schedule = opm_embedded.current_schedule
report_step = opm_embedded.current_report_step
summary_state = opm_embedded.current_summary_state

if (not 'setup_done' in locals()):
    executed = False
    setup_done = True

# Time-stepping:


"""
        custom_content_pyaction = None
        for icv_name in self.icv_names:
            custom_assignments = self._find_and_assign(icv_name, icv_function)
            custom_content_pyaction = ""

            if custom_assignments:
                custom_fu_lines += custom_assignments + "\n"

            define_lines_pyaction = "# Continuously updated summary state \n\n"
            for icv_name in self.icv_names:
                define_lines_pyaction += f"summary_state['FUT_{icv_name}'] += summary_state['TIMESTEP']\n\n"
            for icv_name in self.icv_names:
                if self.case.python_dependent:
                    custom_content_pyaction = self.get_custom_content(icv_name, icv_function, 1, False)
                custom_content = self.get_custom_content(icv_name, icv_function, 1, False)

                if custom_content is None:
                    logger.debug(f"No ICVALGORITHM given for icv {icv_name}.")
                else:
                    define_lines_pyaction += custom_content_pyaction
        if custom_content is not None:
            if self.custom_conditions.get(icv_function).get("UDQ") is not None:
                content = self.custom_conditions.get(icv_function).get("UDQ").get("1")
                content = [f"  {line.strip()}\n" for line in content.splitlines()]
                content_summary_state = []
                for index, line in enumerate(content):
                    content[index] = re.sub(r"[^\w\)]*$", "", line) + " /\n"
                    if "DEFINE" in line:
                        content_summary_state.append(self._define_to_pyaction(line))
                    elif "ASSIGN" in line:
                        content_summary_state.append(self._assign_to_pyaction(line))
                content_summary_state = "".join(content_summary_state)
                define_lines_pyaction += content_summary_state
                if "ASSIGN" not in content:
                    logger.warning(
                        "When you define a custom UDQ without an ICV remember "
                        f"to assign every values. See ICVALGORITHM UDQ {content}"
                    )
        area_lines_pyaction = """
def get_area_by_index(index, table):
    for row in table:
        if row[0] == index:
            return row[2]
    return None
"""

        if self.case.icv_table:
            fu_pos, fu_area = self.assign_fupos_from_opening_table()
            area_lines_pyaction += self.input_icv_opening_table_pyaction(self.case.icv_table)
            area_lines_pyaction += fu_area

        create_fixed_pyaction_keyword = create_fixed_pyaction_keyword = """
keyword_1day = f"NEXTSTEP\\n  1.0 / \\n"
keyword_01day = f"NEXTSTEP\\n  0.1 / \\n"
keyword_2day = f"NEXTSTEP\\n  2.0 / \\n"
"""

        udq_define_pyaction += (
            custom_fu_lines
            + define_lines_pyaction
            + area_lines_pyaction
            + create_fixed_pyaction_keyword
        )
        udq_define_pyaction = reduce_newlines(udq_define_pyaction)
        self.input_icvcontrol = udq_define_pyaction

    def assign_fupos_from_opening_table(self) -> tuple[str, str]:
        """Assign FUPOS_ICV to the max position of that ICV.

        Returns:

            Updated UDQDEFINE withst
            FUPOS_ICV,
            DEFINE _FUARE_ICV
        """
        fu_pos_pyaction = "\n"
        fu_area_pyaction = "\n"
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
            fu_pos_pyaction += f"summary_state['FUPOS_{icv}'] = {position}\n"
            fu_area_pyaction += f"""
summary_state['FUARE_{icv}'] = get_area_by_index(summary_state['FUPOS_{icv}'], flow_trim_{table_name})
            """
        return fu_pos_pyaction, fu_area_pyaction


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
        summary_state = re.findall(r"summary_state\['(\w+)'\]", self.init_icvcontrol)
        summary_state += re.findall(r"summary_state\['(\w+)'\]", self.input_icvcontrol)
        summary_values = summary_state + fu_lines.splitlines()
        summary_values = remove_duplicates(summary_values)
        summary = ""
        for value in summary_values:
            if len(value) > 8:
                raise ValueError(
                    f"The UDQ parameter '{value}' is longer than 8 characters. This will cause errors in Eclipse."
                )
            summary += value + "\n\n"
        
        self.summary = summary

    def _assign_to_pyaction(self, assign_text: str) -> str:
        """Convert ASSIGN lines into pyaction summary_state assignments.

        Example:
          "ASSIGN FUXXX 0.1 /\nASSIGN FUBAR 2.5 /\n"
        -> "summary_state['FUXXX'] = 0.1\nsummary_state['FUBAR'] = 2.5\n"

        Args:
            assign_text: Text containing ASSIGN statements.

        Returns:
            Pyaction format assignments.

        """
        if not assign_text:
            return ""
        out_lines = []
        for raw in assign_text.splitlines():
            line = raw.strip()
            if not line or not line.upper().startswith("ASSIGN"):
                continue
            # Remove leading ASSIGN and trailing /
            body = re.sub(r"^\s*ASSIGN\s+", "", line, flags=re.IGNORECASE).strip()
            body = re.sub(r"\s*/\s*$", "", body).strip()

            # Split into variable and value
            parts = body.split()
            if len(parts) >= 2:
                var_name = parts[0]
                var_value = parts[1]
                # Try to convert to float for numeric values
                try:
                    var_value_num = float(var_value)
                    var_value = repr(var_value_num)
                except ValueError:
                    # Keep original if not numeric (e.g., strings or expressions)
                    pass
                out_lines.append(f"summary_state['{var_name}'] = {var_value}")

        return ("\n".join(out_lines) + "\n") if out_lines else ""

    def _define_to_pyaction(self, define_text: str) -> str:
        """
        Convert DEFINE lines into pyaction summary_state assignments.

        Example:
          "DEFINE SWCT_X0 SWCT WELL(X0) SEG(X0) * FWCT /\n"
        -> "summary_state['SWCT_X0'] = summary_state['SWCT:WELL(X0):SEG(X0)'] * summary_state['FWCT']\n"

        """
        if not define_text:
            return ""
        out_lines = []
        for raw in define_text.splitlines():
            line = raw.strip()
            if not line or not line.upper().startswith("DEFINE"):
                continue
            # Remove leading DEFINE and trailing /
            body = re.sub(r"^\s*DEFINE\s+", "", line, flags=re.IGNORECASE).strip()
            body = re.sub(r"\s*/\s*$", "", body).strip()

            # Split into tokens
            tokens = body.split()
            if not tokens:
                continue

            lhs = tokens[0]  # e.g., "SWCT_X0"
            rhs_tokens = tokens[1:]  # e.g., ["SWCT", "WELL(X0)", "SEG(X0)", "*", "FWCT"]

            # Build RHS: group consecutive non-operator tokens with ":", replace operators
            rhs_expr = ""
            i = 0
            while i < len(rhs_tokens):
                token = rhs_tokens[i]
                # Check if token is an operator
                if token in ["+", "-", "*", "/", ">", "<", ">=", "<=", "==", "!="]:
                    rhs_expr += f" {token} "
                    i += 1
                else:
                    # Collect consecutive non-operator tokens and join with ":"
                    group = [token]
                    i += 1
                    while i < len(rhs_tokens) and rhs_tokens[i] not in [
                        "+",
                        "-",
                        "*",
                        "/",
                        ">",
                        "<",
                        ">=",
                        "<=",
                        "==",
                        "!=",
                    ]:
                        group.append(rhs_tokens[i])
                        i += 1
                    key = ":".join(group)
                    rhs_expr += f"summary_state['{key}']"

            out_lines.append(f"summary_state['{lhs}'] = {rhs_expr}")

        return ("\n".join(out_lines) + "\n") if out_lines else ""

    def _expression_to_pyaction(self, expression_text: str) -> str:
        """Convert general UDQ expressions into pyaction summary_state format.

        Example:
          "FUWCT_X0 > FUWCTBRN AND /\nFUPOS_X0 > 1 /\n"
        -> "summary_state['FUWCT_X0'] > summary_state['FUWCTBRN'] and\nsummary_state['FUPOS_X0'] > 1\n"

        Args:
            expression_text: Text containing UDQ expressions.

        Returns:
            Pyaction format expressions.

        """
        if not expression_text:
            return ""
        out_lines = []
        for raw in expression_text.splitlines():
            line = raw.strip()
            if not line:
                continue
            # Remove trailing /
            line = re.sub(r"\s*/\s*$", "", line).strip()
            if not line:
                continue

            # Split into tokens and process each
            tokens = line.split()
            processed_tokens = []
            for token in tokens:
                # Check if token is a variable (contains letters, underscores, and possibly numbers, but not operators)
                if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", token):
                    # Assume it's a variable if it doesn't match common operators
                    if token.upper() not in ["AND", "OR", "NOT", "TRUE", "FALSE"]:
                        processed_tokens.append(f"summary_state['{token}']")
                    else:
                        # Convert logical operators to Python equivalents
                        if token.upper() == "AND":
                            processed_tokens.append("and")
                        elif token.upper() == "OR":
                            processed_tokens.append("or")
                        elif token.upper() == "NOT":
                            processed_tokens.append("not")
                        else:
                            processed_tokens.append(token.lower())
                else:
                    # Keep operators and numbers as is
                    processed_tokens.append(token)

            out_lines.append(" ".join(processed_tokens))

        return ("\n".join(out_lines) + "\n") if out_lines else ""

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
            content_lines = [f"  {line.strip()}\n" for line in content.splitlines()]
            for index, line in enumerate(content_lines):
                if not line.isspace():
                    # Remove trailing non-word characters unless they are ) or ' at word boundary
                    content_lines[index] = re.sub(r"(?:\B'|[^\w\)'])*$", "", line) + " /\n"
                else:
                    content_lines[index] = ""
            content = "".join(content_lines)
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

    def parse_custom_content_pyaction(
        self, current_icv: str, custom_data: dict, content: str, is_end_of_records=True
    ) -> str:
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
            if "DEFINE" in content:
                content_pyaction = self._define_to_pyaction(content)
            elif "ASSIGN" in content:
                content_pyaction = self._assign_to_pyaction(content)
            else:
                content_pyaction = self._expression_to_pyaction(content)
            if criteria == "map":
                pass
            if isinstance(content, dict):
                content = custom_data[current_icv][criteria]
            if re.search(r"\d|\w", content) is None:
                raise ValueError("Missing content in CONTROL_CRITERIA keyword!")
            if current_icv != "UDQ":
                for x_value, icv in custom_data[current_icv]["map"][criteria].items():
                    content_pyaction = re.sub(rf"WELL\({x_value}\)", f"{self.well_names[icv]}", content_pyaction)
                    content_pyaction = re.sub(rf"SEG\({x_value}\)", str(self.segments[icv]), content_pyaction)
                    content_pyaction = re.sub(rf"\_{x_value}\b", f"_{icv}", content_pyaction)
            if current_icv != "UDQ":
                for x_value, icv in custom_data[current_icv]["map"][criteria].items():
                    content_pyaction = re.sub(rf"WELL\({x_value}\)", f"{self.well_names[icv]}", content_pyaction)
                    content_pyaction = re.sub(rf"SEG\({x_value}\)", str(self.segments[icv]), content_pyaction)
                    content_pyaction = re.sub(rf"\_{x_value}\b", f"_{icv}", content_pyaction)
            # Replace inconsistent end records and space with consistent version
            # content_lines = [f"  {line.strip()}\n" for line in content_pyaction.splitlines()]
            # for index, line in enumerate(content_lines):
            #    if not line.isspace():
            #        # Remove trailing non-word characters unless they are ) or ' at word boundary
            #        content_lines[index] = re.sub(r"(?:\B'|[^\w\)'])*$", "", line) + " /\n"
            #    else:
            #        content_lines[index] = ""
            # content_pyaction = "".join(content_lines)
        content_variables = re.findall(r"[x]\d", content_pyaction)
        if content_variables != []:
            logger.info(
                f"ICVALGORITHM ICV {current_icv} criteria {criteria} "
                f"contains an x value '{content_variables}' that did not "
                f"get translated into an ICV-name.\nCustom criteria is: {content_pyaction}."
            )
        return f"{content_pyaction}"

    def get_custom_content(
        self, icv_name: str, icv_function: ICVMethod, criteria: int | str | None, is_end_of_records: bool = True
    ) -> str | None:
        """Helper method to get correct custom content.

        Args:
            icv_name: Current ICV.
            icv_function: The ICVMethod type calling this function.

        Returns:
            The custom content for the current ICV.

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
                            custom_content += self.parse_custom_content_pyaction(icv, custom_data, data, is_end_of_records)
                if icv_name in custom_data:
                    data = custom_data[icv_name].get(str(criteria))
                    if data is None:
                        return None
                    else:
                        custom_content = self.parse_custom_content_pyaction(icv_name, custom_data, data, is_end_of_records)
                if icv_function == ICVMethod.UDQ:
                    custom_content = ""
                    for icv in custom_data:
                        if icv == "UDQ":
                            data = custom_data["UDQ"]
                        else:
                            data = custom_data[icv].get(str(criteria))
                        if icv_name == icv.split()[0]:
                            custom_content += self.parse_custom_content_pyaction(icv, custom_data, data, is_end_of_records)
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
        assigns_pyaction = ""
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
            assigns_pyaction += f" summary_state['{re.sub(r'(DEFINE )', '', match)}'] = {init_value[icv]}\n"

        if self.case.python_dependent:
            return assigns_pyaction
        return assigns
