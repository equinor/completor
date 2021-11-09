"""Test Completor LATERAL_TO_DEVICE keyword"""

from pathlib import Path

import common
import pytest

_TESTDIR = Path(__file__).absolute().parent / "data"
_TEST_FILE = "ml_well.sch"

COMPLETION_TWO_ROWS = """
COMPLETION
-- Well  Branch Start End Screen   Well/   Roughness Annulus Nvalve Valve Device
--       Number MD    MD  Tubing   Casing            Content /Joint Type  Number
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
--Number    Alpha       x   y   a   b   c   d   e   f   rhocal  viscal
1           0.00021   0.0   1.0 1.1 1.2 0.9 1.3 1.4 2.1 1000.25    1.45
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
    common.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_lat2device_non_existing(tmpdir):
