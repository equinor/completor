"""Test failure of lumping when switching from SEGMENTLENGTH 0 to -1"""

from pathlib import Path

from tests import utils_for_tests

_TESTDIR = Path(__file__).absolute().parent / "data"
_TEST_FILE = "test.sch"

with open(Path(_TESTDIR / "A-1.SCH"), encoding="utf-8") as file:
    A1 = file.read()


with open(Path(_TESTDIR / "B-1.SCH"), encoding="utf-8") as file:
    B1 = file.read()


A1_LUMPING_WITH_TOPBOTTOM = """
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MEASURED_DEPTH   MEASURED_DEPTH  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
A-1 1    0  2196 0.150 0.216 1.5E-5 GP   0 ICD  1
A-1 1 2196  2500 0.150 0.216 1.5E-5 GP 0.5 ICD  1
A-1 1 2500  2600 0.150 0.216 1.5E-5 GP   1 ICD  1
A-1 1 2600  2750 0.150 0.216 1.5E-5 GP   1 ICD  2
A-1 1 2750  3000 0.150 0.216 1.5E-5 GP   1 ICD  3
A-1 1 3000  3163 0.150 0.216 1.5E-5 GP 2.0 ICD  3
A-1 1 3163  4335 0.150 0.216 1.5E-5 GP   1 PERF 1
A-1 1 4335 99999 0.150 0.216 1.5E-5 GP   0 ICD  1
/

WSEGSICD
-- Device no  Strength  Dens. cal.  Visc. cal.  Water fract.
1              0.001          1000        1           0.3
2              0.002          1000        1           0.4
3              0.003          1000        1           0.5
/

SEGMENTLENGTH
  -1
/

USE_STRICT
  FALSE
/
"""


A1_LUMPING_WITHOUT_TOPBOTTOM = """
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MEASURED_DEPTH   MEASURED_DEPTH  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
A-1 1 2196  2500 0.150 0.216 1.5E-5 GP 0.5 ICD  1
A-1 1 2500  2600 0.150 0.216 1.5E-5 GP   1 ICD  1
A-1 1 2600  2750 0.150 0.216 1.5E-5 GP   1 ICD  2
A-1 1 2750  3000 0.150 0.216 1.5E-5 GP   1 ICD  3
A-1 1 3000  3163 0.150 0.216 1.5E-5 GP 2.0 ICD  3
A-1 1 3163  4335 0.150 0.216 1.5E-5 GP   1 PERF 1
/

WSEGSICD
-- Device no  Strength  Dens. cal.  Visc. cal.  Water fract.
1              0.001          1000        1           0.3
2              0.002          1000        1           0.4
3              0.003          1000        1           0.5
/

SEGMENTLENGTH
  -1
/

USE_STRICT
  FALSE
/
"""

A1_CELLS_WITH_TOPBOTTOM = """
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MEASURED_DEPTH   MEASURED_DEPTH  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
A-1 1    0  2196 0.150 0.216 1.5E-5 GP   0 ICD  1
A-1 1 2196  2500 0.150 0.216 1.5E-5 GP 0.5 ICD  1
A-1 1 2500  2600 0.150 0.216 1.5E-5 GP   1 ICD  1
A-1 1 2600  2750 0.150 0.216 1.5E-5 GP   1 ICD  2
A-1 1 2750  3000 0.150 0.216 1.5E-5 GP   1 ICD  3
A-1 1 3000  3163 0.150 0.216 1.5E-5 GP 2.0 ICD  3
A-1 1 3163  4335 0.150 0.216 1.5E-5 GP   1 PERF 1
A-1 1 4335 99999 0.150 0.216 1.5E-5 GP   1 ICD  1
/

WSEGSICD
-- Device no  Strength  Dens. cal.  Visc. cal.  Water fract.
1              0.001          1000        1           0.3
2              0.002          1000        1           0.4
3              0.003          1000        1           0.5
/

SEGMENTLENGTH
  0
/

USE_STRICT
  FALSE
/
"""


B1_LUMPING_WITH_TOPBOTTOM = """
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MEASURED_DEPTH   MEASURED_DEPTH  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
B-1 1    0  3573 0.150 0.216 1.5E-5 GP    0 VALVE 1
B-1 1 3573  3672 0.150 0.216 1.5E-5 GP 0.50 VALVE 1
B-1 1 3672  3711 0.150 0.216 1.5E-5 GP    0 VALVE 1
B-1 1 3711  4273 0.150 0.216 1.5E-5 GP    1 VALVE 2
B-1 1 4273  4813 0.150 0.216 1.5E-5 GP 0.50 VALVE 1
B-1 1 4813  5110 0.150 0.216 1.5E-5 GP    1 VALVE 3
B-1 1 5110 99999 0.150 0.216 1.5E-5 GP    0 VALVE 1
B-1 2    0  3698 0.150 0.216 1.5E-5 GP    0 VALVE 1
B-1 2 3698  3928 0.150 0.216 1.5E-5 GP 0.50 VALVE 1
B-1 2 3928  4382 0.150 0.216 1.5E-5 GP    1 VALVE 2
B-1 2 4382  4408 0.150 0.216 1.5E-5 GP    0 VALVE 1
B-1 2 4408  4505 0.150 0.216 1.5E-5 GP 0.50 VALVE 1
B-1 2 4505  4771 0.150 0.216 1.5E-5 GP 0.33 VALVE 1
B-1 2 4771  4959 0.150 0.216 1.5E-5 GP    1 VALVE 1
B-1 2 4959  5363 0.150 0.216 1.5E-5 GP    1 VALVE 3
B-1 2 5363 99999 0.150 0.216 1.5E-5 GP    1 VALVE 1
B-1 3    0  3627 0.150 0.216 1.5E-5 GP    0 VALVE 1
B-1 3 3627  3717 0.150 0.216 1.5E-5 GP 0.50 VALVE 1
B-1 3 3717  4068 0.150 0.216 1.5E-5 GP    1 VALVE 2
B-1 3 4068  4250 0.150 0.216 1.5E-5 GP    1 VALVE 1
B-1 3 4250  4732 0.150 0.216 1.5E-5 GP 0.33 VALVE 1
B-1 3 4732  4771 0.150 0.216 1.5E-5 GP 0.50 VALVE 1
B-1 3 4771  4922 0.150 0.216 1.5E-5 GP 0.50 VALVE 2
B-1 3 4922  5115 0.150 0.216 1.5E-5 GP 0.67 VALVE 1
B-1 3 5115 99999 0.150 0.216 1.5E-5 GP    0 VALVE 1
/

WSEGVALV
-- Device no    Cv     Ac           ADDITIONAL_PIPE_LENGTH_FRICTION_PRESSURE_DROP
1    0.85    1.00e-5      5*
2    0.85    2.00e-5      5*
3    0.85    3.00e-5      5*
/

SEGMENTLENGTH
  -1
/

USE_STRICT
  FALSE
/
"""


