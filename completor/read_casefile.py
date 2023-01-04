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
