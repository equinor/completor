"""Tests for the icv_file_handling module"""

import os
import shutil
from pathlib import Path

from completor import initialization, read_casefile
from tests.utils_for_tests import _assert_file_output, assert_files_exist_and_nonempty, completor_runner

_TESTDIR = Path(__file__).absolute().parent / "data"
CASE_TEXT = """
SCHFILE
  'tests/icvc/data/dummy_schedule_file.sch'
/

COMPLETION
--WELL Branch Start  End   Screen    Well/ Roughness Annulus Nvalve Valve Device
--     Number    mD   mD   Tubing   Casing Roughness Content /Joint  Type Number
--                       Diameter Diameter
A-1        1    0 99999     0.10   0.2159   0.00300      GP      1  AICD      1
B-1        1    0 99999     0.10   0.2159   0.00300      GP      1  AICD      1
/

ICVCONTROL
-- D: FUD
-- H: FUH
-- FAC: Maximum rate factor for icv-control
-- FR: ICV function repetitions
-- OSTP: OPERSTEP (NEXTSTEP in operation icv-functions)
-- WSTP: WAITSTEP (NEXTSTEP in waiting icv-functions)

-- WELL ICV SEGMENT AC-TABLE  STEPS    ICVDATE  FREQ  MIN MAX OPENING
    A-1   A      97 0.1337     60    1.JAN.2033    30    0   1      0
    A-1   B      98 0.1337     60    1.JAN.2033    30    0   1      0
    B-1   C     101 0.1337     60    1.JAN.2033    30    0   1      0
    B-1   D     102 0.1337     60    1.JAN.2033    30    0   1      0
    B-1   E     103 0.1337     60    1.JAN.2033    30    0   1      0
/
"""

UPDATE_SEGMENT = """
UPDATE_SEGMENT_NUMBER
True
/"""

CASE = read_casefile.ICVReadCasefile(CASE_TEXT)
INITIALS = initialization.Initialization(CASE)
WELL_NAME = "A-1"
ICV_NAME = "A"
FILE_DATA = {
    "output_directory": "out",
    "function_prefix": "BAL",
    "schedule_file_path": "dummy_schedule_file.sch",
    "input_case_file": "initialization.case",
}


def test_create_all_include_files(tmpdir):
    """Tests the create_include_files function."""
    tmpdir.chdir()
    shutil.copy(_TESTDIR / "dummy_schedule_file.sch", tmpdir)
    shutil.copy(_TESTDIR / "initialization.case", tmpdir)

    completor_runner(inputfile="initialization.case", schedulefile="dummy_schedule_file.sch")

    assert_files_exist_and_nonempty(["include_icvc.sch"])

    with open("include_icvc.sch") as f:
        result = f.read()

    expected_method_sections = [
        "--- WELL1 A ICVMethod.CHOKE_WAIT ---",
        "--- WELL1 A ICVMethod.CHOKE ---",
        "--- WELL1 A ICVMethod.OPEN_WAIT ---",
        "--- WELL1 A ICVMethod.OPEN ---",
        "--- WELL2 G ICVMethod.OPEN_WAIT ---",
        "--- WELL2 G ICVMethod.OPEN ---",
    ]

    for section in expected_method_sections:
        assert section in result


def test_create_master_schedule_file(tmpdir):
    """Test that the master schedule file is created."""
    tmpdir.chdir()
    shutil.copy(_TESTDIR / "dummy_schedule_file.sch", tmpdir)
    shutil.copy(_TESTDIR / "initialization.case", tmpdir)

    completor_runner(inputfile="initialization.case", schedulefile="dummy_schedule_file.sch")

    assert_files_exist_and_nonempty(["dummy_schedule_file_advanced.wells"])


def test_insert_include_path_right_before_next_date(tmpdir):
    """Test that we insert the paths to the created INCLUDE files just before the next data."""
    tmpdir.chdir()
    shutil.copy(_TESTDIR / "dummy_schedule_file_with_include.sch", tmpdir)
    shutil.copy(_TESTDIR / "dummy_case.case", tmpdir)

    # Generate new file
    completor_runner(inputfile="dummy_case.case", schedulefile="dummy_schedule_file_with_include.sch")

    new_schedule_file_path = "dummy_schedule_file_with_include_advanced.wells"
    new_schedule_file = Path(new_schedule_file_path)
    assert new_schedule_file.is_file()

    expected = Path(_TESTDIR / "dummy_include_file.true")
    _assert_file_output(new_schedule_file, expected)


def test_casefile_sparse_dir_structure(tmp_path):
    """Test function for validating sparse directory structure and file copying."""
    input_dir = tmp_path / "lvl1" / "lvl2" / "lvl3"
    case = Path(input_dir / "field")
    case.mkdir(parents=True)
    sch = Path(input_dir / "include" / "schedule")
    sch.mkdir(parents=True)
    shutil.copy(_TESTDIR / "initialization.case", case)
    shutil.copy(_TESTDIR / "dummy_schedule_file.sch", sch)
    os.chdir(input_dir)

    completor_runner(inputfile="field/initialization.case", schedulefile="include/schedule/dummy_schedule_file.sch")

    assert_files_exist_and_nonempty(
        [
            "include/schedule/summary_icvc.sch",
            "include/schedule/include_icvc.sch",
            "include/schedule/dummy_schedule_file_advanced.wells",
        ]
    )
