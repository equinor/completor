"""Tests for icv-control error messages."""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from completor.exceptions.clean_exceptions import CompletorError
from completor.exceptions.exceptions import CaseReaderFormatError
from completor.initialization import Initialization
from completor.read_casefile import ICVReadCasefile

BASE_CASE = """
SCHFILE
  'dummy_schedule_file.sch'
/

COMPLETION
--WELL Branch Start   End   Screen    Well/ Rough Annulus Nvalve Valve Device
--     Number    mD    mD   Tubing   Casing Rough Content /Joint  Type Number
--                        Diameter Diameter
A-1        1      0 99999     0.10   0.2159 0.003      GP      1  PERF      1
B-1        1      0 99999     0.10   0.2159 0.003      GP      1  PERF      1
/

"""

VARIANT_1 = """
ICVCONTROL
-- WELL	ICV	SEGMENT	AC-TABLE STEPS	  ICVDATE FREQ MIN MAX OPENING
    A-1   A      97 0.1337      60 1.JAN.2033   30   0   1       0
    A-1   B      98 0.1337      60 1.JAN.2033   30   0   1       0
    A-1   C     183 0.1337      60 1.JAN.2033   30   0   1       0
    A-1   D     184 0.1337      60 1.JAN.2033   30   0   1       0
    B-1   H      56 0.1337      60 1.JAN.2033   30   0   1       0
    B-1   I      57 0.1337      60 1.JAN.2033   30   0   1       0
    B-1   E     184 0.1337      60 1.JAN.2033   30   0   1       0
    B-1   F     185 0.1337      60 1.JAN.2033   30   0   1       0
    B-1   G     186 0.1337      60 1.JAN.2033   30   0   1       0
/
"""

VARIANT_1_EXTENDED = """
ICVCONTROL
-- WELL	ICV	SEGMENT	AC-TABLE STEPS	  ICVDATE FREQ MIN MAX OPENING FUD FUH FUL OPERSTEP WAITSTEP  INIT
    A-1   A      97 0.1337      60 1.JAN.2033   30   0   1       0   5   2 0.1      0.2      1.0  0.01
    A-1   B      98 0.1337      60 1.JAN.2033   30   0   1       0   5   2 0.1      0.2      1.0  0.02
    A-1   C     183 0.1337      60 1.JAN.2033   30   0   1       0   5   2 0.1      0.2      1.0  0.03
    A-1   D     184 0.1337      60 1.JAN.2033   30   0   1       0   5   2 0.1      0.2      1.0  0.04
    B-1   H      56 0.1337      60 1.JAN.2033   30   0   1       0   5   2 0.1      0.2      1.0  0.05
    B-1   I      57 0.1337      60 1.JAN.2033   30   0   1       0   5   2 0.1      0.2      1.0  0.06
    B-1   E     184 0.1337      60 1.JAN.2033   30   0   1       0   5   2 0.1      0.2      1.0  0.07
    B-1   F     185 0.1337      60 1.JAN.2033   30   0   1       0   5   2 0.1      0.2      1.0  0.08
    B-1   G     186 0.1337      60 1.JAN.2033   30   0   1       0   5   2 0.1      0.2      1.0  0.09
/
"""

VARIANT_MISSING_END_MARKER = """
ICVCONTROL
-- WELL	ICV	SEGMENT	AC-TABLE STEPS	  ICVDATE  FREQ	  MIN MAX OPENING
    A-1   A      97   0.1337    60 1.JAN.2033    90     0   1       0
"""

VARIANT_MISSING_WELL_NAME = """
ICVCONTROL
-- ICV  SEGMENT AC-TABLE  STEPS  ICVDATE   FREQ   MIN MAX OPENING
    A      97   0.1337     60 1.JAN.2033     90     0   1       0
/
"""

VARIANT_MISSING_AREA = """
ICVCONTROL
-- WELL ICV SEGMENT AC-TABLE STEPS    ICVDATE FREQ  MIN MAX OPENING
    A-1   A      97 0.1337      60 1.JAN.2033   90    0   1       0
    A-1   B      98             60 1.JAN.2033   90    0   1       0
/
"""

