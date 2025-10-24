"""Test functions for icv-control end point installation."""

import os
import shutil
from pathlib import Path

import pytest

from tests.utils_for_tests import assert_files_exist_and_nonempty, completor_runner

_TESTDIR = Path(__file__).absolute().parent / "data"


def test_run_icvc(tmpdir):
    """Test icv-control for command line run. Schedule included on command line."""
    shutil.copy(_TESTDIR / "initialization.case", tmpdir)
    shutil.copy(_TESTDIR / "dummy_schedule_file.sch", tmpdir)
    tmpdir.chdir()
    completor_runner(inputfile="initialization.case", schedulefile="dummy_schedule_file.sch")

    assert_files_exist_and_nonempty(["summary_icvc.sch", "dummy_schedule_file_advanced.wells", "include_icvc.sch"])


def test_run_icvc_schedule_in_case(tmpdir):
    """Test icv-control with schedule file in the case file and not the CLI."""
    shutil.copy(_TESTDIR / "initialization.case", tmpdir)
    shutil.copy(_TESTDIR / "dummy_schedule_file.sch", tmpdir)
    tmpdir.chdir()

    completor_runner(inputfile="initialization.case", schedulefile="dummy_schedule_file.sch")

    assert_files_exist_and_nonempty(["summary_icvc.sch", "include_icvc.sch", "dummy_schedule_file_advanced.wells"])


def test_run_icvc_with_output(tmpdir):
    """Test icv-control for command line run including output file option."""
    shutil.copy(_TESTDIR / "initialization.case", tmpdir)
    shutil.copy(_TESTDIR / "dummy_schedule_file.sch", tmpdir)
    tmpdir.chdir()
    os.chdir(tmpdir)

    completor_runner(
        inputfile="initialization.case", schedulefile="dummy_schedule_file.sch", outputfile="icvcontrol_1.sch"
    )
    assert_files_exist_and_nonempty(["summary_icvc.sch", "include_icvc.sch", "icvcontrol_1.sch"], tmpdir)


def test_missing_input_case_in_main(tmpdir):
    """Test for error message with missing input schedule file"""
    tmpdir.chdir()
    with pytest.raises(FileNotFoundError) as e:
        completor_runner(inputfile="non_existing.case")
        assert "ERROR" in str(e) and "Case file does not exist" in str(e)


def test_run_icvc_without_schedule(tmpdir):
    """Test icv-control without input schedule file."""
    shutil.copy(_TESTDIR / "initialization_nosch.case", tmpdir)
    tmpdir.chdir()
    with pytest.raises(SystemExit) as e:
        completor_runner(inputfile="initialization_nosch.case")

        assert "ERROR" in str(e) and "Need input schedule" in str(e)
