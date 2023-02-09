"""Test functions for the Completor read_casefile module."""

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from completor.exceptions import CaseReaderFormatError  # type: ignore
from completor.main import get_content_and_path  # type: ignore
from completor.read_casefile import ReadCasefile  # type: ignore

_TESTDIR = Path(__file__).absolute().parent / "data"
with open(Path(_TESTDIR / "case.testfile"), encoding="utf-8") as case_file:
    _THECASE = ReadCasefile(case_file.read())


def test_read_case_completion():
    """Test the function which reads the COMPLETION keyword."""
    df_true = pd.DataFrame(
        [
            ["A1", 1, 0.0, 1000.0, 0.1, 0.2, 1e-4, "OA", 3, "AICD", 1],
            ["A1", 2, 500, 1000, 0.1, 0.2, 1e-4, "GP", 0, "VALVE", 1],
            ["A2", 1, 0, 500, 0.1, 0.2, 1e-5, "OA", 3, "DAR", 1],
            ["A2", 1, 500, 500, 0, 0, 0, "PA", 0.0, "PERF", 0],
            ["A2", 1, 500, 1000, 0.1, 0.2, 1e-4, "OA", 0.0, "PERF", 0],
            ["A3", 1, 0, 1000, 0.1, 0.2, 1e-4, "OA", 3, "AICD", 2],
            ["A3", 2, 500, 1000, 0.1, 0.2, 1e-4, "GP", 1, "VALVE", 2],
            ["11", 1, 0, 500, 0.1, 0.2, 1e-4, "OA", 3, "DAR", 2],
            ["11", 1, 500, 500, 0, 0, 0, "PA", 0, "PERF", 0],
            ["11", 1, 500, 1000, 0.1, 0.2, 1e-4, "OA", 3, "AICV", 2],
