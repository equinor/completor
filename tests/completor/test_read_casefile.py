"""Test functions for the Completor read_casefile module."""

import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from completor.constants import Headers
from completor.exceptions import CaseReaderFormatError, CompletorError  # type: ignore
from completor.main import get_content_and_path  # type: ignore
from completor.read_casefile import ReadCasefile  # type: ignore

_TESTDIR = Path(__file__).absolute().parent / "data"
with open(Path(_TESTDIR / "case.testfile"), encoding="utf-8") as case_file:
    _THECASE = ReadCasefile(case_file.read())


def test_read_case_completion():
    """Test the function which reads the COMPLETION keyword."""
    df_true = pd.DataFrame(
        [
            ["A1", 1, 0.0, 1000.0, 0.1, 0.2, 1e-4, "OA", 3, "AICD", 1],
            ["A1", 2, 500, 1000, 0.1, 0.2, 1e-4, "GP", 0, "VALVE", 1],
            ["A2", 1, 0, 500, 0.1, 0.2, 1e-5, "OA", 3, "DAR", 1],
            ["A2", 1, 500, 500, 0, 0, 0, "PA", 0.0, "PERF", 0],
            ["A2", 1, 500, 1000, 0.1, 0.2, 1e-4, "OA", 0.0, "PERF", 0],
            ["A3", 1, 0, 1000, 0.1, 0.2, 1e-4, "OA", 3, "AICD", 2],
            ["A3", 2, 500, 1000, 0.1, 0.2, 1e-4, "GP", 1, "VALVE", 2],
            ["11", 1, 0, 500, 0.1, 0.2, 1e-4, "OA", 3, "DAR", 2],
            ["11", 1, 500, 500, 0, 0, 0, "PA", 0, "PERF", 0],
            ["11", 1, 500, 1000, 0.1, 0.2, 1e-4, "OA", 3, "AICV", 2],
        ],
        columns=[
            Headers.WELL,
            Headers.BRANCH,
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.INNER_DIAMETER,
            Headers.OUTER_DIAMETER,
            Headers.ROUGHNESS,
            Headers.ANNULUS,
            Headers.VALVES_PER_JOINT,
            Headers.DEVICE_TYPE,
            Headers.DEVICE_NUMBER,
        ],
    )

    pd.testing.assert_frame_equal(df_true, _THECASE.completion_table, check_exact=False, rtol=0.0001)


def test_read_case_joint_length():
    """Test the function which reads the JOINTLENGTH keyword."""
    assert _THECASE.joint_length == 14.0, "Failed joint length"


def test_read_case_segment_length():
    """Test the function which reads SEGMENTLENGTH keyword."""
    assert _THECASE.segment_length == 12.0, "Failed segment length"


def test_read_case_wsegvalv():
    """Test the function which reads WSEGVALV keyword."""
    df_true = pd.DataFrame(
        [
            ["VALVE", 1, 0.85, 0.01, "5*", 0.04],
            ["VALVE", 2, 0.95, 0.02, "5*", 0.04],
        ],
        columns=[
            Headers.DEVICE_TYPE,
            Headers.DEVICE_NUMBER,
            Headers.FLOW_COEFFICIENT,
            Headers.FLOW_CROSS_SECTIONAL_AREA,
            Headers.ADDITIONAL_PIPE_LENGTH_FRICTION_PRESSURE_DROP,
            Headers.MAX_FLOW_CROSS_SECTIONAL_AREA,
        ],
    )
    pd.testing.assert_frame_equal(df_true, _THECASE.wsegvalv_table)


