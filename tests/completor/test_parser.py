"""Test functions for the Completor parser module."""

from pathlib import Path

import numpy as np

from completor import parse  # type: ignore

_TESTDIR = Path(__file__).absolute().parent / "data"


def test_unpack_record():
    """
    Test unpack_records handles eclipse multiple values correctly.

    E.g. 3* should be unpacked to 1*, 1*, 1*, and 2*10 unpacked to 10, 10.
    """
    tested = ["3", "2*", "1", "6*"]
    true = ["3", "1*", "1*", "1", "1*", "1*", "1*", "1*", "1*", "1*"]
    assert parse.unpack_records(tested) == true


def test_locate_keyword():
