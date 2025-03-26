"""Test Completor LATERAL_TO_DEVICE keyword"""

from pathlib import Path

import pytest
import utils_for_tests

from completor.exceptions.clean_exceptions import CompletorError

_TESTDIR = Path(__file__).absolute().parent / "data"
_TEST_FILE = "ml_well.sch"

COMPLETION_TWO_ROWS = """
COMPLETION
-- Well  Branch Start End Screen   Well/   Roughness Annulus Nvalve Valve Device
--       Number MEASURED_DEPTH    MEASURED_DEPTH  Tubing   Casing            Content /Joint Type  Number
--                        Diameter Diameter
A1        1    0    99999 0.15     0.2159   0.00065 GP      1       AICD  1
A1        2    0    99999 0.15     0.2159   0.00065 GP      1       AICD  1
/
"""

USE_STRICT_JOINT_LENGTH = """
USE_STRICT
TRUE
/
JOINT_LENGTH
12
/
"""

WSEGAICD = """
WSEGAICD
--Number    Alpha       x   y   a   b   c   d   e   f   rhocal  viscal  Z
1           0.00021   0.0   1.0 1.1 1.2 0.9 1.3 1.4 2.1 1000.25    1.45 5
/
"""


def test_lat2device(tmpdir):
    """
    Test completor with a two-branch well.

    The lateral of the well, A1, is connected to the main branch via the device layer.

    1. One active well
    2. Multi-lateral well with two branches
    """
    tmpdir.chdir()
    case_file = f"""
    -- Case file for testing the LATERAL_TO_DEVICE keyword.
    SCHFILE
    ml_well.sch
    /

    {COMPLETION_TWO_ROWS}

    {USE_STRICT_JOINT_LENGTH}

    SEGMENTLENGTH
    0.0
    /
    {WSEGAICD}
    -- Lateral 2 in well A1 is routed to the device layer in lateral 1.
    LATERAL_TO_DEVICE
    --WELL  LATERAL
        A1        2
    /
    """
    schedule_file = Path(_TESTDIR / "ml_well.sch")
    true_file = Path(_TESTDIR / "lat2device.true")
    utils_for_tests.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_lat2device_non_existing(tmpdir):
    """
    Test completor with a two-branch well.

    The lateral of the well, A1, is connected to the main branch via the device layer.

    Attempt to connect a branch that does not exist (i.e. branch 3 in a 2 branch well).
    As expected, the default route to the tubing layer is chosen for branches not set in
    LATERAL_TO_DEVICE. The non-existing branch included in LATERAL_TO_DEVICE is ignored.

    1. One active well
    2. Multi-lateral well with two branches
    """
    tmpdir.chdir()
    case_file = f"""
-- Case file for testing the LATERAL_TO_DEVICE keyword.
SCHFILE
ml_well.sch
/

{COMPLETION_TWO_ROWS}
{USE_STRICT_JOINT_LENGTH}
{WSEGAICD}

-- Lateral 2 in well A1 is routed to the device layer in lateral 1.
LATERAL_TO_DEVICE
--WELL  LATERAL
    A1        3
/
    """
    schedule_file = Path(_TESTDIR / "ml_well.sch")
    true_file = Path(_TESTDIR / "lat2device_nonexisting.true")

    utils_for_tests.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_lat2device_no_device(tmpdir, caplog):
    """
    Test completor with a two-branch well.

    The lateral of the well, A1, is connected to the main branch via the device layer.

    Attempt to connect to a device layer that does not exist.
    Completor halts with an error message.

    1. One active well
    2. Multi-lateral well with two branches
    """
    tmpdir.chdir()
    case_file = f"""
-- Case file for testing the LATERAL_TO_DEVICE keyword.
SCHFILE
ml_well_l2d_nodevicetest.sch
/

COMPLETION
-- Well  Branch Start End Screen   Well/   Roughness Annulus Nvalve Valve Device
--       Number MEASURED_DEPTH    MEASURED_DEPTH  Tubing   Casing            Content /Joint Type  Number
--                        Diameter Diameter
A1     1        0  2190.166  0.15  0.2159  0.00065   GP      0      AICD  1
A1     1 2190.166     99999  0.15  0.2159  0.00065   GP      1      AICD  1
A1     2        0     99999  0.15  0.2159  0.00065   GP      1      AICD  1
/

{USE_STRICT_JOINT_LENGTH}
{WSEGAICD}

-- Lateral 2 in well A1 is routed to the device layer in lateral 1.
LATERAL_TO_DEVICE
--WELL  LATERAL
    A1        2
/
    """
    schedule_file = Path(_TESTDIR / "ml_well_l2d_nodevicetest.sch")
    with pytest.raises(CompletorError) as e:
        utils_for_tests.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    assert "Cannot find a device layer at junction of lateral 2 in A1" in str(e)


def test_lat2tubing(tmpdir):
    """
    Test completor with a two-branch well.

    The lateral of the well, A1, is connected to the main branch via the tubing layer.

    1. One active well
    2. Multi-lateral well with two branches
    """
    tmpdir.chdir()
    case_file = f"""
    -- Case file for testing the LATERAL_TO_DEVICE keyword.
    SCHFILE
    ml_well.sch
    /

    {COMPLETION_TWO_ROWS}
    {WSEGAICD}
    {USE_STRICT_JOINT_LENGTH}
    """
    schedule_file = Path(_TESTDIR / "ml_well.sch")
    true_file = Path(_TESTDIR / "lat2tubing.true")
    utils_for_tests.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)
