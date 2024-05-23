"""Test Completor main functions."""

from pathlib import Path

import common  # type: ignore
import pytest
from utils import completor_runner

from completor import main  # type: ignore

_TESTDIR = Path(__file__).absolute().parent / "data"
_TEST_FILE = "test.sch"

with open(Path(_TESTDIR / "welldefinition.testfile"), encoding="utf-8") as file:
    WELL_DEFINITION = file.read()

WB_PERF_TEST = """
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MD   MD  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
  'A1'     1    0  3000  0.2      0.25    1.00E-4    GP      0     PERF     0
/
GP_PERF_DEVICELAYER
 TRUE
/
"""

WB_PERF_TEST_MINIMUM_SEGMENT_LENGTH_13 = """
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MD   MD  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
  'A1'     1    0  3000  0.2      0.25    1.00E-4    GP      0     PERF     0
/
GP_PERF_DEVICELAYER
 TRUE
/
MINIMUM_SEGMENT_LENGTH
 13.0
/
"""

WSEGDAR = """
WSEGDAR
-- Number   Cv      Oil_Ac  Gas_Ac Water_Ac whf_low  whf_high ghf_low  ghf_high
    1       0.1     0.4     0.3     0.2     0.6         0.70    0.8     0.9
/
"""

WSEGAICD = """
WSEGAICD
--Number    Alpha       x   y   a   b   c   d   e   f   rhocal  viscal
1           0.00021   0.0   1.0 1.1 1.2 0.9 1.3 1.4 2.1 1000.25    1.45
/
"""

WSEGAICD_TWO_AICD = """
WSEGAICD
--Number    Alpha       x   y       a       b       c       d       e       f       rhocal  viscal
1           0.00021   0.0   1.0     1.1     1.2     0.9     1.3     1.4     2.1     1000.25    1.45
2           0.00042   0.1   1.1     1.0     1.0     1.0     1.0     1.0     1.0     1001.25    1.55
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

WSEGVALV = """
WSEGVALV
-- DeviceNumber     Cv      Ac      L
        1         0.85      0.01  5*
/
"""

WSEGICV = """
WSEGICV
-- DEVICE   CV      AC      DEFAULTS  AC_MAX
1           0.95    3       5*         4
2           2       4       5*         4
/
"""


def test_perf(tmpdir):
    """
    Test completor case with only perf.

    1. 1 passive well & 1 active well
    2. Single lateral well
    """
    tmpdir.chdir()
    case_file = WB_PERF_TEST
    true_file = Path(_TESTDIR / "wb_perf.true")
    common.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_perf_minimum_segment_length_13(tmpdir):
    """
    Test completor case with only perf.

    Minimum segment length set to 13.0
    """
    tmpdir.chdir()
    case_file = WB_PERF_TEST_MINIMUM_SEGMENT_LENGTH_13
    true_file = Path(_TESTDIR / "wb_perf_minimum_segment_length13.true")
    common.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_aicd(tmpdir):
    """
    Test completor case with only AICD.

    1. 1 passive well & 1 active well
    2. Single lateral well
    """
    tmpdir.chdir()
    case_file = f"""
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MD   MD  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
   A1     1    0   3000   0.2     0.25    1.00E-4    GP      1     AICD    1
/
{WSEGAICD}
    """
    true_file = Path(_TESTDIR / "wb_aicd.true")
    common.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_oa(tmpdir):
    """
    Test completor case with open annulus.

    1. 1 passive well & 1 active well
    2. Single lateral well
    """
    tmpdir.chdir()
    case_file = f"""
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MD   MD  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
   A1    1     0   3000   0.2     0.25    1.00E-4     OA     1     AICD    1
