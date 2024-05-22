"""Test functions for the Completor parser module."""

from pathlib import Path

import numpy as np

from completor import parse  # type: ignore

_TESTDIR = Path(__file__).absolute().parent / "data"


def test_unpack_record():
    """
    Test unpack_records handles multiple values correctly.

    E.g. 3* should be unpacked to 1*, 1*, 1*, and 2*10 unpacked to 10, 10.
    """
    tested = ["3", "2*", "1", "6*"]
    true = ["3", "1*", "1*", "1", "1*", "1*", "1*", "1*", "1*", "1*"]
    assert parse.unpack_records(tested) == true


def test_locate_keyword():
    """Test locate_keyword find the correct start and end indexes of keywords."""
    test1 = ["COMPDAT", "1 2 3 /", "/", "COMPDAT", "2 3 4 /", "/"]

    start_compdat, end_compdat = parse.locate_keyword(test1, "COMPDAT", "/", take_first=False)
    np.testing.assert_array_equal(start_compdat, [0, 3])
    np.testing.assert_array_equal(end_compdat, [2, 5])
