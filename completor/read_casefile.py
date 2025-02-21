from __future__ import annotations

import re
from collections.abc import Mapping
from io import StringIO
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd

from completor import input_validation, parse
from completor.constants import Content, Headers, Keywords, Method, WellData, DensitySelector, DualrcpSelector
from completor.exceptions.clean_exceptions import CompletorError
from completor.exceptions.exceptions import CaseReaderFormatError
from completor.logger import logger
from completor.utils import clean_file_lines


def _mapper(map_file: str) -> dict[str, str]:
    """Read two-column file and store data as values and keys in a dictionary.

    Used to map between pre-processing tools and reservoir simulator file names.

    Args:
        map_file: Two-column text file.

    Returns:
        Dictionary of key and values taken from the mapfile.
    """
    mapper = {}
    with open(map_file, encoding="utf-8") as lines:
        for line in lines:
            if not line.startswith("--"):
                keyword_pair = line.strip().split()
                if len(keyword_pair) == 2:
                    key = keyword_pair[0]
                    value = keyword_pair[1]
                    mapper[key] = value
                else:
                    logger.warning("Illegal line '%s' in mapfile", keyword_pair)
    return mapper


class ReadCasefile:
    """Class for reading Completor case files.

    This class reads the case/input file of the Completor program.
    It reads the following keywords:
    SCHEDULE_FILE, OUT_FILE, COMPLETION, SEGMENTLENGTH, JOINTLENGTH AUTONOMOUS_INFLOW_CONTROL_DEVICE, WELL_SEGMENTS_VALVE,
    INFLOW_CONTROL_DEVICE, DENSITY_DRIVEN, DUAL_RATE_CONTROLLED_PRODUCTION, INFLOW_CONTROL_VALVE, PVTFILE, PVTTABLE.
    In the absence of some keywords, the program uses the default values.

    Attributes:
        content (List[str]): List of strings.
        n_content (int): Dimension of content.
        joint_length (float): JOINTLENGTH keyword. Default to 12.0.
        segment_length (float): SEGMENTLENGTH keyword. Default to 0.0.
        pvt_file (str): The pvt file content.
        pvt_file_name (str): The pvt file name.
        completion_table (pd.DataFrame): ....
        wsegaicd_table (pd.DataFrame): AUTONOMOUS_INFLOW_CONTROL_DEVICE.
        wsegsicd_table (pd.DataFrame): INFLOW_CONTROL_DEVICE.
        wsegvalv_table (pd.DataFrame): WELL_SEGMENTS_VALVE.
        wsegicv_table (pd.DataFrame): INFLOW_CONTROL_VALVE.
        wsegdensity_table (pd.DataFrame): DENSITY_DRIVEN.
        wsegdualrcp_table (pd.DataFrame): DUAL_RATE_CONTROLLED_PRODUCTION.
        strict (bool): USE_STRICT. If TRUE it will exit if any lateral is not defined in the case-file. Default to TRUE.
        lat2device (pd.DataFrame): LATERAL_TO_DEVICE.
        gp_perf_devicelayer (bool): GRAVEL_PACKED_PERFORATED_DEVICELAYER. If TRUE all wells with
            gravel pack and perforation completion are given a device layer.
            If FALSE (default) all wells with this type of completions are untouched by Completor.
    """

    def __init__(self, case_file: str, schedule_file: str | None = None, output_file: str | None = None):
        """Initialize ReadCasefile.

        Args:
            case_file: Case/input file name.
            schedule_file: Schedule/well file if not defined in case file.
            output_file: File to write output to.

        """
        self.case_file = case_file.splitlines()
        self.content = clean_file_lines(self.case_file, "--")
        self.n_content = len(self.content)

        # assign default values
        self.joint_length = 12.0
        self.minimum_segment_length: float = 0.0
        self.strict = True
        self.gp_perf_devicelayer = False
        self.schedule_file = schedule_file
        self.output_file = output_file
        self.completion_table = pd.DataFrame()
        self.completion_icv_tubing = pd.DataFrame()
        self.pvt_table = pd.DataFrame()
        self.wsegaicd_table = pd.DataFrame()
        self.wsegsicd_table = pd.DataFrame()
        self.wsegvalv_table = pd.DataFrame()
        self.wsegdensity_table = pd.DataFrame()
        self.wsegdualrcp_table = pd.DataFrame()
        self.wsegicv_table = pd.DataFrame()
        self.lat2device = pd.DataFrame()
        self.mapfile: pd.DataFrame | str | None = None
        self.mapper: Mapping[str, str] | None = None

        # Run programs
        self.read_completion()
        self.read_joint_length()
        self.segment_length = self.read_segment_length()
        self.method = self.segmentation_method(self.segment_length)
        self.read_strictness()
        self.read_gp_perf_devicelayer()
        self.read_mapfile()
        self.read_wsegaicd()
        self.read_wsegvalv()
        self.read_wsegsicd()
        self.read_wsegdensity()
        self.read_wsegdualrcp()
        self.read_wsegicv()
        self.read_lat2device()
        self.read_minimum_segment_length()

    def read_completion(self) -> None:
        """Read the COMPLETION keyword in the case file.

        Raises:
            ValueError: If COMPLETION keyword is not defined in the case.
        """
        start_index, end_index = parse.locate_keyword(self.content, Keywords.COMPLETION)
        if start_index == end_index:
            raise ValueError("No completion is defined in the case file.")

        # Table headers
        header = [
            Headers.WELL,
            Headers.BRANCH,
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.INNER_DIAMETER,
            Headers.OUTER_DIAMETER,
            Headers.ROUGHNESS,
            Headers.ANNULUS,
            Headers.VALVES_PER_JOINT,
            Headers.DEVICE_TYPE,
            Headers.DEVICE_NUMBER,
        ]
        df_temp = self._create_dataframe_with_columns(header, start_index, end_index)
        # Set default value for packer segment
        df_temp = input_validation.set_default_packer_section(df_temp)
        # Set default value for PERF segments
        df_temp = input_validation.set_default_perf_section(df_temp)
        # Give errors if 1* is found for non packer segments
        df_temp = input_validation.check_default_non_packer(df_temp)
        # Fix the data types format
        df_temp = input_validation.set_format_completion(df_temp)
        # Check overall user inputs on completion
        input_validation.assess_completion(df_temp)
        df_temp = self.read_icv_tubing(df_temp)
        self.completion_table = df_temp.copy(deep=True)

    def read_icv_tubing(self, df_temp: pd.DataFrame) -> pd.DataFrame:
        """Split the ICV Tubing definition from the completion table.

        Args:
            df_temp: COMPLETION table.

        Returns:
            Updated COMPLETION table.
        """
        if not df_temp.loc[
            (df_temp[Headers.START_MEASURED_DEPTH] == df_temp[Headers.END_MEASURED_DEPTH])
            & (df_temp[Headers.DEVICE_TYPE] == Content.INFLOW_CONTROL_VALVE)
        ].empty:
            # take ICV tubing table
            self.completion_icv_tubing = df_temp.loc[
                (df_temp[Headers.START_MEASURED_DEPTH] == df_temp[Headers.END_MEASURED_DEPTH])
                & (df_temp[Headers.DEVICE_TYPE] == Content.INFLOW_CONTROL_VALVE)
            ].reset_index(drop=True)
            # drop its line
            df_temp = df_temp.drop(
                df_temp.loc[
                    (df_temp[Headers.START_MEASURED_DEPTH] == df_temp[Headers.END_MEASURED_DEPTH])
                    & (df_temp[Headers.DEVICE_TYPE] == Content.INFLOW_CONTROL_VALVE)
                ].index[:]
            ).reset_index(drop=True)
        return df_temp

    def read_lat2device(self) -> None:
        """Read the LATERAL_TO_DEVICE keyword in the case file.

        The keyword takes two arguments, a well name and a branch number.
        The branch will be connected to the device layer in the mother branch.
        If a branch number is not given, the specific branch will be connected to the
        tubing layer in the mother branch. E.g. assume that A-1 is a three branch well
        where branch 2 is connected to the tubing layer in the mother branch and
        branch 3 is connected to the device layer in the mother branch.
        The LATERAL_TO_DEVICE keyword will then look like this:

        LATERAL_TO_DEVICE
        --WELL    BRANCH
        A-1       3
        /
        """
        header = [Headers.WELL, Headers.BRANCH]
        start_index, end_index = parse.locate_keyword(self.content, Keywords.LATERAL_TO_DEVICE)

        if start_index == end_index:
            # set default behaviour (if keyword not in case file)
            self.lat2device = pd.DataFrame([], columns=header)  # empty df
            return
        self.lat2device = self._create_dataframe_with_columns(header, start_index, end_index)
        input_validation.validate_lateral_to_device(self.lat2device, self.completion_table)
        self.lat2device[Headers.BRANCH] = self.lat2device[Headers.BRANCH].astype(np.int64)

    def read_joint_length(self) -> None:
        """Read the JOINTLENGTH keyword in the case file."""
        start_index, end_index = parse.locate_keyword(self.content, Keywords.JOINT_LENGTH)
        if end_index == start_index + 2:
            self.joint_length = float(self.content[start_index + 1])
            if self.joint_length <= 0:
                logger.warning("Invalid joint length. It is set to default 12.0 m")
                self.joint_length = 12.0
        else:
            logger.info("No joint length is defined. It is set to default 12.0 m")

    def read_segment_length(self) -> float | str:
        """Read the SEGMENTLENGTH keyword in the case file.

        Raises:
            CompletorError: If SEGMENTLENGTH is not float or string.
        """
        start_index, end_index = parse.locate_keyword(self.content, Keywords.SEGMENT_LENGTH)
        if end_index == start_index + 2:
            try:
                return float(self.content[start_index + 1])
            except ValueError:
                return self.content[start_index + 1]

        else:
            logger.info(
                "SEGMENTLENGTH keyword undefined, using default strategy 'cells' "
                "to create segments based on the grid dimensions."
            )
            return 0.0

    @staticmethod
    def segmentation_method(segment_length: float | str) -> Method:
        """Determine the method of segmentation, and log the implication to info.

        Args:
            segment_length: The string or number value from the SEGMENTLENGTH keyword.

        Returns:
            The method used to create the segments.

        Raises:
            ValueError: If value of segment_length is invalid.
        """
        if isinstance(segment_length, float):
            if segment_length > 0.0:
                logger.info("Segments are defined per fixed %s meters.", segment_length)
                return Method.FIX
            if segment_length == 0.0:
                logger.info("Segments are defined based on the grid dimensions.")
                return Method.CELLS
            if segment_length < 0.0:
                logger.info(
                    "Segments are defined based on the COMPLETION keyword. "
                    "Attempting to pick segments' measured depth from case file."
                )
                return Method.USER

        if isinstance(segment_length, str):
            if "welsegs" in segment_length.lower() or "infill" in segment_length.lower():
                logger.info(
                    "Segments are defined based on the WELL_SEGMENTS%s keyword. "
                    "Retaining the original tubing segment structure.",
                    Keywords.WELL_SEGMENTS,
                )
                return Method.WELSEGS
            if "cell" in segment_length.lower():
                logger.info("Segment lengths are created based on the grid dimensions.")
                return Method.CELLS
            if "user" in segment_length.lower():
                logger.info(
                    "Segments are defined based on the COMPLETION keyword. "
                    "Attempting to pick segments' measured depth from casefile."
                )
                return Method.USER
        raise CompletorError(
            f"Unrecognized method for SEGMENTLENGTH keyword '{segment_length}'. The value should be one of: "
            f"'{Keywords.WELL_SEGMENTS}', 'CELLS', 'USER'. "
            "Alternatively a negative number for 'USER', zero for 'CELLS', or positive number for 'FIX'.",
        )

    def read_strictness(self) -> None:
        """Read the USE_STRICT keyword in the case file.

        If USE_STRICT = True the program exits if a branch in the schedule file is not defined in the case file.
        The default value is True, meaning that to allow for Completor to ignore missing branches in the case file,
        it has to be set to False.
        This feature was introduced when comparing Completor with a different advanced well modelling
        tool using a complex simulation model.

        Best practice: All branches in all wells should be defined in the case file.
        """
        start_index, end_index = parse.locate_keyword(self.content, Keywords.USE_STRICT)
        if end_index == start_index + 2:
            strict = self.content[start_index + 1]
            if strict.upper() == "FALSE":
                self.strict = False
        logger.info("case-strictness is set to %d", self.strict)

    def read_gp_perf_devicelayer(self) -> None:
        """Read the GRAVEL_PACKED_PERFORATED_DEVICELAYER keyword in the case file.

        If GRAVEL_PACKED_PERFORATED_DEVICELAYER = True the program assigns a device layer to
        wells with GP PERF type completions. If GRAVEL_PACKED_PERFORATED_DEVICELAYER = False, the
        program does not add a device layer to the well. I.e. the well is
        untouched by the program. The default value is False.
        """
        start_index, end_index = parse.locate_keyword(self.content, Keywords.GRAVEL_PACKED_PERFORATED_DEVICELAYER)
        if end_index == start_index + 2:
            gp_perf_devicelayer = self.content[start_index + 1]
            self.gp_perf_devicelayer = gp_perf_devicelayer.upper() == "TRUE"
        logger.info("gp_perf_devicelayer is set to %s", self.gp_perf_devicelayer)

    def read_minimum_segment_length(self) -> None:
        """Read the MINIMUM_SEGMENT_LENGTH keyword in the case file.

        The default value is 0.0, meaning that no segments are lumped by this keyword.
        The program will continue to coalesce segments until all segments are longer than the given minimum.
        """
        start_index, end_index = parse.locate_keyword(self.content, Keywords.MINIMUM_SEGMENT_LENGTH)
        if end_index == start_index + 2:
            min_seg_len = self.content[start_index + 1]
            self.minimum_segment_length = input_validation.validate_minimum_segment_length(min_seg_len)
        logger.info("minimum_segment_length is set to %s", self.minimum_segment_length)

    def read_mapfile(self) -> None:
        """Read the MAP_FILE keyword in the case file (if any) into a mapper."""
        start_index, end_index = parse.locate_keyword(self.content, Keywords.MAP_FILE)
        if end_index == start_index + 2:
            # the content is in between the keyword and the /
            self.mapfile = parse.remove_string_characters(self.content[start_index + 1])
            self.mapper = _mapper(self.mapfile)

    def read_wsegvalv(self) -> None:
        """Read the WELL_SEGMENTS_VALVE keyword in the case file.

        Raises:
            CompletorError: If WESEGVALV is not defined and VALVE is used in COMPLETION. If the device number is not found.
        """
        start_index, end_index = parse.locate_keyword(self.content, Keywords.WELL_SEGMENTS_VALVE)
        if start_index == end_index:
            if Content.VALVE in self.completion_table[Headers.DEVICE_TYPE]:
                raise CompletorError("WELL_SEGMENTS_VALVE keyword must be defined, if VALVE is used in the completion.")
        else:
            # Table headers
            header = [
                Headers.DEVICE_NUMBER,
                Headers.FLOW_COEFFICIENT,
                Headers.FLOW_CROSS_SECTIONAL_AREA,
                Headers.ADDITIONAL_PIPE_LENGTH_FRICTION_PRESSURE_DROP,
            ]
            try:
                df_temp = self._create_dataframe_with_columns(header, start_index, end_index)
                df_temp[Headers.MAX_FLOW_CROSS_SECTIONAL_AREA] = np.nan
            except CaseReaderFormatError:
                header += [Headers.MAX_FLOW_CROSS_SECTIONAL_AREA]
                df_temp = self._create_dataframe_with_columns(header, start_index, end_index)

            self.wsegvalv_table = input_validation.set_format_wsegvalv(df_temp)
            device_checks = self.completion_table[self.completion_table[Headers.DEVICE_TYPE] == Content.VALVE][
                Headers.DEVICE_NUMBER
            ].to_numpy()
            if not check_contents(device_checks, self.wsegvalv_table[Headers.DEVICE_NUMBER].to_numpy()):
                raise CompletorError(
                    f"Not all device in {Keywords.COMPLETION} is specified in {Keywords.WELL_SEGMENTS_VALVE}"
                )

    def read_wsegsicd(self) -> None:
        """Read the INFLOW_CONTROL_DEVICE keyword in the case file.

        Raises:
            CompletorError: If INFLOW_CONTROL_DEVICE is not defined and ICD is used in COMPLETION,
                or if the device number is not found.
                If not all devices in COMPLETION are specified in INFLOW_CONTROL_DEVICE.
        """
        start_index, end_index = parse.locate_keyword(self.content, Keywords.INFLOW_CONTROL_DEVICE)
        if start_index == end_index:
            if Content.INFLOW_CONTROL_DEVICE in self.completion_table[Headers.DEVICE_TYPE]:
                raise CompletorError(
                    f"{Keywords.INFLOW_CONTROL_DEVICE} keyword must be defined, if ICD is used in the completion."
                )
        else:
            # Table headers
            header = [
                Headers.DEVICE_NUMBER,
                Headers.STRENGTH,
                Headers.CALIBRATION_FLUID_DENSITY,
                Headers.CALIBRATION_FLUID_VISCOSITY,
                Headers.WATER_CUT,
            ]
            self.wsegsicd_table = input_validation.set_format_wsegsicd(
                self._create_dataframe_with_columns(header, start_index, end_index)
            )
            # Check if the device in COMPLETION is exist in INFLOW_CONTROL_DEVICE
            device_checks = self.completion_table[
                self.completion_table[Headers.DEVICE_TYPE] == Content.INFLOW_CONTROL_DEVICE
            ][Headers.DEVICE_NUMBER].to_numpy()
            if not check_contents(device_checks, self.wsegsicd_table[Headers.DEVICE_NUMBER].to_numpy()):
                raise CompletorError(f"Not all device in COMPLETION is specified in {Keywords.INFLOW_CONTROL_DEVICE}")

    def read_wsegaicd(self) -> None:
        """Read the AUTONOMOUS_INFLOW_CONTROL_DEVICE keyword in the case file.

        Raises:
            ValueError: If invalid entries in AUTONOMOUS_INFLOW_CONTROL_DEVICE.
            CompletorError: If AUTONOMOUS_INFLOW_CONTROL_DEVICE is not defined, and AICD is used in COMPLETION,
                or if the device number is not found.
                If all devices in COMPLETION are not specified in AUTONOMOUS_INFLOW_CONTROL_DEVICE.
        """
        start_index, end_index = parse.locate_keyword(self.content, Keywords.AUTONOMOUS_INFLOW_CONTROL_DEVICE)
        if start_index == end_index:
            if Content.AUTONOMOUS_INFLOW_CONTROL_DEVICE in self.completion_table[Headers.DEVICE_TYPE]:
                raise CompletorError(
                    f"{Keywords.AUTONOMOUS_INFLOW_CONTROL_DEVICE} keyword must be defined, "
                    "if AICD is used in the completion."
                )
        else:
            # Table headers
            header = [
                Headers.DEVICE_NUMBER,
                Headers.STRENGTH,
                Headers.X,
                Headers.Y,
                Headers.A,
                Headers.B,
                Headers.C,
                Headers.D,
                Headers.E,
                Headers.F,
                Headers.AICD_CALIBRATION_FLUID_DENSITY,
                Headers.AICD_FLUID_VISCOSITY,
            ]
            self.wsegaicd_table = input_validation.set_format_wsegaicd(
                self._create_dataframe_with_columns(header, start_index, end_index)
            )
            device_checks = self.completion_table[
                self.completion_table[Headers.DEVICE_TYPE] == Content.AUTONOMOUS_INFLOW_CONTROL_DEVICE
            ][Headers.DEVICE_NUMBER].to_numpy()
            if not check_contents(device_checks, self.wsegaicd_table[Headers.DEVICE_NUMBER].to_numpy()):
                raise CompletorError(
                    f"Not all device in COMPLETION is specified in {Keywords.AUTONOMOUS_INFLOW_CONTROL_DEVICE}"
                )

    def read_wsegdensity(self) -> None:
        """Read the DENSITY_DRIVEN keyword in the case file.

        Raises:
            ValueError: If there are invalid entries in DENSITY_DRIVEN.
            CompletorError: If not all device in COMPLETION is specified in DENSITY_DRIVEN.
                If DENSITY_DRIVEN keyword not defined, when DENSITY is used in the completion.
        """
        density_index = parse.locate_keyword(self.content, Keywords.DENSITY_DRIVEN[0])
        density_deprecated_index = parse.locate_keyword(self.content, Keywords.DENSITY_DRIVEN[1])

        # Determine which keyword is present
        if density_index[0] != density_index[1]:  # If WSEGDENSITY exists
            start_index, end_index = density_index
            DensitySelector.update_selection(use_deprecated=False)
        elif density_deprecated_index[0] != density_deprecated_index[1]:  # If WSEGDAR exists
            start_index, end_index = density_deprecated_index
            DensitySelector.update_selection(use_deprecated=True)
        else:
            start_index, end_index = 0, 0  # Default values when no keyword is found

        if start_index == end_index:
            if DensitySelector.get_selected(Content.DENSITY_DRIVEN) in self.completion_table[Headers.DEVICE_TYPE]:
                raise CompletorError(
                    f"{DensitySelector.get_selected(Keywords.DENSITY_DRIVEN)} keyword must be defined, if DENSITY is used in the completion"
                )
        else:
            # Table headers
            header = [
                Headers.DEVICE_NUMBER,
                Headers.FLOW_COEFFICIENT,
                Headers.OIL_FLOW_CROSS_SECTIONAL_AREA,
                Headers.GAS_FLOW_CROSS_SECTIONAL_AREA,
                Headers.WATER_FLOW_CROSS_SECTIONAL_AREA,
                Headers.WATER_HOLDUP_FRACTION_LOW_CUTOFF,
                Headers.WATER_HOLDUP_FRACTION_HIGH_CUTOFF,
                Headers.GAS_HOLDUP_FRACTION_LOW_CUTOFF,
                Headers.GAS_HOLDUP_FRACTION_HIGH_CUTOFF,
            ]

            # Fix table format
            if (self.completion_table[Headers.DEVICE_TYPE].str.contains(DensitySelector.get_selected(Content.DENSITY_DRIVEN)).any()):
                self.wsegdensity_table = input_validation.set_format_wsegdensity(
                    self._create_dataframe_with_columns(header, start_index, end_index)
                )
                device_checks = self.completion_table[
                    self.completion_table[Headers.DEVICE_TYPE] == DensitySelector.get_selected(Content.DENSITY_DRIVEN)
                ][Headers.DEVICE_NUMBER].to_numpy()
                if not check_contents(device_checks, self.wsegdensity_table[Headers.DEVICE_NUMBER].to_numpy()):
                    raise CompletorError(
                        f"Not all device in COMPLETION is specified in {DensitySelector.get_selected(Keywords.DENSITY_DRIVEN)}"
                    )

    def read_wsegdualrcp(self) -> None:
        """Read the DUAL_RATE_CONTROLLED_PRODUCTION keyword in the case file.

        Raises:
            ValueError: If invalid entries in DUAL_RATE_CONTROLLED_PRODUCTION.
            CompletorError: DUAL_RATE_CONTROLLED_PRODUCTION keyword not defined when DUALRCP is used in completion.
                If all devices in COMPLETION are not specified in DUAL_RATE_CONTROLLED_PRODUCTION.
        """
        dualrcp_index = parse.locate_keyword(self.content, Keywords.DUAL_RATE_CONTROLLED_PRODUCTION[0])
        dualrcp_deprecated_index = parse.locate_keyword(self.content, Keywords.DUAL_RATE_CONTROLLED_PRODUCTION[1])

        # Determine which keyword is present
        if dualrcp_index[0] != dualrcp_index[1]:  # If WSEGDUALRCP exists
            start_index, end_index = dualrcp_index
            DualrcpSelector.update_selection(use_deprecated=False)
        elif dualrcp_deprecated_index[0] != dualrcp_deprecated_index[1]:  # If WSEGAICV exists
            start_index, end_index = dualrcp_deprecated_index
            DualrcpSelector.update_selection(use_deprecated=True)
        else:
            start_index, end_index = 0, 0  # Default values when no keyword is found

        if start_index == end_index:
            if DualrcpSelector.get_selected(Content.DUAL_RATE_CONTROLLED_PRODUCTION) in self.completion_table[Headers.DEVICE_TYPE]:
                raise CompletorError(
                    f"{DualrcpSelector.get_selected(Keywords.DUAL_RATE_CONTROLLED_PRODUCTION)} keyword must be defined, "
                    "if DUALRCP is used in the completion."
                )
        else:
            # Table headers
            header = [
                Headers.DEVICE_NUMBER,
                Headers.DUALRCP_WATER_CUT,
                Headers.DUALRCP_GAS_HOLDUP_FRACTION,
                Headers.DUALRCP_CALIBRATION_FLUID_DENSITY,
                Headers.DUALRCP_FLUID_VISCOSITY,
                Headers.ALPHA_MAIN,
                Headers.X_MAIN,
                Headers.Y_MAIN,
                Headers.A_MAIN,
                Headers.B_MAIN,
                Headers.C_MAIN,
                Headers.D_MAIN,
                Headers.E_MAIN,
                Headers.F_MAIN,
                Headers.ALPHA_PILOT,
                Headers.X_PILOT,
                Headers.Y_PILOT,
                Headers.A_PILOT,
                Headers.B_PILOT,
                Headers.C_PILOT,
                Headers.D_PILOT,
                Headers.E_PILOT,
                Headers.F_PILOT,
            ]
            # Fix table format
            self.wsegdualrcp_table = input_validation.set_format_wsegdualrcp(
                self._create_dataframe_with_columns(header, start_index, end_index)
            )
            # Check if the device in COMPLETION is exist in DUAL_RATE_CONTROLLED_PRODUCTION
            device_checks = self.completion_table[
                self.completion_table[Headers.DEVICE_TYPE] == DualrcpSelector.get_selected(Content.DUAL_RATE_CONTROLLED_PRODUCTION)
            ][Headers.DEVICE_NUMBER].to_numpy()
            if not check_contents(device_checks, self.wsegdualrcp_table[Headers.DEVICE_NUMBER].to_numpy()):
                raise CompletorError(
                    f"Not all devices in COMPLETION are specified in {DualrcpSelector.get_selected(Keywords.DUAL_RATE_CONTROLLED_PRODUCTION)}"
                )

    def read_wsegicv(self) -> None:
        """Read INFLOW_CONTROL_VALVE keyword in the case file.

        Raises:
            ValueError: If invalid entries in INFLOW_CONTROL_VALVE.
            CompletorError: INFLOW_CONTROL_VALVE keyword not defined when ICV is used in completion.
        """

        start_index, end_index = parse.locate_keyword(self.content, Keywords.INFLOW_CONTROL_VALVE)
        if start_index == end_index:
            if Content.INFLOW_CONTROL_VALVE in self.completion_table[Headers.DEVICE_TYPE]:
                raise CompletorError("INFLOW_CONTROL_VALVE keyword must be defined, if ICV is used in the completion")
        else:
            # Table headers
            header = [Headers.DEVICE_NUMBER, Headers.FLOW_COEFFICIENT, Headers.FLOW_CROSS_SECTIONAL_AREA]
            try:
                df_temp = self._create_dataframe_with_columns(header, start_index, end_index)
                df_temp[Headers.MAX_FLOW_CROSS_SECTIONAL_AREA] = np.nan
            except CaseReaderFormatError:
                header += [Headers.MAX_FLOW_CROSS_SECTIONAL_AREA]
                df_temp = self._create_dataframe_with_columns(header, start_index, end_index)
            # Fix format
            self.wsegicv_table = input_validation.set_format_wsegicv(df_temp)
            # Check if the device in COMPLETION exists in INFLOW_CONTROL_VALVE
            device_checks = self.completion_table[
                self.completion_table[Headers.DEVICE_TYPE] == Content.INFLOW_CONTROL_VALVE
            ][Headers.DEVICE_NUMBER].to_numpy()
            if not check_contents(device_checks, self.wsegicv_table[Headers.DEVICE_NUMBER].to_numpy()):
                raise CompletorError("Not all device in COMPLETION is specified in INFLOW_CONTROL_VALVE")

    def get_completion(self, well_name: str | None, branch: int) -> pd.DataFrame:
        """Create the COMPLETION table for the selected well and branch.

        Args:
            well_name: Well name.
            branch: Branch/lateral number.

        Returns:
            COMPLETION for that well and branch.
        """
        df_temp = self.completion_table[self.completion_table[Headers.WELL] == well_name]
        df_temp = df_temp[df_temp[Headers.BRANCH] == branch]
        return df_temp

    def check_input(self, well_name: str, well_data: WellData) -> None:
        """Ensure that the completion table (given in the case-file) is complete.

        If one branch is completed, all branches must be completed, unless not 'strict'.
        This function relates to the USE_STRICT <bool> keyword used in the case file.
        When a branch is undefined in the case file, but appears in the schedule file,
        the completion selected by Completor is gravel packed perforations if USE_STRICT is set to False.

        Args:
            well_name: Well name.
            schedule_data: Schedule file data.

        Returns:
            COMPLETION for that well and branch.

        Raises:
            CompletorError: If strict is true and there are undefined branches.
        """
        if sorted(list(well_data.keys())) != Keywords.main_keywords:
            found_keys = set(well_data.keys())
            raise CompletorError(
                f"Well '{well_name}' is missing keyword(s): '{', '.join(set(Keywords.main_keywords) - found_keys)}'!"
            )
        df_completion = self.completion_table[self.completion_table.WELL == well_name]
        # Check that all branches are defined in the case-file.

        # TODO(#173): Use TypedDict for this, and remove the type: ignore.
        branch_nos = set(well_data[Keywords.COMPLETION_SEGMENTS][Headers.BRANCH]).difference(  # type: ignore
            set(df_completion[Headers.BRANCH])
        )
        if len(branch_nos):
            logger.warning("Well %s has branch(es) not defined in case-file", well_name)
            if self.strict:
                raise CompletorError("USE_STRICT True: Define all branches in case file.")

            for branch_no in branch_nos:
                logger.warning("Adding branch %s for Well %s", branch_no, well_name)
                # copy first entry
                lateral = pd.DataFrame(
                    [self.completion_table.loc[self.completion_table.WELL == well_name].iloc[0]],
                    columns=self.completion_table.columns,
                )
                lateral[Headers.START_MEASURED_DEPTH] = 0
                lateral[Headers.END_MEASURED_DEPTH] = 999999
                lateral[Headers.DEVICE_TYPE] = Content.PERFORATED
                lateral[Headers.ANNULUS] = Content.GRAVEL_PACKED
                lateral[Headers.BRANCH] = branch_no
                # add new entry
                self.completion_table = pd.concat([self.completion_table, lateral])

    def connect_to_tubing(self, well_name: str, lateral: int) -> bool:
        """Connect a branch to the tubing- or device-layer.

        Args:
            well_name: Well name.
            lateral: Lateral number.

        Returns:
            TRUE if lateral is connected to tubing layer.
            FALSE if lateral is connected to device layer.
        """
        laterals = self.lat2device[self.lat2device.WELL == well_name].BRANCH
        if lateral in laterals.to_numpy():
            return False
        return True

    def _create_dataframe_with_columns(
        self, header: list[str], start_index: int, end_index: int, keyword: str | None = None
    ) -> pd.DataFrame:
        """Helper method to create a dataframe with given columns' header and content.

        Args:
            header: List of column names.
            start_index: From (but not including) where in `self.content`.
            end_index: to where to include in the body of the table.

        Returns:
            Combined DataFrame.

        Raises:
            CaseReaderFormatError: If keyword is malformed, or has different amount of data than the header.
        """
        if keyword is None:
            keyword = self.content[start_index]
        table_header = " ".join(header)
        # Handle weirdly formed keywords.
        if start_index + 1 == end_index or self.content[start_index + 1].endswith("/"):
            content_str = "\n".join(self.content[start_index + 1 :]) + "\n"
            # (?<=\/) - positive look-behind for slash newline
            # \/{1}   - match exactly one slash
            #  (?=\n) - positive look-ahead for newline
            match = re.search(r"(?<=\/\n{1})\/{1}(?=\n)", content_str)
            if match is None:
                raise CaseReaderFormatError(
                    "Cannot determine correct end of record '/' for keyword.", self.case_file, header, keyword
                )
            end_record = match.span()[0]
            # From keyword to the end (without the last slash)
            content_ = content_str[:end_record].split("/\n")[:-1]
            content_ = [line.strip() for line in content_]
            table_content = "\n".join(content_) + "\n"
        else:
            table_content = "\n".join(self.content[start_index + 1 : end_index])

        header_len = len(table_header.split())
        content_list_len = [len(line.split()) for line in table_content.splitlines()]
        if not all(header_len == x for x in content_list_len):
            message = (
                "Problem with case file. Note that the COMPLETION keyword takes "
                "exactly 11 (eleven) columns. Blank portion is now removed.\n"
            )
            raise CaseReaderFormatError(message, lines=self.case_file, header=header, keyword=keyword)

        table = table_header + "\n" + table_content

        df_temp = pd.read_csv(StringIO(table), sep=" ", dtype="object", index_col=False)
        return parse.remove_string_characters(df_temp)


def check_contents(values: npt.NDArray[Any], reference: npt.NDArray[Any]) -> bool:
    """Check if all members of a list is in another list.

    Args:
        values: Array to be evaluated.
        reference: Reference array.

    Returns:
        True if members of values are present in reference, false otherwise.
    """
    return all(comp in reference for comp in values)
