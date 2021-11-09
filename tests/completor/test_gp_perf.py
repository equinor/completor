"""Test that Completor does not add a device layer for completions with GP PERF only."""

from pathlib import Path

import common

_TESTDIR = Path(__file__).absolute().parent / "data"
_TEST_FILE = "test.sch"

with open(Path(_TESTDIR / "welldefinition.testfile"), encoding="utf-8") as file:
    WELL_DEFINITION = file.read()

GP_PERF_BASE_CASE = """
COMPLETION
A1 1 0 3000 0.2 0.25 1.00E-4 GP 0 PERF 0
/
"""


def test_gp_perf_default(tmpdir):
    """
    Test Completor case with only gravel packs and perforation.

    No GP_PERF_DEVICELAYER keyword (default to False).
    """
    tmpdir.chdir()
    common.open_files_run_create(GP_PERF_BASE_CASE, WELL_DEFINITION, _TEST_FILE)
    common.assert_results(WELL_DEFINITION, _TEST_FILE)


def test_gp_perf_false(tmpdir):
    """
    Test Completor case with only gravel packs and perforation.

    GP_PERF_DEVICELAYER keyword explicitly set to False.
    """
    tmpdir.chdir()
    case_file = f"""
    {GP_PERF_BASE_CASE}

    GP_PERF_DEVICELAYER
     FALSE
    /
    """
    common.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    common.assert_results(WELL_DEFINITION, _TEST_FILE)


def test_gp_perf_true(tmpdir):
    """
    Test Completor case with only gravel packs and perforation.

    GP_PERF_DEVICELAYER keyword explicitly set to True.
    """
    tmpdir.chdir()
    case_file = f"""
    {GP_PERF_BASE_CASE}

    GP_PERF_DEVICELAYER
     TRUE
    /
    """
    true_file = Path(_TESTDIR / "wb_perf.true")
    common.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_mix_in_branch(tmpdir):