/
{WSEGAICD}
    """
    true_file = Path(_TESTDIR / "wb_aicdoa.true")
    common.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_packer(tmpdir):
    """
    Test completor case with packers.

    1. 1 passive well & 1 active well
    2. Single lateral well
    """
    tmpdir.chdir()
    case_file = f"""
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MD   MD  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
   A1    1       0 2024   0.2     0.25    1.00E-4    OA      1     AICD     1
   A1    1    2024 2024   0.2     0.25    1.00E-4    PA      1     AICD     1
   A1    1    2024 3000   0.2     0.25    1.00E-4    OA      1     AICD     1
/
{WSEGAICD_TWO_AICD}
    """
    true_file = Path(_TESTDIR / "wb_aicdpa.true")
    common.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_packer_aicdicd(tmpdir):
    """
    Test completor case with packers.

    1. 1 passive well & 1 active well
    2. Single lateral well
    3. AICD and ICD is installed
    """
    tmpdir.chdir()
    case_file = f"""
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MD   MD  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
   A1    1       0 2024   0.2     0.25    1.00E-4    OA     0.5    VALVE    1
   A1    1    2024 2024   0.2     0.25    1.00E-4    PA     0      AICD     1
   A1    1    2024 3000   0.2     0.25    1.00E-4    OA     0.5    ICD      1
/
WSEGSICD
-- DeviceNumber Strength    RhoCal      VisCal  WatFract.
1               0.0001        1000      1        0.5
/
{WSEGAICD_TWO_AICD}
{WSEGVALV}
    """
    true_file = Path(_TESTDIR / "wb_aicdicdpa.true")
    common.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_packer_aicdvalve(tmpdir):
    """
    Test completor case with packers.

    1. 1 passive well & 1 active well
    2. Single lateral well
    3. AICD and VALVE is installed
    4. joint length 24
    """
    tmpdir.chdir()
    case_file = f"""
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MD   MD  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
   A1    1       0 2024   0.2     0.25    1.00E-4     OA     2     VALVE    1
   A1    1    2024 2024   0.2     0.25    1.00E-4     PA     1     AICD     1
   A1    1    2024 3000   0.2     0.25    1.00E-4     OA     1     AICD     2
/
JOINTLENGTH
24
/
{WSEGAICD_TWO_AICD}
{WSEGVALV}
    """
    true_file = Path(_TESTDIR / "wb_aicdvalvepa.true")
    common.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_packer_oagp(tmpdir):
    """
    Test completor case with GP and open annulus.

    1. 1 passive well & 1 active well
    2. Single lateral well
    3. AICD is installed
    """
    tmpdir.chdir()
    case_file = f"""
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MD   MD  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
   A1     1     0  2024   0.2     0.25    1.00E-4    GP      2     AICD     1
   A1     1  2024  2024   0.2     0.25    1.00E-4    PA      1     AICD     1
   A1     1  2024  3000   0.2     0.25    1.00E-4    OA      5     AICD     1
/
{WSEGAICD}
    """
    true_file = Path(_TESTDIR / "wb_aicdoagp.true")
    common.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_inc(tmpdir):
    """
    Test completor case WELSEGS defined in INC.

    1. 1 passive well & 1 active well
    2. Single lateral well
    3. one of the annular zone dont have devices
    """
    tmpdir.chdir()
    case_file = WB_PERF_TEST
    schedule_file = Path(_TESTDIR / "welldefinition2.testfile")
    true_file = Path(_TESTDIR / "wb_perf.true")
    common.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    print("true_file:")
    print(true_file)
    print("test_file:")
    print(_TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_dar(tmpdir):
    """
    Test completor case with DAR.
    """
    tmpdir.chdir()
    case_file = f"""
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MD   MD  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
   A1    1     0   3000    0.2    0.25    1.00E-4     GP      1    DAR      1
/
{WSEGAICD}
{WSEGDAR}
    """
    true_file = Path(_TESTDIR / "wb_dar.true")
    common.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_aicv(tmpdir):
    """
    Test completor case with AICV.

    1. 1 passive well & 1 active well
    2. Single lateral well
    """
    tmpdir.chdir()
    case_file = f"""
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MD   MD  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
   A1    1     0   3000   0.2     0.25    1.00E-4     GP     1     AICV    1
