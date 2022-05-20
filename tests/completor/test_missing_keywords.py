"""Test output from Completor if keywords missing in input files."""

from pathlib import Path

import common
import pytest

COMPLETION = """
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MD   MD  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
   A1    1     0  10000  0.15364  0.1905 1.524E-005   GP     1   __TYPE__   1
/
GP_PERF_DEVICELAYER
  TRUE
/
"""
SCHFILE = """
SCHFILE
data/file.sch
/
"""
WSEGAICD = """
WSEGAICD
--Number    Alpha       x   y   a   b   c   d   e   f   rhocal  viscal
1           0.00021   0.0   1.0 1.1 1.2 0.9 1.3 1.4 2.1 1000.25    1.45
/
"""
WSEGSICD = """
WSEGSICD
-- DeviceNumber Strength RhoCal VisCal WatFract.
        1        0.1234   1234    1       1*
/
"""
WSEGVALV = """
WSEGVALV
-- DeviceNumber Cv      Ac    L
        1     0.1234 1.234e-4 5*
/
"""
WSEGAICV_MAIN = """
WSEGAICV
--NUMBER WCT GVF RhoCal VisCal Alp.Main x.Main y.Main a.Main b.Main c.Main d.Main e.Main
--f.Main Alp.Pilot x.Pilot y.Pilot a.Pilot b.Pilot c.Pilot d.Pilot e.Pilot f.Pilot /
1 0.95 0.95 1000 0.45 0.001 0.9 1.0 1.0 1.0 1.0 1.1 1.2 1.3"""

WSEGAICV_PILOT = """ 0.002 0.9 1.0 1.0 1.0 1.0 1.1 1.2 1.3
/
"""

WSEGAICV = WSEGAICV_MAIN + WSEGAICV_PILOT
WSEGDAR = """
WSEGDAR
-- Number   Cv  Oil_Ac Gas_Ac Water_Ac whf_low  whf_high ghf_low  ghf_high
1   0.1 0.4 0.3 0.2 0.6 0.70    0.8 0.9
/
"""
WELSPECS = """
WELSPECS
--WELL GRP I J DREF PHASE DRAD INFEQ SIINS XFLOW PRTAB DENS
   A1  GRP 1 1 0.0   OIL   1*    1*   SHUT   1*    1*   1* /
/
"""
COMPDAT = """
COMPDAT
-- WELL I J K K2 FLAG SAT CF  DIAM  KH  SKIN DFACT DIR  RO
    A1  1 1 1  1 OPEN 1* 1.27 0.31 114.9 0.0   1*   X  19.7 /
/
"""
WELSEGS = """
WELSEGS
-- WELL SEGTVD SEGMD WBVOL INFO PDROPCOMP MPMODEL
    A1   0.0    0.0    1*  ABS     HF-      HO /
-- SEG SEG2 BRANCH OUT MD TVD DIAM ROUGHNESS
    2    2    1     1 0.0 0.0 0.15 0.00065 /
/
"""
COMPSEGS = """
COMPSEGS
A1 /
-- I J K BRANCH STARTMD ENDMD DIR DEF SEG
   1 1 1    1     0.0    0.1   1* 3*   31 /
