from __future__ import annotations

import re
from collections.abc import Mapping
from io import StringIO

import numpy as np
import pandas as pd

from completor import input_validation as val
from completor import parse
from completor.completion import WellSchedule
from completor.constants import Headers
from completor.exceptions import CaseReaderFormatError
from completor.logger import logger
from completor.utils import abort, clean_file_lines


def _mapper(map_file: str) -> dict[str, str]:
    """
    Read two-column file and store data as values and keys in a dictionary.

    Used to map between pre-processing tools and reservoir simulator file names.

    Args:
        map_file: Two-column text file

    Returns:
        Dictionary of key and values taken from the mapfile
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
    """
    Class for reading Completor case files.

    This class reads the case/input file of the Completor program.
    It reads the following keywords:
    SCHFILE, OUTFILE, COMPLETION, SEGMENTLENGTH, JOINTLENGTH
    WSEGAICD, WSEGVALV, WSEGSICD, WSEGDAR, WSEGAICV, WSEGICV, PVTFILE, PVTTABLE.
    In the absence of some keywords, the program uses the default values.

    Attributes:
        content (List[str]): List of strings
        n_content (int): Dimension of content
        joint_length (float): JOINTLENGTH keyword. Default: 12.0
        segment_length (float): SEGMENTLENGTH keyword. Default: 0.0
        pvt_file (str): The pvt file content
        pvt_file_name (str): The pvt file name
        completion_table (pd.DataFrame): ...
        wsegaicd_table (pd.DataFrame): WSEGAICD
        wsegsicd_table (pd.DataFrame): WSEGSICD
        wsegvalv_table (pd.DataFrame): WSEGVALV
        wsegicv_table (pd.DataFrame): WSEGICV
        wsegdar_table (pd.DataFrame): WSEGDAR
        wsegaicv_table (pd.DataFrame): WSEGAICV
        strict (bool): USE_STRICT. If TRUE it will exit if
            any lateral is not defined in the case-file. Default: TRUE
        lat2device (pd.DataFrame): LATERAL_TO_DEVICE
        gp_perf_devicelayer (bool): GP_PERF_DEVICELAYER. If TRUE all wells with
            gravel pack and perforation completion are given a device layer. If FALSE
            (default) all wells with this type of completions are untouched by Completor


    See the following functions for a description of the DataFrame formats:
    * `wsegvalv_table <wsegvalv_table>`
    * `wsegsicd_table <wsegsicd_table>`
    * `wsegaicd_table <wsegaicd_table>`
    * `wsegdar_table <wsegdar_table>`
    * `wsegaicv_table <wsegaicv_table>`
    * `lat2device <lat2device>`

    """

    def __init__(self, case_file: str, schedule_file: str | None = None, output_file: str | None = None):
        """
        Initialize ReadCasefile.

        Args:
            case_file: Case/input file name
            user_schedule_file: Schedule/well file if not defined in case file
            user_pvt: PVT file if not defined in case file

        """
        self.case_file = case_file.splitlines()
        self.content = clean_file_lines(self.case_file, "--")
        self.n_content = len(self.content)

        # assign default values
        self.joint_length = 12.0
        self.segment_length: float | str = 0.0
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
        self.wsegdar_table = pd.DataFrame()
        self.wsegaicv_table = pd.DataFrame()
        self.wsegicv_table = pd.DataFrame()
        self.lat2device = pd.DataFrame()
        self.mapfile: pd.DataFrame | str | None = None
        self.mapper: Mapping[str, str] | None = None

        # Run programs
        self.read_completion()
        self.read_joint_length()
        self.read_segment_length()
        self.read_strictness()
        self.read_gp_perf_devicelayer()
        self.read_mapfile()
        self.read_wsegaicd()
        self.read_wsegvalv()
        self.read_wsegsicd()
        self.read_wsegdar()
        self.read_wsegaicv()
        self.read_wsegicv()
        self.read_lat2device()
        self.read_minimum_segment_length()

    def read_completion(self) -> None:
        """
        Read the COMPLETION keyword in the case file.

        Raises:
            ValueError: If COMPLETION keyword is not defined in the case.

        The COMPLETION keyword information is stored in a class property
        DataFrame ``self.completion_table`` with the following format:

        .. list-table:: completion_table
          :widths: 10 10
          :header-rows: 1

          * - COLUMN
            - TYPE
          * - WELL
            - str
          * - BRANCH
            - int
          * - STARTMD
            - float
          * - ENDMD
            - float
          * - INNER_DIAMETER
            - float
          * - OUTER_DIAMETER
            - float
          * - ROUGHNESS
            - float
          * - ANNULUS
            - str
          * - NVALVEPERJOINT
            - float
          * - DEVICETYPE
            - str
          * - DEVICENUMBER
            - int

        """
        start_index, end_index = self.locate_keyword("COMPLETION")
        if start_index == end_index:
            raise ValueError("No completion is defined in the case file.")

        # Table headers
        header = [
            Headers.WELL,
            Headers.BRANCH,
            Headers.START_MD,
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
        df_temp = val.set_default_packer_section(df_temp)
        # Set default value for PERF segments
        df_temp = val.set_default_perf_section(df_temp)
        # Give errors if 1* is found for non packer segments
        df_temp = val.check_default_non_packer(df_temp)
        # Fix the data types format
        df_temp = val.set_format_completion(df_temp)
        # Check overall user inputs on completion
        val.assess_completion(df_temp)
        df_temp = self.read_icv_tubing(df_temp)
        self.completion_table = df_temp.copy(deep=True)

    def read_icv_tubing(self, df_temp: pd.DataFrame) -> pd.DataFrame:
        """
        Split the ICV Tubing definition from the completion table

        Args:
            df_temp: COMPLETION table

        Returns:
            Updated COMPLETION table

        """
        if not df_temp.loc[
            (df_temp[Headers.START_MD] == df_temp[Headers.END_MEASURED_DEPTH]) & (df_temp[Headers.DEVICE_TYPE] == "ICV")
        ].empty:
            # take ICV tubing table
            self.completion_icv_tubing = df_temp.loc[
                (df_temp[Headers.START_MD] == df_temp[Headers.END_MEASURED_DEPTH])
                & (df_temp[Headers.DEVICE_TYPE] == "ICV")
            ].reset_index(drop=True)
            # drop its line
            df_temp = df_temp.drop(
                df_temp.loc[
                    (df_temp[Headers.START_MD] == df_temp[Headers.END_MEASURED_DEPTH])
                    & (df_temp[Headers.DEVICE_TYPE] == "ICV")
                ].index[:]
            ).reset_index(drop=True)
        return df_temp

    def read_lat2device(self) -> None:
        """
        Read the LATERAL_TO_DEVICE keyword in the case file.

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

        The LATERAL_TO_DEVICE keyword information is stored in a class property
        DataFrame ``lat2device`` with the following format:

        .. _lat2device:
        .. list-table:: lat2device
           :widths: 10 10
           :header-rows: 1

           * - COLUMN
             - TYPE
           * - WELL
             - str
           * - BRANCH
             - int

        """
        # Table headers
        header = [Headers.WELL, Headers.BRANCH]
        start_index, end_index = self.locate_keyword("LATERAL_TO_DEVICE")

        if start_index == end_index:
            # set default behaviour (if keyword not in case file)
            self.lat2device = pd.DataFrame([], columns=header)  # empty df
            return
        self.lat2device = self._create_dataframe_with_columns(header, start_index, end_index)
        val.validate_lateral2device(self.lat2device, self.completion_table)
        self.lat2device[Headers.BRANCH] = self.lat2device[Headers.BRANCH].astype(np.int64)

    def read_joint_length(self) -> None:
        """Read the JOINTLENGTH keyword in the case file."""
        start_index, end_index = self.locate_keyword("JOINTLENGTH")
        if end_index == start_index + 2:
            self.joint_length = float(self.content[start_index + 1])
            if self.joint_length <= 0:
                logger.warning("Invalid joint length. It is set to default 12.0 m")
                self.joint_length = 12.0
        else:
            logger.info("No joint length is defined. It is set to default 12.0 m")

    def read_segment_length(self) -> None:
        """
        Read the SEGMENTLENGTH keyword in the case file.

        Raises:
            SystemExit: If SEGMENTLENGTH is not float or string.

        """
        start_index, end_index = self.locate_keyword("SEGMENTLENGTH")
        if end_index == start_index + 2:
            try:
                self.segment_length = float(self.content[start_index + 1])
                # 'Fix' method if value is positive.
                if self.segment_length > 0.0:
                    logger.info("Segments are defined per %s meters.", self.segment_length)
                # 'User' method if value is negative.
                elif self.segment_length < 0.0:
                    logger.info(
                        "Segments are defined based on the COMPLETION keyword. "
                        "Attempting to pick segments' measured depth from .case file."
                    )
                # 'Cells' method if value is zero.
                elif self.segment_length == 0:
                    logger.info("Segments are defined based on the grid dimensions.")

            except ValueError:
                try:
                    self.segment_length = str(self.content[start_index + 1])
                    # 'Welsegs' method
                    if "welsegs" in self.segment_length.lower() or "infill" in self.segment_length.lower():
                        logger.info(
                            "Segments are defined based on the WELSEGS keyword. "
                            "Retaining the original tubing segment structure."
                        )
                    # 'User' method if value is negative
                    elif "user" in self.segment_length.lower():
                        logger.info(
                            "Segments are defined based on the COMPLETION keyword. "
                            "Attempting to pick segments' measured depth from casefile."
                        )
                    # 'Cells' method
                    elif "cell" in self.segment_length.lower():
                        logger.info("Segment lengths are created based on the grid dimensions.")
                except ValueError as err:
                    raise abort("SEGMENTLENGTH takes number or string") from err
        else:
            # 'Cells' method if value is 0.0 or undefined
            logger.info("No segment length is defined. " "Segments are created based on the grid dimension.")

    def read_strictness(self) -> None:
        """
        Read the USE_STRICT keyword in the case file.

        If USE_STRICT = True the program exits if a branch in the schedule file
        is not defined in the case file. The default value is True, meaning that
        to allow for Completor to ignore missing branches in the case file it
        has to be set to False. This feature was introduced when comparing
        Completor with a different advanced well modelling tool using a complex
        simulation model.

        Best practice: All branches in all wells should be defined in the case file.

        """
        start_index, end_index = self.locate_keyword("USE_STRICT")
        if end_index == start_index + 2:
            strict = self.content[start_index + 1]
            if strict.upper() == "FALSE":
                self.strict = False
        logger.info("case-strictness is set to %d", self.strict)

    def read_gp_perf_devicelayer(self) -> None:
        """
        Read the GP_PERF_DEVICELAYER keyword in the case file.

        If GP_PERF_DEVICELAYER = True the program assigns a device layer to
        wells with GP PERF type completions. If GP_PERF_DEVICELAYER = False, the
        program does not add a device layer to the well. I.e. the well is
        untouched by the program. The default value is False.

        """
        start_index, end_index = self.locate_keyword("GP_PERF_DEVICELAYER")
        if end_index == start_index + 2:
            gp_perf_devicelayer = self.content[start_index + 1]
            self.gp_perf_devicelayer = gp_perf_devicelayer.upper() == "TRUE"
        logger.info("gp_perf_devicelayer is set to %s", self.gp_perf_devicelayer)

    def read_minimum_segment_length(self) -> None:
        """
        Read the MINIMUM_SEGMENT_LENGTH keyword in the case file.
        The default value is 0.0, meaning that no segments are lumped by this
        keyword. The program will continue to coalesce segments until all
        segments are longer than the given minimum.
        """
        start_index, end_index = self.locate_keyword("MINIMUM_SEGMENT_LENGTH")
        if end_index == start_index + 2:
            min_seg_len = self.content[start_index + 1]
            self.minimum_segment_length = val.validate_minimum_segment_length(min_seg_len)
        logger.info("minimum_segment_length is set to %s", self.minimum_segment_length)

    def read_mapfile(self) -> None:
        """Read the MAPFILE keyword in the case file (if any) into a mapper."""
        start_index, end_index = self.locate_keyword("MAPFILE")
        if end_index == start_index + 2:
            # the content is in between the keyword and the /
            self.mapfile = parse.remove_string_characters(self.content[start_index + 1])
            self.mapper = _mapper(self.mapfile)
        else:
            self.mapfile = None
            self.mapper = None

    def read_wsegvalv(self) -> None:
        """
        Read the WSEGVALV keyword in the case file.

        Raises:
            SystemExit: If WESEGVALV is not defined and VALVE is used in COMPLETION. \
                If the device number is not found. \

        The function uses the class property DataFrame completion_table defined
        in ``read_completion``.  The function sets the class property DataFrame
        vsegvalv_table with the following format:

        .. _wsegvalv_table:
        .. list-table:: wsegvalv_table
            :widths: 10 10
            :header-rows: 1

            * - COLUMN
              - TYPE
            * - DEVICETYPE
              - str
            * - DEVICENUMBER
              - int
            * - CV
              - float
            * - AC
              - float
            * - L
              - float
            * - Ac_Max (optional)
              - float

        """
        start_index, end_index = self.locate_keyword("WSEGVALV")
        if start_index == end_index:
            if "VALVE" in self.completion_table[Headers.DEVICE_TYPE]:
                raise abort("WSEGVALV keyword must be defined, " "if VALVE is used in the completion")
        else:
            # Table headers
            header = [Headers.DEVICE_NUMBER, Headers.CV, Headers.AC, Headers.L]
            try:
                df_temp = self._create_dataframe_with_columns(header, start_index, end_index)
                df_temp[Headers.AC_MAX] = np.nan
            except CaseReaderFormatError:
                header += [Headers.AC_MAX]
                df_temp = self._create_dataframe_with_columns(header, start_index, end_index)

            self.wsegvalv_table = val.set_format_wsegvalv(df_temp)
            device_checks = self.completion_table[self.completion_table[Headers.DEVICE_TYPE] == "VALVE"][
                Headers.DEVICE_NUMBER
            ].to_numpy()
            if not check_contents(device_checks, self.wsegvalv_table[Headers.DEVICE_NUMBER].to_numpy()):
                raise abort("Not all device in COMPLETION is specified in WSEGVALV")

    def read_wsegsicd(self) -> None:
        """
        Read the WSEGSICD keyword in the case file.

        Raises:
            SystemExit: If WSEGSICD is not defined and ICD is used in COMPLETION, \
                Or if the device number is not found. \
                If not all device in COMPLETION is specified in WSEGSICD.

        The function uses the class property DataFrame completion_table defined
        in ``read_completion``. The function generates a class property
        DataFrame wsegsicd_table with the following format:

        .. _wsegsicd_table:
        .. list-table:: wsegsicd_table
            :widths: 10 10
            :header-rows: 1

            * - COLUMN
              - TYPE
            * - DEVICETYPE
              - str
            * - DEVICENUMBER
              - int
            * - STRENGTH
              - float
            * - RHOCAL_ICD
              - float
            * - VISCAL_ICD
              - float
            * - WCUT
              - float

        """
        start_index, end_index = self.locate_keyword("WSEGSICD")
        if start_index == end_index:
            if "ICD" in self.completion_table[Headers.DEVICE_TYPE]:
                raise abort("WSEGSICD keyword must be defined, " "if ICD is used in the completion")
        else:
            # Table headers
            header = [Headers.DEVICE_NUMBER, Headers.STRENGTH, Headers.RHOCAL_ICD, Headers.VISCAL_ICD, Headers.WCUT]
            self.wsegsicd_table = val.set_format_wsegsicd(
                self._create_dataframe_with_columns(header, start_index, end_index)
            )
            # Check if the device in COMPLETION is exist in WSEGSICD
            device_checks = self.completion_table[self.completion_table[Headers.DEVICE_TYPE] == "ICD"][
                Headers.DEVICE_NUMBER
            ].to_numpy()
            if not check_contents(device_checks, self.wsegsicd_table[Headers.DEVICE_NUMBER].to_numpy()):
                raise abort("Not all device in COMPLETION is specified in WSEGSICD")

    def read_wsegaicd(self) -> None:
        """
        Read the WSEGAICD keyword in the case file.

        Raises:
            ValueError: If invalid entries in WSEGAICD.
            SystemExit: If WSEGAICD is not defined and AICD is used in COMPLETION, \
                or if the device number is not found. \
                If not all device in COMPLETION is specified in WSEGAICD.

        The function uses the class property DataFrame completion_table defined
        in ``read_completion``. It generates a class property DataFrame
        wsegaicd_table with the following format:

        .. _wsegaicd_table:
        .. list-table:: wsegaicd_table
            :widths: 10 10
            :header-rows: 1

            * - COLUMN
              - TYPE
            * - DEVICETYPE
              - str
            * - DEVICENUMBER
              - int
            * - ALPHA
              - float
            * - X
              - float
            * - Y
              - float
            * - A
              - float
            * - B
              - float
            * - C
              - float
            * - D
              - float
            * - E
              - float
            * - F
              - float
            * - RHOCAL_AICD
              - float
            * - VISCAL_AICD
              - float

        """
        start_index, end_index = self.locate_keyword("WSEGAICD")
        if start_index == end_index:
            if "AICD" in self.completion_table[Headers.DEVICE_TYPE]:
                raise abort("WSEGAICD keyword must be defined, " "if AICD is used in the completion")
        else:
            # Table headers
            header = [
                Headers.DEVICE_NUMBER,
                Headers.ALPHA,
                Headers.X,
                Headers.Y,
                Headers.A,
                Headers.B,
                Headers.C,
                Headers.D,
                Headers.E,
                Headers.F,
                Headers.RHOCAL_AICD,
                Headers.VISCAL_AICD,
            ]
            # Fix table format
            self.wsegaicd_table = val.set_format_wsegaicd(
                self._create_dataframe_with_columns(header, start_index, end_index)
            )
            device_checks = self.completion_table[self.completion_table[Headers.DEVICE_TYPE] == "AICD"][
                Headers.DEVICE_NUMBER
            ].to_numpy()
            if not check_contents(device_checks, self.wsegaicd_table[Headers.DEVICE_NUMBER].to_numpy()):
                raise abort("Not all device in COMPLETION is specified in WSEGAICD")

    def read_wsegdar(self) -> None:
        """
        Read the WSEGDAR keyword in the case file.

        Raises:
            ValueError: If there are invalid entries in WSEGDAR
            SystemExit: If not all device in COMPLETION is specified in WSEGDAR. \
                If WSEGDAR keyword not defined, when DAR is used in the completion.

        The function uses the class property DataFrame completion_table defined
        in ``read_completion``. It generates a class property
        DataFrame wsegdar_table with the following format:

        .. _wsegdar_table:
        .. list-table:: wsegdar_table
            :widths: 10 10
            :header-rows: 1

            * - COLUMN
              - TYPE
            * - DEVICETYPE
              - str
            * - DEVICENUMBER
              - int
            * - CV_DAR
              - float
            * - AC_OIL
              - float
            * - AC_GAS
              - float
            * - AC_WATER
              - float
            * - WHF_LCF_DAR
              - float
            * - WHF_HCF_DAR
              - float
            * - GHF_LCF_DAR
              - float
            * - GHF_HCF_DAR
              - float

        """
        start_index, end_index = self.locate_keyword("WSEGDAR")
        if start_index == end_index:
            if "DAR" in self.completion_table[Headers.DEVICE_TYPE]:
                raise abort("WSEGDAR keyword must be defined, if DAR is used in the completion")
        else:
            # Table headers
            header = [
                Headers.DEVICE_NUMBER,
                Headers.CV_DAR,
                Headers.AC_OIL,
                Headers.AC_GAS,
                Headers.AC_WATER,
                Headers.WHF_LCF_DAR,
                Headers.WHF_HCF_DAR,
                Headers.GHF_LCF_DAR,
                Headers.GHF_HCF_DAR,
            ]

            # Fix table format
            if self.completion_table[Headers.DEVICE_TYPE].str.contains("DAR").any():
                self.wsegdar_table = val.set_format_wsegdar(
                    self._create_dataframe_with_columns(header, start_index, end_index)
                )
                device_checks = self.completion_table[self.completion_table[Headers.DEVICE_TYPE] == "DAR"][
                    Headers.DEVICE_NUMBER
                ].to_numpy()
                if not check_contents(device_checks, self.wsegdar_table[Headers.DEVICE_NUMBER].to_numpy()):
                    raise abort("Not all device in COMPLETION is specified in WSEGDAR")

    def read_wsegaicv(self) -> None:
        """
        Read the WSEGAICV keyword in the case file.

        Raises:
            ValueError: If invalid entries in WSEGAICV.
            SystemExit: WSEGAICV keyword not defined when AICV is used in completion.\
                If not all devices in COMPLETION are specified in WSEGAICV.


        The function uses the class property DataFrame completion_table defined
        in ``read_completion``. It generates a class property
        DataFrame wsegaicv_table with the following format:

        .. _wsegaicv_table:
        .. list-table:: wsegaicv_table
            :widths: 10 10
            :header-rows: 1

            * - COLUMN
              - TYPE
            * - DEVICETYPE
              - str
            * - DEVICENUMBER
              - int
            * - WCT_AICV
              - float
            * - GHF_AICV
              - float
            * - RHOCAL_AICV
              - float
            * - VISCAL_AICV
              - float
            * - ALPHA_MAIN
              - float
            * - X_MAIN
              - float
            * - Y_MAIN
              - float
            * - A_MAIN
              - float
            * - B_MAIN
              - float
            * - C_MAIN
              - float
            * - D_MAIN
              - float
            * - E_MAIN
              - float
            * - F_MAIN
              - float
            * - ALPHA_PILOT
              - float
            * - X_PILOT
              - float
            * - Y_PILOT
              - float
            * - A_PILOT
              - float
            * - B_PILOT
              - float
            * - C_PILOT
              - float
            * - D_PILOT
              - float
            * - E_PILOT
              - float
            * - F_PILOT
              - float


        """
        start_index, end_index = self.locate_keyword("WSEGAICV")
        if start_index == end_index:
            if "AICV" in self.completion_table[Headers.DEVICE_TYPE]:
                raise abort("WSEGAICV keyword must be defined, " "if AICV is used in the completion")
        else:
            # Table headers
            header = [
                Headers.DEVICE_NUMBER,
                Headers.WCT_AICV,
                Headers.GHF_AICV,
                Headers.RHOCAL_AICV,
                Headers.VISCAL_AICV,
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
            self.wsegaicv_table = val.set_format_wsegaicv(
                self._create_dataframe_with_columns(header, start_index, end_index)
            )
            # Check if the device in COMPLETION is exist in WSEGAICV
            device_checks = self.completion_table[self.completion_table[Headers.DEVICE_TYPE] == "AICV"][
                Headers.DEVICE_NUMBER
            ].to_numpy()
            if not check_contents(device_checks, self.wsegaicv_table[Headers.DEVICE_NUMBER].to_numpy()):
                raise abort("Not all devices in COMPLETION are specified in WSEGAICV")

    def read_wsegicv(self) -> None:
        """
        Read WSEGICV keyword in the case file.

        Raises:
            ValueError: If invalid entries in WSEGICV.
            SystemExit: WSEGICV keyword not defined when ICV is used in completion.

        The function uses the class property DataFrame completion_table defined
        in ``read_completion``. It generates a class property
        DataFrame wsegicv_table with the following format:
        .. _wsegicv_table:
        .. list-table:: wsegicv_table
            :widths: 10 10
            :header-rows: 1

            * - COLUMN
              - TYPE
            * - DEVICETYPE
              - str
            * - DEVICENUMBER
              - int
            * - CV
              - float
            * - AC
              - float
            * - DEFAULTS
              - float
            * - AC_MAX
              - float
        """

        start_index, end_index = self.locate_keyword("WSEGICV")
        if start_index == end_index:
            if "ICV" in self.completion_table[Headers.DEVICE_TYPE]:
                raise abort("WSEGICV keyword must be defined, " "if ICV is used in the completion")
        else:
            # Table headers
            header = [Headers.DEVICE_NUMBER, Headers.CV, Headers.AC]
            try:
                df_temp = self._create_dataframe_with_columns(header, start_index, end_index)
                df_temp[Headers.AC_MAX] = np.nan
            except CaseReaderFormatError:
                header += [Headers.AC_MAX]
                df_temp = self._create_dataframe_with_columns(header, start_index, end_index)
            # Fix format
            self.wsegicv_table = val.set_format_wsegicv(df_temp)
            # Check if the device in COMPLETION exists in WSEGICV
            device_checks = self.completion_table[self.completion_table[Headers.DEVICE_TYPE] == "ICV"][
                Headers.DEVICE_NUMBER
            ].to_numpy()
            if not check_contents(device_checks, self.wsegicv_table[Headers.DEVICE_NUMBER].to_numpy()):
                raise abort("Not all device in COMPLETION is specified in WSEGICV")

    def get_completion(self, well_name: str | None, branch: int) -> pd.DataFrame:
        """
        Create the COMPLETION table for the selected well and branch.

        Args:
            well_name: Well name
            branch: Branch/lateral number

        Returns:
            COMPLETION for that well and branch

        The function uses the class property DataFrame completion_table defined
        in ``read_completion``.

        """
        df_temp = self.completion_table[self.completion_table[Headers.WELL] == well_name]
        df_temp = df_temp[df_temp[Headers.BRANCH] == branch]
        return df_temp

    def check_input(self, well_name: str, schedule: WellSchedule) -> None:
        """
        Ensure that the completion table (given in the case-file) is complete.

        If one branch is completed, all branches must be completed,
        unless not 'strict'. This function relates to the USE_STRICT <bool> keyword
        used in the case file. When a branch is undefined in the case file,
        but appears in the schedule file, the completion selected by Completor is gravel
        packed perforations if USE_STRICT is set to False.

        Args:
            well_name: Well name
            schedule: Schedule object

        Returns:
            COMPLETION for that well and branch

        The function updates the class property DataFrame completion_table defined
        in ``read_completion``.

        """
        msw = schedule.msws[well_name]
        compl = self.completion_table[self.completion_table.WELL == well_name]

        # check that all branches are defined in case-file
        branch_nos = set(msw["compsegs"].BRANCH).difference(set(compl.BRANCH))
        if len(branch_nos):
            logger.warning("Well %s has branch(es) not defined in case-file", well_name)
            if self.strict:
                raise abort("USE_STRICT True: Define all branches in case file.")
            else:
                for branch_no in branch_nos:
                    logger.warning("Adding branch %s for Well %s", branch_no, well_name)
                    # copy first entry
                    lateral = pd.DataFrame(
                        [self.completion_table.loc[self.completion_table.WELL == well_name].iloc[0]],
                        columns=self.completion_table.columns,
                    )
                    lateral[Headers.START_MEASURED_DEPTH] = 0
                    lateral[Headers.END_MEASURED_DEPTH] = 999999
                    lateral[Headers.DEVICE_TYPE] = "PERF"
                    lateral[Headers.ANNULUS] = "GP"
                    lateral[Headers.BRANCH] = branch_no
                    # add new entry
                    self.completion_table = pd.concat([self.completion_table, lateral])

    def connect_to_tubing(self, well_name: str, lateral: int) -> bool:
        """
        Connect a branch to the tubing- or device-layer.

        Args:
            well_name: Well name
            lateral: Lateral number

        Returns:
            TRUE if lateral is connected to tubing layer.
            FALSE if lateral is connected to device layer.

        The function uses the class property DataFrame lat2device defined in
        ``read_lat2device``.

        """
        laterals = self.lat2device[self.lat2device.WELL == well_name].BRANCH
        if lateral in laterals.to_numpy():
            return False
        return True

    def locate_keyword(self, keyword: str) -> tuple[int, int]:
        return parse.locate_keyword(self.content, keyword)

    def _create_dataframe_with_columns(
        self, header: list[str], start_index: int, end_index: int, keyword: str | None = None
    ) -> pd.DataFrame:
        """
        Helper method to create a dataframe with given columns' header and content.

        Args:
            header: List of column names
            start_index: From (but not including) where in ``self.content``
            end_index: to where to include in the body of the table

        Returns:
            Combined DataFrame.

        Raises:
            CaseReaderFormatError: If keyword is malformed,
                or has different amount of data than the header.

        """
        if keyword is None:
            keyword = self.content[start_index]
        table_header = " ".join(header)
        table_content = ""
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


def check_contents(values: np.ndarray, reference: np.ndarray) -> bool:
    """
    Check if all members of a list is in another list.

    Args:
        val_array: Array to be evaluated
        ref_array: Reference array

    Returns:
        True if members of val_array are present in ref_array, false otherwise

    """
    return all(comp in reference for comp in values)
