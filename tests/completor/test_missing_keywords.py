"""Test output from Completor if keywords missing in input files."""

from pathlib import Path

import pytest
import utils_for_tests

from completor.constants import Content
from completor.exceptions import CompletorError

COMPLETION = """
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MEASURED_DEPTH   MEASURED_DEPTH  Tubing   Casing            Content Joint   Type  Number
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
-- DeviceNumber Cv      Ac    ADDITIONAL_PIPE_LENGTH_FRICTION_PRESSURE_DROP
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
-- WELL I J K K2 FLAG SAT CF  DIAM  FORMATION_PERMEABILITY_THICKNESS  SKIN D_FACTOR DIR  RO
    A1  1 1 1  1 OPEN 1* 1.27 0.31 114.9 0.0   1*   X  19.7 /
/
"""
WELSEGS = """
WELSEGS
-- WELL SEGTVD SEGMD WBVOL INFO PDROPCOMP MULTIPHASE_FLOW_MODEL
    A1   0.0    0.0    1*  ABS     HF-      HO /
-- START_SEGMENT_NUMBER END_SEGMENT_NUMBER BRANCH OUT MEASURED_DEPTH TRUE_VERTICAL_DEPTH DIAM ROUGHNESS
    2    2    1     1 0.0 0.0 0.15 0.00065 /
/
"""
COMPSEGS = """
COMPSEGS
A1 /
-- I J K BRANCH STARTMD ENDMD DIR DEF START_SEGMENT_NUMBER
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
    """Set the contents of case file from a completion type and combination of keywords."""
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
    """Test output to screen from Completor.

    Uses combinations of keywords in input case- and schedule files.
    """
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    set_case(Content.PERFORATED, ["completion"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs", "compsegs"], schedule_file)
    utils_for_tests.open_files_run_create(case_file, schedule_file, _outfile)
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""


def test_missing_welspecs(tmpdir, capsys):
    """Test output to screen from Completor missing WELL_SPECIFICATION."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    set_case(Content.PERFORATED, ["completion"], case_file)
    set_schedule(["compdat", "welsegs", "compsegs"], schedule_file)
    expected_error_message = "Well 'A1' is missing keyword(s): 'WELSPECS'!"
    with pytest.raises(CompletorError) as e:
        utils_for_tests.open_files_run_create(case_file, schedule_file, _outfile)
    assert expected_error_message in str(e.value)


def test_missing_compdat(tmpdir):
    """Test output to screen from Completor missing COMPLETION_DATA."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    set_case(Content.PERFORATED, ["completion"], case_file)
    set_schedule(["welspecs", "welsegs", "compsegs"], schedule_file)
    expected_error_message = "Well 'A1' is missing keyword(s): 'COMPDAT'!"
    with pytest.raises(CompletorError) as e:
        utils_for_tests.open_files_run_create(case_file, schedule_file, _outfile)
    assert expected_error_message in str(e.value)


def test_missing_welsegs(tmpdir):
    """Test output to screen from Completor missing WELL_SEGMENTS."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    expected_error_message = "Well 'A1' is missing keyword(s): 'WELSEGS'!"
    set_case(Content.PERFORATED, ["completion"], case_file)
    set_schedule(["welspecs", "compdat", "compsegs"], schedule_file)
    with pytest.raises(CompletorError) as e:
        utils_for_tests.open_files_run_create(case_file, schedule_file, _outfile)
    assert expected_error_message in str(e.value)


