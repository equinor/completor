from __future__ import annotations

import re
from collections.abc import Mapping
from io import StringIO

import numpy as np
import pandas as pd

from completor import input_validation as val
from completor import parse
from completor.completion import WellSchedule
from completor.exceptions import CaseReaderFormatError
from completor.logger import logger
from completor.utils import abort, clean_file_lines


def _mapper(map_file: str) -> dict[str, str]:
    """
    Read two-column file and store data as values and keys in a dictionary.

    Used to map between RMS and Eclipse file names.

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

    def __init__(
        self,
        case_file: str,
        schedule_file: str | None = None,
        output_file: str | None = None,
    ):
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
          * - INNER_ID
            - float
          * - OUTER_ID
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
            "WELL",
            "BRANCH",
            "STARTMD",
            "ENDMD",
            "INNER_ID",
            "OUTER_ID",
            "ROUGHNESS",
            "ANNULUS",
            "NVALVEPERJOINT",
            "DEVICETYPE",
            "DEVICENUMBER",
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
        if not df_temp.loc[(df_temp["STARTMD"] == df_temp["ENDMD"]) & (df_temp["DEVICETYPE"] == "ICV")].empty:
            # take ICV tubing table
            self.completion_icv_tubing = df_temp.loc[
                (df_temp["STARTMD"] == df_temp["ENDMD"]) & (df_temp["DEVICETYPE"] == "ICV")
            ].reset_index(drop=True)
            # drop its line
            df_temp = df_temp.drop(
                df_temp.loc[(df_temp["STARTMD"] == df_temp["ENDMD"]) & (df_temp["DEVICETYPE"] == "ICV")].index[:]
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
        header = ["WELL", "BRANCH"]
        start_index, end_index = self.locate_keyword("LATERAL_TO_DEVICE")

        if start_index == end_index:
            # set default behaviour (if keyword not in case file)
            self.lat2device = pd.DataFrame([], columns=header)  # empty df
            return
        self.lat2device = self._create_dataframe_with_columns(header, start_index, end_index)
        self.lat2device["BRANCH"] = self.lat2device["BRANCH"].astype(np.int64)
        val.validate_lateral2device(self.lat2device, self.completion_table)

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
                # 'Fix' method, if value is positive
                if self.segment_length > 0.0:
                    logger.info("Segments are defined per %s meters.", self.segment_length)
                # 'User' method if value is negative
                elif self.segment_length < 0.0:
                    logger.info(
                        "Segments are defined based on the COMPLETION keyword. "
                        "Attempting to pick segments' measured depth from .case file."
                    )
                # 'Cells' method if value is zero
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
                    raise abort("SEGMENTLENGTH takes float or string") from err
        else:
            # 'Cells' method if value is 0.0 or undefined
