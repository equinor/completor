"""This module create the resulting ICV-Control Eclipse functions"""

from __future__ import annotations

import re

import pandas as pd

from completor.constants import ICVMethod
from completor.initialization import Initialization
from completor.initialization_pyaction import InitializationPyaction
from completor.logger import logger
from completor.utils import insert_comment


class IcvFunctions:
    """This class defines a framework of icv functions used by the icv-control
    algorithm.

    """

    def __init__(self, initials: Initialization, initials_pyaction: InitializationPyaction | None = None) -> None:
        self.initials: Initialization | InitializationPyaction = initials
        self.initials_pyaction = initials_pyaction
        self.opening_icv_lim = [0.01, 0.99]
        self.custom_conditions = initials.case.custom_conditions
        self.python_dependent = initials.case.python_dependent
        if self.python_dependent and initials_pyaction is not None:
            self.initials = initials_pyaction

    def create_actionx(self, record1: str, record2: str, action: str) -> str:
        """
        Creates a general purpose Eclipse ACTIONX statement.

        Args:
            record1: Record 1 in the ACTIONX statement.
            record2: Record 2 in the ACTIONX statement.
            action: The action to be taken by the ACTIONX statement.

        Returns:
            Eclipse ACTIONX statement.

        """
        return f"ACTIONX\n{record1}{record2}\n{action}\n"

    def create_action_name(
        self, icv_name: str, icv_function: ICVMethod, step: int | None = None, criteria: int | None = None
    ) -> str:
        """
        Creates an action name (first element of record1) for a specific action
        to be taken by ACTIONX. Example: CH1W1_A01.

        Args:
            icv_name: Icv name. Letter from A through Z.
            icv_function: Abbreviation for the type of icv function.
            number_of_icvs: Number of icvs in well with current icv (icv_name).
            step: The step number following the icv name in action name.
            criteria: Integer value denoting the criteria.

        Returns:
            An icv-control action name.

        """
        crit = "_" if criteria is None else f"{criteria}"
        step_str: str
        if step is None:
            step_str = "_"
        elif step > 999:
            step_str = str(step)
        elif len(crit) == 2 or len(icv_name) == 2:
            step_str = f"000{step}"[-3:]
        else:
            step_str = "_" + f"000{step}"[-3:]

        if (
            (len(crit) == 2 and len(icv_name) == 2)
            or (len(crit) == 2 and len(step_str) == 4)
            or (len(icv_name) == 2 and len(step_str) == 4)
        ):
            action_name_templates = {
                ICVMethod.OPEN: f"O{crit}{icv_name}{step_str}",
                ICVMethod.OPEN_WAIT: f"H{crit}{icv_name}{step_str}",
                ICVMethod.OPEN_READY: f"RDYO{crit}{icv_name}",
                ICVMethod.OPEN_STOP: f"STPO{crit}{icv_name}",
                ICVMethod.OPEN_WAIT_STOP: f"SPOW{crit}{icv_name}",
                ICVMethod.CHOKE: f"C{crit}{icv_name}{step_str}",
                ICVMethod.CHOKE_WAIT: f"W{crit}{icv_name}{step_str}",
                ICVMethod.CHOKE_READY: f"RDYC{crit}{icv_name}",
                ICVMethod.CHOKE_STOP: f"STPC{crit}{icv_name}",
                ICVMethod.CHOKE_WAIT_STOP: f"SPCW{crit}{icv_name}",
            }
        elif (len(crit) == 2 or len(icv_name) == 2) and len(step_str) < 4:
            action_name_templates = {
                ICVMethod.OPEN: f"OP{crit}{icv_name}{step_str}",
                ICVMethod.OPEN_WAIT: f"WO{crit}{icv_name}{step_str}",
                ICVMethod.OPEN_READY: f"REDYO{crit}{icv_name}",
                ICVMethod.OPEN_STOP: f"STPO{crit}{icv_name}",
                ICVMethod.OPEN_WAIT_STOP: f"STPOW{crit}{icv_name}",
                ICVMethod.CHOKE: f"C{crit}{icv_name}{step_str}",
                ICVMethod.CHOKE_WAIT: f"WC{crit}{icv_name}{step_str}",
                ICVMethod.CHOKE_READY: f"REDYC{crit}{icv_name}",
                ICVMethod.CHOKE_STOP: f"STPC{crit}{icv_name}",
                ICVMethod.CHOKE_WAIT_STOP: f"STPCW{crit}{icv_name}",
            }
        else:
            action_name_templates = {
                ICVMethod.OPEN: f"OP{crit}{icv_name}{step_str}",
                ICVMethod.OPEN_WAIT: f"WO{crit}{icv_name}{step_str}",
                ICVMethod.OPEN_READY: f"READYO{crit}{icv_name}",
                ICVMethod.OPEN_STOP: f"STOPO{crit}{icv_name}",
                ICVMethod.OPEN_WAIT_STOP: f"STOPOW{crit}{icv_name}",
                ICVMethod.CHOKE: f"CH{crit}{icv_name}{step_str}",
                ICVMethod.CHOKE_WAIT: f"WC{crit}{icv_name}{step_str}",
                ICVMethod.CHOKE_READY: f"READYC{crit}{icv_name}",
                ICVMethod.CHOKE_STOP: f"STOPC{crit}{icv_name}",
                ICVMethod.CHOKE_WAIT_STOP: f"STOPCW{crit}{icv_name}",
            }
        if len(action_name_templates[icv_function]) > 8:
            logger.warning(
                f"Function name '{action_name_templates[icv_function]}'"
                f" exceed Eclipse's maximum of 8 characters for keywords."
                f" Created for icv function '{icv_function}'."
            )
        return action_name_templates[icv_function]

    def create_record1(self, action_name: str, trigger_number_times: int, trigger_minimum_interval: int | str) -> str:
        """Creates record1 in the Eclipse ACTIONX statement for icv-control.

        Args:
            action_name: The action name, first element of ACTIONX record 1.
            trigger_number_times: The number of times this action can be triggered.
            trigger_minimum_interval: Minimum time interval between action triggers.

        Returns:
            Record 1 of the Eclipse ACTIONX keyword.

        """

        if trigger_minimum_interval == "":
            return f"  {action_name} {trigger_number_times} /\n"

        return f"  {action_name} {trigger_number_times} {trigger_minimum_interval} /\n"

    def create_record2_choke_wait(self, icv_name: str, step: int, criteria: int) -> str:
        """Creates the ACTIONX record 2 inequalities for the choke wait function.

        Args:
            icv_name: One or two symbols, I.E: A or Z9.
            step: Counter for ACTIONX.
            criteria: Integer value denoting the criteria.

        Returns:
            ACTIONX record 2 for the wait choke function.

        """
        icv_function = ICVMethod.CHOKE_WAIT
        end_rec = " /\n/\n"
        custom_content = self.initials.get_custom_content(icv_name, icv_function, criteria)

        insert_futstp = ""
        if step >= 2:
            insert_futstp = f"  FUTSTP > FUL_{icv_name} AND /\n"
        insert_parameter_block = (
            f"{insert_futstp}"
            f"  FUTC_{icv_name} <= FUD_{icv_name} AND /\n"
            f"  FUP_{icv_name} = 2 AND /\n"
            f"  FUT_{icv_name} > FUFRQ_{icv_name}"
        )

        if self.python_dependent:
            insert_futstp = ""
            if step >= 2:
                insert_futstp = f"summary_state['TIMESTEP'] > summary_state['FUL_{icv_name}'] and \n"
            insert_parameter_block = (
                f"{insert_futstp}"
                f"summary_state['FUTC_{icv_name}'] <= summary_state['FUD_{icv_name}'] and \n"
                f"summary_state['FUP_{icv_name}'] == 2 and \n"
                f"summary_state['FUT_{icv_name}'] > summary_state['FUFRQ_{icv_name}']"
            )

            if custom_content is not None and custom_content != "":
                return f"if ({insert_parameter_block} and \n{custom_content}):"
            else:
                return f"if ({insert_parameter_block} + {end_rec}:"
        if custom_content is not None and custom_content != "":
            return f"{insert_parameter_block} AND /\n{custom_content}"
        return insert_parameter_block + end_rec

    def create_record2_choke_wait_stop(self, icv_name: str, criteria: int | None = None) -> str:
        """Creates the ACTIONX record 2 for the choke wait stop function.

        Args:
            icv_name: One or two symbols naming the icv.
            criteria: Integer value denoting the criteria. Defaults to 1 if None or not provided.

        Returns:
            ACTIONX record 2 for the wait open function.

        """
        if criteria is None:
            criteria = 1

        icv_function = ICVMethod.CHOKE_WAIT_STOP
        end_rec = " /\n/\n"
        custom_content = self.initials.get_custom_content(icv_name, icv_function, criteria)
        insert_parameter_block = f"  FUP_{icv_name} = 2 AND /\n  FUTC_{icv_name} != 0"
        if self.python_dependent:
            return ""
        if custom_content is not None and custom_content != "":
            return f"{insert_parameter_block} AND /\n{custom_content}"
        else:
            return insert_parameter_block + end_rec
        # No need for pyaction as python will handle the choke wait stop differently

    def create_record2_open_wait(self, icv_name: str, step: int, criteria: int) -> str:
        """Creates the ACTIONX record 2 inequalities for the wait open function.

        Args:
            icv_name: One or two symbols naming the ICV.
            step: Counter for ACTIONX.
            criteria: Integer value denoting the criteria.

        Output:
            ACTIONX record 2 for the wait open function.

        """
        icv_function = ICVMethod.OPEN_WAIT
        end_rec = " /\n/\n"
        custom_content = self.initials.get_custom_content(icv_name, icv_function, criteria)

        insert_futstp = ""
        if step >= 2:
            insert_futstp = f"  FUTSTP > FUL_{icv_name} AND /\n"

        insert_parameter_block = (
            f"{insert_futstp}"
            f"  FUTO_{icv_name} <= FUD_{icv_name} AND /\n"
            f"  FUP_{icv_name} = 2 AND /\n"
            f"  FUT_{icv_name} > FUFRQ_{icv_name}"
        )

        if self.python_dependent:
            insert_futstp = ""
            if step >= 2:
                insert_futstp = f"summary_state['TIMESTEP'] > summary_state['FUL_{icv_name}'] and \n"
            insert_parameter_block = (
                f"{insert_futstp}"
                f"summary_state['FUTO_{icv_name}'] <= summary_state['FUD_{icv_name}'] and \n"
                f"summary_state['FUP_{icv_name}'] == 2 and \n"
                f"summary_state['FUT_{icv_name}'] > summary_state['FUFRQ_{icv_name}']"
            )

            if custom_content is not None and custom_content != "":
                return f"if ({insert_parameter_block} and \n{custom_content}):"
            else:
                return f"if ({insert_parameter_block} + {end_rec}:"

        if custom_content is not None and custom_content != "":
            return f"{insert_parameter_block} AND /\n{custom_content}"
        else:
            return insert_parameter_block + end_rec

    def create_record2_open_wait_stop(self, icv_name: str, criteria: int | None = None) -> str:
        """Creates the ACTIONX record 2 for the open wait stop function.

        Args:
            icv_name: One or two symbols naming the ICV.
            criteria: Integer value denoting the criteria. Defaults to 1 if None or not provided.

        Returns:
            ACTIONX record 2 for the wait open function.

        """
        if criteria is None:
            criteria = 1
        icv_function = ICVMethod.OPEN_WAIT_STOP
        end_rec = " /\n/\n"
        custom_content = self.initials.get_custom_content(icv_name, icv_function, criteria)
        insert_parameter_block = f"  FUP_{icv_name} = 2 AND /\n  FUTO_{icv_name} != 0"
        if self.python_dependent:
            return ""
        if custom_content is not None and custom_content != "":
            return f"{insert_parameter_block} AND /\n{custom_content}"
        else:
            return insert_parameter_block + end_rec
        # No need for pyaction as python will handle the choke wait stop differently

    def create_record2_choke_ready(self, icv_name: str, criteria: int | None) -> str:
        """Creates the ACTIONX record 2 inequalities for the ready choke function.

        Args:
            icv_name: One or two symbols.
            criteria: Integer value denoting the criteria.

        Output:
            ACTIONX record 2 for the ready choke function.

        """
        icv_function = ICVMethod.CHOKE_READY
        end_rec = " /\n/\n"
        custom_content = self.initials.get_custom_content(icv_name, icv_function, criteria)

        insert_parameter_block = f"  FUTC_{icv_name} > FUD_{icv_name} AND /\n  FUP_{icv_name} = 2"
        if self.python_dependent:
            insert_parameter_block = (
                f"summary_state['FUTC_{icv_name}'] > summary_state['FUD_{icv_name}'] and\n"
                f"summary_state['FUP_{icv_name}'] == 2\n"
            )
            if custom_content is not None and custom_content != "":
                return f"if ({insert_parameter_block} and \n{custom_content}):"
            else:
                return f"if ({insert_parameter_block} + {end_rec}):"
        if custom_content is not None and custom_content != "":
            return f"{insert_parameter_block} AND /\n{custom_content}"
        else:
            return insert_parameter_block + end_rec

    def create_record2_open_ready(self, icv_name: str, criteria: int | None) -> str:
        """Creates the ACTIONX record 2 inequalities for the ready open function.

        Args:
            icv_name: One or two symbols.
            criteria: Integer value denoting the criteria.

        Output:
            ACTIONX record 2 for the ready open function.

        """

        icv_function = ICVMethod.OPEN_READY
        end_rec = " /\n/\n"
        custom_content = self.initials.get_custom_content(icv_name, icv_function, criteria)
        insert_parameter_block = f"  FUTO_{icv_name} > FUD_{icv_name} AND /\n  FUP_{icv_name} = 2"
        if self.python_dependent:
            insert_parameter_block = (
                f"summary_state['FUTO_{icv_name}'] > summary_state['FUD_{icv_name}'] and\n"
                f"summary_state['FUP_{icv_name}'] == 2"
            )
            if custom_content is not None and custom_content != "":
                return f"if ({insert_parameter_block} and \n{custom_content}):"
            else:
                return f"if ({insert_parameter_block} + {end_rec}):"
        if custom_content is not None and custom_content != "":
            return f"{insert_parameter_block} AND /\n{custom_content}"
        else:
            return insert_parameter_block + end_rec

    def create_record2_choke_stop(self, icv_name: str, criteria: int | None) -> str:
        """Creates the ACTIONX record 2 inequalities for the stop choke function.

        Args:
            icv_name: One or two symbols.
            criteria: Integer value denoting the criteria.

        Returns:
            ACTIONX record 2 for the stop choke function.

        """
        icv_function = ICVMethod.CHOKE_STOP
        insert_parameter_block = f"  FUP_{icv_name} = 4 AND /\n  FUTC_{icv_name} != 0"

        end_rec = " /\n/\n"
        custom_content = self.initials.get_custom_content(icv_name, icv_function, criteria)

        if self.python_dependent:
            insert_parameter_block = f"summary_state['FUP_{icv_name}'] == 4 and \nsummary_state['FUTC_{icv_name}'] != 0"
            if custom_content is not None and custom_content != "":
                return f"if ({insert_parameter_block} and \n{custom_content}):"
            else:
                return f"if ({insert_parameter_block} + {end_rec}):"

        if custom_content is not None and custom_content != "":
            return f"{insert_parameter_block} AND /\n{custom_content}"
        else:
            return insert_parameter_block + end_rec

    def create_record2_open_stop(self, icv_name: str, criteria: int | None) -> str:
        """Creates the ACTIONX record 2 inequalities for the stop open function.

        Args:
            icv_name: One or two symbols naming the ICV.
            criteria: Integer value denoting the criteria.

        Returns:
            ACTIONX record 2 for the stop open function.

        """
        icv_function = ICVMethod.OPEN_STOP
        insert_parameter_block = f"  FUP_{icv_name} = 3 AND /\n  FUTO_{icv_name} != 0"
        end_rec = " /\n/\n"
        custom_content = self.initials.get_custom_content(icv_name, icv_function, criteria)

        if self.python_dependent:
            insert_parameter_block = f"summary_state['FUP_{icv_name}'] == 3 and \nsummary_state['FUTO_{icv_name}'] != 0"
            if custom_content is not None and custom_content != "":
                return f"if ({insert_parameter_block} and \n{custom_content}):"
            else:
                return f"if ({insert_parameter_block} + {end_rec}):"
        if custom_content is not None and custom_content != "":
            return f"{insert_parameter_block} AND /\n{custom_content}"
        else:
            return insert_parameter_block + end_rec

    def create_record2_choke(self, icv_name: str, step: int, criteria: int | None) -> str:
        """Creates the ACTIONX record 2 inequalities for the choke function.

        Args:
            icv_name: One or two symbols naming the ICV.
            step: Counter for ACTIONX.
            criteria: Integer value denoting the criteria.

        Returns:
            ACTIONX record 2 for the choke function.

        """
        icv_function = ICVMethod.CHOKE
        end_rec = " /\n/\n"
        num_icvs = self.initials.number_of_icvs(icv_name)
        custom_content = self.initials.get_custom_content(icv_name, icv_function, criteria)
        insert_parameter_block = (
            f"  FUTSTP < FUH_{icv_name} AND /\n"
            f"  FUTSTP > FUL_{icv_name} AND /\n"
            f"  FUTC_{icv_name} > FUD_{icv_name} AND /\n"
            f"  FUP_{icv_name} = 4"
        )
        insert_futstp = ""

        if self.python_dependent:
            insert_parameter_block = (
                f"summary_state['TIMESTEP'] < summary_state['FUH_{icv_name}'] and \n"
                f"summary_state['TIMESTEP'] > summary_state['FUL_{icv_name}'] and \n"
                f"summary_state['FUTC_{icv_name}'] > summary_state['FUD_{icv_name}'] and \n"
                f"summary_state['FUP_{icv_name}'] == 4"
            )
            insert_futstp = ""
            # if step % 2 == 0:
            #    return f"if (summary_state['FUP_{icv_name}'] == 4:\n"
            if custom_content is not None and custom_content != "":
                return f"if ({insert_parameter_block} and \n{custom_content}):"
            if num_icvs == 2:
                return f"if ({insert_parameter_block} + {end_rec}):"
            else:
                insert_futstp = f"""
                summary_state['TIMESTEP'] < summary_state['FUH_{icv_name}'] and
                summary_state['TIMESTEP'] > summary_state['FUL_{icv_name}'] and
                """
            return (
                f"if ({insert_futstp}"
                f"summary_state['FUTC_{icv_name}'] > summary_state['FUD_{icv_name}'] and \n"
                f"summary_state['FUP_{icv_name}'] == 4"
                f" + {end_rec}):"
            )

        if step % 2 == 0:
            return f"  FUP_{icv_name} = 4{end_rec}"
        if custom_content is not None and custom_content != "":
            return f"{insert_parameter_block} AND /\n{custom_content}"
        if num_icvs == 2:
            return f"{insert_parameter_block}" f"{end_rec}"

        if step == 1:
            insert_futstp = f"  FUTSTP < FUH_{icv_name} AND /\n" f"  FUTSTP > FUL_{icv_name} AND /\n"
        elif step >= 2:
            insert_futstp = f"  FUTSTP > FUL_{icv_name} AND /\n"
        return f"{insert_futstp}" f"  FUTC_{icv_name} > FUD_{icv_name} AND /\n" f"  FUP_{icv_name} = 4" f"{end_rec}"

    def create_record2_open(self, icv_name: str, step: int, criteria: int | None) -> str:
        """Creates the ACTIONX record 2 inequalities for the open function.

        Args:
            icv_name: One or two symbols naming the ICV.
            step: Counter for ACTIONX.
            criteria: Integer value denoting the criteria.

        Returns:
            ACTIONX record 2 for the open function.

        """
        icv_function = ICVMethod.OPEN
        end_rec = " /\n/\n"
        num_icvs = self.initials.number_of_icvs(icv_name)
        custom_content = self.initials.get_custom_content(icv_name, icv_function, criteria)
        insert_parameter_block = (
            f"  FUTSTP < FUH_{icv_name} AND /\n"
            f"  FUTSTP > FUL_{icv_name} AND /\n"
            f"  FUTO_{icv_name} > FUD_{icv_name} AND /\n"
            f"  FUP_{icv_name} = 3"
        )
        end_rec = " /\n/\n"
        insert_futstp = ""

        if self.python_dependent:
            insert_parameter_block = (
                f"summary_state['TIMESTEP'] < summary_state['FUH_{icv_name}'] and \n"
                f"summary_state['TIMESTEP'] > summary_state['FUL_{icv_name}'] and \n"
                f"summary_state['FUTO_{icv_name}'] > summary_state['FUD_{icv_name}'] and \n"
                f"summary_state['FUP_{icv_name}'] == 3"
            )
            # if step % 2 == 0:
            #    return f"if (summary_state['FUP_{icv_name}'] == 3):\n"
            if custom_content is not None and custom_content != "":
                return f"if ({insert_parameter_block} and \n{custom_content}):"
            if num_icvs == 2:
                return f"if ({insert_parameter_block} + {end_rec}):"
            else:
                insert_futstp = f"""summary_state['TIMESTEP'] < summary_state['FUH_{icv_name}'] and
                summary_state['TIMESTEP'] > summary_state['FUL_{icv_name}'] and
                """
            return (
                f"if ({insert_futstp}"
                f"summary_state['FUTO_{icv_name}'] > summary_state['FUD_{icv_name}'] and \n"
                f"summary_state['FUP_{icv_name}'] == 3"
                f" + {end_rec}):"
            )

        if step % 2 == 0:
            return f"  FUP_{icv_name} = 3{end_rec}"
        if custom_content is not None and custom_content != "":
            return f"{insert_parameter_block} AND /\n{custom_content}"
        if num_icvs == 2:
            return insert_parameter_block + end_rec

        if step == 1:
            insert_futstp = f"  FUTSTP < FUH_{icv_name} AND /\n" f"  FUTSTP > FUL_{icv_name} AND /\n"
        elif step >= 2:
            insert_futstp = f"  FUTSTP > FUL_{icv_name} AND /\n"
        return f"{insert_futstp}" f"  FUTO_{icv_name} > FUD_{icv_name} AND /\n" f"  FUP_{icv_name} = 3" f"{end_rec}"

    def create_action(
        self,
        icv_name: str,
        icv_function: str | ICVMethod,
        step: int | None = None,
        opening_table: dict[str, pd.DataFrame] | None = None,
    ) -> str:
        """Creates Eclipse ACTIONX actions for icv-control choke functions.

        Args:
            icv_name: One or two symbols naming the ICV.
            icv_function: Abbreviation for icv functions.
            step: value separating the first and remaining actions in the wait function.
            opening_table: Table of openings from ICVTABLE keyword if exists.

        Returns:
            The action to be taken in different choke functions for icv-control.

        Raises:
            ValueError: if the icv_function keyword is not recognized.
            ValueError: if step is None when required for OPEN or CHOKE functions.

        """
        well_name = self.initials.well_names[icv_name]
        segment = self.initials.segments[icv_name]
        area = self.initials.areas[icv_name]
        table_name = self.initials.areas[icv_name]
        table = True
        if re.sub(r"[^a-zA-Z]", "", area) != "":
            cv_area = self.initials.case.icv_table[area].iloc[-1]
            eff_area = cv_area["CV"] * cv_area["AREA"]
            area = f"{eff_area:.3e}"  # put everything as scientific with 3 decimals
        else:
            table = False

        if icv_function == ICVMethod.OPEN:
            if step is None:
                raise ValueError(f"step is required for {icv_function} function")
            if (step % 2) == 0:
                action = (
                    f"WSEGVALV\n"
                    f"  {well_name} {segment} 1.0 FUARE_{icv_name} 5* {area} /\n/\n"
                    "NEXTSTEP\n"
                    f"  {self.initials.operation_step[icv_name]} /\n"
                )
            else:
                if opening_table and table:
                    opening_area = (
                        f"  DEFINE FUPOS_{icv_name} (FUPOS_{icv_name} + 1) /\n" f"  UPDATE FUPOS_{icv_name} NEXT /\n"
                    )
                else:
                    opening_area = (
                        f"  DEFINE FUARE_{icv_name} (FUARE_{icv_name} / 0.6) /\n" f"  UPDATE FUARE_{icv_name} NEXT /\n"
                    )
                action = f"UDQ\n{opening_area}/\nNEXTSTEP\n  0.1 /\n"
            if self.python_dependent:
                if opening_table and table:
                    action = (
                        f"\tsummary_state['FUPOS_{icv_name}'] += 1\n"
                        f"\tschedule.insert_keywords(keyword_01day, report_step+1)\n"
                        f"\tif summary_state['FUP_{icv_name}'] == 4:\n"
                        f"\t\tarea = get_area_by_index(summary_state['FUPOS_{icv_name}'], flow_trim_{table_name})\n"
                        f"\t\tsummary_state['FUARE_{icv_name}'] = area\n"
                        f"\t\tkeyword_wsegvalv = f'WSEGVALV\\n {well_name} {segment} 1.0 FUARE_{icv_name} 5* {area} /\\n/'\n"
                        f"\t\tschedule.insert_keywords(keyword_wsegvalv, report_step)\n"
                        f"\t\tschedule.insert_keywords(keyword_2day, report_step+1)\n"
                    )
                else:
                    raise ValueError("PYTHON dependent code for input without flowtrim table is not supported.")
            return action

        if icv_function == ICVMethod.OPEN_WAIT:
            if self.python_dependent:
                return (
                    f"\tsummary_state['FUTO_{icv_name}'] += summary_state['TIMESTEP'] \n"
                    f"\tschedule.insert_keywords(keyword_1day, report_step+1)\n"
                )
            return (
                "UDQ\n"
                f"  DEFINE FUTO_{icv_name} FUTO_{icv_name} + TIMESTEP /\n/\n"
                "NEXTSTEP\n"
                f"  {self.initials.wait_step[icv_name]} /\n"
            )

        if icv_function == ICVMethod.OPEN_READY:
            if self.python_dependent:
                return f"\tsummary_state['FUP_{icv_name}'] = 3\n"
            return f"UDQ\n  ASSIGN FUP_{icv_name} 3 /\n/"

        if icv_function == ICVMethod.OPEN_STOP:
            if self.python_dependent:
                return (
                    f"\tsummary_state['FUP_{icv_name}'] = 2\n"
                    f"\tsummary_state['FUTO_{icv_name}'] = 0\n"
                    f"\tsummary_state['FUT_{icv_name}'] = 0\n"
                )
            return (
                "UDQ\n"
                f"  ASSIGN FUP_{icv_name} 2 /\n"
                f"  ASSIGN FUTO_{icv_name} 0 /\n"
                f"  ASSIGN FUT_{icv_name} 0 /\n"
                f"  UPDATE FUT_{icv_name} ON /\n/"
            )

        if icv_function == ICVMethod.OPEN_WAIT_STOP:
            if self.python_dependent:
                return ""
            return f"UDQ\n  ASSIGN FUTO_{icv_name} 0 /\n/"

        if icv_function == ICVMethod.CHOKE_WAIT_STOP:
            if self.python_dependent:
                return ""
            return f"UDQ\n  ASSIGN FUTC_{icv_name} 0 /\n/"

        if icv_function == ICVMethod.CHOKE:
            if step is None:
                raise ValueError(f"step is required for {icv_function} function")
            if (step % 2) == 0:
                action = (
                    f"WSEGVALV\n"
                    f"  {well_name} {segment} 1.0 FUARE_{icv_name} 5* {area} /\n/\n"
                    "NEXTSTEP\n"
                    f"  {self.initials.operation_step[icv_name]} /\n"
                )
            else:
                if opening_table and table:
                    opening_area = (
                        f"  DEFINE FUPOS_{icv_name} (FUPOS_{icv_name} - 1) /\n" f"  UPDATE FUPOS_{icv_name} NEXT /\n"
                    )
                else:
                    opening_area = (
                        f"  DEFINE FUARE_{icv_name} (FUARE_{icv_name} * 0.6) /\n" f"  UPDATE FUARE_{icv_name} NEXT /\n"
                    )

                action = f"UDQ\n{opening_area}/\nNEXTSTEP\n  0.1 /\n"
            if self.python_dependent:
                if opening_table and table:
                    action = (
                        f"\tsummary_state['FUPOS_{icv_name}'] -= 1\n"
                        f"\tschedule.insert_keywords(keyword_01day, report_step+1)\n"
                        f"\tif summary_state['FUP_{icv_name}'] == 4:\n"
                        f"\t\tarea = get_area_by_index(summary_state['FUPOS_{icv_name}'], flow_trim_{table_name})\n"
                        f"\t\tsummary_state['FUARE_{icv_name}'] = area\n"
                        f"\t\tkeyword_wsegvalv = f'WSEGVALV\\n {well_name} {segment} 1.0 FUARE_{icv_name} 5* {area} /\\n/'\n"
                        f"\t\tschedule.insert_keywords(keyword_wsegvalv, report_step)\n"
                        f"\t\tschedule.insert_keywords(keyword_2day, report_step+1)\n"
                    )
                else:
                    raise ValueError("PYTHON dependent code for input without flowtrim table is not supported.")
            return action

        if icv_function == ICVMethod.CHOKE_WAIT:
            if self.python_dependent:
                return (
                    f"\tsummary_state['FUTC_{icv_name}'] += summary_state['TIMESTEP'] \n"
                    f"\tschedule.insert_keywords(keyword_1day, report_step+1)\n"
                )
            return (
                "UDQ\n"
                f"  DEFINE FUTC_{icv_name} FUTC_{icv_name} + TIMESTEP /\n/\n"
                "NEXTSTEP\n"
                f"  {self.initials.wait_step[icv_name]} /\n"
            )

        if icv_function == ICVMethod.CHOKE_READY:
            if self.python_dependent:
                return f"\tsummary_state['FUP_{icv_name}'] = 4\n"
            return f"UDQ\n  ASSIGN FUP_{icv_name} 4 /\n/"

        if icv_function == ICVMethod.CHOKE_STOP:
            if self.python_dependent:
                return (
                    f"\tsummary_state['FUP_{icv_name}'] = 2\n"
                    f"\tsummary_state['FUTC_{icv_name}'] = 0\n"
                    f"\tsummary_state['FUT_{icv_name}'] = 0\n"
                )
            return (
                "UDQ\n"
                f"  ASSIGN FUP_{icv_name} 2 /\n"
                f"  ASSIGN FUTC_{icv_name} 0 /\n"
                f"  ASSIGN FUT_{icv_name} 0 /\n"
                f"  UPDATE FUT_{icv_name} ON /\n/"
            )

        # All legal values of icv_function have already caused this function to return
        # If we encounter something not caught, the value is wrong:
        raise ValueError(f"The icv function type {icv_function} is not recognized")

    def create_choke_wait(
        self,
        icv_name: str,
        trigger_number_times: int,
        trigger_minimum_interval: int,
        actionx_repeater: int = 99,
        criteria: int | None = None,
    ) -> str:
        """Creates the wait choke icv-control function.

        Args:
            icv_name: One or two symbols naming the ICV.
            trigger_number_times: The number of times this action can be triggered.
            trigger_minimum_interval: Minimum time interval between action triggers.
            actionx_repeater: Times to repeat ACTIONX in the choke wait function.
            criteria: Integer value denoting the criteria.

        Returns:
            The icv-control wait choke function.

        """
        if criteria is None:
            criteria = 1

        icv_function = ICVMethod.CHOKE_WAIT
        step = 1
        actionx = ""
        action_name = self.create_action_name(icv_name, icv_function, step, criteria)
        record1 = self.create_record1(action_name, trigger_number_times, trigger_minimum_interval)
        record2 = self.create_record2_choke_wait(icv_name, step, criteria)
        action = self.create_action(icv_name, icv_function, step)
        actionx += insert_comment(icv_function, step, criteria)
        actionx += self.create_actionx(record1, record2, action)
        while step < actionx_repeater:
            step += 1
            actionx += insert_comment(icv_function, step, criteria)
            action_name = self.create_action_name(icv_name, icv_function, step, criteria)
            record1 = self.create_record1(action_name, 1, "")
            record2 = self.create_record2_choke_wait(icv_name, step, criteria)
            action = self.create_action(icv_name, icv_function, step)
            actionx += self.create_actionx(record1, record2, action)
        actionx += actionx_repeater * "ENDACTIO\n"
        if self.python_dependent:
            pyaction = f"# TEST PYACTION {icv_function} for {icv_name} criteria number {criteria}\n"
            pyaction += record2 + "\n"
            pyaction += action + "\n"
            return pyaction
        return actionx

    def create_open_wait(self, icv_name: str, actionx_repeater: int = 99, criteria: int | None = None) -> str:
        """Creates the icv-control wait open function.

        Args:
            icv_name: One or two symbols naming the ICV.
            actionx_repeater: Times to repeat ACTIONX in the choke wait function.
            criteria: Integer value denoting the criteria.
        Returns:
            The icv-control wait open function.

        """
        if criteria is None:
            criteria = 1

        icv_function = ICVMethod.OPEN_WAIT
        step = 1
        actionx = ""
        action_name = self.create_action_name(icv_name, icv_function, step, criteria)
        record1 = self.create_record1(action_name, 10000, 10)
        record2 = self.create_record2_open_wait(icv_name, step, criteria)
        action = self.create_action(icv_name, icv_function, step)
        actionx += insert_comment(icv_function, step, criteria)
        actionx += self.create_actionx(record1, record2, action)
        while step < actionx_repeater:
            step += 1
            actionx += insert_comment(icv_function, step, criteria)
            action_name = self.create_action_name(icv_name, icv_function, step, criteria)
            record1 = self.create_record1(action_name, 1, "")
            record2 = self.create_record2_open_wait(icv_name, step, criteria)
            action = self.create_action(icv_name, icv_function, step)
            actionx += self.create_actionx(record1, record2, action)
        if self.python_dependent:
            pyaction = f"# TEST PYACTION {icv_function} for {icv_name} criteria number {criteria}\n"
            pyaction += record2 + "\n"
            pyaction += action + "\n"
            return pyaction
        return actionx + actionx_repeater * "ENDACTIO\n"

    def create_choke_wait_stop(self, icv_name: str, criteria: int | None = None) -> str:
        """Creates the icv-control choke wait stop function.

        Args:
            icv_name: One or two symbols naming the ICV.
            criteria: Integer value denoting the criteria.

        Returns:
            The icv-control wait open function.

        """
        icv_function = ICVMethod.CHOKE_WAIT_STOP
        actionx = ""
        action_name = self.create_action_name(icv_name, icv_function, None, criteria=criteria)
        record1 = self.create_record1(action_name, 10000, 10)
        record2 = self.create_record2_choke_wait_stop(icv_name, criteria=criteria)
        action = self.create_action(icv_name, icv_function)
        actionx += insert_comment(icv_function)
        actionx += self.create_actionx(record1, record2, action)
        if self.python_dependent:
            pyaction = f"# TEST PYACTION {icv_function} for {icv_name} criteria number {criteria}\n"
            pyaction += record2 + "\n"
            pyaction += action + "\n"
            return pyaction
        return actionx + "ENDACTIO\n\n"

    def create_open_wait_stop(self, icv_name: str, criteria: int | None = None) -> str:
        """Creates the icv-control open wait stop function.

        Args:
            icv_name: Icv name. Letter from A through Z.

        Returns:
            The icv-control wait open function.

        """
        icv_function = ICVMethod.OPEN_WAIT_STOP
        actionx = ""
        action_name = self.create_action_name(icv_name, icv_function, None, criteria=criteria)
        record1 = self.create_record1(action_name, 10000, 10)
        record2 = self.create_record2_open_wait_stop(icv_name, criteria=criteria)
        action = self.create_action(icv_name, icv_function)
        actionx += insert_comment(icv_function)
        actionx += self.create_actionx(record1, record2, action)
        if self.python_dependent:
            pyaction = f"# TEST PYACTION {icv_function} for {icv_name} criteria number {criteria}\n"
            pyaction += record2 + "\n"
            pyaction += action + "\n"
            return pyaction
        return actionx + "ENDACTIO\n\n"

    def create_choke_ready(
        self,
        icv_name: str,
        criteria: int | None = None,
        trigger_number_times: int = 10,
        trigger_minimum_interval: str = "",
    ) -> str:
        """Creates the ready choke function for icv-control.

        Args:
            icv_name: One or two symbols naming the ICV.
            criteria: Integer value denoting the criteria.
            trigger_number_times: The number of times this action can be triggered.
            trigger_minimum_interval: Minimum time interval between action triggers.

        Returns:
            The icv-control ready choke function.

        """
        if criteria is None:
            criteria = 1

        icv_function = ICVMethod.CHOKE_READY
        action_name = self.create_action_name(icv_name, icv_function, None, criteria)
        record1 = self.create_record1(action_name, trigger_number_times, trigger_minimum_interval)
        record2 = self.create_record2_choke_ready(icv_name, criteria)
        action = self.create_action(icv_name, icv_function, None)
        if self.python_dependent:
            pyaction = f"# TEST PYACTION {icv_function} for {icv_name} criteria number {criteria}\n"
            pyaction += record2 + "\n"
            pyaction += action + "\n"
            return pyaction
        return (
            insert_comment(icv_function, criteria=criteria)
            + self.create_actionx(record1, record2, action)
            + "ENDACTIO\n\n"
        )

    def create_open_ready(
        self,
        icv_name: str,
        criteria: int | None = 1,
        trigger_number_times: int = 10,
        trigger_minimum_interval: str = "",
    ) -> str:
        """Creates the ready open function for icv-control.

        Args:
            icv_name: One or two symbols naming the ICV.
            criteria: Integer value denoting the criteria.
            trigger_number_times: The number of times this action can be triggered.
            trigger_minimum_interval: Minimum time interval between action triggers.

        Returns:
            The icv-control ready open function.

        """
        icv_function = ICVMethod.OPEN_READY
        action_name = self.create_action_name(icv_name, icv_function, None, criteria)
        record1 = self.create_record1(action_name, trigger_number_times, trigger_minimum_interval)
        record2 = self.create_record2_open_ready(icv_name, criteria)
        action = self.create_action(icv_name, icv_function, None)
        if self.python_dependent:
            pyaction = f"# TEST PYACTION {icv_function} for {icv_name} criteria number {criteria}\n"
            pyaction += record2 + "\n"
            pyaction += action + "\n"
            return pyaction
        return (
            insert_comment(icv_function, criteria=criteria)
            + self.create_actionx(record1, record2, action)
            + "ENDACTIO\n\n"
        )

    def create_choke_stop(
        self, icv_name: str, criteria: int | None, trigger_number_times: int, trigger_minimum_interval: str
    ) -> str:
        """The icv-control stop choke function.

        Args:
            icv_name: One or two symbols naming the ICV.
            criteria: Integer value denoting the criteria.
            trigger_number_times: The number of times this action can be triggered.
            trigger_minimum_interval: Minimum time interval between action triggers.

        Returns:
            The icv-control stop choke function.

        """
        icv_function = ICVMethod.CHOKE_STOP
        action_name = self.create_action_name(icv_name, icv_function, None, criteria)
        record1 = self.create_record1(action_name, trigger_number_times, trigger_minimum_interval)
        record2 = self.create_record2_choke_stop(icv_name, criteria)
        action = self.create_action(icv_name, icv_function, None)
        if self.python_dependent:
            pyaction = f"# TEST PYACTION {icv_function} for {icv_name} criteria number {criteria}\n"
            pyaction += record2 + "\n"
            pyaction += action + "\n"
            return pyaction
        return insert_comment(icv_function) + self.create_actionx(record1, record2, action) + "ENDACTIO\n\n"

    def create_open_stop(
        self, icv_name: str, criteria: int | None, trigger_number_times: int, trigger_minimum_interval: str
    ) -> str:
        """The icv-control stop open function.

        Args:
            icv_name: One or two symbols naming the ICV.
            criteria: Integer value denoting the criteria.
            trigger_number_times: The number of times this action can be triggered.
            trigger_minimum_interval: Minimum time interval between action triggers.

        Returns:
            The icv-control stop open function.

        """
        icv_function = ICVMethod.OPEN_STOP
        action_name = self.create_action_name(icv_name, icv_function, None, criteria)
        record1 = self.create_record1(action_name, trigger_number_times, trigger_minimum_interval)
        record2 = self.create_record2_open_stop(icv_name, criteria)
        action = self.create_action(icv_name, icv_function, None)
        if self.python_dependent:
            pyaction = f"# TEST PYACTION {icv_function} for {icv_name} criteria number {criteria}\n"
            pyaction += record2 + "\n"
            pyaction += action + "\n"
            return pyaction
        return insert_comment(icv_function) + self.create_actionx(record1, record2, action) + "ENDACTIO\n\n"

    def create_choke(
        self,
        icv_name: str,
        criteria: int | None,
        trigger_number_times: int,
        trigger_minimum_interval: int | str = "",
        actionx_repeater: int = 9,
    ) -> str:
        """The icv-control choke function.

        Args:
            icv_name: One or two symbols naming the ICV.
            criteria: Integer value denoting the criteria.
            trigger_number_times: The number of times this action can be triggered.
            trigger_minimum_interval: Minimum time interval between action triggers.
            actionx_repeater: Times to repeat ACTIONX in the choke wait function.

        Returns:
            The icv-control choke function.

        """
        icv_function = ICVMethod.CHOKE
        step = 1
        actionx = ""
        action_name = self.create_action_name(icv_name, icv_function, step, criteria)
        record1 = self.create_record1(action_name, trigger_number_times, trigger_minimum_interval)
        record2 = self.create_record2_choke(icv_name, step, criteria)
        action = self.create_action(icv_name, icv_function, step, self.initials.case.icv_table)
        actionx += insert_comment(icv_function, step, criteria)
        actionx += self.create_actionx(record1, record2, action)
        while step < actionx_repeater:
            step += 1
            actionx += insert_comment(icv_function, step, criteria)
            action_name = self.create_action_name(icv_name, icv_function, step, criteria)
            record1 = self.create_record1(action_name, 1, "")
            record2 = self.create_record2_choke(icv_name, step, criteria)
            action = self.create_action(icv_name, icv_function, step, self.initials.case.icv_table)
            actionx += self.create_actionx(record1, record2, action)
        actionx += actionx_repeater * "ENDACTIO\n"
        if self.python_dependent:
            pyaction = f"# TEST PYACTION {icv_function} for {icv_name} criteria number {criteria}\n"
            pyaction += record2 + "\n"
            pyaction += action + "\n"
            return pyaction
        return actionx

    def create_open(
        self,
        icv_name: str,
        criteria: int | None,
        trigger_number_times: int,
        trigger_minimum_interval: int | str,
        actionx_repeater: int = 9,
    ) -> str:
        """The icv-control open choke function.

        Args:
            icv_name: One or two symbols naming the ICV.
            criteria: Integer value denoting the criteria.
            trigger_number_times: The number of times this action can be triggered.
            trigger_minimum_interval: Minimum time interval between action triggers.
            actionx_repeater: Times to repeat ACTIONX in the choke wait function.

        Returns:
            The icv-control open choke function.

        """
        icv_function = ICVMethod.OPEN
        step = 1
        actionx = ""
        action_name = self.create_action_name(icv_name, icv_function, step, criteria)
        record1 = self.create_record1(action_name, trigger_number_times, trigger_minimum_interval)
        record2 = self.create_record2_open(icv_name, step, criteria)
        action = self.create_action(icv_name, icv_function, step, self.initials.case.icv_table)
        actionx += insert_comment(icv_function, step, criteria)
        actionx += self.create_actionx(record1, record2, action)
        while step < actionx_repeater:
            step += 1
            actionx += insert_comment(icv_function, step, criteria)
            action_name = self.create_action_name(icv_name, icv_function, step, criteria)
            record1 = self.create_record1(action_name, 1, "")
            record2 = self.create_record2_open(icv_name, step, criteria)
            action = self.create_action(icv_name, icv_function, step, self.initials.case.icv_table)
            actionx += self.create_actionx(record1, record2, action)
        if self.python_dependent:
            pyaction = f"# TEST PYACTION {icv_function} for {icv_name} criteria number {criteria}\n"
            pyaction += record2 + "\n"
            pyaction += action + "\n"
            return pyaction
        return actionx + actionx_repeater * "ENDACTIO\n"
