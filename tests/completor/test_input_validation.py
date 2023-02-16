"""Test functions for input validation."""

from pathlib import Path

import pytest

from completor.input_validation import validate_minimum_segment_length
from completor.read_casefile import ReadCasefile

_TESTDIR = Path(__file__).absolute().parent / "data"
_TEST_FILE = "test.sch"


def test_lat2dev_with_annulus(tmpdir):
    """
    Test output to screen from Completor.

    """
    tmpdir.chdir()
    with pytest.raises(SystemExit) as e:
        with open(Path(_TESTDIR / "case_lat2dev.testfile"), encoding="utf-8") as case_file:
            ReadCasefile(case_file.read())
    assert e.type == SystemExit


def test_validate_minimum_segment_length():
    """
    Test the validate_minimum_segment_length function.
    """

    with pytest.raises(SystemExit):
        validate_minimum_segment_length("DUMMY")

    with pytest.raises(SystemExit):
        validate_minimum_segment_length(-5.0)
