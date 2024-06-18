"""Test Completor NaN in COMPDAT to output schedule file."""

from pathlib import Path

import utils

_TESTDIR = Path(__file__).absolute().parent / "data"
_TEST_FILE = "ml_well.sch"


def test_nan(tmpdir):
    """Test that the correct numbers of output elements are produced with changing input.

    Completor should produce 1* in rows of 13 elements in the COMPDAT output when the
    input number of columns changes between 13 and 14.
    """
    tmpdir.chdir()
    case_file = Path(_TESTDIR / "nan.casefile")
    schedule_file = Path(_TESTDIR / "nan.sch")
    true_file = Path(_TESTDIR / "nan.true")
    utils.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    utils.assert_results(true_file, _TEST_FILE)


def test_nan_2(tmpdir):
    """Test that the correct numbers of output elements are produced with fixed input.

    Completor should produce 1* in rows with 13 elements in the COMPDAT output when the
    input number of columns is 13.
    """
    tmpdir.chdir()
    case_file = Path(_TESTDIR / "nan.casefile")
    schedule_file = Path(_TESTDIR / "nan2.sch")
    true_file = Path(_TESTDIR / "nan2.true")
    utils.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    utils.assert_results(true_file, _TEST_FILE)
