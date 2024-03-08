"""Test functions for well creation."""

from __future__ import annotations

from pathlib import Path

import common
import pytest

from completor.constants import SegmentCreationMethod  # type: ignore
from completor.create_wells import CreateWells  # type: ignore
from completor.read_casefile import ReadCasefile  # type: ignore

_TESTDIR = Path(__file__).absolute().parent / "data"
_TEST_FILE = "test.sch"


def test_duplicates(tmpdir):
    """Test completor case with duplicated entries in COMPDAT and COMPSEGS.
    Completor produces a number for the second COMPDAT entry, but it is a mistake."""
    tmpdir.chdir()
    case_file = Path(_TESTDIR / "duplicate.case")
    schedule_file = Path(_TESTDIR / "duplicate.sch")
    true_file = Path(_TESTDIR / "duplicate.true")
    common.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_segment_creation_method():
    """Test _method maps string and number input to correct SegmentCreationMethod."""

    def replace_segment_length_value(text: str, value_to_insert: str) -> CreateWells:
        """Helper replacing segment length keyword's value and create well."""
        lines = text.splitlines()
        lines[-2] = value_to_insert
        # Reintroduce linebreaks
        text = "\n".join(lines)
        case = ReadCasefile(text, "dummy_value.sch")
        return CreateWells(case)

    base_case = """
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
JOINTLENGTH
14.0
/
SEGMENTLENGTH
0
/
"""
    # Test default value
    well = replace_segment_length_value(base_case, "")
    assert well.method == SegmentCreationMethod.CELLS

    # Test string values
    well = replace_segment_length_value(base_case, "User")
    assert well.method == SegmentCreationMethod.USER

    well = replace_segment_length_value(base_case, "WELseGs")
    assert well.method == SegmentCreationMethod.WELSEGS

    well = replace_segment_length_value(base_case, "infill")
    assert well.method == SegmentCreationMethod.WELSEGS

    well = replace_segment_length_value(base_case, "Cell")
    assert well.method == SegmentCreationMethod.CELLS

    # Test number values (i.e. it can be cast to float)
    well = replace_segment_length_value(base_case, "22")
    assert well.method == SegmentCreationMethod.FIX

    well = replace_segment_length_value(base_case, "-1")
    assert well.method == SegmentCreationMethod.USER

    well = replace_segment_length_value(base_case, "0")
    assert well.method == SegmentCreationMethod.CELLS

    with pytest.raises(ValueError):
