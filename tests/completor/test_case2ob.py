"""
This module tests that the roughness and ID for segments in the overburden
are described by the case file and not the input schedule file.
"""

import common

from completor.constants import Headers

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
/

JOINT_LENGTH
12
/

WSEGAICD
--Number    Alpha       x   y   a   b   c   d   e   f   rhocal  viscal
1           0.00021   0.0   1.0 1.1 1.2 0.9 1.3 1.4 2.1 1000.25    1.45
/
    """
    schedule_file = """
-- One-branch well schedule for testing that tubing roughness is taken from case file
WELSPECS
A1  MYGRP 35  113  0.0  OIL  1*  STD  SHUT  YES  1  AVG  1* /
/

COMPDAT
--WELL I   J  K1 K2 OP/SH  SATN TRAN        WBDIA  KH         SKIN DFACT DIR PEQVR
 'A1'  35 113 72 72 OPEN   1*   298.626067  0.2159 196217.868 30   1*    Y   /
 'A1'  36 113 72 72 OPEN   1*   387.741486  0.2159 254075.894 30   1*    Y   /
/

WELSEGS
--WELL    TDEP      CLEN  VOL  TYPE  DROPT  MPMOD
 'A1'   1565.2834   1893   1*   ABS    HF-     HO /
--SEGS  SEGE BRNCH  SEGJ       CLEN       NDEP       TDIA      ROUGH       AREA
     2     2     1     1 2000.00000 1566.40678      0.159    0.00065         1* /
     3     3     1     2 2167.24558 1566.40678      0.159    0.00065         1* /
     4     4     1     3 2228.00876 1566.16386      0.159    0.00065         1* /
/

COMPSEGS
 'A1' /
--   I     J     K BRNCH       MD_S       MD_E   DIR IJK_E       CDEP  CLEN SEGNO
    35   113    72     1   2178.280   2202.052    1*    1*  1566.2504    1*     3 /
    36   113    72     1   2202.052   2253.965    1*    1* 1566.09798    1*     4 /
/
"""
    true_file = """
-- One-branch well schedule for testing that tubing roughness is taken from case file

WELSPECS
 A1   MYGRP 35  113  0.0   OIL   1*   STD   SHUT   YES   1   AVG   1* /
 /


COMPDAT
-- Well : A1 : Lateral : 1
-- WELL  I   J    K   K2 FLAG  SAT CF          DIAM   KH          SKIN DFACT DIR
    A1   35  113  72  72  OPEN  1* 298.626067  0.2159 196217.868  30.0  1*    Y   /
    A1   36  113  72  72  OPEN  1* 387.741486  0.2159 254075.894  30.0  1*    Y   /
/


WELSEGS
-- WELL  SEGMENTTVD  SEGMENTMD WBVOLUME INFOTYPE PDROPCOMP MPMODEL
    A1   1565.2834   1893.0     1*       ABS      HF-       HO      /
-- Tubing layer
--  SEG  SEG2  BRANCH  OUT MD       TVD       DIAM ROUGHNESS
    2    2     1       1   2000.000 1566.407  0.1   0.003     /
    3    3     1       2   2167.246 1566.407  0.1   0.003     /
    4    4     1       3   2190.166 1566.315  0.1   0.003     /
    5    5     1       4   2228.008 1566.164  0.1   0.003     /
-- Device layer
--  SEG  SEG2  BRANCH  OUT MD       TVD       DIAM ROUGHNESS
    6    6     2       4   2190.266 1566.315  0.1  0.003      / -- AICD types
    7    7     3       5   2228.108 1566.164  0.1  0.003      / -- AICD types
/


COMPSEGS
A1 /
--  I   J    K  BRANCH STARTMD  ENDMD    DIR DEF  SEG
    35  113  72   2    2178.280 2202.052  1*  3*   6  /
    36  113  72   3    2202.052 2253.965  1*  3*   7  /
/


WSEGAICD
------------------------------------------------------------------------------------------------
-- Well : A1 : Lateral : 1
------------------------------------------------------------------------------------------------
-- WELL  SEG  SEG2   ALPHA  SF     RHO  VIS DEF   X   Y FLAG   A   B   C   D   E   F
'A1' 6 6 0.00021 -0.5047955578 1000.25 1.45  5* 0.0 1.0 OPEN 1.1 1.2 0.9 1.3 1.4 2.1 /
'A1' 7 7 0.00021 -0.2311559725 1000.25 1.45  5* 0.0 1.0 OPEN 1.1 1.2 0.9 1.3 1.4 2.1 /
/

    """

    common.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)
