"""Test output from Completor if keywords missing in input files."""

from pathlib import Path

import pytest
import utils

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
-- WELL I J K K2 FLAG SAT CF  DIAM  FORMATION_PERMEABILITY_THICKNESS  SKIN NON_DARCY_FLOW_FACTOR DIR  RO
    A1  1 1 1  1 OPEN 1* 1.27 0.31 114.9 0.0   1*   X  19.7 /
/
"""
WELSEGS = """
WELSEGS
-- WELL SEGTVD SEGMD WBVOL INFO PDROPCOMP MULTIPHASE_FLOW_MODEL
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
/
"""
CASE_KEYWORDS = {
    "completion": COMPLETION,
    "wsegaicd": WSEGAICD,
    "wsegsicd": WSEGSICD,
    "wsegvalv": WSEGVALV,
    "wsegaicv": WSEGAICV,
    "wsegdar": WSEGDAR,
}
SCHEDULE_KEYWORDS = {"welspecs": WELSPECS, "compdat": COMPDAT, "welsegs": WELSEGS, "compsegs": COMPSEGS}


def set_files(tmpdir):
    """Set the file names to be read by create()."""
    tmpdir.chdir()
    _testdir = Path(tmpdir).absolute().parent
    _outfile = "test.out"
    case_file = Path(_testdir / "file.case")
    schedule_file = Path(_testdir / "file.sch")
    return _testdir, _outfile, case_file, schedule_file


def set_case(completion_type, combination, case_file):
    """Set contents of case file from a completion type and combination of keywords."""
    case_content = ""
    for case_keyword in combination:
        case_content += CASE_KEYWORDS[case_keyword].replace("__TYPE__", completion_type)
    Path(case_file).write_text(case_content, encoding="utf-8")


def set_schedule(combination, schedule_file):
    """Set up the contents of the schedule file from a combination of keywords."""
    schedule_content = ""
    for keyword in combination:
        schedule_content += SCHEDULE_KEYWORDS[keyword]
    Path(schedule_file).write_text(schedule_content, encoding="utf-8")


def test_minimum_input(tmpdir, capsys):
    """
    Test output to screen from Completor.

    Uses combinations of keywords in input case- and schedule files.
    """
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    set_case("PERF", ["completion"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs", "compsegs"], schedule_file)
    utils.open_files_run_create(case_file, schedule_file, _outfile)
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""


def test_missing_welspecs(tmpdir, capsys):
    """Test output to screen from Completor missing WELSPECS."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    set_case("PERF", ["completion"], case_file)
    set_schedule(["compdat", "welsegs", "compsegs"], schedule_file)
    utils.open_files_run_create(case_file, schedule_file, _outfile)
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""


def test_missing_compdat(tmpdir):
    """Test output to screen from Completor missing COMPDAT."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    outputmessage = "Input schedule file missing COMPDAT keyword."
    set_case("PERF", ["completion"], case_file)
    set_schedule(["welspecs", "welsegs", "compsegs"], schedule_file)
    with pytest.raises(ValueError, match=outputmessage):
        utils.open_files_run_create(case_file, schedule_file, _outfile)


def test_missing_welsegs(tmpdir):
    """Test output to screen from Completor missing WELSEGS."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    outputmessage = "Input schedule file missing WELSEGS keyword."
    set_case("PERF", ["completion"], case_file)
    set_schedule(["welspecs", "compdat", "compsegs"], schedule_file)
    with pytest.raises(ValueError, match=outputmessage):
        utils.open_files_run_create(case_file, schedule_file, _outfile)


def test_inconsistent_files(tmpdir):
    """Test output to screen from Completor missing COMPSEGS."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    outputmessage = (
        "Inconsistent case and input schedule files. " "Check well names and WELSPECS, COMPDAT, WELSEGS and COMPSEGS."
    )
    set_case("PERF", ["completion"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs"], schedule_file)
    with pytest.raises(ValueError, match=outputmessage):
        utils.open_files_run_create(case_file, schedule_file, _outfile)


def test_missing_completion(tmpdir):
    """Test output to screen from Completor missing COMPLETION."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    outputmessage = "No completion is defined in the case file."
    set_case("PERF", ["wsegaicd"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs", "compsegs"], schedule_file)
    with pytest.raises(ValueError, match=outputmessage):
        utils.open_files_run_create(case_file, schedule_file, _outfile)


def test_missing_wsegaicd(tmpdir):
    """Test output to screen from Completor missing WSEGAICD."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    expected_error_message = "Missing keyword 'DEVICETYPE AICD' in input files."
    set_case("AICD", ["completion"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs", "compsegs"], schedule_file)
    with pytest.raises(ValueError, match=expected_error_message):
        utils.open_files_run_create(case_file, schedule_file, _outfile)


def test_missing_wsegsicd(tmpdir):
    """Test output to screen from Completor missing WSEGSICD."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    expected_error_message = "Missing keyword 'DEVICETYPE ICD' in input files."
    set_case("ICD", ["completion"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs", "compsegs"], schedule_file)
    with pytest.raises(ValueError, match=expected_error_message):
        utils.open_files_run_create(case_file, schedule_file, _outfile)


def test_missing_wsegvalv(tmpdir):
    """Test output to screen from Completor missing WSEGVALV."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    expected_error_message = "Missing keyword 'DEVICETYPE VALVE' in input files."
    set_case("VALVE", ["completion"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs", "compsegs"], schedule_file)
    with pytest.raises(ValueError, match=expected_error_message):
        utils.open_files_run_create(case_file, schedule_file, _outfile)


def test_full_wsegdar(tmpdir, capsys):
    """
    Test output to screen from Completor with full DAR input.

    Make a separate test for this keyword as it requires more input
    that need to be correct.
    """
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    set_case("DAR", ["completion", "wsegdar"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs", "compsegs"], schedule_file)
    utils.open_files_run_create(case_file, schedule_file, _outfile)
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""


def test_missing_wsegdar(tmpdir):
    """Test output to screen from Completor with missing WSEGDAR keyword."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    expected_error_message = "Missing keyword 'DEVICETYPE DAR' in input files."
    set_case("DAR", ["completion"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs", "compsegs"], schedule_file)
    with pytest.raises(ValueError, match=expected_error_message):
        utils.open_files_run_create(case_file, schedule_file, _outfile)


def test_full_wsegaicv(tmpdir, capsys):
    """
    Test output to screen from Completor with full AICV input.

    Make a separate test for this keyword as it requires more input
    that need to be correct.
    """
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    set_case("AICV", ["completion", "wsegaicv"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs", "compsegs"], schedule_file)
    utils.open_files_run_create(case_file, schedule_file, _outfile)
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""


def test_missing_wsegaicv(tmpdir):
    """Test output to screen from Completor with missing WSEGAICV keyword."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    expected_error_message = "Missing keyword 'DEVICETYPE AICV' in input files."
    set_case("AICV", ["completion"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs", "compsegs"], schedule_file)
    with pytest.raises(ValueError, match=expected_error_message):
        utils.open_files_run_create(case_file, schedule_file, _outfile)
