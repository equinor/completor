"""Tests the class functions in the initialization module"""

from pathlib import Path

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from completor import input_validation
from completor.initialization import Initialization
from completor.read_casefile import ICVReadCasefile

_TESTDIR = Path(__file__).absolute().parent / "data"
SCHEDULE_FILE_UPDATE_TEST = "icvc_update.sch"

CASE_TEXT_TWO_ICVS = """
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
-- WELL ICV SEGMENT AC-TABLE  STEPS    ICVDATE  FREQ  MIN  MAX  OPENING
    A-1   A      97   TABEL1     60 1.JAN.2033    30    0    1       T6
    A-1   B      98   TABEL1     60 1.JAN.2033    42    0    1        0
/
"""

CASE_TEXT_TWO_ICVS_INIT_OPENING_NO_TABLE = """
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
-- WELL  ICV  SEGMENT  AC-TABLE STEPS    ICVDATE   FREQ  MIN MAX OPENING
    A-1    A       97  4.705E-3    60 1.JAN.2033     30    0   1 0.001337
    A-1    B       98  4.705E-3    60 1.JAN.2033     42    0   1 0.01337
/

CONTROL_CRITERIA
  FUNCTION: [UDQ]
  ICV: [A, B]
  DEFINE FUGOR_x0 ( SGOR WELL(x0) SEG(x0) / WGOR WELL(x0) ) /
/

CONTROL_CRITERIA
  FUNCTION: [UDQ]
                        ASSIGN TEST 0.02 /
/

CONTROL_CRITERIA
  FUNCTION: [UDQ]
  DEFINE TEST /
/

CONTROL_CRITERIA
  FUNCTION: [UDQ]
  DEFINE TESTERIN /
  ASSIGN TESTERIN 0.01

/
"""

CASE_TEXT_TWO_ICVS_INIT_OPENING_NO_TABLE_T1 = """
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
    A-1   A      97 4.705E-3     60 1.JAN.2033    30    0   1      T1
    A-1   B      98 4.705E-3     60 1.JAN.2033    42    0   1      T2
/
"""

CASE_TEXT_TWO_ICVS_OPENING_VALUE = """
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
-- WELL ICV SEGMENT AC-TABLE STEPS    ICVDATE  FREQ  MIN MAX OPENING
    A-1   A      97   TABEL1    60 1.JAN.2033   90     0   1      T1
    A-1   B      98   TABEL1    60 1.JAN.2033   90     0   1      T2
/
"""

CASE_TEXT_THREE_ICVS = """
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
-- WELL ICV SEGMENT AC-TABLE   STEPS   ICVDATE  FREQ  MIN MAX OPENING FUD FUH FUL  OSP  WSP  INIT
A-1       A      97 TABEL1        60 1.JAN.2033   30    0   1       0 5.0   2 0.1  0.2  1.0  0.01
A-1       B      98 TABEL1        60 1.JAN.2033   30    0   1       0   5   2 0.1  0.2  1.0  0.02
A-1       C      99 311537-03     60 1.JAN.2033   30    0 0.5       0   4   1 0.2  0.2  1.0  0.03
/
"""


CASE_TEXT_THREE_ICVS_OPENING = """
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
-- WELL ICV SEGMENT   AC-TABLE STEPS   ICVDATE  FREQ  MIN MAX OPENING FUD FUH FUL  OPERSTEP WAITSTEP  INIT
    A-1   A      97     TABEL1    60 1.JAN.2033   30    0   1      T1   5   2 0.1       0.2      1.0  0.01
    A-1   B      98     TABEL1    60 1.JAN.2033   30    0   1      T2   5   2 0.1       0.2      1.0  0.02
    A-1   C      99  311537-03    60 1.JAN.2033   30    0 0.5      T3   5   2 0.1       0.2      1.0  0.03
/
"""

CASE_TEXT_THREE_ICVS_NO_TABLE = """
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
-- WELL ICV SEGMENT   AC-TABLE STEPS   ICVDATE  FREQ  MIN MAX OPENING FUD FUH FUL  OPERSTEP WAITSTEP  INIT
    A-1   A      97     TABEL1    60 1.JAN.2033   30    0   1      T1   5   2 0.1       0.2      1.0  0.01
    A-1   B      98     TABEL1    60 1.JAN.2033   30    0   1      T2   5   2 0.1       0.2      1.0  0.02
    A-1   C      99  311537-03    60 1.JAN.2033   30    0 0.5      T3   5   2 0.1       0.2      1.0  0.03
/
"""

