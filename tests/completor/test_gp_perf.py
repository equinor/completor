"""Test that Completor does not add a device layer for completions with GP PERF only."""

from pathlib import Path

import utils_for_tests

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
    """Test Completor case with only gravel packs and perforation.

    No GP_PERF_DEVICELAYER keyword set, default to False.
    """
    tmpdir.chdir()
    utils_for_tests.open_files_run_create(GP_PERF_BASE_CASE, WELL_DEFINITION, _TEST_FILE)
    utils_for_tests.assert_results(WELL_DEFINITION, _TEST_FILE)


def test_gp_perf_false(tmpdir):
    """Test Completor case with only gravel packs and perforation.

    GP_PERF_DEVICELAYER keyword explicitly set to False.
    """
    tmpdir.chdir()
    case_file = f"""
    {GP_PERF_BASE_CASE}

    GP_PERF_DEVICELAYER
     FALSE
    /
    """
    utils_for_tests.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    utils_for_tests.assert_results(WELL_DEFINITION, _TEST_FILE)


def test_gp_perf_true(tmpdir):
    """Test Completor case with only gravel packs and perforation.

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
    utils_for_tests.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_mix_in_branch(tmpdir):
    """Test completor case with gp_perf and aicd in same branch.

    GP_PERF_DEVICELAYER not set.
    """
    tmpdir.chdir()
    case_file = """
    COMPLETION
    A1 1 0    2024 0.2 0.25 1.00E-4 GP 0 PERF 0
    A1 1 2024 3000 0.2 0.25 1.00E-4 GP 1 AICD 1
    /

    WSEGAICD
    1   0.00021 0.0 1.0 1.1 1.2 0.9 1.3 1.4 2.1 1000.25    1.45
    /
    """
    true_file = Path(_TESTDIR / "wb_perf_mix_inbranch.true")
    utils_for_tests.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_mix_multibranch(tmpdir):
    """Test completor case with gp_perf and aicd in two different branches.

    GP_PERF_DEVICELAYER not set.
    """
    tmpdir.chdir()
    case_file = """
    COMPLETION
    A1 1 0 3000 0.2 0.25 1.00E-4 GP 0 PERF 0
    A1 2 0 3000 0.2 0.25 1.00E-4 GP 1 AICD 1
    /

    WSEGAICD
    1   0.00021 0.0 1.0 1.1 1.2 0.9 1.3 1.4 2.1 1000.25    1.45
    /
    """
    with open(Path(_TESTDIR / "welldefinition_2branch.testfile"), encoding="utf-8") as f:
        schedule_file = f.read()
    true_file = Path(_TESTDIR / "wb_perf_mix_multibranch.true")
    utils_for_tests.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)
