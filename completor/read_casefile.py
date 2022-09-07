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