/
{WSEGAICD}
{WSEGDAR}
{WSEGAICV}
    """
    true_file = Path(_TESTDIR / "wb_aicv.true")
    common.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_daraicv(tmpdir):
    """
    Test completor case with DAR AICV.

    1. 1 passive well & 1 active well
    2. Single lateral well
    """
    tmpdir.chdir()
    case_file = f"""
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MD   MD  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
   A1    1       0 2024   0.2     0.25    1.00E-4     OA     1     DAR      1
   A1    1    2024 2024   0.2     0.25    1.00E-4     PA     1     AICD     1
   A1    1    2024 3000   0.2     0.25    1.00E-4     OA     1     AICV     1
/
{WSEGAICD}
{WSEGDAR}
{WSEGAICV}
    """
    true_file = Path(_TESTDIR / "wb_daraicv.true")
    common.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_multilateral(tmpdir):
    """
    Test completor case with only AICD.

    1. 1 passive well & 1 active well
    2. multilateral
    """
    tmpdir.chdir()
    case_file = f"""
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MD   MD  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
   A1    1     0   3000   0.2     0.25    1.00E-4    OA      1     AICD     1
   A1    2     0   3000   0.2     0.25    1.00E-4    OA      1     AICD     1
/
{WSEGAICD}
    """
    schedule_file = Path(_TESTDIR / "welldefinition3.testfile")
    true_file = Path(_TESTDIR / "wb_multilateral.true")
    common.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_nocf(tmpdir):
    """
    Test completor case with CF and KH are not explicitly defined.

    1. 1 passive well & 1 active well
    2. Single lateral well
    """
    tmpdir.chdir()
    case_file = """
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MD   MD  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
   A1     1    0   3000   0.2     0.25    1.00E-4    GP      1     PERF     0
/
GP_PERF_DEVICELAYER
 TRUE
/
    """
    schedule_file = Path(_TESTDIR / "welldefinition4.testfile")
    true_file = Path(_TESTDIR / "wb_nocf.true")
    common.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_segment_length(tmpdir):
    """
    Test completor case with user segment length.

    1. 1 passive well & 1 active well
    2. Single lateral well
    3. AICD and VALVE is installed
    4. joint length 12
    """
    tmpdir.chdir()
    case_file = f"""
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MD   MD  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
   A1    1       0 2024   0.2     0.25    1.00E-4    OA      1     VALVE    1
   A1    1    2024 2024   0.2     0.25    1.00E-4    PA      1     AICD     1
   A1    1    2024 3000   0.2     0.25    1.00E-4    OA      1     AICD     1
/
SEGMENTLENGTH
2
/
JOINTLENGTH
12
/
{WSEGAICD_TWO_AICD}
{WSEGVALV}
    """
    true_file = Path(_TESTDIR / "wb_segmentlength.true")
    common.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_segment_comp(tmpdir):
    """
    Test completor case with user segment from COMPLETION.

    1. 1 passive well & 1 active well
    2. Single lateral well
    3. AICD and VALVE is installed
    4. joint length 12
    """
    tmpdir.chdir()
    case_file = f"""
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MD   MD  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
   A1     1      0 2006   0.2     0.25    1.00E-4     OA      1   VALVE     1
   A1     1   2006 2008   0.2     0.25    1.00E-4     OA      1   VALVE     1
   A1     1   2008 2015   0.2     0.25    1.00E-4     OA      1   VALVE     1
   A1     1   2015 2024   0.2     0.25    1.00E-4     OA      1   VALVE     1
   A1     1   2024 2024   0.2     0.25    1.00E-4     PA      1   AICD      1
   A1     1   2024 5000   0.2     0.25    1.00E-4     OA      1   AICD      2
