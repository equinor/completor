"""Test that Completor generates Python-based density device layers correctly."""

from pathlib import Path

import utils_for_tests

# Paths and constants
_TESTDIR = Path(__file__).absolute().parent / "data"
_TEST_FILE = "test.sch"

with open(Path(_TESTDIR / "welldefinition_2branch.testfile"), encoding="utf-8") as file:
    WELL_DEFINITION = file.read()

COMPLETION = """
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MEASURED_DEPTH   MEASURED_DEPTH  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
   A1    1     0   3000    0.2    0.25    1.00E-4     GP      1    DENSITY      1
   A1    2     0   3000    0.2    0.25    1.00E-4     GP      2    DENSITY      1
/
"""

WSEGDENSITY = """
WSEGDENSITY
-- Number   Cv      Oil_Ac  Gas_Ac Water_Ac whf_low  whf_high ghf_low  ghf_high
    1       0.1     0.4     0.3     0.2     0.6         0.70    0.8     0.9
/
"""

PYTHON = """
PYTHON
TRUE
/
"""


def test_density_main_schedule_pyaction(tmpdir):
    """
    Test completor case with DENSITY.
    """
    tmpdir.chdir()
    case_file = f"""
{COMPLETION}
{WSEGDENSITY}
{PYTHON}
    """
    true_file = Path(_TESTDIR / "density_python.true")
    utils_for_tests.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE, assert_text=True)


def test_density_pyaction_includes(tmpdir):
    """
    Test completor case with DENSITY for includes outputs.
    """
    tmpdir.chdir()
    case_file = f"""
{COMPLETION}
{WSEGDENSITY}
{PYTHON}
    """
    utils_for_tests.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    py_file_a1_1 = Path("wsegdensity_A1_1.py")
    py_file_a1_2 = Path("wsegdensity_A1_2.py")
    true_file_a1_1 = _TESTDIR / "wsegdensity_A1_1.true"
    true_file_a1_2 = _TESTDIR / "wsegdensity_A1_2.true"
    assert py_file_a1_1.exists(), f"Missing {py_file_a1_1.name}"
    assert py_file_a1_2.exists(), f"Missing {py_file_a1_2.name}"
    assert py_file_a1_1.read_text().strip() == true_file_a1_1.read_text().strip(), f"Mismatch in {py_file_a1_1.name}"
    assert py_file_a1_2.read_text().strip() == true_file_a1_2.read_text().strip(), f"Mismatch in {py_file_a1_2.name}"
