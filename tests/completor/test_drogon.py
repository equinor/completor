"""Test function for Completor with Drogon."""

from pathlib import Path

import common
import pytest

_TESTDIR_DROGON = Path(__file__).absolute().parent / "data" / "drogon"
_TEST_FILE = "test.sch"


with open(_TESTDIR_DROGON / "test_cases.files", encoding="utf-8") as file:
    CASE_FILES = file.readlines()


@pytest.mark.parametrize(
    "drogon_case",
    [pytest.param(line.strip("\n")) for line in CASE_FILES if not line.startswith("--")],
)
def test_drogons(drogon_case, tmpdir):
    """Test Completor with Drogon cases."""

    # Copy pvt file to tmpdir before creating schedule files
    tmpdir.chdir()