VARIANT_WRONG_FORMAT = """
ICVCONTROL
-- WELL	ICV	SEGMENT	AC-TABLE STEPS	ICVDATE  FREQ  MIN MAX OPENING
    A-1   A      97   0.1337    60 1.JAN.2033  90    0   1       0
    A-1   B       F   FORMAT    60 1.JAN.2033  00    0   1       0
/
"""

VARIANT_REFER_TO_TABLE_WITH_NO_TABLE = """
SCHFILE
  test.sch
/

COMPLETION
--WELL Branch Start  End   Screen    Well/ Roughness Annulus Nvalve Valve Device
--     Number    mD   mD   Tubing   Casing Roughness Content /Joint  Type Number
--                       Diameter Diameter
WELL1      1    0 99999     0.10   0.2159   0.00300      GP      1  AICD      1
/

ICVCONTROL
-- D: FUD
-- H: FUH
-- FAC: Maximum rate factor for icv-control
-- FR: ICV function repetitions
-- OSTP: OPERSTEP (NEXTSTEP in operation icv-functions)
-- WSTP: WAITSTEP (NEXTSTEP in waiting icv-functions)
-- WELL ICV SEGMENT AC-TABLE STEPS     ICVDATE  FREQ  MIN MAX OPENING
    A-1   A      97   0.1337    60  1.JAN.2033    90    0   1      T1
    A-1   B      98   0.1337    60  1.JAN.2033    90    0   1      T2
/
"""

VARIANT_LONG_UDQ_NAME = """
SCHFILE
  test.sch
/

COMPLETION
--WELL Branch Start  End   Screen    Well/ Roughness Annulus Nvalve Valve Device
--     Number    mD   mD   Tubing   Casing Roughness Content /Joint  Type Number
--                       Diameter Diameter
WELL1      1    0 99999     0.10   0.2159   0.00300      GP      1  AICD      1
/

ICVCONTROL
-- D: FUD
-- H: FUH
-- FAC: Maximum rate factor for icv-control
-- FR: ICV function repetitions
-- OSTP: OPERSTEP (NEXTSTEP in operation icv-functions)
-- WSTP: WAITSTEP (NEXTSTEP in waiting icv-functions)
-- WELL ICV SEGMENT AC-TABLE  STEPS    ICVDATE  FREQ  MIN MAX OPENING
    A-1   A      97 0.1337       60  1.JAN.2033   90    0   1       0
/

CONTROL_CRITERIA
  FUNCTION: [UDQ]
  ICV: [A]
  DEFINE TESTERI_x0 /
/
"""

VARIANT_REFER_TO_TABLE_WITH_OPENING_AREA = """
SCHFILE
  test.sch
/

COMPLETION
--WELL Branch Start  End   Screen    Well/ Roughness Annulus Nvalve Valve Device
--     Number    mD   mD   Tubing   Casing Roughness Content /Joint  Type Number
--                       Diameter Diameter
WELL1      1    0 99999     0.10   0.2159   0.00300      GP      1  AICD      1
/

ICVCONTROL
-- D: FUD
-- H: FUH
-- FAC: Maximum rate factor for icv-control
-- FR: ICV function repetitions
-- OSTP: OPERSTEP (NEXTSTEP in operation icv-functions)
-- WSTP: WAITSTEP (NEXTSTEP in waiting icv-functions)
-- WELL ICV SEGMENT AC-TABLE  STEPS   ICVDATE   FREQ MIN MAX OPENING
    A-1   A      97   TABEL1     60  1.JAN.2033   90   0   1   0.047
    A-1   B      98   TABEL1     60  1.JAN.2033   90   0   1   0.047
/

ICVTABLE
TABEL1 /
-- Pos     Cd           m2
1       0.830       2.2774E-04
2       0.814       3.3613E-04
3       0.830       5.5484E-04
4       0.830       8.8387E-04
5       0.830       1.3103E-03
6       0.830       1.7368E-03
7       0.830       2.1626E-03
8       0.830       3.9671E-03
9       0.830       7.3426E-03
10      0.830       1.0463E-02
/
"""