/
SEGMENTLENGTH
-1
/
JOINTLENGTH
12
/
{WSEGAICD_TWO_AICD}
{WSEGVALV}
    """
    true_file = Path(_TESTDIR / "wb_segmentcomp.true")
    common.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


@pytest.mark.parametrize(
    "schfilestring",
    ["  testdir/testfile", " testdir/testfile", "testdir/testfile"],
)
def test_read_schedule_from_casefile(schfilestring, tmpdir):
    """
    Test reading the schedule file from the SCHFILE keyword in the casefile.

    Checks that any string pre- and proceeded by whitespaces and in quotes are
    accepted as a schedule-file string.
    """
    tmpdir.chdir()
    Path(tmpdir / "testdir").mkdir()
    # Create a temporary "schedulefile" containing something
    with open("testdir/testfile", "w", encoding="utf-8") as sch_file:
        sch_file.write("Some schedule data\n")

    # Create case_content with the non-clean path to the schedule file
    case_content = f"SCHFILE\n'{schfilestring}'\n/"
    schedule_content, path_from_case = main.get_content_and_path(case_content, None, "SCHFILE")
    assert path_from_case == "testdir/testfile"
    assert "Some schedule data" in schedule_content


@pytest.mark.parametrize(
    "outfilestring",
    ["  testdir/testfile", " testdir/testfile", "testdir/testfile"],
)
def test_read_outputfile_from_casefile(outfilestring, tmpdir):
    """
    Test reading the output file from the OUTFILE keyword in the casefile.

    Checks that any string pre- and proceeded by whitespaces and in quotes are
    accepted as a output-file string.
    """
    tmpdir.chdir()
    Path(tmpdir / "testdir").mkdir()
    # Create a temporary "schedulefile" containing something
    with open("testdir/testfile", "w", encoding="utf-8") as case_file:
        case_file.write("Some case data\n")

    # Create case_content with the non-clean path to the schedule file
    case_content = f"OUTFILE\n'{outfilestring}'\n/"
    _, path_from_case = main.get_content_and_path(case_content, None, "OUTFILE")
    assert path_from_case == "testdir/testfile"


def test_wrong_well_id(tmpdir):
    """Test output to screen from Completor when inner ID > outer ID."""
    tmpdir.chdir()
    output_message = "Check screen/tubing and well/casing ID in case file."
    case_file = f"""
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MD   MD  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
   A1     1    0  3000    0.3      0.2    1.00E-4    GP      1     AICD     1
/
    {WSEGAICD}
    """
    with pytest.raises(ValueError, match=output_message):
        common.open_files_run_create(case_file, WELL_DEFINITION, _TEST_FILE)


def test_well_name_in_quotes(tmpdir):
    """Test completor schedule with wellname in quotes."""
    tmpdir.chdir()
    case_file = WB_PERF_TEST
    schedule_file = Path(_TESTDIR / "welldefinition_quotes.testfile")
    true_file = Path(_TESTDIR / "wb_perf_quotes.true")
    common.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_well_name_in_single_quotes(tmpdir):
    """Test completor schedule with wellname in single quotation marks."""
    tmpdir.chdir()
    case_file = WB_PERF_TEST
    schedule_file = Path(_TESTDIR / "welldefinition_single_quotes.testfile")
    true_file = Path(_TESTDIR / "wb_perf_single_quotes.true")
    common.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_well_name_with_slash(tmpdir):
    """Test completor with a slash in the wellname."""
    tmpdir.chdir()
    case_file = """
    COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MD   MD  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
  'A/1'  1     0   3000   0.2     0.25    1.00E-4    GP      1      PERF    0
/

GP_PERF_DEVICELAYER
 TRUE
