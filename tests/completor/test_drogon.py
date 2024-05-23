"""Test function for Completor with Drogon."""

from pathlib import Path

import pytest
import utils

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
    case_path = Path(_TESTDIR_DROGON / drogon_case)
    with open(case_path, encoding="utf-8") as case_file:
        lines = [line.strip("\n") for line in case_file.readlines()]
    schedule_name = lines[lines.index("SCHFILE") + 1]
    schedule_path = Path(_TESTDIR_DROGON / schedule_name)
    true_file = Path(_TESTDIR_DROGON / drogon_case.replace(".case", ".true"))
    utils.open_files_run_create(case_path, schedule_path, _TEST_FILE)
    utils.assert_results(true_file, _TEST_FILE)
