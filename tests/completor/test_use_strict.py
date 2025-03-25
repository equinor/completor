"""Test the Completor USE_STRICT keyword."""

from pathlib import Path

import pytest
import utils_for_tests

from completor.exceptions.clean_exceptions import CompletorError

_TESTDIR = Path(__file__).absolute().parent / "data"
_TEST_FILE = "ml_well.sch"

JOINT_LENGTH_AND_WSEGAICD = """
JOINT_LENGTH
  12
/

WSEGAICD
--Number    Alpha       x   y   a   b   c   d   e   f   rhocal  viscal      z
1           0.00021   0.0   1.0 1.1 1.2 0.9 1.3 1.4 2.1 1000.25    1.45     5
/
"""
_TESTDIR = Path(__file__).absolute().parent / "data"
_TEST_FILE = "ml_well.sch"

WSEGAICD = """
WSEGAICD
--Number    Alpha       x   y   a   b   c   d   e   f   rhocal  viscal      z
1           0.00021   0.0   1.0 1.1 1.2 0.9 1.3 1.4 2.1 1000.25    1.45     1.1
/
"""


def test_use_strict_true(tmpdir):
    """Test case file with USE_STRICT keyword set to True.

    Uses a two-branch well, A1, and both branches are defined in the case file COMPLETION keyword.

    1. One active well.
    2. Multi-lateral well with two branches.
    """
    tmpdir.chdir()
    case_file = f"""
-- Case file for testing the LATERAL_TO_DEVICE keyword.
SCHFILE
ml_well.sch
/

COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MEASURED_DEPTH   MEASURED_DEPTH  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
A1    1        0  2190.266 0.15  0.2159  0.00065   GP      0       AICD  1
A1    1 2190.266  99999    0.15  0.2159  0.00065   GP      1       AICD  1
A1    2        0  99999    0.15  0.2159  0.00065   GP      1       AICD  1
/

USE_STRICT
TRUE
/

{JOINT_LENGTH_AND_WSEGAICD}
    """
    schedule_file = Path(_TESTDIR / "ml_well.sch")
    true_file = Path(_TESTDIR / "usestrict_true.true")
    utils_for_tests.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_use_strict_true_false_default(tmpdir):
    """Test case file with USE_STRICT keyword set to True, False, and undefined.

    Uses a two-branch well, A1, and both branches are defined in the case file COMPLETION keyword.

    1. One active well.
    2. Multi-lateral well with two branches.
    """
    tmpdir.chdir()
    completion_keyword = """
COMPLETION
--Well Branch Start  End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MEASURED_DEPTH    MEASURED_DEPTH  Tubing   Casing            Content Joint   Type  Number
--                       Diameter Diameter
   A1    1     0     2190.166 0.15 0.2159  0.00065     GP     0     AICD    1
   A1    1  2190.166 99999    0.15 0.2159  0.00065     GP     1     AICD    1
   A1    2     9     99999    0.15 0.2159  0.00065     GP     1     AICD    1
/
"""

    # USESTRICT set to True
    case_use_strict_true = f"""
{completion_keyword}
USE_STRICT
  TRUE
/
{JOINT_LENGTH_AND_WSEGAICD}
"""
    schedule_file = Path(_TESTDIR / "ml_well.sch")

    true_file_strict_true = Path(_TESTDIR / "usestrict_true.true")
    utils_for_tests.open_files_run_create(case_use_strict_true, schedule_file, _TEST_FILE)
    utils_for_tests.assert_results(true_file_strict_true, _TEST_FILE)

    # Test with USESTRICT set to False
    case_use_strict_false = f"""
{completion_keyword}
USE_STRICT
  FALSE
/
{JOINT_LENGTH_AND_WSEGAICD}
"""
    true_file_strict_false = Path(_TESTDIR / "usestrict_false.true")
    utils_for_tests.open_files_run_create(case_use_strict_false, schedule_file, _TEST_FILE)
    utils_for_tests.assert_results(true_file_strict_false, _TEST_FILE)

    # USESTRICT keyword not defined
    case_use_strict_default = f"""
{completion_keyword}
{JOINT_LENGTH_AND_WSEGAICD}
"""
    true_file_strict_default = Path(_TESTDIR / "usestrict_default.true")
    utils_for_tests.open_files_run_create(case_use_strict_default, schedule_file, _TEST_FILE)
    utils_for_tests.assert_results(true_file_strict_default, _TEST_FILE)


def test_use_strict_true_missing_branch(tmpdir):
    """Test case with USE_STRICT set to True, with a missing branch.

    Uses a two-branch well, A1, where only one branch is defined in the case file COMPLETION keyword.

    1. One active well.
    2. Multi-lateral well with two branches.
    """
    tmpdir.chdir()
    case_file = f"""
-- Case file for testing the LATERAL_TO_DEVICE keyword.

SCHFILE
  ml_well.sch
/

COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MEASURED_DEPTH   MEASURED_DEPTH  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
   A1    1    0     2190.166 0.15 0.2159  0.00065     GP     0     AICD     1
   A1    1 2190.166 99999    0.15 0.2159  0.00065     GP     1     AICD     1
/

USE_STRICT
  TRUE
/

{JOINT_LENGTH_AND_WSEGAICD}
    """
    schedule_file = Path(_TESTDIR / "ml_well.sch")
    with pytest.raises(CompletorError) as e:
        utils_for_tests.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    assert "USE_STRICT True: Define all branches in case file." in str(e)


def test_use_strict_default_missing_branch(tmpdir):
    """Test case with with USE_STRICT set to True, with the default branch missing.

    Uses a two-branch well, A1, where only one branch is defined in the case file COMPLETION keyword.

    1. One active well.
    2. Multi-lateral well with two branches.
    """
    tmpdir.chdir()
    case_file = f"""
-- Case file for testing the LATERAL_TO_DEVICE keyword.
SCHFILE
ml_well.sch
/
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve Valve Device
--     Number  MEASURED_DEPTH   MEASURED_DEPTH  Tubing   Casing            Content /Joint Type  Number
--                      Diameter Diameter
   A1     1    0  99999  0.15     0.2159  0.00065    GP       1   AICD     1
/

{JOINT_LENGTH_AND_WSEGAICD}
    """
    schedule_file = Path(_TESTDIR / "ml_well.sch")
    with pytest.raises(CompletorError) as e:
        utils_for_tests.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    assert "USE_STRICT True: Define all branches in case file." in str(e)


def test_use_strict_false_missing_branch(tmpdir):
    """Test case with USE_STRICT set to False, with a missing branch.

    Uses a two-branch well, A1, where only one branch is defined in the case file COMPLETION keyword.

    1. One active well.
    2. Multi-lateral well with two branches.
    """
    tmpdir.chdir()
    case_file = f"""
SCHFILE
ml_well.sch
/
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve Valve Device
--     Number  MEASURED_DEPTH   MEASURED_DEPTH  Tubing   Casing            Content /Joint Type  Number
--                      Diameter Diameter
   A1    1     0  99999  0.15     0.2159  0.00065     GP      1   AICD     1
/
USE_STRICT
  FALSE
/

{JOINT_LENGTH_AND_WSEGAICD}
    """
    schedule_file = Path(_TESTDIR / "ml_well.sch")
    true_file = Path(_TESTDIR / "usestrict_false_missingbranch.true")
    utils_for_tests.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)
