"""Test that Completor generates Python-based density device layers correctly."""

import re
from pathlib import Path

import utils_for_tests

# Paths and constants
_TESTDIR = Path(__file__).absolute().parent / "data"
_TEST_FILE = "density_python.sch"

with open(_TESTDIR / "density_python.testfile", encoding="utf-8") as f:
    WELL_DEFINITION = f.read()

DENSITY_CASE = """
COMPLETION
A2 1 0 10000 0.15364 0.1905 1.524E-005 GP 1 DAR 1
OP5 1 0 10000 0.15364 0.1905 1.524E-005 GP 1 DAR 1
OP5 2 0 10000 0.15364 0.1905 1.524E-005 GP 1 DAR 2
/

JOINTLENGTH
12.0
/

WSEGDENSITY
1 1.0 7.5e-4 1.56e-4 1.53e-4 0.05 0.15 0.15 0.30
2 1.0 5e-4 1.4e-4 1.35e-4 0.10 0.20 0.05 0.20
/

WSEGDENSITY_PY
TRUE
/

SEGMENTLENGTH
-1
/
"""


def strip_metadata_header(text: str) -> str:
    """
    Removes the metadata header block at the top of the output.
    """
    pattern = r"-{100}\n-- Output from Completor[\s\S]+?-- Created at : .+\n-{100}\n+"
    return re.sub(pattern, "", text, count=1, flags=re.MULTILINE)


def test_density_python(tmpdir):
    tmpdir.chdir()

    # Generate output
    utils_for_tests.open_files_run_create(DENSITY_CASE, WELL_DEFINITION, _TEST_FILE)

    # Load and clean schedule files
    generated_schedule = Path(_TEST_FILE)
    expected_schedule = _TESTDIR / "density_python.true"

    actual = strip_metadata_header(generated_schedule.read_text().strip())
    expected = expected_schedule.read_text().strip()

    assert actual == expected, "Schedule mismatch"

    # Check Python files
    for well in ["A2", "OP5"]:
        py_file = Path(f"wsegdensity_{well}.py")
        true_file = _TESTDIR / f"wsegdensity_{well}.true"
        assert py_file.exists(), f"Missing {py_file.name}"
        assert true_file.exists(), f"Missing {true_file.name}"
        assert py_file.read_text().strip() == true_file.read_text().strip(), f"Mismatch in {py_file.name}"