CASE_TEXT_FIVE_ICVS = """
SCHFILE
  'data/dummy_schedule_file.sch'
/

COMPLETION
--WELL Branch Start  End   Screen    Well/ Roughness Annulus Nvalve Valve Device
--     Number    mD   mD   Tubing   Casing Roughness Content /Joint  Type Number
--                       Diameter Diameter
WELL1     1    0 99999     0.10   0.2159   0.00300      GP      1  AICD      1
WELL2    1    0 99999     0.10   0.2159   0.00300      GP      1  AICD      1
/

ICVCONTROL
-- D: FUD
-- H: FUH
-- FAC: Maximum rate factor for icv-control
-- FR: ICV function repetitions
-- OSTP: OPERSTEP (NEXTSTEP in operation icv-functions)
-- WSTP: WAITSTEP (NEXTSTEP in waiting icv-functions)
--
-- WELL ICV SEGMENT AC-TABLE  STEPS    ICVDATE  FREQ  MIN MAX OPENING
  WELL1   A      97   0.1337     60 1.JAN.2033    90    0   1       0
  WELL1   B      98   0.1337     60 1.JAN.2033    90    0   1       0
  WELL2   E     142   0.1337     60 1.JAN.2033    90    0   1       0
  WELL2   F     143   0.1337     60 1.JAN.2033    90    0   1       0
  WELL2   G     144   0.1337     60 1.JAN.2033    90    0   1       0
/
"""

CASE_TEXT_TIME_DEPENDENCY = """
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
-- WELL  ICV SEGMENT AC-TABLE  STEPS     ICVDATE  FREQ  MIN MAX OPENING FUD FUH FUL OPERSTEP  WAITSTEP   INIT
  WELL1    A      97   0.1337    100  1.JAN.2022    30    0   1       0   5   2 0.1      0.2       1.0   0.01
  WELL1   AA      98   0.1337    100  1.JAN.2022    30    0   1       0   5   2 0.1      0.2       1.0  0.021
/
"""

ICV_TABLE_TABEL1 = """
ICVTABLE
-- Valve name
TABEL1 /
-- Position  Cv       Area
1           1.0  0.0000474
2           1.0  0.0000790
3           1.0  0.0001317
4           1.0  0.0002195
5           1.0  0.0003659
6           1.0  0.0006098
7           1.0  0.0010160
8           1.0  0.0016938
9           1.0  0.0028230
10          1.0  0.13370
/"""

ICV_TABLE_TBL2 = """
ICVTABLE
-- Valve name
311537-03 /
-- Position  Cv     Area
1           1.0  0.0001337
2           1.0  0.0001340
3           1.0  0.0001341
4           1.0  0.0001341
5           1.0  0.0001373
6           1.0  0.0001400
7           1.0  0.0011377
8           1.0  0.0011402
9           1.0  0.0021412
10          1.0  0.0041422
/"""

ICV_TABLE_TABEL10_CV10 = """
ICVTABLE
-- Valve name
TABEL1 /
-- Position  Cv       Area
1           10  0.0000474
2           10  0.0000790
3           10  0.0001317
4           10  0.0002195
5           10  0.0003659
6           10  0.0006098
7           10  0.0010160
8           10  0.0016938
9           10  0.0028230
10          10  0.13370
/"""

ICV_TABLE_TBL20_CV10 = """
ICVTABLE
-- Valve name
311537-03 /
-- Position  Cv     Area
1           10  0.0001337
2           10  0.0001340
3           10  0.0001341
4           10  0.0001341
5           10  0.0001373
6           10  0.0001400
7           10  0.0011377
8           10  0.0011402
9           10  0.0021412
10          10  0.0041422
/"""

UPDATE_SEGMENT = """
UPDATE_SEGMENT_NUMBER
True
/"""


