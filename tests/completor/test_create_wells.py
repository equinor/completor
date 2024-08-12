"""Test functions for well creation."""

from __future__ import annotations

from pathlib import Path

import pytest
import utils

from completor.constants import Method  # type: ignore
from completor.exceptions import CompletorError
from completor.read_casefile import ReadCasefile  # type: ignore

_TESTDIR = Path(__file__).absolute().parent / "data"
_TEST_FILE = "test.sch"


def test_duplicates(tmpdir):
    """Test completor case with duplicated entries in COMPDAT and COMPSEGS.

    Completor produces a number for the second COMPDAT entry, but it is a mistake.
    """
    tmpdir.chdir()
    case_file = Path(_TESTDIR / "duplicate.case")
    schedule_file = Path(_TESTDIR / "duplicate.sch")
    true_file = Path(_TESTDIR / "duplicate.true")
    utils.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    utils.assert_results(true_file, _TEST_FILE)


@pytest.mark.parametrize(
    "segment_length,expected",
    [
        pytest.param("", Method.CELLS, id="default"),
        pytest.param("User", Method.USER, id="user"),
        pytest.param("WELseGs", Method.WELSEGS, id="welsegs"),
        pytest.param("infill", Method.WELSEGS, id="infill"),
        pytest.param("Cell", Method.CELLS, id="cells"),
        # Test number values (i.e. it can be cast to float).
        pytest.param("22", Method.FIX, id="fix_float"),
        pytest.param("-1", Method.USER, id="user_float)"),
        pytest.param("0", Method.CELLS, id="cells_float"),
    ],
)
def test_segment_creation_method(segment_length, expected):
    """Test _method maps string and number input to correct SegmentCreationMethod."""

    case_obj = f"""
COMPLETION
    A1  1     0   2000  0.150  0.216  0.123  GP  0  ICD  1
    A1  1  2000  99999  0.150  0.216  0.123  GP  0  ICD  1
/
WSEGSICD
    1  0.00123  1234.00  1.23  0.1
/
USE_STRICT
    TRUE
/
SEGMENTLENGTH
    {segment_length}
/
"""
    # Test default value
    case_obj = ReadCasefile(case_obj, "dummy_value.sch")
    assert case_obj.method == expected


def test_error_segment_creation_method():
    case_obj = """
COMPLETION
A1  1     0   2000  0.150  0.216  0.123  GP  0  ICD  1
A1  1  2000  99999  0.150  0.216  0.123  GP  0  ICD  1
/
WSEGSICD
1  0.00123  1234.00  1.23  0.1
/
USE_STRICT
TRUE
/
SEGMENTLENGTH
NON_VALID_INPUT
/
"""
    # Test default value
    with pytest.raises(CompletorError) as e:
        ReadCasefile(case_obj, "dummy_value.sch")
    assert "Unrecognized method for SEGMENTLENGTH keyword 'NON_VALID_INPUT'" in str(e.value)


def test_tubing_segment_icv(tmpdir):
    """Test completor case with ICV to create a special tubing segmentation.

    Completor will produce mixes of tubing segmentation between lumped and default.
    """
    tmpdir.chdir()
    case_file = Path(_TESTDIR / "icv_tubing.case")
    schedule_file = Path(_TESTDIR / "icv_sch.sch")
    true_file = Path(_TESTDIR / "icv_tubing.true")
    utils.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    utils.assert_results(true_file, _TEST_FILE)