def test_read_case_wsegicv():
    """Test the function which reads WSEGVALV keyword."""
    df_true = pd.DataFrame(
        [
            ["ICV", 1, 1.0, 2.0, 2.0],
            ["ICV", 2, 3, 4, 1.0],
        ],
        columns=[
            Headers.DEVICE_TYPE,
            Headers.DEVICE_NUMBER,
            Headers.FLOW_COEFFICIENT,
            Headers.FLOW_CROSS_SECTIONAL_AREA,
            Headers.MAX_FLOW_CROSS_SECTIONAL_AREA,
        ],
    )
    pd.testing.assert_frame_equal(df_true, _THECASE.wsegicv_table)


def test_read_case_wsegaicd():
    """Test the function which reads WSEGAICD keyword."""
    df_true = pd.DataFrame(
        [
            ["AICD", 1, 0.00021, 0.0, 1.0, 1.1, 1.2, 0.9, 1.3, 1.4, 2.1, 1000.25, 1.45],
            ["AICD", 2, 0.00042, 0.1, 1.1, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1001.25, 1.55],
        ],
        columns=[
            Headers.DEVICE_TYPE,
            Headers.DEVICE_NUMBER,
            Headers.STRENGTH,
            Headers.X,
            Headers.Y,
            Headers.A,
            Headers.B,
            Headers.C,
            Headers.D,
            Headers.E,
            Headers.F,
            Headers.RHOCAL_AICD,
            Headers.VISCAL_AICD,
        ],
    )
    df_true[Headers.DEVICE_NUMBER] = df_true[Headers.DEVICE_NUMBER].astype(np.int64)
    df_true.iloc[:, 2:] = df_true.iloc[:, 2:].astype(np.float64)
    pd.testing.assert_frame_equal(df_true, _THECASE.wsegaicd_table)


def test_read_case_wsegsicd():
    """Test the function which reads WSEGSICD keyword."""
    df_true = pd.DataFrame(
        [
            ["ICD", 1, 0.001, 1000.0, 1.0, 0.1],
            ["ICD", 2, 0.002, 1000.0, 0.9, 0.2],
        ],
        columns=[
            Headers.DEVICE_TYPE,
            Headers.DEVICE_NUMBER,
            Headers.STRENGTH,
            Headers.CALIBRATION_FLUID_DENSITY,
            Headers.CALIBRATION_FLUID_VISCOSITY,
            Headers.WATER_CUT,
        ],
    )
    df_true[Headers.DEVICE_NUMBER] = df_true[Headers.DEVICE_NUMBER].astype(np.int64)
    pd.testing.assert_frame_equal(df_true, _THECASE.wsegsicd_table)


def test_read_case_wsegdar():
    """Test the function which reads WSEGDAR keyword."""
    df_true = pd.DataFrame(
        [
            ["DAR", 1, 0.1, 0.4, 0.3, 0.2, 0.6, 0.70, 0.8, 0.9],
            ["DAR", 2, 0.1, 0.4, 0.3, 0.2, 0.5, 0.60, 0.7, 0.8],
        ],
        columns=[
            Headers.DEVICE_TYPE,
            Headers.DEVICE_NUMBER,
            Headers.CV_DAR,
            Headers.AC_OIL,
            Headers.AC_GAS,
            Headers.AC_WATER,
            Headers.WHF_LCF_DAR,
            Headers.WHF_HCF_DAR,
            Headers.GHF_LCF_DAR,
            Headers.GHF_HCF_DAR,
        ],
    )
    df_true[Headers.DEVICE_NUMBER] = df_true[Headers.DEVICE_NUMBER].astype(np.int64)
    df_true.iloc[:, 2:] = df_true.iloc[:, 2:].astype(np.float64)
    pd.testing.assert_frame_equal(df_true, _THECASE.wsegdar_table)


def test_new_dar_old_parameters():
    """Test the function which reads WSEGDAR keyword."""
    with open(Path(_TESTDIR / "dar.testfile"), encoding="utf-8") as old_dar_case:
        _OLDDARCASE = old_dar_case.read()

    with pytest.raises(CaseReaderFormatError) as err:
        ReadCasefile(_OLDDARCASE)

    expected_err = "Too few entries in data for keyword 'WSEGDAR', expected 9"
    assert expected_err in str(err.value)