def test_read_icvcontrol_from_casetext():
    """
    Test that the data read from ICVCONTROL
    keyword is in the correct format.
    """

    df_temp = pd.DataFrame(
        [
            ["A-1", "A", 97, "TABEL1", 60, "1.JAN.2033", 30, 0, 1, "T6", 1, 10, 0.1, 2.0, 1.0, 0.01],
            ["A-1", "B", 98, "TABEL1", 60, "1.JAN.2033", 42, 0, 1, "0", 1, 10, 0.1, 2.0, 1.0, 0.01],
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
    initialization = Initialization(ICVReadCasefile(CASE_TEXT_TWO_ICVS))
    expected_ICVCONTROL_keyword = input_validation.set_format_icvcontrol(df_temp)
    ICVCONTROL_keyword = initialization.icv_control_table
    assert_frame_equal(ICVCONTROL_keyword, expected_ICVCONTROL_keyword)


def test_input_file_text_two_icvs():
    """Test output of the INPUT-file text for well with two icvs."""

    expected_input_file_text = """-- User input, specific for this input file

UDQ

------------------------------------------------------------
-- Time-stepping:

  ASSIGN FUD_A 1.0 /
  ASSIGN FUH_A 10.0 /
  ASSIGN FUL_A 0.1 /

  ASSIGN FUD_B 1.0 /
  ASSIGN FUH_B 10.0 /
  ASSIGN FUL_B 0.1 /


------------------------------------------------------------
-- Balance criteria


  ASSIGN FUTC_A 0 /
  ASSIGN FUTO_A 0 /
  ASSIGN FUP_A 2 /

  ASSIGN FUTC_B 0 /
  ASSIGN FUTO_B 0 /
  ASSIGN FUP_B 2 /
/
"""

    initialization = Initialization(ICVReadCasefile(CASE_TEXT_TWO_ICVS))
    assert initialization.init_icvcontrol == expected_input_file_text


def test_input_file_text_three_icvs():
    """Test output of the INPUT-file text for well with three icvs."""

    myinit_three_icvs = Initialization(ICVReadCasefile(CASE_TEXT_THREE_ICVS))

    expected_input_file_text = """-- User input, specific for this input file

UDQ

------------------------------------------------------------
-- Time-stepping:

  ASSIGN FUD_A 5.0 /
  ASSIGN FUH_A 2.0 /
  ASSIGN FUL_A 0.1 /

  ASSIGN FUD_B 5.0 /
  ASSIGN FUH_B 2.0 /
  ASSIGN FUL_B 0.1 /

  ASSIGN FUD_C 4.0 /
  ASSIGN FUH_C 1.0 /
  ASSIGN FUL_C 0.2 /


------------------------------------------------------------
-- Balance criteria


  ASSIGN FUTC_A 0 /
  ASSIGN FUTO_A 0 /
  ASSIGN FUP_A 2 /

  ASSIGN FUTC_B 0 /
  ASSIGN FUTO_B 0 /
  ASSIGN FUP_B 2 /

  ASSIGN FUTC_C 0 /
  ASSIGN FUTO_C 0 /
  ASSIGN FUP_C 2 /
/
"""

    assert myinit_three_icvs.init_icvcontrol == expected_input_file_text


def test_output_input_icvcontrol_file_two_icvs_opening_value(log_warning):
    """UDQdefine with two icvs with opening value.
    --WELL	ICV SEGMENT AC-TABLE FUD FUH FUL STEPS	  ICVDATE OSP WSP  FREQ	 INIT MIN MAX OPENING
    A-1      A       97     TABEL1   5   2 0.1    60 1.JAN.2033 0.2 1.0    90  0.01   0   1 T1
    A-1      B       98     TABEL1   5   2 0.1    60 1.JAN.2033 0.2 1.0    90  0.02   0   1 T2
    """
    case = CASE_TEXT_TWO_ICVS_OPENING_VALUE + ICV_TABLE_TABEL1
    expected_input_icvcontrol_output = """UDQ

-- Initialization

  ASSIGN FUFRQ_A 90 /
  ASSIGN FUFRQ_B 90 /

  ASSIGN FUT_A 90 /
  ASSIGN FUT_B 90 /

  ASSIGN FUCH_A 0.0 /
  ASSIGN FUOP_A 1.0 /

  ASSIGN FUCH_B 0.0 /
  ASSIGN FUOP_B 1.0 /

  ASSIGN FUTSTP 0 /

-- Definition of parameters,
-- continuously updated:

  DEFINE FUTSTP TIMESTEP /
  DEFINE FUT_A FUT_A + TIMESTEP /
  DEFINE FUT_B FUT_B + TIMESTEP /

  DEFINE FUPOS_A 1 /
  DEFINE FUPOS_B 2 /

  DEFINE FUARE_A TU_TABEL1[FUPOS_A] /
  DEFINE FUARE_B TU_TABEL1[FUPOS_B] /
/"""

    initialization = Initialization(ICVReadCasefile(case))
    assert initialization.input_icvcontrol == expected_input_icvcontrol_output


def test_output_input_icvcontrol_file_two_icvs(log_warning):
    expected_input_icvcontrol_output = """UDQ

-- Initialization

  ASSIGN FUFRQ_A 30 /
  ASSIGN FUFRQ_B 42 /

  ASSIGN FUT_A 30 /
  ASSIGN FUT_B 42 /

  ASSIGN FUCH_A 0.0 /
  ASSIGN FUOP_A 1.0 /

  ASSIGN FUCH_B 0.0 /
  ASSIGN FUOP_B 1.0 /

  ASSIGN FUTSTP 0 /

  ASSIGN FUGOR_A 0.01 /

-- Definition of parameters,
-- continuously updated:

  DEFINE FUTSTP TIMESTEP /
  DEFINE FUT_A FUT_A + TIMESTEP /
  DEFINE FUT_B FUT_B + TIMESTEP /

  DEFINE FUGOR_A ( SGOR 'A-1' 97 / WGOR 'A-1' ) /
  ASSIGN TEST 0.02 /
  ASSIGN TESTERIN 0.01 /
  DEFINE TEST /
  DEFINE TESTERIN /

  ASSIGN FUARE_A 4.705E-3 /
  ASSIGN FUARE_B 4.705E-3 /
/"""

    initialization = Initialization(ICVReadCasefile(CASE_TEXT_TWO_ICVS_INIT_OPENING_NO_TABLE))
    assert initialization.input_icvcontrol == expected_input_icvcontrol_output


def test_output_input_icvcontrol_file_two_icvs_init_opening_no_table(log_warning):
    """
        WELL	ICV SEGMENT AC-TABLE FUD FUH FUL STEPS	  ICVDATE OSP WSP  FREQ	 INIT MIN MAX OPENING
    A-1       A      97 4.705E-3 5   2 0.1    60 1.JAN.2033 0.2 1.0    30  0.01   0   1 0.001337
    A-1       B      98 4.705E-3 5   2 0.1    60 1.JAN.2033 0.2 1.0    42  0.02   0   1 0.01337
    """
    expected_input_icvcontrol_output = """UDQ

-- Initialization

  ASSIGN FUFRQ_A 30 /
  ASSIGN FUFRQ_B 42 /

  ASSIGN FUT_A 30 /
  ASSIGN FUT_B 42 /

  ASSIGN FUCH_A 0.0 /
  ASSIGN FUOP_A 1.0 /

  ASSIGN FUCH_B 0.0 /
  ASSIGN FUOP_B 1.0 /

  ASSIGN FUTSTP 0 /

  ASSIGN FUGOR_A 0.01 /

-- Definition of parameters,
-- continuously updated:

  DEFINE FUTSTP TIMESTEP /
  DEFINE FUT_A FUT_A + TIMESTEP /
  DEFINE FUT_B FUT_B + TIMESTEP /

  DEFINE FUGOR_A ( SGOR 'A-1' 97 / WGOR 'A-1' ) /
  ASSIGN TEST 0.02 /
  ASSIGN TESTERIN 0.01 /
  DEFINE TEST /
  DEFINE TESTERIN /

  ASSIGN FUARE_A 4.705E-3 /
  ASSIGN FUARE_B 4.705E-3 /
/"""

    initialization = Initialization(ICVReadCasefile(CASE_TEXT_TWO_ICVS_INIT_OPENING_NO_TABLE))
    assert initialization.input_icvcontrol == expected_input_icvcontrol_output


def test_output_input_icvcontrol_file_three_icvs(log_warning):
    myinit_three_icvs = Initialization(ICVReadCasefile(CASE_TEXT_THREE_ICVS_NO_TABLE))

    expected_input_icvcontrol_output = """UDQ

-- Initialization

  ASSIGN FUFRQ_A 30 /
  ASSIGN FUFRQ_B 30 /
  ASSIGN FUFRQ_C 30 /

  ASSIGN FUT_A 30 /
  ASSIGN FUT_B 30 /
  ASSIGN FUT_C 30 /

  ASSIGN FUCH_A 0.0 /
  ASSIGN FUOP_A 1.0 /

  ASSIGN FUCH_B 0.0 /
  ASSIGN FUOP_B 1.0 /

  ASSIGN FUCH_C 0.0 /
  ASSIGN FUOP_C 0.5 /

  ASSIGN FUTSTP 0 /

-- Definition of parameters,
-- continuously updated:

  DEFINE FUTSTP TIMESTEP /
  DEFINE FUT_A FUT_A + TIMESTEP /
  DEFINE FUT_B FUT_B + TIMESTEP /
  DEFINE FUT_C FUT_C + TIMESTEP /

/"""

    assert myinit_three_icvs.input_icvcontrol == expected_input_icvcontrol_output


def test_input_file_text_time_dependent(log_warning):
    """Test output of the input file text with time dependency."""

    result = Initialization(ICVReadCasefile(CASE_TEXT_TIME_DEPENDENCY))

    expected_input_file_text = """-- User input, specific for this input file

UDQ

------------------------------------------------------------
-- Time-stepping:

  ASSIGN FUD_A 5.0 /
  ASSIGN FUH_A 2.0 /
  ASSIGN FUL_A 0.1 /

  ASSIGN FUD_AA 5.0 /
  ASSIGN FUH_AA 2.0 /
  ASSIGN FUL_AA 0.1 /


------------------------------------------------------------
-- Balance criteria


  ASSIGN FUTC_A 0 /
  ASSIGN FUTO_A 0 /
  ASSIGN FUP_A 2 /

  ASSIGN FUTC_AA 0 /
  ASSIGN FUTO_AA 0 /
  ASSIGN FUP_AA 2 /
/
"""

    assert result.init_icvcontrol == expected_input_file_text


def test_create_icv_opening_table():
    """Test output of the INPUT-file text for well with three icvs."""
    input_case = CASE_TEXT_THREE_ICVS + ICV_TABLE_TABEL1 + ICV_TABLE_TBL2
    expected_input_file_text = """-- User input, specific for this input file

UDQ

------------------------------------------------------------
-- Time-stepping:

  ASSIGN FUD_A 5.0 /
  ASSIGN FUH_A 2.0 /
  ASSIGN FUL_A 0.1 /

  ASSIGN FUD_B 5.0 /
  ASSIGN FUH_B 2.0 /
  ASSIGN FUL_B 0.1 /

  ASSIGN FUD_C 4.0 /
  ASSIGN FUH_C 1.0 /
  ASSIGN FUL_C 0.2 /


------------------------------------------------------------
-- Balance criteria


  ASSIGN FUTC_A 0 /
  ASSIGN FUTO_A 0 /
  ASSIGN FUP_A 2 /

  ASSIGN FUTC_B 0 /
  ASSIGN FUTO_B 0 /
  ASSIGN FUP_B 2 /

  ASSIGN FUTC_C 0 /
  ASSIGN FUTO_C 0 /
  ASSIGN FUP_C 2 /
/


------------------------------------------------------------
-- ICV opening position tables
UDT
-- ICV  A  B
  'TU_TABEL1' 1 /
  'NV' 1 2 3 4 5 6 7 8 9 10 /
  4.740e-05 7.900e-05 1.317e-04 2.195e-04 3.659e-04 6.098e-04 1.016e-03 1.694e-03 2.823e-03 1.337e-01 /
  /
/

UDT
-- ICV  C
  'TU_311537-03' 1 /
  'NV' 1 2 3 4 5 6 7 8 9 10 /
  1.337e-04 1.340e-04 1.341e-04 1.341e-04 1.373e-04 1.400e-04 1.138e-03 1.140e-03 2.141e-03 4.142e-03 /
  /
/

"""

    result = Initialization(ICVReadCasefile(input_case))
    assert result.init_icvcontrol == expected_input_file_text


def test_create_icv_opening_table_cv_area():
    """Test output of the INPUT-file text for well with three icvs."""
    input_case = CASE_TEXT_THREE_ICVS + ICV_TABLE_TABEL10_CV10 + ICV_TABLE_TBL20_CV10
    expected_input_file_text = """-- User input, specific for this input file

UDQ

------------------------------------------------------------
-- Time-stepping:

  ASSIGN FUD_A 5.0 /
  ASSIGN FUH_A 2.0 /
  ASSIGN FUL_A 0.1 /

  ASSIGN FUD_B 5.0 /
  ASSIGN FUH_B 2.0 /
  ASSIGN FUL_B 0.1 /

  ASSIGN FUD_C 4.0 /
  ASSIGN FUH_C 1.0 /
  ASSIGN FUL_C 0.2 /


------------------------------------------------------------
-- Balance criteria


  ASSIGN FUTC_A 0 /
  ASSIGN FUTO_A 0 /
  ASSIGN FUP_A 2 /

  ASSIGN FUTC_B 0 /
  ASSIGN FUTO_B 0 /
  ASSIGN FUP_B 2 /

  ASSIGN FUTC_C 0 /
  ASSIGN FUTO_C 0 /
  ASSIGN FUP_C 2 /
/


------------------------------------------------------------
-- ICV opening position tables
UDT
-- ICV  A  B
  'TU_TABEL1' 1 /
  'NV' 1 2 3 4 5 6 7 8 9 10 /
  4.740e-04 7.900e-04 1.317e-03 2.195e-03 3.659e-03 6.098e-03 1.016e-02 1.694e-02 2.823e-02 1.337e+00 /
  /
/

UDT
-- ICV  C
  'TU_311537-03' 1 /
  'NV' 1 2 3 4 5 6 7 8 9 10 /
  1.337e-03 1.340e-03 1.341e-03 1.341e-03 1.373e-03 1.400e-03 1.138e-02 1.140e-02 2.141e-02 4.142e-02 /
  /
/

"""

    result = Initialization(ICVReadCasefile(input_case))
    assert result.init_icvcontrol == expected_input_file_text


def test_output_input_icvcontrol_file_two_icvs_opening_tableslog_warning():
    """Test output input_icvcontrol.udq when opening tables are supplied."""
    input_case = CASE_TEXT_TWO_ICVS + ICV_TABLE_TABEL1
    expected_input_icvcontrol_output = """UDQ

-- Initialization

  ASSIGN FUFRQ_A 30 /
  ASSIGN FUFRQ_B 42 /

  ASSIGN FUT_A 30 /
  ASSIGN FUT_B 42 /

  ASSIGN FUCH_A 0.0 /
  ASSIGN FUOP_A 1.0 /

  ASSIGN FUCH_B 0.0 /
  ASSIGN FUOP_B 1.0 /

  ASSIGN FUTSTP 0 /

-- Definition of parameters,
-- continuously updated:

  DEFINE FUTSTP TIMESTEP /
  DEFINE FUT_A FUT_A + TIMESTEP /
  DEFINE FUT_B FUT_B + TIMESTEP /

  DEFINE FUPOS_A 6 /
  DEFINE FUPOS_B 10 /

  DEFINE FUARE_A TU_TABEL1[FUPOS_A] /
  DEFINE FUARE_B TU_TABEL1[FUPOS_B] /
/"""

    result = Initialization(ICVReadCasefile(input_case))

    assert result.input_icvcontrol == expected_input_icvcontrol_output


def test_output_input_icvcontrol_file_three_icvs_opening_tables(log_warning):
    """Test output input_icvcontrol.udq when two opening tables are supplied."""
    input_case = CASE_TEXT_THREE_ICVS + ICV_TABLE_TABEL1 + ICV_TABLE_TBL2
    expected_input_icvcontrol_output = """UDQ

-- Initialization

  ASSIGN FUFRQ_A 30 /
  ASSIGN FUFRQ_B 30 /
  ASSIGN FUFRQ_C 30 /

  ASSIGN FUT_A 30 /
  ASSIGN FUT_B 30 /
  ASSIGN FUT_C 30 /

  ASSIGN FUCH_A 0.0 /
  ASSIGN FUOP_A 1.0 /

  ASSIGN FUCH_B 0.0 /
  ASSIGN FUOP_B 1.0 /

  ASSIGN FUCH_C 0.0 /
  ASSIGN FUOP_C 0.5 /

  ASSIGN FUTSTP 0 /

-- Definition of parameters,
-- continuously updated:

  DEFINE FUTSTP TIMESTEP /
  DEFINE FUT_A FUT_A + TIMESTEP /
  DEFINE FUT_B FUT_B + TIMESTEP /
  DEFINE FUT_C FUT_C + TIMESTEP /

  DEFINE FUPOS_A 10 /
  DEFINE FUPOS_B 10 /
  DEFINE FUPOS_C 10 /

  DEFINE FUARE_A TU_TABEL1[FUPOS_A] /
  DEFINE FUARE_B TU_TABEL1[FUPOS_B] /
  DEFINE FUARE_C TU_311537-03[FUPOS_C] /
/"""
    result = Initialization(ICVReadCasefile(input_case))

    assert result.input_icvcontrol == expected_input_icvcontrol_output


def test_output_input_icvcontrol_custom_content(log_warning):
    """Test output input_icvcontrol.udq when two opening tables are supplied."""
    input_CONTROL_CRITERIA = """
     \t CONTROL_CRITERIA
  FUNCTION: [UDQ] -- A Dummy comment
  ICV: [A, B,                                    C]
    TEST_x0 TO neigbor_x1 WELL(X0) SEG(X1) INSERT IN POS 1 UDQ REPLACEMENT
    TEST_x2 COND TO INSERT IN POS 2 WELL(x2) SEG(X2) /
/

CONTROL_CRITERIA -- Should not affect the UDQDEFINE file
  FUNCTION: [CHOKE]
  ICV: [A, B, C]
  CRITERIA: [1,2]
 POS1 A, J ICV /
 POS2 A, J ICV /
/

CONTROL_CRITERIA
  FUNCTION: [UDQ] -- A Dummy comment
  ICV: [B, C, A]
DEFINE PRINT_B

/

CONTROL_CRITERIA
  FUNCTION: [UDQ] -- A Dummy comment
  ICV: [B]
ASSIGN WRITE_B
/

\t CONTROL_CRITERIA
  FUNCTION: [UDQ] -- A Dummy comment
  ICV: [B, C, A]
 POS1_x1 test_X2 SEG(x1) WELL(X1) ICV /
POS2_x1 test_x2 SEG(X2) WELL(x2) ICV -- malformed end of rec

/ \t

    """
    input_case = CASE_TEXT_THREE_ICVS_NO_TABLE + input_CONTROL_CRITERIA

    expected_input_icvcontrol_output = """UDQ

-- Initialization

  ASSIGN FUFRQ_A 30 /
  ASSIGN FUFRQ_B 30 /
  ASSIGN FUFRQ_C 30 /

  ASSIGN FUT_A 30 /
  ASSIGN FUT_B 30 /
  ASSIGN FUT_C 30 /

  ASSIGN FUCH_A 0.0 /
  ASSIGN FUOP_A 1.0 /

  ASSIGN FUCH_B 0.0 /
  ASSIGN FUOP_B 1.0 /

  ASSIGN FUCH_C 0.0 /
  ASSIGN FUOP_C 0.5 /

  ASSIGN FUTSTP 0 /

  ASSIGN PRINT_B 0.02 /

-- Definition of parameters,
-- continuously updated:

  DEFINE FUTSTP TIMESTEP /
  DEFINE FUT_A FUT_A + TIMESTEP /
  DEFINE FUT_B FUT_B + TIMESTEP /
  DEFINE FUT_C FUT_C + TIMESTEP /

  TEST_A TO NEIGBOR_B 'A-1' 98 INSERT IN POS 1 UDQ REPLACEMENT /
  TEST_C COND TO INSERT IN POS 2 'A-1' 99 /
  ASSIGN WRITE_B /
  DEFINE PRINT_B /
  POS1_C TEST_A 99 'A-1' ICV /
  POS2_C TEST_A 97 'A-1' ICV /

/"""
    result = Initialization(ICVReadCasefile(input_case))

    assert result.input_icvcontrol == expected_input_icvcontrol_output


def test_output_input_icvcontrol_custom_content_icv_table(log_warning):
    """Test output input_icvcontrol.udq when two opening tables are supplied."""
    input_CONTROL_CRITERIA = """
     \t CONTROL_CRITERIA
  FUNCTION: [UDQ] -- A Dummy comment
  ICV: [A,B,C]
    DEFINE SPAM_x0 and some other stuff /
    DEFINE EGGS_x1 -- missing eor
/

CONTROL_CRITERIA -- Should not affect the UDQDEFINE file
  FUNCTION: [CHOKE]
  ICV: [A, B]
  CRITERIA: [1,2]
 POS1 A, J ICV /
 POS2 A, J ICV /
/"""
    expected_input_icvcontrol_output = """UDQ

-- Initialization

  ASSIGN FUFRQ_A 30 /
  ASSIGN FUFRQ_B 30 /
  ASSIGN FUFRQ_C 30 /

  ASSIGN FUT_A 30 /
  ASSIGN FUT_B 30 /
  ASSIGN FUT_C 30 /

  ASSIGN FUCH_A 0.0 /
  ASSIGN FUOP_A 1.0 /

  ASSIGN FUCH_B 0.0 /
  ASSIGN FUOP_B 1.0 /

  ASSIGN FUCH_C 0.0 /
  ASSIGN FUOP_C 0.5 /

  ASSIGN FUTSTP 0 /

  ASSIGN SPAM_A 0.01 /
  ASSIGN EGGS_B 0.02 /

-- Definition of parameters,
-- continuously updated:

  DEFINE FUTSTP TIMESTEP /
  DEFINE FUT_A FUT_A + TIMESTEP /
  DEFINE FUT_B FUT_B + TIMESTEP /
  DEFINE FUT_C FUT_C + TIMESTEP /

  DEFINE SPAM_A AND SOME OTHER STUFF /
  DEFINE EGGS_B /

  DEFINE FUPOS_A 10 /
  DEFINE FUPOS_B 10 /
  DEFINE FUPOS_C 10 /

  DEFINE FUARE_A TU_TABEL1[FUPOS_A] /
  DEFINE FUARE_B TU_TABEL1[FUPOS_B] /
  DEFINE FUARE_C TU_311537-03[FUPOS_C] /
/"""
    input_case = CASE_TEXT_THREE_ICVS + ICV_TABLE_TABEL1 + ICV_TABLE_TBL2 + input_CONTROL_CRITERIA
    result = Initialization(ICVReadCasefile(input_case))

    assert result.input_icvcontrol == expected_input_icvcontrol_output


def test_output_input_icvcontrol_custom_content_icv_table2(log_warning):
    """Test output input_icvcontrol.udq when two opening tables are supplied."""

    input_CONTROL_CRITERIA = """
     \t CONTROL_CRITERIA
  FUNCTION: [UDQ] -- A Dummy comment
  ICV: [A,B,C], [B,A], [C,B]
    DEFINE SPAM_x0 and some other stuff /
    DEFINE EGGS_x1 -- missing eor
/
"""
    expected_input_icvcontrol_output = """UDQ

-- Initialization

  ASSIGN FUFRQ_A 30 /
  ASSIGN FUFRQ_B 30 /
  ASSIGN FUFRQ_C 30 /

  ASSIGN FUT_A 30 /
  ASSIGN FUT_B 30 /
  ASSIGN FUT_C 30 /

  ASSIGN FUCH_A 0.0 /
  ASSIGN FUOP_A 1.0 /

  ASSIGN FUCH_B 0.0 /
  ASSIGN FUOP_B 1.0 /

  ASSIGN FUCH_C 0.0 /
  ASSIGN FUOP_C 0.5 /

  ASSIGN FUTSTP 0 /

  ASSIGN SPAM_A 0.01 /
  ASSIGN EGGS_B 0.02 /

  ASSIGN SPAM_B 0.02 /
  ASSIGN EGGS_A 0.01 /

  ASSIGN SPAM_C 0.03 /
  ASSIGN EGGS_B 0.02 /

-- Definition of parameters,
-- continuously updated:

  DEFINE FUTSTP TIMESTEP /
  DEFINE FUT_A FUT_A + TIMESTEP /
  DEFINE FUT_B FUT_B + TIMESTEP /
  DEFINE FUT_C FUT_C + TIMESTEP /

  DEFINE SPAM_A AND SOME OTHER STUFF /
  DEFINE EGGS_B /
  DEFINE SPAM_B AND SOME OTHER STUFF /
  DEFINE EGGS_A /
  DEFINE SPAM_C AND SOME OTHER STUFF /
  DEFINE EGGS_B /

  DEFINE FUPOS_A 1 /
  DEFINE FUPOS_B 2 /
  DEFINE FUPOS_C 3 /

  DEFINE FUARE_A TU_TABEL1[FUPOS_A] /
  DEFINE FUARE_B TU_TABEL1[FUPOS_B] /
  DEFINE FUARE_C TU_311537-03[FUPOS_C] /
/"""

    input_case = CASE_TEXT_THREE_ICVS_OPENING + ICV_TABLE_TABEL1 + ICV_TABLE_TBL2 + input_CONTROL_CRITERIA
    result = Initialization(ICVReadCasefile(input_case))
    assert result.input_icvcontrol == expected_input_icvcontrol_output


@pytest.mark.parametrize("icv, expected_num_icvs", (["A", 2], ["B", 2], ["E", 3], ["F", 3], ["G", 3]))
def test_number_of_icvs(icv, expected_num_icvs):
    """Test to find number of icvs in well from input segment name."""
    initialization = Initialization(ICVReadCasefile(CASE_TEXT_FIVE_ICVS))
    number_of_icvs = initialization.number_of_icvs(icv)
    assert number_of_icvs == expected_num_icvs


def test_create_summary_content():
    """Check that .summary files are created correctly."""
    custom_content = """
CONTROL_CRITERIA
  FUNCTION: [UDQ]
  ICV: [A]
  DEFINE TEST_x0 WWIR WELL(x0) * FU_x0 /
  DEFINE TEST_x0 (-1.0) * SWFR WELL(x1) SEG(x0) /
/"""

    expected = """FUFRQ_A

FUFRQ_B

FUT_A

FUT_B

FUCH_A

FUOP_A

FUCH_B

FUOP_B

FUTSTP

TEST_A

FUP_A

FUTC_A

FUTO_A

FUP_B

FUTC_B

FUTO_B

SFOPN
'A-1' 97 /
'A-1' 98 /
/

"""
    initialization = Initialization(ICVReadCasefile(CASE_TEXT_TWO_ICVS + custom_content))
    assert expected == initialization.summary
