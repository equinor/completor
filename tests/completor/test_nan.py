"""Test Completor NaN in COMPDAT to output schedule file."""

from pathlib import Path

import common

_TESTDIR = Path(__file__).absolute().parent / "data"
_TEST_FILE = "ml_well.sch"


def test_nan(tmpdir):
    """
    Test that the correct amount of output elements are produced with changing input.

    Completor should produce 1* in rows of 13 elements in the COMPDAT output when the
    input number of columns changes between 13 and 14.
    """
    tmpdir.chdir()