VARIANT_ICVNAME_NA = """
ICVCONTROL
-- WELL ICV SEGMENT AC-TABLE STEPS    ICVDATE   FREQ  MIN MAX OPENING
    A-1  NA      97   0.1337    60 1.JAN.2033     90    0   1       0
/
"""


def test_icvcontrol_correct(tmpdir, caplog):
    """Test that no error message is output if enough
    data is given and types are correct."""

    tmpdir.chdir()
    case_content = BASE_CASE + VARIANT_1
    case_object = ICVReadCasefile(case_content)
    expected = pd.DataFrame(
        [
            ["A-1", "A", 97, 0.1337, 60, "1.JAN.2033", 30, 0, 1, 0, 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["A-1", "B", 98, 0.1337, 60, "1.JAN.2033", 30, 0, 1, 0, 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["A-1", "C", 183, 0.1337, 60, "1.JAN.2033", 30, 0, 1, 0, 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["A-1", "D", 184, 0.1337, 60, "1.JAN.2033", 30, 0, 1, 0, 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["B-1", "H", 56, 0.1337, 60, "1.JAN.2033", 30, 0, 1, 0, 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["B-1", "I", 57, 0.1337, 60, "1.JAN.2033", 30, 0, 1, 0, 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["B-1", "E", 184, 0.1337, 60, "1.JAN.2033", 30, 0, 1, 0, 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["B-1", "F", 185, 0.1337, 60, "1.JAN.2033", 30, 0, 1, 0, 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["B-1", "G", 186, 0.1337, 60, "1.JAN.2033", 30, 0, 1, 0, 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
        ],
        columns=[
            "WELL",
            "ICV",
            "SEGMENT",
            "AC-TABLE",
            "STEPS",
            "ICVDATE",
            "FREQ",
            "MIN",
            "MAX",
            "OPENING",
            "FUD",
            "FUH",
            "FUL",
            "OPERSTEP",
            "WAITSTEP",
            "INIT",
        ],
    )
    expected = expected.astype(
        {
            "WELL": str,
            "ICV": str,
            "SEGMENT": int,
            "AC-TABLE": str,
            "FUD": float,
            "FUH": float,
            "FUL": float,
            "STEPS": int,
            "ICVDATE": str,
            "OPERSTEP": float,
            "WAITSTEP": float,
            "FREQ": int,
            "INIT": float,
            "MIN": float,
            "MAX": float,
            "OPENING": str,
        }
    )
    assert_frame_equal(case_object.icv_control_table, expected)


def test_icvcontrol_extended_correct(tmpdir, caplog):
    """Test that no error message is output if enough
    data is given and types are correct for the extended table."""

    tmpdir.chdir()
    case_content = BASE_CASE + VARIANT_1_EXTENDED
    case_object = ICVReadCasefile(case_content)
    expected = pd.DataFrame(
        [
            ["A-1", "A", 97, 0.1337, 60, "1.JAN.2033", 30, 0, 1, 0, 5, 2, 0.1, 0.2, 1.0, 0.01],
            ["A-1", "B", 98, 0.1337, 60, "1.JAN.2033", 30, 0, 1, 0, 5, 2, 0.1, 0.2, 1.0, 0.02],
            ["A-1", "C", 183, 0.1337, 60, "1.JAN.2033", 30, 0, 1, 0, 5, 2, 0.1, 0.2, 1.0, 0.03],
            ["A-1", "D", 184, 0.1337, 60, "1.JAN.2033", 30, 0, 1, 0, 5, 2, 0.1, 0.2, 1.0, 0.04],
            ["B-1", "H", 56, 0.1337, 60, "1.JAN.2033", 30, 0, 1, 0, 5, 2, 0.1, 0.2, 1.0, 0.05],
            ["B-1", "I", 57, 0.1337, 60, "1.JAN.2033", 30, 0, 1, 0, 5, 2, 0.1, 0.2, 1.0, 0.06],
            ["B-1", "E", 184, 0.1337, 60, "1.JAN.2033", 30, 0, 1, 0, 5, 2, 0.1, 0.2, 1.0, 0.07],
            ["B-1", "F", 185, 0.1337, 60, "1.JAN.2033", 30, 0, 1, 0, 5, 2, 0.1, 0.2, 1.0, 0.08],
            ["B-1", "G", 186, 0.1337, 60, "1.JAN.2033", 30, 0, 1, 0, 5, 2, 0.1, 0.2, 1.0, 0.09],
        ],
        columns=[
            "WELL",
            "ICV",
            "SEGMENT",
            "AC-TABLE",
            "STEPS",
            "ICVDATE",
            "FREQ",
            "MIN",
            "MAX",
            "OPENING",
            "FUD",
            "FUH",
            "FUL",
            "OPERSTEP",
            "WAITSTEP",
            "INIT",
        ],
    )
    expected = expected.astype(
        {
            "WELL": str,
            "ICV": str,
            "SEGMENT": int,
            "AC-TABLE": str,
            "FUD": float,
            "FUH": float,
            "FUL": float,
            "STEPS": int,
            "ICVDATE": str,
            "OPERSTEP": float,
            "WAITSTEP": float,
            "FREQ": int,
            "INIT": float,
            "MIN": float,
            "MAX": float,
            "OPENING": str,
        }
    )
    assert_frame_equal(case_object.icv_control_table, expected)


def test_icvcontrol_missing_end_marker(tmpdir, caplog):
    """Test that the appropriate error message is
    output when end marker is missing in ICVCONTROL keyword."""

    tmpdir.chdir()
    case_content = BASE_CASE + VARIANT_MISSING_END_MARKER
    expected_error_message = "Keyword ICVCONTROL has no end record"
    with pytest.raises(CompletorError) as exception:
        ICVReadCasefile(case_content)
    assert exception.type == CompletorError
    assert expected_error_message in str(exception.value)


def test_icvcontrol_missing_wellname(tmpdir):
    """Check correct error message is given if well name is missing in
    ICVCONTROL keyword.
    """

    tmpdir.chdir()
    case_content = BASE_CASE + VARIANT_MISSING_WELL_NAME
    with pytest.raises(CaseReaderFormatError) as exc:
        ICVReadCasefile(case_content)

    expected = "Too few entries in data for keyword 'ICVCONTROL', expected 16 entries:"
    assert expected in str(exc.value)


def test_icvcontrol_icv_name_na(tmpdir):
    """Test that ICV name cannot be NA."""
    case_content = BASE_CASE + VARIANT_ICVNAME_NA
    with pytest.raises(ValueError) as exc:
        Initialization(ICVReadCasefile(case_content))

    expected = "Python reads NA as NaN, thus ICV name cannot be NA!"

    assert expected in str(exc.value)


def test_icvcontrol_wrong_format(tmpdir, caplog):
    """Test that the appropriate error message is output when a format is wrong."""
    tmpdir.chdir()
    case_content = BASE_CASE + VARIANT_WRONG_FORMAT
    expected = "ICVCONTROL table is formatted incorrectly. Note, the ordering of columns have changed"
    with pytest.raises(CaseReaderFormatError) as e:
        ICVReadCasefile(case_content)
    assert expected in str(e.value)


def test_refer_to_init_opening_table_with_no_table():
    with pytest.raises(ValueError) as e:
        Initialization(ICVReadCasefile(VARIANT_REFER_TO_TABLE_WITH_NO_TABLE))
    assert "Table was reference in the case file for ICV A, but no table was found." in str(e.value)


def test_refer_to_table_with_area_opening():
    with pytest.raises(ValueError) as e:
        Initialization(ICVReadCasefile(VARIANT_REFER_TO_TABLE_WITH_OPENING_AREA))
    assert "Seems like you refer to a table" in str(e.value)


def test_to_long_udq_name_in_control_criteria():
    """DEFINE TESTERI_x0 /"""
    with pytest.raises(ValueError) as e:
        Initialization(ICVReadCasefile(VARIANT_LONG_UDQ_NAME))
    assert "The UDQ parameter 'TESTERI_A' is longer than 8 characters. This will cause errors in Eclipse." in str(
        e.value
    )