def test_read_case_wsegaicv():
    """Test the function which reads WSEGAICV keyword."""
    df_true = pd.DataFrame(
        [
            [
                "AICV",
                1,
                0.95,
                0.95,
                1000.0,
                0.45,
                0.001,
                0.9,
                1.0,
                1.0,
                1.0,
                1.0,
                1.1,
                1.2,
                1.3,
                0.002,
                0.9,
                1.0,
                1.0,
                1.0,
                1.0,
                1.1,
                1.2,
                1.3,
            ],
            [
                "AICV",
                2,
                0.80,
                0.85,
                1001.0,
                0.55,
                0.005,
                0.1,
                1.1,
                1.0,
                1.0,
                1.0,
                1.4,
                1.5,
                1.6,
                0.022,
                0.1,
                1.0,
                1.0,
                1.0,
                1.0,
                2.1,
                2.2,
                2.3,
            ],
        ],
        columns=[
            Headers.DEVICE_TYPE,
            Headers.DEVICE_NUMBER,
            Headers.WCT_AICV,
            Headers.GHF_AICV,
            Headers.RHOCAL_AICV,
            Headers.VISCAL_AICV,
            Headers.ALPHA_MAIN,
            Headers.X_MAIN,
            Headers.Y_MAIN,
            Headers.A_MAIN,
            Headers.B_MAIN,
            Headers.C_MAIN,
            Headers.D_MAIN,
            Headers.E_MAIN,
            Headers.F_MAIN,
            Headers.ALPHA_PILOT,
            Headers.X_PILOT,
            Headers.Y_PILOT,
            Headers.A_PILOT,
            Headers.B_PILOT,
            Headers.C_PILOT,
            Headers.D_PILOT,
            Headers.E_PILOT,
            Headers.F_PILOT,
        ],
    )
    df_true[Headers.DEVICE_NUMBER] = df_true[Headers.DEVICE_NUMBER].astype(np.int64)
    pd.testing.assert_frame_equal(df_true, _THECASE.wsegaicv_table)


def test_error_missing_column_completion():
    """Check that a missing column in COMPLETION causes error."""
    completion_string = """
COMPLETION
--Well    Branch   StartMD   EndmD    Screen     Well/CasingDiameter Roughness       Annulus     Nvalve/Joint     ValveType
--        Number                      Tubing     Casing              Roughness       Content
--                                    Diameter   Diameter
'A1'       1        0         1000     0.1        0.2                 1E-4            OA          3                AICD
'A1'       2        500       1000     0.1        0.2                 1E-4            GP          0                VALVE
/
"""  # noqa: more human readable at this witdth.

    with pytest.raises(CaseReaderFormatError) as err:
        ReadCasefile(case_file=completion_string, schedule_file="none")

    expected_err = [
        "Error at line 6 in case file:\n",
        "Too few entries in data for keyword 'COMPLETION', expected 11 entries:",
    ]
    for expected in expected_err:
        assert expected in str(err.value)


def test_error_extra_column_completion():
    """Check that an extra column in COMPLETION causes error."""
    completion_string = """
COMPLETION
--Well    Branch   StartMD   EndmD    Screen     Well/CasingDiameter Roughness       Annulus     Nvalve/Joint     ValveType     DeviceNumber
--        Number                      Tubing     Casing              Roughness       Content
--                                    Diameter   Diameter
  'A1'       1        0         1000     0.1        0.2                 1E-4            OA          3                AICD          1
  'A1'       2        500       1000     0.1        0.2                 1E-4            GP          0                VALVE         1                extra_value
/
"""  # noqa: more human readable at this witdth.

    with pytest.raises(CaseReaderFormatError) as err:
        ReadCasefile(case_file=completion_string, schedule_file="none")

    expected_err = [
        "Error at line 7 in case file:\n",
        "Too many entries in data for keyword 'COMPLETION', expected 11 entries:",
    ]
    for expected in expected_err:
        assert expected in str(err.value)