/
    """
    schedule_file = Path(_TESTDIR / "welldefinition_slash.testfile")
    true_file = Path(_TESTDIR / "welldefinition_slash.true")
    common.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_leading_whitespace_terminating_slash(tmpdir):
    """Verify leading whitespace does not affect reading of sch file keywords."""
    tmpdir.chdir()
    case_file = Path(_TESTDIR / "well_4_lumping_tests_oa.case")
    schedule_file = Path(_TESTDIR / "leading_whitespace_terminating_slash.sch")
    true_file = Path(_TESTDIR / "user_created_lumping_oa.true")
    common.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_error_missing_keywords(tmpdir, caplog):
    """Check error is reported if any of
    WELSPECS, WELSEGS, COMPDAT or COMSEGS are missing."""
    tmpdir.chdir()
    case_file = str(_TESTDIR / "well_4_lumping_tests_oa.case")
    schedule_file = Path(_TESTDIR / "drogon" / "drogon_input.sch")

    # Modify schedule file to remove WELSPECS
    with open(schedule_file, encoding="utf-8") as f:
        schedule_content = f.read()

    modified_schedule_path = Path(tmpdir / schedule_file.name)
    modified_content = "\n".join(schedule_content.splitlines()[5:])
    with open(modified_schedule_path, "w", encoding="utf-8") as new_sch:
        new_sch.write(modified_content)

    with pytest.raises(SystemExit) as exc:
        completor_runner(inputfile=case_file, schedulefile=modified_schedule_path, outputfile="output.sch")

    assert exc.value.code == 1
    assert "Keyword WELSPECS is not found" in caplog.messages


def test_wsegicv_bottom(tmpdir):
    """Test completor case with ICV to create a special tubing segmentation.
    Completor will produce mixes of tubing segmentation between lumped and default.
    Placing ICV below ICD segments."""
    tmpdir.chdir()
    case_file = Path(_TESTDIR / "icv_device1.case")
    schedule_file = Path(_TESTDIR / "icv_sch.sch")
    true_file = Path(_TESTDIR / "icv_device1.true")
    common.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_wsegicv_top(tmpdir):
    """Test completor case with ICV to create a special tubing segmentation.
    Completor will produce mixes of tubing segmentation between lumped and default.
    Placing ICV above ICD segments and on overlapping depths.
    """
    tmpdir.chdir()
    case_file = Path(_TESTDIR / "icv_device2.case")
    schedule_file = Path(_TESTDIR / "icv_sch.sch")
    true_file = Path(_TESTDIR / "icv_device2.true")
    common.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_wsegicv_mix(tmpdir):
    """Test completor case with ICV to create a special tubing segmentation.
    Completor will produce mixes of tubing segmentation between lumped and default.
    Placing ICV in the middle of ICDs segments"""
    tmpdir.chdir()
    case_file = Path(_TESTDIR / "icv_device3.case")
    schedule_file = Path(_TESTDIR / "icv_sch.sch")
    true_file = Path(_TESTDIR / "icv_device3.true")
    common.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_wsegicv_mid(tmpdir):
    """Test completor case with ICV to create a special tubing segmentation.
    Completor will produce mixes of tubing segmentation between lumped and default.
    Placing ICVs in middle and in between of ICDs segments"""
    tmpdir.chdir()
    case_file = Path(_TESTDIR / "icv_device4.case")
    schedule_file = Path(_TESTDIR / "icv_sch.sch")
    true_file = Path(_TESTDIR / "icv_device4.true")
    common.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_rathole_gp(tmpdir):
    """Test completor case with rathole on the end of the well with extending
    tubing segment further top on the reservoir and bottom of the well.
    Placing gravel pack in the annulus layer."""
    tmpdir.chdir()
    case_file = Path(_TESTDIR / "rathole_gp.case")
    schedule_file = Path(_TESTDIR / "rathole.sch")
    true_file = Path(_TESTDIR / "rathole_gp.true")
    common.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_rathole_oapa(tmpdir):
    """Test completor case with rathole on the end of the well with extending
    tubing segment further top on the reservoir and bottom of the well.
    Placing combination of annulus and packer in annulus layer."""
    tmpdir.chdir()
    case_file = Path(_TESTDIR / "rathole_oapa.case")
    schedule_file = Path(_TESTDIR / "rathole.sch")
    true_file = Path(_TESTDIR / "rathole_oapa.true")
    common.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)
