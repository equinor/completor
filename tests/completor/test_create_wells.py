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
