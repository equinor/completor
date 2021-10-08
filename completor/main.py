"""Main module of Completor."""

from __future__ import annotations

import argparse
import logging
import os
import re
import time
from collections.abc import Callable, Mapping
from typing import overload

import numpy as np

import completor
from completor import parse
from completor.completion import WellSchedule
from completor.constants import Keywords
from completor.create_output import CreateOutput
from completor.create_wells import CreateWells
from completor.logger import handle_error_messages, logger
from completor.read_casefile import ReadCasefile
from completor.utils import abort, clean_file_line, clean_file_lines, get_completor_version
from completor.visualization import close_figure, create_pdfpages

try:
    from typing import Literal
except ImportError:
    pass


def create_get_well_name(schedule_lines: dict[int, str]) -> Callable[[int], str]:
    """
    Create a function to get the well name from line number.

    Args:
        schedule_lines: All lines in schedule file

    Returns:
        get_well_name (Function)
    """
    keys = np.array(sorted(list(schedule_lines.keys())))

    def get_well_name(line_number: int) -> str:
        """
        Get well name for WELSEGS or COMPSEGS.

        Assumes that line_number points to one of these keywords.

        Args:
            line_number: Line number

        Returns:
            Well name

        """
        i = (keys == line_number).nonzero()[0][0]
        next_line = schedule_lines[keys[i + 1]]
        return next_line.split()[0]

    return get_well_name


def format_chunk(chunk_str: str) -> list[list[str]]:
    """
    Format the data-records and resolve the repeat-mechanism of Eclipse.

    E.g. 3* == 1* 1* 1*, 3*250 == 250 250 250

    Args:
        chunk_str: A chunk data-record

    Returns:
        Expanded Eclipse values
    """
    chunk = re.split(r"\s+/", chunk_str)[:-1]