def test_read_case_output_file_with_OUTFILE(tmpdir):
    """Test the function which reads OUTFILE keyword when not command line"""
    shutil.copy(_TESTDIR / "case.testfile", tmpdir)
    tmpdir.chdir()
    with open("case.testfile", encoding="utf-8") as file:
        case_content = file.read()
    output_file = get_content_and_path(case_content, None, "OUTFILE")
    assert output_file[1] == "output.file", "Failed reading PVTFILE keyword"


def test_create_dataframe_with_columns():
    """Test both formats keywords in case-file can appear as."""
    case_content = """COMPLETION
--Well Branch StartMD EndmD Screen   Well/Casing Roughness Annulus Nvalve/Joint ValveType DeviceNumber
--     Number               Tubing   Casing      Roughness Content
--                          Diameter Diameter
'A1'    1      0       1000  0.1      0.2         1E-4      OA      3            AICD      1 /
'A1'    2      500     1000  0.1      0.2         1E-4      GP      0            VALVE     1 /
/

WSEGSICD
  1 0.001 1000 1.0 0.1 /
  2 0.002 1000 0.9 0.2 /
/

WSEGAICD
--Number    Alpha       x   y   a   b   c   d   e   f   rhocal  viscal
1           0.00021   0.0   1.0 1.1 1.2 0.9 1.3 1.4 2.1 1000.25    1.45
2           0.00042   0.1   1.1 1.0 1.0 1.0 1.0 1.0 1.0 1001.25    1.55
/

"""  # noqa: more human readable at this width.
    case = ReadCasefile(case_content)

    df_true = pd.DataFrame(
        [
            ["ICD", 1, 0.001, 1000.0, 1.0, 0.1],
            ["ICD", 2, 0.002, 1000.0, 0.9, 0.2],
        ],
        columns=[
            Headers.DEVICE_TYPE,
            Headers.DEVICE_NUMBER,
            Headers.STRENGTH,
            Headers.CALIBRATION_FLUID_DENSITY,
            Headers.CALIBRATION_FLUID_VISCOSITY,
            Headers.WATER_CUT,
        ],
    )

    pd.testing.assert_frame_equal(df_true, case.wsegsicd_table)


def test_read_minimum_segment_length():
    """Tests the function which reads MINIMUM_SEGMENTLENGTH keyword."""
    assert _THECASE.minimum_segment_length == 0.0, "Failed reading" " MINIMUM_SEGMENTLENGTH keyword"


def test_error_wrong_format_keyword():
    """Test keywords in the wrong format fails."""
    case_content = """COMPLETION
--Well Branch StartMD EndmD Screen   Well/Casing Roughness Annulus Nvalve/Joint ValveType DeviceNumber BlankPortion
--     Number               Tubing   Casing      Roughness Content
--                          Diameter Diameter
'A1'    1      0       1000  0.1      0.2         1E-4      OA      3            AICD      1 /
'A1'    2      500     1000  0.1      0.2         1E-4      GP      0            VALVE     1 /
/

WSEGSICD
  1 0.001 1000 1.0 0.1 /


"""  # noqa: more human readable at this width.

    with pytest.raises(CompletorError) as e:
        ReadCasefile(case_content)
    assert "Keyword WSEGSICD has no end record" in str(e)

    case_content += """
WSEGVALV
-- Device no    Cv     Ac           ADDITIONAL_PIPE_LENGTH_FRICTION_PRESSURE_DROP
          1    1.0    9.62e-6      5*
/

"""
    # Check it still fails if more keywords after wrong formatted keyword
    with pytest.raises(CaseReaderFormatError) as exc:
        ReadCasefile(case_content)
    assert "Cannot determine correct end of record " in str(exc.value)

    case_wrong_no_columns = """COMPLETION
--Well Branch StartMD EndmD Screen   Well/Casing Roughness Annulus Nvalve/Joint ValveType DeviceNumber
--     Number               Tubing   Casing      Roughness Content
--                          Diameter Diameter
'A1'    1      0       1000  0.1      0.2         1E-4      OA      3            AICD      1 /
'A1'    2      500     1000  0.1      0.2         1E-4      GP      0            VALVE     1 /
/


WSEGAICD
--Number    Alpha       x   y   a   b   c   d   e   f   rhocal  viscal
1    0.00021   0.0   1.0 1.1 1.2 0.9 1.3 1.4 2.1 1.1 0.5 1000.25    1.45
2    0.00042   0.1   1.1 1.0 1.0 1.0 1.0 1.0 1.0 1.5 0.8 1001.25    1.55
/
"""  # noqa: more human readable at this width.

    with pytest.raises(CaseReaderFormatError) as exc:
        ReadCasefile(case_wrong_no_columns)
    assert "Too many entries in data for keyword 'WSEGAICD'" in str(exc.value)


