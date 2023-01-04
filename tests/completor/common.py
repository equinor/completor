"""Common Completor test functions."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from completor import main, parse  # type: ignore
from completor.read_schedule import fix_compsegs, fix_welsegs  # type: ignore
from completor.utils import clean_file_lines  # type: ignore


def open_files_run_create(
    case: Path | str, schedule: Path | str, output: Path | str, show_figure: bool = False
) -> None:
    """
    Open files supplied as a path and convert the data to a string.

    Then run main.py's create function with the data.
    """

    if isinstance(case, Path):
        with open(case, encoding="utf-8") as file:
            case = file.read()

    if isinstance(schedule, Path):
        with open(schedule, encoding="utf-8") as file:
            schedule = file.read()

    if isinstance(output, Path):
        with open(output, encoding="utf-8") as file:
            output = file.read()

        main.create(case, schedule, output, show_figure)
    else:
        main.create(case, schedule, output)
