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
        ],
        columns=[
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
        ],
    )

    pd.testing.assert_frame_equal(df_true, _THECASE.completion_table, check_exact=False, rtol=0.0001)


def test_read_case_joint_length():
    """Test the function which reads the JOINTLENGTH keyword."""
    assert _THECASE.joint_length == 14.0, "Failed joint length"


def test_read_case_segment_length():
    """Test the function which reads SEGMENTLENGTH keyword."""
    assert _THECASE.segment_length == 12.0, "Failed segment length"


def test_read_case_wsegvalv():
    """Test the function which reads WSEGVALV keyword."""
    df_true = pd.DataFrame(
        [
            ["VALVE", 1, 0.85, 0.01, "5*", 0.04],
            ["VALVE", 2, 0.95, 0.02, "5*", 0.04],
        ],
        columns=["DEVICETYPE", "DEVICENUMBER", "CV", "AC", "L", "AC_MAX"],
    )
    pd.testing.assert_frame_equal(df_true, _THECASE.wsegvalv_table)


def test_read_case_wsegicv():
    """Test the function which reads WSEGVALV keyword."""
    df_true = pd.DataFrame(
        [
            ["ICV", 1, 1.0, 2.0, 2.0],
            ["ICV", 2, 3, 4, 1.0],
        ],
        columns=["DEVICETYPE", "DEVICENUMBER", "CV", "AC", "AC_MAX"],
    )
    pd.testing.assert_frame_equal(df_true, _THECASE.wsegicv_table)


def test_read_case_wsegaicd():
    """Test the function which reads WSEGAICD keyword."""
    df_true = pd.DataFrame(
        [
            ["AICD", 1, 0.00021, 0.0, 1.0, 1.1, 1.2, 0.9, 1.3, 1.4, 2.1, 1000.25, 1.45],
            ["AICD", 2, 0.00042, 0.1, 1.1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1001.25, 1.55],
        ],
        columns=[
            "DEVICETYPE",
            "DEVICENUMBER",
            "ALPHA",
            "X",
            "Y",
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "RHOCAL_AICD",
            "VISCAL_AICD",
        ],
    )
    df_true["DEVICENUMBER"] = df_true["DEVICENUMBER"].astype(np.int64)
    df_true.iloc[:, 2:] = df_true.iloc[:, 2:].astype(np.float64)
    pd.testing.assert_frame_equal(df_true, _THECASE.wsegaicd_table)


def test_read_case_wsegsicd():
    """Test the function which reads WSEGSICD keyword."""
    df_true = pd.DataFrame(
        [
            ["ICD", 1, 0.001, 1000, 1.0, 0.1],
            ["ICD", 2, 0.002, 1000, 0.9, 0.2],
        ],
        columns=["DEVICETYPE", "DEVICENUMBER", "STRENGTH", "RHOCAL_ICD", "VISCAL_ICD", "WCUT"],
    )
    df_true["DEVICENUMBER"] = df_true["DEVICENUMBER"].astype(np.int64)
    df_true.iloc[:, 2:] = df_true.iloc[:, 2:].astype(np.float64)
    pd.testing.assert_frame_equal(df_true, _THECASE.wsegsicd_table)


def test_read_case_wsegdar():
    """Test the function which reads WSEGDAR keyword."""
    df_true = pd.DataFrame(
        [
            ["DAR", 1, 0.1, 0.4, 0.3, 0.2, 0.6, 0.70, 0.8, 0.9],
            ["DAR", 2, 0.1, 0.4, 0.3, 0.2, 0.5, 0.60, 0.7, 0.8],
        ],
        columns=[
            "DEVICETYPE",
            "DEVICENUMBER",
            "CV_DAR",
            "AC_OIL",
            "AC_GAS",
            "AC_WATER",
            "WHF_LCF_DAR",
            "WHF_HCF_DAR",
            "GHF_LCF_DAR",
            "GHF_HCF_DAR",
        ],
    )
    df_true["DEVICENUMBER"] = df_true["DEVICENUMBER"].astype(np.int64)
    df_true.iloc[:, 2:] = df_true.iloc[:, 2:].astype(np.float64)
    pd.testing.assert_frame_equal(df_true, _THECASE.wsegdar_table)


def test_new_dar_old_parameters():
    """Test the function which reads WSEGDAR keyword."""
    with open(Path(_TESTDIR / "dar.testfile"), encoding="utf-8") as old_dar_case:
        _OLDDARCASE = old_dar_case.read()

    with pytest.raises(CaseReaderFormatError) as err:
        ReadCasefile(_OLDDARCASE)

    expected_err = "Too few entries in data for keyword 'WSEGDAR', expected 9"
    assert expected_err in str(err.value)


def test_read_case_wsegaicv():
    """Test the function which reads WSEGAICV keyword."""