def test_read_case_completion_icv():
    """Test the function to read ICV completion in case file."""
    with open(Path(_TESTDIR / "icv_tubing.case"), encoding="utf-8") as fh:
        case = ReadCasefile(fh.read())
    df_true = pd.DataFrame(
        [
            ["A1", 1, 0.0, 2010.0, 0.2, 0.25, 1.00e-4, "GP", 0.0, "ICD", 1],
            ["A1", 1, 2010.0, 2030.0, 0.2, 0.25, 1.00e-4, "GP", 0.0, "ICD", 1],
            ["A1", 1, 2030.0, 3000.0, 0.2, 0.25, 1.00e-4, "GP", 1.0, "ICV", 1],
            ["A1", 2, 0.0, 2010.0, 0.2, 0.25, 1.00e-4, "GP", 0.0, "ICD", 1],
            ["A1", 2, 2010.0, 3000.0, 0.2, 0.25, 1.00e-4, "GP", 1.0, "ICD", 1],
            ["A1", 2, 3000.0, 4000.0, 0.2, 0.25, 1.00e-4, "GP", 0.0, "ICD", 1],
            ["A2", 1, 0.0, 3000.0, 0.2, 0.25, 1.00e-4, "GP", 1.0, "ICV", 2],
        ],
        columns=[
            Headers.WELL,
            Headers.BRANCH,
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.INNER_DIAMETER,
            Headers.OUTER_DIAMETER,
            Headers.ROUGHNESS,
            Headers.ANNULUS,
            Headers.VALVES_PER_JOINT,
            Headers.DEVICE_TYPE,
            Headers.DEVICE_NUMBER,
        ],
    )

    pd.testing.assert_frame_equal(df_true, case.completion_table, check_exact=False)


def test_read_case_completion_icv_tubing():
    """Test the function to read ICV completion tubing in case file."""
    with open(Path(_TESTDIR / "icv_tubing.case"), encoding="utf-8") as case_file:
        case = ReadCasefile(case_file.read())
    df_true = pd.DataFrame(
        [
            ["A1", 1, 2010.0, 2010.0, 0.2, 0.25, 1.00e-4, "GP", 1.0, "ICV", 1],
            ["A1", 1, 2030.0, 2030.0, 0.2, 0.25, 1.00e-4, "GP", 1.0, "ICV", 1],
        ],
        columns=[
            Headers.WELL,
            Headers.BRANCH,
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.INNER_DIAMETER,
            Headers.OUTER_DIAMETER,
            Headers.ROUGHNESS,
            Headers.ANNULUS,
            Headers.VALVES_PER_JOINT,
            Headers.DEVICE_TYPE,
            Headers.DEVICE_NUMBER,
        ],
    )
    pd.testing.assert_frame_equal(df_true, case.completion_icv_tubing, check_exact=False)
