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