B1_LUMPING_WITHOUT_TOPBOTTOM = """
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MEASURED_DEPTH   MEASURED_DEPTH  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
B-1 1 3573  3672 0.150 0.216 1.5E-5 GP 0.50 VALVE 1
-- No grid blocks to be assigned to this completion interval (0 VPJ)
B-1 1 3672  3711 0.150 0.216 1.5E-5 GP    0 VALVE 1
B-1 1 3711  4273 0.150 0.216 1.5E-5 GP    1 VALVE 2
B-1 1 4273  4813 0.150 0.216 1.5E-5 GP 0.50 VALVE 1
B-1 1 4813  5110 0.150 0.216 1.5E-5 GP    1 VALVE 3
B-1 2 3698  3928 0.150 0.216 1.5E-5 GP 0.50 VALVE 1
B-1 2 3928  4382 0.150 0.216 1.5E-5 GP    1 VALVE 2
B-1 2 4382  4408 0.150 0.216 1.5E-5 GP    0 VALVE 1
B-1 2 4408  4505 0.150 0.216 1.5E-5 GP 0.50 VALVE 1
B-1 2 4505  4771 0.150 0.216 1.5E-5 GP 0.33 VALVE 1
B-1 2 4771  4959 0.150 0.216 1.5E-5 GP    1 VALVE 1
B-1 2 4959  5363 0.150 0.216 1.5E-5 GP    1 VALVE 3
B-1 3 3627  3717 0.150 0.216 1.5E-5 GP 0.50 VALVE 1
B-1 3 3717  4068 0.150 0.216 1.5E-5 GP    1 VALVE 2
B-1 3 4068  4250 0.150 0.216 1.5E-5 GP    1 VALVE 1
B-1 3 4250  4732 0.150 0.216 1.5E-5 GP 0.33 VALVE 1
B-1 3 4732  4771 0.150 0.216 1.5E-5 GP 0.50 VALVE 1
B-1 3 4771  4922 0.150 0.216 1.5E-5 GP 0.50 VALVE 2
B-1 3 4922  5115 0.150 0.216 1.5E-5 GP 0.67 VALVE 1
/

WSEGVALV
-- Device no    Cv     Ac   ADDITIONAL_PIPE_LENGTH_FRICTION_PRESSURE_DROP
1    0.85    1.00e-5      5*
2    0.85    2.00e-5      5*
3    0.85    3.00e-5      5*
/

SEGMENTLENGTH
  -1
/

USE_STRICT
  FALSE
/
"""


def test_a1_cells(tmpdir):
    """Test completor case with cells based segmentation and
    single branch well."""

    tmpdir.chdir()
    case_file = A1_CELLS_WITH_TOPBOTTOM
    true_file = Path(_TESTDIR / "a1_cells_with_topbottom.true")
    utils_for_tests.open_files_run_create(case_file, A1, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_a1_lump_with_topbottom(tmpdir):
    """Test completor case with lumping for single branch well and
    0-x and y-99999 (topbottom) included."""

    tmpdir.chdir()
    case_file = A1_LUMPING_WITH_TOPBOTTOM
    true_file = Path(_TESTDIR / "a1_lumping_with_topbottom.true")
    utils_for_tests.open_files_run_create(case_file, A1, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_a1_lump_without_topbottom(tmpdir):
    """Test completor case with lumping for single branch well and
    0-x and y-99999 excluded."""

    tmpdir.chdir()
    case_file = A1_LUMPING_WITHOUT_TOPBOTTOM
    true_file = Path(_TESTDIR / "a1_lumping_without_topbottom.true")
    utils_for_tests.open_files_run_create(case_file, A1, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_b1_lump_with_topbottom(tmpdir):
    """Test completor case with lumping for a three branch well
    and 0-x and y-99999 included."""

    tmpdir.chdir()
    case_file = B1_LUMPING_WITH_TOPBOTTOM
    true_file = Path(_TESTDIR / "b1_lumping_with_topbottom.true")
    utils_for_tests.open_files_run_create(case_file, B1, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_b1_lump_without_topbottom(tmpdir):
    """Test completor case with lumping for a three branch well
    and 0-x and y-99999 excluded."""

    tmpdir.chdir()
    print(tmpdir)
    case_file = B1_LUMPING_WITHOUT_TOPBOTTOM
    true_file = Path(_TESTDIR / "b1_lumping_without_topbottom.true")
    utils_for_tests.open_files_run_create(case_file, B1, _TEST_FILE)
    print(true_file)
    print(_TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)
