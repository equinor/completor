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
