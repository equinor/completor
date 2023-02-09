"""
This module tests that the roughness and ID for segments in the overburden
are described by the case file and not the input schedule file.
"""

import common

_TEST_FILE = "test.sch"


def test_perf(tmpdir):
    """
    Test case where the case and schedule files have differing overburden values.

    The roughness and ID of the overburden segment do not match between the files.
    """
    tmpdir.chdir()
    case_file = """
-- Case file for testing that overburden segments are described with data from the
-- case file and not the input schedule file.
COMPLETION
--WELL Branch  Start End Screen   Well/  Roughness Annulus Nvalve  Valve  Device
--     Number  mD    mD  Tubing   Casing           Content /Joint  Type   Number
--                       Diameter Diameter
A1      1      0   99999 0.10     0.2159    0.00300   GP   1       AICD   1