def test_inconsistent_files(tmpdir):
    """Test output to screen from Completor missing COMPLETION_SEGMENTS."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    expected_error_message = "Well 'A1' is missing keyword(s): 'COMPSEGS'!"
    set_case(Content.PERFORATED, ["completion"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs"], schedule_file)
    with pytest.raises(CompletorError) as e:
        utils_for_tests.open_files_run_create(case_file, schedule_file, _outfile)
    assert expected_error_message in str(e.value)


def test_missing_completion(tmpdir):
    """Test output to screen from Completor missing COMPLETION."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    expected_error_message = "No completion is defined in the case file."
    set_case(Content.PERFORATED, ["wsegaicd"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs", "compsegs"], schedule_file)
    with pytest.raises(ValueError, match=expected_error_message):
        utils_for_tests.open_files_run_create(case_file, schedule_file, _outfile)


def test_missing_wsegaicd(tmpdir):
    """Test output to screen from Completor missing AUTONOMOUS_INFLOW_CONTROL_DEVICE."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    expected_error_message = "Missing keyword 'DEVICETYPE AICD' in input files."
    set_case(Content.AUTONOMOUS_INFLOW_CONTROL_DEVICE, ["completion"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs", "compsegs"], schedule_file)
    with pytest.raises(ValueError, match=expected_error_message):
        utils_for_tests.open_files_run_create(case_file, schedule_file, _outfile)


def test_missing_wsegsicd(tmpdir):
    """Test output to screen from Completor missing INFLOW_CONTROL_DEVICE."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    expected_error_message = "Missing keyword 'DEVICETYPE ICD' in input files."
    set_case(Content.INFLOW_CONTROL_DEVICE, ["completion"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs", "compsegs"], schedule_file)
    with pytest.raises(ValueError, match=expected_error_message):
        utils_for_tests.open_files_run_create(case_file, schedule_file, _outfile)


def test_missing_wsegvalv(tmpdir):
    """Test output to screen from Completor missing WELL_SEGMENTS_VALVE."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    expected_error_message = "Missing keyword 'DEVICETYPE VALVE' in input files."
    set_case(Content.VALVE, ["completion"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs", "compsegs"], schedule_file)
    with pytest.raises(ValueError, match=expected_error_message):
        utils_for_tests.open_files_run_create(case_file, schedule_file, _outfile)


def test_full_wsegdar(tmpdir, capsys):
    """
    Test output to screen from Completor with full DAR input.

    Make a separate test for this keyword as it requires more input
    that need to be correct.
    """
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    set_case(Content.DENSITY_ACTIVATED_RECOVERY, ["completion", "wsegdar"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs", "compsegs"], schedule_file)
    utils_for_tests.open_files_run_create(case_file, schedule_file, _outfile)
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""


def test_missing_wsegdar(tmpdir):
    """Test output to screen from Completor with missing DENSITY_ACTIVATED_RECOVERY keyword."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    expected_error_message = "Missing keyword 'DEVICETYPE DAR' in input files."
    set_case(Content.DENSITY_ACTIVATED_RECOVERY, ["completion"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs", "compsegs"], schedule_file)
    with pytest.raises(ValueError, match=expected_error_message):
        utils_for_tests.open_files_run_create(case_file, schedule_file, _outfile)


def test_full_wsegaicv(tmpdir, capsys):
    """
    Test output to screen from Completor with full AICV input.

    Make a separate test for this keyword as it requires more input
    that need to be correct.
    """
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    set_case(Content.AUTONOMOUS_INFLOW_CONTROL_VALVE, ["completion", "wsegaicv"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs", "compsegs"], schedule_file)
    utils_for_tests.open_files_run_create(case_file, schedule_file, _outfile)
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == ""


def test_missing_wsegaicv(tmpdir):
    """Test output to screen from Completor with missing AUTONOMOUS_INFLOW_CONTROL_VALVE keyword."""
    tmpdir.chdir()
    _, _outfile, case_file, schedule_file = set_files(tmpdir)
    expected_error_message = "Missing keyword 'DEVICETYPE AICV' in input files."
    set_case(Content.AUTONOMOUS_INFLOW_CONTROL_VALVE, ["completion"], case_file)
    set_schedule(["welspecs", "compdat", "welsegs", "compsegs"], schedule_file)
    with pytest.raises(ValueError, match=expected_error_message):
        utils_for_tests.open_files_run_create(case_file, schedule_file, _outfile)
