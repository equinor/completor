"""Test functions for Completor end point installation."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

_TESTDIR_DROGON = Path(__file__).absolute().parent / "data" / "drogon"


def test_run_completor(tmpdir):
    """Test Completor for command line run. Schedule included on command line."""
    shutil.copy(_TESTDIR_DROGON / "perf_gp.case", tmpdir)
    shutil.copy(_TESTDIR_DROGON / "drogon_input.sch", tmpdir)
    tmpdir.chdir()
    subprocess.run(
        ["completor", "-i", "perf_gp.case", "-s", "drogon_input.sch", "-o", "perf_gp.out"], check=True, shell=False
    )
    assert Path("perf_gp.out").is_file()
    assert os.path.getsize("perf_gp.out") > 0


def test_run_completor_schedule_in_case(tmpdir):
    """Test Completor with schedule file given in the case file and not in the CLI."""
    shutil.copy(_TESTDIR_DROGON / "perf_gp.case", tmpdir)
    shutil.copy(_TESTDIR_DROGON / "drogon_input.sch", tmpdir)
    tmpdir.chdir()
    subprocess.run(["completor", "-i", "perf_gp.case", "-o", "perf_gp.out"], check=True, shell=False)
    assert Path("perf_gp.out").is_file()
    assert os.path.getsize("perf_gp.out") > 0


def test_run_completor_without_schedule(tmpdir):
    """Test Completor without input schedule file."""
    shutil.copy(_TESTDIR_DROGON / "perf_gp_nosched.case", tmpdir)
    tmpdir.chdir()
    with pytest.raises(subprocess.CalledProcessError) as err:
        subprocess.run(
            ["completor", "-i", "perf_gp_nosched.case", "-o", "perf_gp_nosched.out"], check=True, shell=False
        )
    assert err.value.returncode == 1
    assert not Path("perf_gp_nosched.out").is_file()


def test_figure(tmpdir):
    """Test Completor for command line run including figure option."""
    shutil.copy(_TESTDIR_DROGON / "perf_gp.case", tmpdir)
    shutil.copy(_TESTDIR_DROGON / "drogon_input.sch", tmpdir)
    tmpdir.chdir()
    subprocess.run(
        ["completor", "-i", "perf_gp.case", "-s", "drogon_input.sch", "-o", "perf_gp.out", "--figure"],
        check=True,
        shell=False,
    )
    assert Path("perf_gp.out").is_file()
    assert os.path.getsize("perf_gp.out") > 0
    assert Path("Well_schematic_001.pdf").is_file()
    assert os.path.getsize("Well_schematic_001.pdf") > 0


def test_run_completor_without_output(tmpdir):
    """Test Completor for command line run excluding output file option."""
    shutil.copy(_TESTDIR_DROGON / "perf_gp.case", tmpdir)
    shutil.copy(_TESTDIR_DROGON / "drogon_input.sch", tmpdir)
    tmpdir.chdir()
    subprocess.run(["completor", "-i", "perf_gp.case", "-s", "drogon_input.sch"], check=True, shell=False)
    assert Path("drogon_input_advanced.wells").is_file()
    assert os.path.getsize("drogon_input_advanced.wells") > 0


def test_run_completor_without_schedule_output(tmpdir):
    """Test Completor for command line run excluding output file option."""
    shutil.copy(_TESTDIR_DROGON / "perf_gp.case", tmpdir)
    shutil.copy(_TESTDIR_DROGON / "drogon_input.sch", tmpdir)
    tmpdir.chdir()
    subprocess.run(["completor", "-i", "perf_gp.case"], check=True, shell=False)
    assert Path("drogon_input_advanced.wells").is_file()
    assert os.path.getsize("drogon_input_advanced.wells") > 0
