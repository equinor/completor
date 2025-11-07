"""Tests for the icv_functions module in icv-control"""

import pytest

from completor.constants import ICVMethod
from completor.icv_functions import IcvFunctions
from completor.initialization import Initialization
from completor.read_casefile import ICVReadCasefile

CASE_TEXT = """
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
--
-- WELL ICV SEGMENT AC-TABLE STEPS       ICVDATE    FREQ  MIN MAX OPENING
WELL1     A   105         A     100   1.JAN.2022      30    0   1     T10
WELL1     B   106         A     100   1.JAN.2022      30    0   1      T5
WELL2     E   142   0.1337      100   1.JAN.2022      30    0   1       0
WELL2     F   143   0.1337      100   1.JAN.2022      30    0   1       0
WELL2     G   144   0.1337      100   1.JAN.2022      30    0   1       0
WELL3    BY   60   1.0077120   1320   1.JAN.2023      30    0   1       0
WELL3    BX   60   0.0077120   1320   1.JAN.2023      30    0   1       0
WELL4    A1   60   0.0077120   1320   1.JAN.2023      30    0   1       0
/

ICVTABLE
A /
-- postition cv area
 1	1 0
 2	1 0
 3	1 5.1191E-05
 4	1 1.3708E-04
 5	1 2.3026E-04
 6	1 3.7484E-04
 7	1 8.3050E-04
 8	1 2.3122E-03
 9  1 5.7019E-03
10	1 7.7120E-03
/

"""

CASE_TEXT_3WELLS = """
SCHFILE
  'data/dummy_schedule_file.sch'
/

COMPLETION
--WELL Branch Start  End   Screen    Well/ Roughness Annulus Nvalve Valve Device
--     Number    mD   mD   Tubing   Casing Roughness Content /Joint  Type Number
--                       Diameter Diameter
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
-- WELL ICV SEGMENT AC-TABLE STEPS     ICVDATE  FREQ MIN MAX OPENING FUD FUH FUL  OPERSTEP WAITSTEP  INIT
WELL2     E   142   0.1337     100  1.JAN.2022    30   0   1       0   5   2 0.1       0.2      1.0  0.07
WELL2     F   143   0.1337     100  1.JAN.2022    30   0   1       0   5   2 0.1       0.2      1.0  0.08
WELL2     G   144   0.1337     100  1.JAN.2022    30   0   1       0   5   2 0.1       0.2      1.0  0.09
/

ICVTABLE
A /
-- postition cv area
 1	1 0
 2	1 0
 3	1 5.1191E-05
 4	1 1.3708E-04
 5	1 2.3026E-04
 6	1 3.7484E-04
 7	1 8.3050E-04
 8	1 2.3122E-03
 9  1 5.7019E-03
10	1 7.7120E-03
/

"""

CASE_TEXT_OPENING_TABLE = """
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
-- WELL ICV SEGMENT AC-TABLE STEPS     ICVDATE  FREQ  MIN MAX OPENING FUD FUH  FUL  OPERSTEP WAITSTEP  INIT
  WELL1   A     105        A   100  1.JAN.2022    30    0   1     T10   5   2  0.1       0.2      1.0  0.01
  WELL1   B     106        A   100  1.JAN.2022    30    0   1      T5   5   2  0.1       0.2      1.0  0.02
/
"""

TEST_ICV_FUNCTIONS = IcvFunctions(Initialization(ICVReadCasefile(CASE_TEXT)))
ICV_NAME = "A"


def test_general_create_actionx():
    """Test creating a general purpose Eclipse ACTIONX statement"""
    record1 = "  CH1W_A01  100  10 /\n"
    record2 = "  WWIR > 100 /\n/"
    action = "UDQ\n  NEXTSTEP = STEP + 1 /\n/"
    actionx = TEST_ICV_FUNCTIONS.create_actionx(record1, record2, action)
    expected_actionx = """ACTIONX
  CH1W_A01  100  10 /
  WWIR > 100 /
/
UDQ
  NEXTSTEP = STEP + 1 /
/
"""
    assert actionx == expected_actionx


@pytest.mark.parametrize(
    "icv_function, step, expected_name",
    [
        (ICVMethod.OPEN, 1, "OP1A_001"),
        (ICVMethod.OPEN, 1, "OP1A_001"),
        (ICVMethod.OPEN, 10, "OP1A_010"),
        (ICVMethod.OPEN, 10, "OP1A_010"),
        (ICVMethod.OPEN_WAIT, 1, "WO1A_001"),
        (ICVMethod.OPEN_WAIT, 1, "WO1A_001"),
        (ICVMethod.OPEN_WAIT, 10, "WO1A_010"),
        (ICVMethod.OPEN_WAIT, 10, "WO1A_010"),
        (ICVMethod.OPEN_READY, 1, "READYO1A"),
        (ICVMethod.OPEN_READY, 1, "READYO1A"),
        (ICVMethod.OPEN_STOP, 1, "STOPO1A"),
        (ICVMethod.OPEN_STOP, 1, "STOPO1A"),
        (ICVMethod.CHOKE, 1, "CH1A_001"),
        (ICVMethod.CHOKE, 1, "CH1A_001"),
        (ICVMethod.CHOKE, 10, "CH1A_010"),
        (ICVMethod.CHOKE, 10, "CH1A_010"),
        (ICVMethod.CHOKE_WAIT, 1, "WC1A_001"),
        (ICVMethod.CHOKE_WAIT, 1, "WC1A_001"),
        (ICVMethod.CHOKE_WAIT, 10, "WC1A_010"),
        (ICVMethod.CHOKE_WAIT, 10, "WC1A_010"),
        (ICVMethod.CHOKE_READY, 1, "READYC1A"),
        (ICVMethod.CHOKE_READY, 1, "READYC1A"),
        (ICVMethod.CHOKE_STOP, 1, "STOPC1A"),
        (ICVMethod.CHOKE_STOP, 1, "STOPC1A"),
    ],
)
def test_create_action_name(icv_function, step, expected_name):
    """Test creating an action name."""
    criterium = 1
    action_name = TEST_ICV_FUNCTIONS.create_action_name(ICV_NAME, icv_function, step, criterium)
    assert action_name == expected_name


def test_create_record1():
    """Test to creating record 1 in the Eclipse ACTIONX keyword"""
    action_name = "CH1W_A05"
    trigger_number_times = 10000
    trigger_minimum_interval = 10
    record1 = TEST_ICV_FUNCTIONS.create_record1(action_name, trigger_number_times, trigger_minimum_interval)
    expected_record1 = "  CH1W_A05 10000 10 /\n"
    assert record1 == expected_record1


def test_create_record2_choke_wait_stop():
    """Test creating record 2 in the Eclipse ACTIONX keyword for icvc.
    Two ICVs."""
    record2 = TEST_ICV_FUNCTIONS.create_record2_choke_wait_stop("A")
    expected_record2 = """  FUP_A = 2 AND /
  FUTC_A != 0 /
/
"""
    assert record2 == expected_record2


def test_create_record2_choke_wait():
    """Tests creating record 2 in the Eclipse ACTIONX keyword for icvc"""
    criteria = 1
    step = 1
    record2 = TEST_ICV_FUNCTIONS.create_record2_choke_wait(ICV_NAME, step, criteria)
    expected_record2 = """  FUTC_A <= FUD_A AND /
  FUP_A = 2 AND /
  FUT_A > FUFRQ_A /
/
"""
    assert record2 == expected_record2


def test_create_record2_choke_wait_step2():
    """Tests creating record 2 in the Eclipse ACTIONX keyword for icvc.
    Two ICVs."""

    criteria = 1
    step = 2
    record2 = TEST_ICV_FUNCTIONS.create_record2_choke_wait("A", step, criteria)
    expected_record2 = """  FUTSTP > FUL_A AND /
  FUTC_A <= FUD_A AND /
  FUP_A = 2 AND /
  FUT_A > FUFRQ_A /
/
"""
    assert record2 == expected_record2


def test_create_record2_open_wait():
    """Tests creating record 2 in the Eclipse ACTIONX keyword for icvc.
    Two ICVs."""
    step = 1
    criteria = 1
    record2 = TEST_ICV_FUNCTIONS.create_record2_open_wait("A", step, criteria)
    expected_record2 = """  FUTO_A <= FUD_A AND /
  FUP_A = 2 AND /
  FUT_A > FUFRQ_A /
/
"""

    assert record2 == expected_record2


def test_create_record2_choke_ready_nicv2():
    """Test creating record 2 in the Eclipse ACTIONX keyword for icvc.
    Two ICVs."""
    criteria = 1
    record2 = TEST_ICV_FUNCTIONS.create_record2_choke_ready("A", criteria)
    expected_record2 = """  FUTC_A > FUD_A AND /
  FUP_A = 2 /
/
"""
    assert record2 == expected_record2


def test_create_record2_open_ready():
    """Test creating record 2 in the Eclipse ACTIONX keyword for icvc.
    Two ICVs."""
    criteria = 1
    record2 = TEST_ICV_FUNCTIONS.create_record2_open_ready("A", criteria)
    expected_record2 = """  FUTO_A > FUD_A AND /
  FUP_A = 2 /
/
"""
    assert record2 == expected_record2


def test_create_record2_choke_stop():
    """Test creating record 2 in the Eclipse ACTIONX keyword for icvc.
    Three ICVs."""
    record2 = TEST_ICV_FUNCTIONS.create_record2_choke_stop("E", 1)
    expected_record2 = """  FUP_E = 4 AND /
  FUTC_E != 0 /
/
"""
    assert record2 == expected_record2


def test_create_record2_open_stop_nicv2():
    """Test creating record 2 in the Eclipse ACTIONX keyword for icvc.
    Two ICVs."""
    record2 = TEST_ICV_FUNCTIONS.create_record2_open_stop("A", 1)
    expected_record2 = """  FUP_A = 3 AND /
  FUTO_A != 0 /
/
"""
    assert record2 == expected_record2


def test_create_record2_open_wait_stop():
    """Test creating record 2 in the Eclipse ACTIONX keyword for icvc.
    Two ICVs."""
    record2 = TEST_ICV_FUNCTIONS.create_record2_open_wait_stop("A")
    expected_record2 = """  FUP_A = 2 AND /
  FUTO_A != 0 /
/
"""
    assert record2 == expected_record2


def test_create_record2_choke_nicv2():
    """Test creating record 2 in the Eclipse ACTIONX keyword for icvc.
    Two ICVs."""
    step = 1
    criteria = 1
    record2 = TEST_ICV_FUNCTIONS.create_record2_choke("A", step, criteria)
    expected_record2 = """  FUTSTP < FUH_A AND /
  FUTSTP > FUL_A AND /
  FUTC_A > FUD_A AND /
  FUP_A = 4 /
/
"""
    assert record2 == expected_record2


def test_create_record2_choke_step_gt1_nicv3():
    """Test creating record 2 in the Eclipse ACTIONX keyword for icvc.
    Three ICVs."""
    step = 2
    criteria = 1
    record2 = TEST_ICV_FUNCTIONS.create_record2_choke("E", step, criteria)
    expected_record2 = "  FUP_E = 4 /\n/\n"
    assert record2 == expected_record2


def test_create_record2_open_nicv2_step1():
    """Test creating record 2 in the Eclipse ACTIONX keyword for icvc.
    Two ICVs."""
    step = 1
    criteria = 1
    record2 = TEST_ICV_FUNCTIONS.create_record2_open("A", step, criteria)
    expected_record2 = """  FUTSTP < FUH_A AND /
  FUTSTP > FUL_A AND /
  FUTO_A > FUD_A AND /
  FUP_A = 3 /
/
"""
    assert record2 == expected_record2


def test_create_record2_open_step_gt1_nicv2():
    """Test creating record 2 in the Eclipse ACTIONX keyword for icvc"""
    step = 2
    criteria = 1
    record2 = TEST_ICV_FUNCTIONS.create_record2_open("A", step, criteria)
    expected_record2 = "  FUP_A = 3 /\n/\n"
    assert record2 == expected_record2


@pytest.mark.parametrize(
    "method, step, expected",
    (
        [
            ICVMethod.OPEN,
            1,
            ("UDQ\n  DEFINE FUARE_A (FUARE_A / 0.6) /\n  UPDATE FUARE_A NEXT /\n/\nNEXTSTEP\n  0.1 /\n"),
        ],
        [ICVMethod.OPEN, 2, "WSEGVALV\n  WELL1 105 1.0 FUARE_A 5* 7.712e-03 /\n/\nNEXTSTEP\n  2.0 /\n"],
        [ICVMethod.OPEN_WAIT, 1, "UDQ\n  DEFINE FUTO_A FUTO_A + TIMESTEP /\n/\nNEXTSTEP\n  1.0 /\n"],
        [ICVMethod.OPEN_READY, 1, "UDQ\n  ASSIGN FUP_A 3 /\n/"],
        [
            ICVMethod.OPEN_STOP,
            1,
            "UDQ\n  ASSIGN FUP_A 2 /\n  ASSIGN FUTO_A 0 /\n  ASSIGN FUT_A 0 /\n  UPDATE FUT_A ON /\n/",
        ],
        [ICVMethod.CHOKE, 2, "WSEGVALV\n  WELL1 105 1.0 FUARE_A 5* 7.712e-03 /\n/\nNEXTSTEP\n  2.0 /\n"],
        [
            ICVMethod.CHOKE,
            3,
            ("UDQ\n  DEFINE FUARE_A (FUARE_A * 0.6) /\n  UPDATE FUARE_A NEXT /\n/\nNEXTSTEP\n  0.1 /\n"),
        ],
        [
            ICVMethod.CHOKE,
            1,
            ("UDQ\n  DEFINE FUARE_A (FUARE_A * 0.6) /\n  UPDATE FUARE_A NEXT /\n/\nNEXTSTEP\n  0.1 /\n"),
        ],
        [ICVMethod.CHOKE, 2, "WSEGVALV\n  WELL1 105 1.0 FUARE_A 5* 7.712e-03 /\n/\nNEXTSTEP\n  2.0 /\n"],
        [ICVMethod.CHOKE_READY, 1, "UDQ\n  ASSIGN FUP_A 4 /\n/"],
        [ICVMethod.CHOKE_READY, 1, "UDQ\n  ASSIGN FUP_A 4 /\n/"],
        [ICVMethod.CHOKE_WAIT, 1, "UDQ\n  DEFINE FUTC_A FUTC_A + TIMESTEP /\n/\nNEXTSTEP\n  1.0 /\n"],
        [
            ICVMethod.CHOKE_STOP,
            1,
            "UDQ\n  ASSIGN FUP_A 2 /\n  ASSIGN FUTC_A 0 /\n  ASSIGN FUT_A 0 /\n  UPDATE FUT_A ON /\n/",
        ],
    ),
)
def test_create_actionx(method, step, expected):
    """Test creating an action in the Eclipse ACTIONX keyword for icvc"""
    result = TEST_ICV_FUNCTIONS.create_action(ICV_NAME, method, step)
    assert result == expected


def test_create_choke_wait_nicv2(log_warning):
    """Test creating the wait choke function"""
    trigger_number_times = 100
    trigger_minimum_interval = 10
    actionx_repeater = 2
    criteria = 1
    choke_wait = TEST_ICV_FUNCTIONS.create_choke_wait(
        "A", trigger_number_times, trigger_minimum_interval, actionx_repeater, criteria
    )
    expected_choke_wait = """ACTIONX
  WC1A_001 100 10 /
  FUTC_A <= FUD_A AND /
  FUP_A = 2 AND /
  FUT_A > FUFRQ_A /
/

UDQ
  DEFINE FUTC_A FUTC_A + TIMESTEP /
/
NEXTSTEP
  1.0 /

ACTIONX
  WC1A_002 1 /
  FUTSTP > FUL_A AND /
  FUTC_A <= FUD_A AND /
  FUP_A = 2 AND /
  FUT_A > FUFRQ_A /
/

UDQ
  DEFINE FUTC_A FUTC_A + TIMESTEP /
/
NEXTSTEP
  1.0 /

ENDACTIO
ENDACTIO
"""
    assert choke_wait == expected_choke_wait


def test_create_open_wait(log_warning):
    """Test to create the wait open icv function"""
    actionx_repeater = 2
    criteria = 1
    icv_name = "A"
    open_wait = TEST_ICV_FUNCTIONS.create_open_wait(icv_name, actionx_repeater, criteria)

    expected_open_wait = """ACTIONX
  WO1A_001 10000 10 /
  FUTO_A <= FUD_A AND /
  FUP_A = 2 AND /
  FUT_A > FUFRQ_A /
/

UDQ
  DEFINE FUTO_A FUTO_A + TIMESTEP /
/
NEXTSTEP
  1.0 /

ACTIONX
  WO1A_002 1 /
  FUTSTP > FUL_A AND /
  FUTO_A <= FUD_A AND /
  FUP_A = 2 AND /
  FUT_A > FUFRQ_A /
/

UDQ
  DEFINE FUTO_A FUTO_A + TIMESTEP /
/
NEXTSTEP
  1.0 /

ENDACTIO
ENDACTIO
"""
    assert open_wait == expected_open_wait


def test_create_choke_ready(log_warning):
    """Test to create the ready choke icv function"""
    trigger_number_times = 10000
    trigger_minimum_interval = ""
    criteria = 1

    choke_ready = TEST_ICV_FUNCTIONS.create_choke_ready("A", criteria, trigger_number_times, trigger_minimum_interval)

    expected_choke_ready = """ACTIONX
  READYC1A 10000 /
  FUTC_A > FUD_A AND /
  FUP_A = 2 /
/

UDQ
  ASSIGN FUP_A 4 /
/
ENDACTIO

"""

    assert choke_ready == expected_choke_ready


def test_create_open_ready(log_warning):
    """Test to create the ready open icv function."""
    criteria = 1
    trigger_number_times = 10000
    trigger_minimum_interval = ""

    open_ready = TEST_ICV_FUNCTIONS.create_open_ready(
        ICV_NAME, criteria, trigger_number_times, trigger_minimum_interval
    )

    expected_open_ready = """ACTIONX
  READYO1A 10000 /
  FUTO_A > FUD_A AND /
  FUP_A = 2 /
/

UDQ
  ASSIGN FUP_A 3 /
/
ENDACTIO

"""
    assert open_ready == expected_open_ready


def test_create_choke_stop(log_warning):
    """Test to create the stop choke icv function."""
    trigger_number_times = 10000
    trigger_minimum_interval = ""
    choke_stop = TEST_ICV_FUNCTIONS.create_choke_stop(ICV_NAME, 1, trigger_number_times, trigger_minimum_interval)
    expected_choke_stop = """ACTIONX
  STOPC1A 10000 /
  FUP_A = 4 AND /
  FUTC_A != 0 /
/

UDQ
  ASSIGN FUP_A 2 /
  ASSIGN FUTC_A 0 /
  ASSIGN FUT_A 0 /
  UPDATE FUT_A ON /
/
ENDACTIO

"""

    assert choke_stop == expected_choke_stop


def test_create_open_stop_nicv2(log_warning):
    """Test to create the stop open icv function."""
    trigger_number_times = 10000
    trigger_minimum_interval = ""
    open_stop = TEST_ICV_FUNCTIONS.create_open_stop(ICV_NAME, 1, trigger_number_times, trigger_minimum_interval)
    expected_open_stop = """ACTIONX
  STOPO1A 10000 /
  FUP_A = 3 AND /
  FUTO_A != 0 /
/

UDQ
  ASSIGN FUP_A 2 /
  ASSIGN FUTO_A 0 /
  ASSIGN FUT_A 0 /
  UPDATE FUT_A ON /
/
ENDACTIO\n
"""

    assert open_stop == expected_open_stop


def test_create_open_wait_stop_nicv3(log_warning):
    """Test to create the stop open icv function."""
    trigger_number_times = 10000
    trigger_minimum_interval = ""
    open_stop = TEST_ICV_FUNCTIONS.create_open_stop("E", 1, trigger_number_times, trigger_minimum_interval)
    expected = """ACTIONX
  STOPO1E 10000 /
  FUP_E = 3 AND /
  FUTO_E != 0 /
/

UDQ
  ASSIGN FUP_E 2 /
  ASSIGN FUTO_E 0 /
  ASSIGN FUT_E 0 /
  UPDATE FUT_E ON /
/
ENDACTIO

"""

    assert open_stop == expected


def test_create_choke_nicv2(log_warning):
    """Test to create the choke icv function."""
    trigger_number_times = 1
    trigger_minimum_interval = ""
    criteria = 1
    actionx_repeater = 2

    choke = TEST_ICV_FUNCTIONS.create_choke(
        "A", criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater
    )

    expected_choke = """ACTIONX
  CH1A_001 1 /
  FUTSTP < FUH_A AND /
  FUTSTP > FUL_A AND /
  FUTC_A > FUD_A AND /
  FUP_A = 4 /
/

UDQ
  DEFINE FUPOS_A (FUPOS_A - 1) /
  UPDATE FUPOS_A NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  CH1A_002 1 /
  FUP_A = 4 /
/

WSEGVALV
  WELL1 105 1.0 FUARE_A 5* 7.712e-03 /
/
NEXTSTEP
  2.0 /

ENDACTIO
ENDACTIO
"""

    assert choke == expected_choke


def test_create_choke_opening_table(log_warning):
    """Test to create the choke icv function when an opening table exists."""
    icv_table_a_b = """
ICVTABLE
-- Valve name
A /
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

    case = ICVReadCasefile(CASE_TEXT + icv_table_a_b)
    initials = Initialization(case)
    tests = IcvFunctions(initials)

    trigger_number_times = 1
    trigger_minimum_interval = ""
    criteria = 1
    actionx_repeater = 6

    choke = tests.create_choke("A", criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater)

    expected = """ACTIONX
  CH1A_001 1 /
  FUTSTP < FUH_A AND /
  FUTSTP > FUL_A AND /
  FUTC_A > FUD_A AND /
  FUP_A = 4 /
/

UDQ
  DEFINE FUPOS_A (FUPOS_A - 1) /
  UPDATE FUPOS_A NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  CH1A_002 1 /
  FUP_A = 4 /
/

WSEGVALV
  WELL1 105 1.0 FUARE_A 5* 1.337e-01 /
/
NEXTSTEP
  2.0 /

ACTIONX
  CH1A_003 1 /
  FUTSTP < FUH_A AND /
  FUTSTP > FUL_A AND /
  FUTC_A > FUD_A AND /
  FUP_A = 4 /
/

UDQ
  DEFINE FUPOS_A (FUPOS_A - 1) /
  UPDATE FUPOS_A NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  CH1A_004 1 /
  FUP_A = 4 /
/

WSEGVALV
  WELL1 105 1.0 FUARE_A 5* 1.337e-01 /
/
NEXTSTEP
  2.0 /

ACTIONX
  CH1A_005 1 /
  FUTSTP < FUH_A AND /
  FUTSTP > FUL_A AND /
  FUTC_A > FUD_A AND /
  FUP_A = 4 /
/

UDQ
  DEFINE FUPOS_A (FUPOS_A - 1) /
  UPDATE FUPOS_A NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  CH1A_006 1 /
  FUP_A = 4 /
/

WSEGVALV
  WELL1 105 1.0 FUARE_A 5* 1.337e-01 /
/
NEXTSTEP
  2.0 /

ENDACTIO
ENDACTIO
ENDACTIO
ENDACTIO
ENDACTIO
ENDACTIO
"""

    assert choke == expected


def test_create_choke_icv_nicv3_criteria2(log_warning):
    """Test to create the close icv function."""
    trigger_number_times = 1
    trigger_minimum_interval = ""
    criteria = 2
    actionx_repeater = 2

    choke = TEST_ICV_FUNCTIONS.create_choke(
        "E", criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater
    )

    expected_choke = """ACTIONX
  CH2E_001 1 /
  FUTSTP < FUH_E AND /
  FUTSTP > FUL_E AND /
  FUTC_E > FUD_E AND /
  FUP_E = 4 /
/

UDQ
  DEFINE FUARE_E (FUARE_E * 0.6) /
  UPDATE FUARE_E NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  CH2E_002 1 /
  FUP_E = 4 /
/

WSEGVALV
  WELL2 142 1.0 FUARE_E 5* 0.1337 /
/
NEXTSTEP
  2.0 /

ENDACTIO
ENDACTIO
"""

    assert choke == expected_choke


def test_create_open_nicv2(log_warning):
    """Test to create the open icv function."""
    trigger_number_times = 1
    trigger_minimum_interval = ""
    criteria = 1
    actionx_repeater = 2

    open = TEST_ICV_FUNCTIONS.create_open(
        ICV_NAME, criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater
    )

    expected_open = """ACTIONX
  OP1A_001 1 /
  FUTSTP < FUH_A AND /
  FUTSTP > FUL_A AND /
  FUTO_A > FUD_A AND /
  FUP_A = 3 /
/

UDQ
  DEFINE FUPOS_A (FUPOS_A + 1) /
  UPDATE FUPOS_A NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  OP1A_002 1 /
  FUP_A = 3 /
/

WSEGVALV
  WELL1 105 1.0 FUARE_A 5* 7.712e-03 /
/
NEXTSTEP
  2.0 /

ENDACTIO
ENDACTIO
"""

    assert open == expected_open


def test_create_open_opening_table(log_warning):
    """Test to create the open icv function when a opening table exists."""

    icv_table_a_b = """
ICVTABLE
-- Valve name
A /
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

    case = ICVReadCasefile(CASE_TEXT_OPENING_TABLE + icv_table_a_b)
    initials = Initialization(case)
    tests = IcvFunctions(initials)

    trigger_number_times = 1
    trigger_minimum_interval = ""
    criteria = 1
    actionx_repeater = 4

    choke = tests.create_open("A", criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater)

    expected_open = """ACTIONX
  OP1A_001 1 /
  FUTSTP < FUH_A AND /
  FUTSTP > FUL_A AND /
  FUTO_A > FUD_A AND /
  FUP_A = 3 /
/

UDQ
  DEFINE FUPOS_A (FUPOS_A + 1) /
  UPDATE FUPOS_A NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  OP1A_002 1 /
  FUP_A = 3 /
/

WSEGVALV
  WELL1 105 1.0 FUARE_A 5* 1.337e-01 /
/
NEXTSTEP
  0.2 /

ACTIONX
  OP1A_003 1 /
  FUTSTP < FUH_A AND /
  FUTSTP > FUL_A AND /
  FUTO_A > FUD_A AND /
  FUP_A = 3 /
/

UDQ
  DEFINE FUPOS_A (FUPOS_A + 1) /
  UPDATE FUPOS_A NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  OP1A_004 1 /
  FUP_A = 3 /
/

WSEGVALV
  WELL1 105 1.0 FUARE_A 5* 1.337e-01 /
/
NEXTSTEP
  0.2 /

ENDACTIO
ENDACTIO
ENDACTIO
ENDACTIO
"""

    assert choke == expected_open


def test_create_open_opening_table_custom_cv(log_warning):
    """Test to create the open icv function when a opening table exists."""
    icv_table_a_b = """
ICVTABLE
-- Valve name
A /
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

    case = ICVReadCasefile(CASE_TEXT_OPENING_TABLE + icv_table_a_b)
    initials = Initialization(case)
    tests = IcvFunctions(initials)

    trigger_number_times = 1
    trigger_minimum_interval = ""
    criteria = 1
    actionx_repeater = 4

    choke = tests.create_open("A", criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater)

    expected_open = """ACTIONX
  OP1A_001 1 /
  FUTSTP < FUH_A AND /
  FUTSTP > FUL_A AND /
  FUTO_A > FUD_A AND /
  FUP_A = 3 /
/

UDQ
  DEFINE FUPOS_A (FUPOS_A + 1) /
  UPDATE FUPOS_A NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  OP1A_002 1 /
  FUP_A = 3 /
/

WSEGVALV
  WELL1 105 1.0 FUARE_A 5* 1.337e+00 /
/
NEXTSTEP
  0.2 /

ACTIONX
  OP1A_003 1 /
  FUTSTP < FUH_A AND /
  FUTSTP > FUL_A AND /
  FUTO_A > FUD_A AND /
  FUP_A = 3 /
/

UDQ
  DEFINE FUPOS_A (FUPOS_A + 1) /
  UPDATE FUPOS_A NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  OP1A_004 1 /
  FUP_A = 3 /
/

WSEGVALV
  WELL1 105 1.0 FUARE_A 5* 1.337e+00 /
/
NEXTSTEP
  0.2 /

ENDACTIO
ENDACTIO
ENDACTIO
ENDACTIO
"""

    assert choke == expected_open


def test_create_open_nicv3_criteria1(log_warning):
    """Test to create the open icv function."""
    trigger_number_times = 1
    trigger_minimum_interval = ""
    criteria = 1
    actionx_repeater = 2

    open = TEST_ICV_FUNCTIONS.create_open(
        "E", criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater
    )

    expected_open = """ACTIONX
  OP1E_001 1 /
  FUTSTP < FUH_E AND /
  FUTSTP > FUL_E AND /
  FUTO_E > FUD_E AND /
  FUP_E = 3 /
/

UDQ
  DEFINE FUARE_E (FUARE_E / 0.6) /
  UPDATE FUARE_E NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  OP1E_002 1 /
  FUP_E = 3 /
/

WSEGVALV
  WELL2 142 1.0 FUARE_E 5* 0.1337 /
/
NEXTSTEP
  2.0 /

ENDACTIO
ENDACTIO
"""

    assert open == expected_open


def test_open_wait_stop(log_warning):
    """Test creating the choke-wait-stop function."""
    icv_function = IcvFunctions(Initialization(ICVReadCasefile(CASE_TEXT)))
    open_wait_stop = icv_function.create_open_wait_stop("A", None)
    expected_open_wait_stop = """ACTIONX
  STOPOW_A 10000 10 /
  FUP_A = 2 AND /
  FUTO_A != 0 /
/

UDQ
  ASSIGN FUTO_A 0 /
/
ENDACTIO

"""
    assert open_wait_stop == expected_open_wait_stop


def test_open_wait_stop_crit1(log_warning):
    """Test creating the choke-wait-stop function."""
    icv_function = IcvFunctions(Initialization(ICVReadCasefile(CASE_TEXT)))
    open_wait_stop = icv_function.create_open_wait_stop("A", 1)
    expected_open_wait_stop = """ACTIONX
  STOPOW1A 10000 10 /
  FUP_A = 2 AND /
  FUTO_A != 0 /
/

UDQ
  ASSIGN FUTO_A 0 /
/
ENDACTIO

"""
    assert open_wait_stop == expected_open_wait_stop


def test_choke_wait_stop(log_warning):
    """Test creating the choke-wait-stop function."""
    icv_function = IcvFunctions(Initialization(ICVReadCasefile(CASE_TEXT)))
    choke_wait_stop = icv_function.create_choke_wait_stop("A", 1)
    expected_choke_wait_stop = """ACTIONX
  STOPCW1A 10000 10 /
  FUP_A = 2 AND /
  FUTC_A != 0 /
/

UDQ
  ASSIGN FUTC_A 0 /
/
ENDACTIO

"""
    assert choke_wait_stop == expected_choke_wait_stop


class TestFunctionName:
    case = ICVReadCasefile(CASE_TEXT)
    icv_function = IcvFunctions(Initialization(case))

    def test_insert_function_name_open_by(self, log_warning):
        """Test open function name with ICV with two characters."""
        icv_name = "BY"
        criteria = 1
        trigger_number_times = 1
        trigger_minimum_interval = ""
        actionx_repeater = 1
        expected = """  OP1BY001 1 /"""
        open = self.icv_function.create_open(
            icv_name, criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater
        )
        assert open.splitlines()[1] == expected

    def test_insert_function_name_open_a_crit22(self, log_warning):
        """Test function name with criterium with two characters."""
        icv_name = "A"
        criteria = 22
        trigger_number_times = 1
        trigger_minimum_interval = ""
        actionx_repeater = 1
        expected = """  OP22A001 1 /"""
        open = self.icv_function.create_open(
            icv_name, criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater
        )
        assert open.splitlines()[1] == expected

    def test_insert_function_name_open_by_crit22(self, log_warning):
        """Test function name with criterium and ICV with two characters."""
        icv_name = "BY"
        criteria = 22
        trigger_number_times = 1
        trigger_minimum_interval = ""
        actionx_repeater = 1
        expected = """  O22BY001 1 /"""
        open = self.icv_function.create_open(
            icv_name, criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater
        )
        assert open.splitlines()[1] == expected

    def test_insert_function_name_open_a_step1000(self, log_warning):
        """Test function name with step with four characters."""
        icv_name = "A"
        criteria = 22
        trigger_number_times = 1
        trigger_minimum_interval = ""
        actionx_repeater = 1000
        expected = """  O22A1000 1 /"""
        open = self.icv_function.create_open(
            icv_name, criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater
        )
        assert open.splitlines()[-1010] == expected

    def test_insert_function_name_open_stop_by(self, log_warning):
        """Test open stop function name with ICV with two characters.."""
        icv_name = "BY"
        criteria = 1
        trigger_number_times = 1
        trigger_minimum_interval = ""
        expected = """  STPO1BY 1 /"""
        open = self.icv_function.create_open_stop(icv_name, criteria, trigger_number_times, trigger_minimum_interval)
        assert open.splitlines()[1] == expected

    def test_insert_function_name_open_stop_a_crit22(self, log_warning):
        """Test function name with criterium with two characters."""
        icv_name = "A"
        criteria = 22
        trigger_number_times = 1
        trigger_minimum_interval = ""
        expected = """  STPO22A 1 /"""
        open = self.icv_function.create_open_stop(icv_name, criteria, trigger_number_times, trigger_minimum_interval)
        assert open.splitlines()[1] == expected

    def test_insert_function_name_open_stop_by_crit22(self, log_warning):
        """Test function name with criterium and ICV with two characters."""
        icv_name = "BY"
        criteria = 22
        trigger_number_times = 1
        trigger_minimum_interval = ""
        expected = """  STPO22BY 1 /"""
        open = self.icv_function.create_open_stop(icv_name, criteria, trigger_number_times, trigger_minimum_interval)
        assert open.splitlines()[1] == expected

    def test_insert_function_name_open_wait_by(self, log_warning):
        """Test open wait function name with ICV with two characters."""
        icv_name = "BY"
        actionx_repeater = 1
        criteria = 1
        expected = """  WO1BY001 10000 10 /"""
        open = self.icv_function.create_open_wait(icv_name, actionx_repeater, criteria)
        assert open.splitlines()[1] == expected

    def test_insert_function_name_open_wait_a_crit22(self, log_warning):
        """Test function name with criterium with two characters."""
        icv_name = "A"
        actionx_repeater = 1
        criteria = 22
        expected = """  WO22A001 10000 10 /"""
        open = self.icv_function.create_open_wait(icv_name, actionx_repeater, criteria)
        assert open.splitlines()[1] == expected

    def test_insert_function_name_open_wait_by_crit22(self, log_warning):
        """Test function name with criterium and ICV with two characters."""
        icv_name = "BY"
        actionx_repeater = 1
        criteria = 22
        expected = """  H22BY001 10000 10 /"""
        open = self.icv_function.create_open_wait(icv_name, actionx_repeater, criteria)
        assert open.splitlines()[1] == expected

    def test_insert_function_name_open_wait_a_step1000(self, log_warning):
        """Test function name with step with four characters."""
        icv_name = "A"
        actionx_repeater = 1000
        criteria = 22
        expected = """  H22A1000 1 /"""
        open = self.icv_function.create_open_wait(icv_name, actionx_repeater, criteria)
        assert open.splitlines()[-1013] == expected

    def test_insert_function_name_open_wait_stop_by(self, log_warning):
        """Test to function name with ICV with to letters."""
        icv_name = "BY"
        criteria = 1
        expected = """  STPOW1BY 10000 10 /"""
        open = self.icv_function.create_open_wait_stop(icv_name, criteria)
        assert open.splitlines()[1] == expected

    def test_insert_function_name_open_wait_stop_a_crit22(self, log_warning):
        """Test function name with criterium with two characters."""
        icv_name = "A"
        criteria = 22
        expected = """  STPOW22A 10000 10 /"""
        open = self.icv_function.create_open_wait_stop(icv_name, criteria)
        assert open.splitlines()[1] == expected

    def test_insert_function_name_open_wait_stop_by_crit22(self, log_warning):
        """Test function name with criterium and ICV with two characters."""
        icv_name = "BY"
        criteria = 22
        expected = """  SPOW22BY 10000 10 /"""
        open = self.icv_function.create_open_wait_stop(icv_name, criteria)
        assert open.splitlines()[1] == expected

    def test_insert_function_name_choke_by(self, log_warning):
        """Test choke function name with ICV with two characters."""
        icv_name = "BY"
        criteria = 1
        trigger_number_times = 1
        trigger_minimum_interval = ""
        actionx_repeater = 1
        expected = """  C1BY001 1 /"""
        choke = self.icv_function.create_choke(
            icv_name, criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater
        )
        assert choke.splitlines()[1] == expected

    def test_insert_function_name_choke_a_crit22(self, log_warning):
        """Test function name with criterium with two characters."""
        icv_name = "A"
        criteria = 22
        trigger_number_times = 1
        trigger_minimum_interval = ""
        actionx_repeater = 1
        expected = """  C22A001 1 /"""
        choke = self.icv_function.create_choke(
            icv_name, criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater
        )
        assert choke.splitlines()[1] == expected

    def test_insert_function_name_choke_by_crit22(self, log_warning):
        """Test function name with criterium and ICV with two characters."""
        icv_name = "BY"
        criteria = 22
        trigger_number_times = 1
        trigger_minimum_interval = ""
        actionx_repeater = 1
        expected = """  C22BY001 1 /"""
        choke = self.icv_function.create_choke(
            icv_name, criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater
        )
        assert choke.splitlines()[1] == expected

    def test_insert_function_name_choke_a_step1000(self, log_warning):
        """Test function name with step with four characters."""
        icv_name = "A"
        criteria = 22
        trigger_number_times = 1
        trigger_minimum_interval = ""
        actionx_repeater = 1000
        expected = """  C22A1000 1 /"""
        choke = self.icv_function.create_choke(
            icv_name, criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater
        )
        assert choke.splitlines()[-1010] == expected

    def test_insert_function_name_choke_wait_by(self, log_warning):
        """Test choke wait function name with ICV with two characters."""
        icv_name = "BY"
        actionx_repeater = 1
        criteria = 1
        expected = """  WC1BY001 1 1 /"""
        choke = self.icv_function.create_choke_wait(icv_name, actionx_repeater, criteria)
        assert choke.splitlines()[1] == expected

    def test_insert_function_name_choke_wait_A1(self, log_warning):
        """Test choke wait function name with ICV with two characters."""
        icv_name = "A1"
        actionx_repeater = 1
        criteria = 1
        expected = """  WC1A1001 1 1 /"""
        choke = self.icv_function.create_choke_wait(icv_name, actionx_repeater, criteria)
        assert choke.splitlines()[1] == expected

    def test_insert_function_name_choke_wait_a_crit22(self, log_warning):
        """Test function name with criterium with two characters."""
        icv_name = "A"
        trigger_number_times = 100
        trigger_minimum_interval = 10
        actionx_repeater = 1
        criteria = 22
        expected = """  WC22A001 100 10 /"""
        choke = self.icv_function.create_choke_wait(
            icv_name, trigger_number_times, trigger_minimum_interval, actionx_repeater, criteria
        )
        assert choke.splitlines()[1] == expected

    def test_insert_function_name_choke_wait_by_crit22(self, log_warning):
        """Test function name with criterium and ICV with two characters."""
        icv_name = "BY"
        trigger_number_times = 13
        trigger_minimum_interval = 37
        actionx_repeater = 1
        criteria = 22
        expected = """  W22BY001 13 37 /"""
        choke = self.icv_function.create_choke_wait(
            icv_name, trigger_number_times, trigger_minimum_interval, actionx_repeater, criteria
        )
        assert choke.splitlines()[1] == expected

    def test_insert_function_name_choke_wait_a_step1000(self, log_warning):
        """Test function name with step with four characters."""
        icv_name = "A"
        trigger_number_times = 13
        trigger_minimum_interval = 37
        actionx_repeater = 1000
        criteria = 22
        expected = """  W22A1000 1 /"""
        choke = self.icv_function.create_choke_wait(
            icv_name, trigger_number_times, trigger_minimum_interval, actionx_repeater, criteria
        )
        assert choke.splitlines()[-1013] == expected

    def test_insert_function_name_choke_wait_stop_by(self, log_warning):
        """Test choke wait stop function name with ICV with two characters."""
        icv_name = "BY"
        criteria = 1
        expected = """  STPCW1BY 10000 10 /"""
        choke = self.icv_function.create_choke_wait_stop(icv_name, criteria)
        assert choke.splitlines()[1] == expected

    def test_insert_function_name_choke_wait_stop_a_crit22(self, log_warning):
        """Test function name with criterium with two characters."""
        icv_name = "A"
        criteria = 22
        expected = """  STPCW22A 10000 10 /"""
        choke = self.icv_function.create_choke_wait_stop(icv_name, criteria)
        assert choke.splitlines()[1] == expected

    def test_insert_function_name_choke_wait_stop_by_crit22(self, log_warning):
        """Test function name with criterium and ICV with two characters."""
        icv_name = "BY"
        criteria = 22
        expected = """  SPCW22BY 10000 10 /"""
        choke = self.icv_function.create_choke_wait_stop(icv_name, criteria)
        assert choke.splitlines()[1] == expected

    def test_insert_function_name_choke_stop_by(self, log_warning):
        """Test choke stop function name with ICV with two characters."""
        icv_name = "BY"
        criteria = 1
        trigger_number_times = 1
        trigger_minimum_interval = ""
        expected = """  STPC1BY 1 /"""
        choke = self.icv_function.create_choke_stop(icv_name, criteria, trigger_number_times, trigger_minimum_interval)
        assert choke.splitlines()[1] == expected

    def test_insert_function_name_choke_stop_a_crit22(self, log_warning):
        """Test function name with criterium with two characters."""
        icv_name = "A"
        criteria = 22
        trigger_number_times = 1
        trigger_minimum_interval = ""
        expected = """  STPC22A 1 /"""
        choke = self.icv_function.create_choke_stop(icv_name, criteria, trigger_number_times, trigger_minimum_interval)
        assert choke.splitlines()[1] == expected

    def test_insert_function_name_choke_stop_by_crit22(self, log_warning):
        """Test function name with criterium and ICV with two characters."""
        icv_name = "BY"
        criteria = 22
        trigger_number_times = 1
        trigger_minimum_interval = ""
        expected = """  STPC22BY 1 /"""
        choke = self.icv_function.create_choke_stop(icv_name, criteria, trigger_number_times, trigger_minimum_interval)
        assert choke.splitlines()[1] == expected


class TestCustomCondition:
    case = ICVReadCasefile(CASE_TEXT)
    icv_function = IcvFunctions(Initialization(case))

    def test_insert_custom_conditions_open_wait_a(self, log_warning):
        """Test to insert custom conditions in open icv function."""
        actionx_repeater = 2

        self.icv_function.initials.custom_conditions = {
            ICVMethod.OPEN_WAIT: {
                "A": {
                    "1": """AD WELL(x0) > AP WELL(x0) AND /
FURAT_x0 > FURAT_x1 AND /
SFOPN WELL(x0) SEG(x1) > 0.96 /""",
                    "map": {"1": {"x0": "A", "x1": "B"}},
                }
            }
        }

        expected = """ACTIONX
  WO1A_001 10000 10 /
  FUTO_A <= FUD_A AND /
  FUP_A = 2 AND /
  FUT_A > FUFRQ_A AND /
  AD 'WELL1' > AP 'WELL1' AND /
  FURAT_A > FURAT_B AND /
  SFOPN 'WELL1' 106 > 0.96 /
/

UDQ
  DEFINE FUTO_A FUTO_A + TIMESTEP /
/
NEXTSTEP
  1.0 /

ACTIONX
  WO1A_002 1 /
  FUTSTP > FUL_A AND /
  FUTO_A <= FUD_A AND /
  FUP_A = 2 AND /
  FUT_A > FUFRQ_A AND /
  AD 'WELL1' > AP 'WELL1' AND /
  FURAT_A > FURAT_B AND /
  SFOPN 'WELL1' 106 > 0.96 /
/

UDQ
  DEFINE FUTO_A FUTO_A + TIMESTEP /
/
NEXTSTEP
  1.0 /

ENDACTIO
ENDACTIO
"""
        open = self.icv_function.create_open_wait("A", actionx_repeater, 1)

        assert open == expected

    def test_insert_custom_conditions_open_wait_a_rep4(self, log_warning):
        """Test to insert custom conditions in open icv function."""
        actionx_repeater = 4
        self.icv_function.initials.custom_conditions = {
            ICVMethod.OPEN_WAIT: {
                "A": {
                    "1": """ADC WELL(x0) > APC WELL(x0) AND /
FURAT_x0 > FURAT_x1 AND /
SFOPN WELL(x0) SEG(x1) > 0.96 /""",
                    "map": {"1": {"x0": "A", "x1": "B"}},
                }
            }
        }

        expected = """ACTIONX
  WO1A_001 10000 10 /
  FUTO_A <= FUD_A AND /
  FUP_A = 2 AND /
  FUT_A > FUFRQ_A AND /
  ADC 'WELL1' > APC 'WELL1' AND /
  FURAT_A > FURAT_B AND /
  SFOPN 'WELL1' 106 > 0.96 /
/

UDQ
  DEFINE FUTO_A FUTO_A + TIMESTEP /
/
NEXTSTEP
  1.0 /

ACTIONX
  WO1A_002 1 /
  FUTSTP > FUL_A AND /
  FUTO_A <= FUD_A AND /
  FUP_A = 2 AND /
  FUT_A > FUFRQ_A AND /
  ADC 'WELL1' > APC 'WELL1' AND /
  FURAT_A > FURAT_B AND /
  SFOPN 'WELL1' 106 > 0.96 /
/

UDQ
  DEFINE FUTO_A FUTO_A + TIMESTEP /
/
NEXTSTEP
  1.0 /

ACTIONX
  WO1A_003 1 /
  FUTSTP > FUL_A AND /
  FUTO_A <= FUD_A AND /
  FUP_A = 2 AND /
  FUT_A > FUFRQ_A AND /
  ADC 'WELL1' > APC 'WELL1' AND /
  FURAT_A > FURAT_B AND /
  SFOPN 'WELL1' 106 > 0.96 /
/

UDQ
  DEFINE FUTO_A FUTO_A + TIMESTEP /
/
NEXTSTEP
  1.0 /

ACTIONX
  WO1A_004 1 /
  FUTSTP > FUL_A AND /
  FUTO_A <= FUD_A AND /
  FUP_A = 2 AND /
  FUT_A > FUFRQ_A AND /
  ADC 'WELL1' > APC 'WELL1' AND /
  FURAT_A > FURAT_B AND /
  SFOPN 'WELL1' 106 > 0.96 /
/

UDQ
  DEFINE FUTO_A FUTO_A + TIMESTEP /
/
NEXTSTEP
  1.0 /

ENDACTIO
ENDACTIO
ENDACTIO
ENDACTIO
"""
        open = self.icv_function.create_open_wait("A", actionx_repeater, 1)

        assert open == expected

    def test_insert_custom_conditions_open_wait_e(self, log_warning):
        """Test to insert custom conditions in open icv function."""
        actionx_repeater = 2

        self.icv_function.initials.custom_conditions = {
            ICVMethod.OPEN_WAIT: {
                "A": {
                    "1": """HEI WELL(x0) > HADE WELL(x1) AND /
FURAT_x0 very larger than FURAT_z AND /
SFOPN WELL(x0) SEG(z) > 0.42 /"""
                },
                "E": {
                    "1": """HEI WELL(x0) > HADE WELL(x1) AND /
FURAT_x0 very larger than FURAT_x2 AND /
SFOPN WELL(x0) SEG(x2) > 0.42 WELL(x1)/""",
                    "map": {"1": {"x0": "E", "x1": "F", "x2": "G"}},
                },
            }
        }

        expected = """ACTIONX
  WO1E_001 10000 10 /
  FUTO_E <= FUD_E AND /
  FUP_E = 2 AND /
  FUT_E > FUFRQ_E AND /
  HEI 'WELL2' > HADE 'WELL2' AND /
  FURAT_E very larger than FURAT_G AND /
  SFOPN 'WELL2' 144 > 0.42 'WELL2' /
/

UDQ
  DEFINE FUTO_E FUTO_E + TIMESTEP /
/
NEXTSTEP
  1.0 /

ACTIONX
  WO1E_002 1 /
  FUTSTP > FUL_E AND /
  FUTO_E <= FUD_E AND /
  FUP_E = 2 AND /
  FUT_E > FUFRQ_E AND /
  HEI 'WELL2' > HADE 'WELL2' AND /
  FURAT_E very larger than FURAT_G AND /
  SFOPN 'WELL2' 144 > 0.42 'WELL2' /
/

UDQ
  DEFINE FUTO_E FUTO_E + TIMESTEP /
/
NEXTSTEP
  1.0 /

ENDACTIO
ENDACTIO
"""
        open = self.icv_function.create_open_wait("E", actionx_repeater)
        assert open == expected

    def test_insert_custom_conditions_open_b(self, log_warning):
        """Test to insert custom conditions in open icv function."""
        trigger_number_times = 1
        trigger_minimum_interval = ""
        criteria = 1
        actionx_repeater = 4

        self.icv_function.initials.custom_conditions = {
            ICVMethod.OPEN: {
                "A": {
                    "1": """WWIR WELL(x0) > WUMXVDJ2 WELL(x1) AND /
FURMAX_x0 < FURAT_x1 AND /
SFOPN WELL(x1) SEG(x0) < 0.99 /"""
                },
                "B": {
                    "1": """WWIR WELL(x0) > WUMXVDJ2 WELL(x1) AND /
FURMAX_x0 < FURAT_x1 AND /
SFOPN WELL(x1) SEG(x0) < 0.99 /""",
                    "map": {"1": {"x0": "B", "x1": "A"}},
                },
            }
        }

        expected = """ACTIONX
  OP1B_001 1 /
  FUTSTP < FUH_B AND /
  FUTSTP > FUL_B AND /
  FUTO_B > FUD_B AND /
  FUP_B = 3 AND /
  WWIR 'WELL1' > WUMXVDJ2 'WELL1' AND /
  FURMAX_B < FURAT_A AND /
  SFOPN 'WELL1' 106 < 0.99 /
/

UDQ
  DEFINE FUPOS_B (FUPOS_B + 1) /
  UPDATE FUPOS_B NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  OP1B_002 1 /
  FUP_B = 3 /
/

WSEGVALV
  WELL1 106 1.0 FUARE_B 5* 7.712e-03 /
/
NEXTSTEP
  2.0 /

ACTIONX
  OP1B_003 1 /
  FUTSTP < FUH_B AND /
  FUTSTP > FUL_B AND /
  FUTO_B > FUD_B AND /
  FUP_B = 3 AND /
  WWIR 'WELL1' > WUMXVDJ2 'WELL1' AND /
  FURMAX_B < FURAT_A AND /
  SFOPN 'WELL1' 106 < 0.99 /
/

UDQ
  DEFINE FUPOS_B (FUPOS_B + 1) /
  UPDATE FUPOS_B NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  OP1B_004 1 /
  FUP_B = 3 /
/

WSEGVALV
  WELL1 106 1.0 FUARE_B 5* 7.712e-03 /
/
NEXTSTEP
  2.0 /

ENDACTIO
ENDACTIO
ENDACTIO
ENDACTIO
"""

        open = self.icv_function.create_open(
            "B", criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater
        )

        assert open == expected

    def test_insert_custom_conditions_open_e(self, log_warning):
        """Test to insert custom conditions in open icv function."""
        trigger_number_times = 1
        trigger_minimum_interval = ""
        criteria = 1
        actionx_repeater = 4

        self.icv_function.initials.custom_conditions = {
            ICVMethod.OPEN: {
                "E": {
                    "1": """WWIR WELL(x0) > WUMXVDJ2 WELL(x1) AND /
FURMAX_x0 < FURAT_x1 AND /
SFOPN WELL(x1) SEG(x0) < 0.99 /""",
                    "map": {"1": {"x0": "E", "x1": "F"}},
                }
            }
        }

        expected = """ACTIONX
  OP1E_001 1 /
  FUTSTP < FUH_E AND /
  FUTSTP > FUL_E AND /
  FUTO_E > FUD_E AND /
  FUP_E = 3 AND /
  WWIR 'WELL2' > WUMXVDJ2 'WELL2' AND /
  FURMAX_E < FURAT_F AND /
  SFOPN 'WELL2' 142 < 0.99 /
/

UDQ
  DEFINE FUARE_E (FUARE_E / 0.6) /
  UPDATE FUARE_E NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  OP1E_002 1 /
  FUP_E = 3 /
/

WSEGVALV
  WELL2 142 1.0 FUARE_E 5* 0.1337 /
/
NEXTSTEP
  2.0 /

ACTIONX
  OP1E_003 1 /
  FUTSTP < FUH_E AND /
  FUTSTP > FUL_E AND /
  FUTO_E > FUD_E AND /
  FUP_E = 3 AND /
  WWIR 'WELL2' > WUMXVDJ2 'WELL2' AND /
  FURMAX_E < FURAT_F AND /
  SFOPN 'WELL2' 142 < 0.99 /
/

UDQ
  DEFINE FUARE_E (FUARE_E / 0.6) /
  UPDATE FUARE_E NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  OP1E_004 1 /
  FUP_E = 3 /
/

WSEGVALV
  WELL2 142 1.0 FUARE_E 5* 0.1337 /
/
NEXTSTEP
  2.0 /

ENDACTIO
ENDACTIO
ENDACTIO
ENDACTIO
"""

        open = self.icv_function.create_open(
            "E", criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater
        )

        assert open == expected

    def test_insert_custom_open_step_gt1_nicv3_criteria1(self, log_warning):
        """Test creating record 2 in the Eclipse ACTIONX keyword for icvc."""
        step = 2
        criteria = 1
        self.icv_function.initials.custom_conditions = {
            ICVMethod.OPEN: {
                "E": {
                    "1": """WWIR WELL(x0) > WUMXVDJ2 WELL(x0) AND /
FURAT_x1 < FURAT_x2 AND /
FURAT_x3 > FURMAX_x3 AND /
SFOPN WELL(x0) SEG(x0) < 0.99 /"""
                }
            }
        }

        open = TEST_ICV_FUNCTIONS.create_record2_open("E", step, criteria)
        expected = "  FUP_E = 3 /\n/\n"
        assert open == expected

    def test_insert_custom_conditions_open_stop_a(self, log_warning):
        """Test to insert custom conditions in open icv function."""
        self.icv_function.initials.custom_conditions = {
            ICVMethod.OPEN_STOP: {"A": {"1": """FURMAX_x0 < FURAT_x0  /""", "map": {"1": {"x0": "A"}}}}
        }

        expected = """  FUP_A = 3 AND /
  FUTO_A != 0 AND /
  FURMAX_A < FURAT_A /
/
"""
        open = self.icv_function.create_record2_open_stop("A", 1)
        assert open == expected

    def test_insert_custom_conditions_open_stop_e(self, log_warning):
        """Test to insert custom conditions in open icv function."""

        self.icv_function.initials.custom_conditions = {
            ICVMethod.OPEN_STOP: {
                "E": {
                    "1": """FURMAX_x0 > FURAT_x1 /
|i| == |1) /
|-i| = 1 /""",
                    "map": {"1": {"x0": "E", "x1": "F"}},
                }
            }
        }

        expected = """  FUP_E = 3 AND /
  FUTO_E != 0 AND /
  FURMAX_E > FURAT_F /
  |i| == |1) /
  |-i| = 1 /
/
"""
        open = self.icv_function.create_record2_open_stop("E", 1)
        assert open == expected

    def test_insert_custom_conditions_open_stop_criteria1_record2(self, log_warning):
        """Test to insert custom conditions in open icv function."""

        self.icv_function.initials.custom_conditions = {
            ICVMethod.OPEN_STOP: {
                "E": {
                    "1": """FURMAX_x0 > FURAT_x1 /
                                sin(pi) = -0""",
                    "map": {"1": {"x0": "E", "x1": "F"}},
                }
            }
        }

        expected = """  FUP_E = 3 AND /
  FUTO_E != 0 AND /
  FURMAX_E > FURAT_F /
  sin(pi) = -0 /
/
"""
        open = self.icv_function.create_record2_open_stop("E", 1)
        assert open == expected

    def test_insert_custom_conditions_open_wait_stop(self, log_warning):
        """Test to insert custom conditions in open-wait-stop icv function."""

        self.icv_function.initials.custom_conditions = {
            ICVMethod.OPEN_WAIT_STOP: {
                "E": {
                    "1": """FUR_x0 > FUR_x1 AND /
                        pi == 3""",
                    "map": {"1": {"x0": "E", "x1": "F"}},
                }
            }
        }

        expected_open_wait_stop = """  FUP_E = 2 AND /
  FUTO_E != 0 AND /
  FUR_E > FUR_F AND /
  pi == 3 /
/
"""
        open_wait_stop = self.icv_function.create_record2_open_wait_stop("E")
        assert open_wait_stop == expected_open_wait_stop

    def test_insert_custom_conditions_choke_wait_stop(self, log_warning):
        """Test to insert custom conditions in choke-wait-stop icv function."""

        self.icv_function.initials.custom_conditions = {
            ICVMethod.CHOKE_WAIT_STOP: {
                "E": {
                    "1": """FURMAX_x0 > FURAT_x1 AND /
                                pi != 3""",
                    "map": {"1": {"x0": "E", "x1": "F"}},
                }
            }
        }

        expected_choke_wait_stop = """ACTIONX
  STOPCW1E 10000 10 /
  FUP_E = 2 AND /
  FUTC_E != 0 AND /
  FURMAX_E > FURAT_F AND /
  pi != 3 /
/

UDQ
  ASSIGN FUTC_E 0 /
/
ENDACTIO

"""
        choke_wait_stop = self.icv_function.create_choke_wait_stop("E", 1)
        assert choke_wait_stop == expected_choke_wait_stop

    def test_insert_custom_conditions_open_wait_stop_criteria(self, log_warning):
        """Test to insert custom conditions in choke-wait-stop icv function."""

        self.icv_function.initials.custom_conditions = {
            ICVMethod.OPEN_WAIT_STOP: {
                "E": {
                    "1": """FURMAX_x0 > FURAT_x1 AND /
                                pi != 3""",
                    "map": {"1": {"x0": "E", "x1": "F"}},
                }
            }
        }

        expected_open_wait_stop = """ACTIONX
  STOPOW1E 10000 10 /
  FUP_E = 2 AND /
  FUTO_E != 0 AND /
  FURMAX_E > FURAT_F AND /
  pi != 3 /
/

UDQ
  ASSIGN FUTO_E 0 /
/
ENDACTIO

"""
        open_wait_stop = self.icv_function.create_open_wait_stop("E", 1)
        assert open_wait_stop == expected_open_wait_stop

    def test_insert_custom_conditions_open_ready_nicv2(self, log_warning):
        """Test to create the ready open icv function."""
        criteria = 1
        trigger_number_times = 10000
        trigger_minimum_interval = ""

        self.icv_function.initials.custom_conditions = {
            ICVMethod.OPEN_READY: {
                "A": {
                    "1": """WWIR WELL1 > WUMXNG3W WELL1 AND /
Left_B > Right_B AND /
SFOPN WELL1 105 < 0.99 /
""",
                    "map": {"1": {"x0": "A"}},
                }
            }
        }

        open_ready = self.icv_function.create_open_ready("A", criteria, trigger_number_times, trigger_minimum_interval)

        expected_open_ready = """ACTIONX
  READYO1A 10000 /
  FUTO_A > FUD_A AND /
  FUP_A = 2 AND /
  WWIR WELL1 > WUMXNG3W WELL1 AND /
  Left_B > Right_B AND /
  SFOPN WELL1 105 < 0.99 /
/

UDQ
  ASSIGN FUP_A 3 /
/
ENDACTIO

"""
        assert open_ready == expected_open_ready

    def test_insert_custom_conditions_open_ready_nicv3_criteria1(self, log_warning):
        """Test to create the ready open icv function."""
        criteria = 1
        trigger_number_times = 10000
        trigger_minimum_interval = ""

        self.icv_function.initials.custom_conditions = {
            ICVMethod.OPEN_READY: {
                "E": {
                    "1": """WWIR WELL1 > WUMXNG3W WELL1 AND /
    Left_x1 > Right_x1 AND /
  SFOPN WELL1 105 < 0.99 /
    """,
                    "map": {"1": {"x0": "E", "x1": "F"}},
                }
            }
        }

        open_ready = self.icv_function.create_open_ready("E", criteria, trigger_number_times, trigger_minimum_interval)

        expected_open_ready = """ACTIONX
  READYO1E 10000 /
  FUTO_E > FUD_E AND /
  FUP_E = 2 AND /
  WWIR WELL1 > WUMXNG3W WELL1 AND /
  Left_F > Right_F AND /
  SFOPN WELL1 105 < 0.99 /
/

UDQ
  ASSIGN FUP_E 3 /
/
ENDACTIO

"""
        assert open_ready == expected_open_ready

    def test_insert_custom_conditions_open_ready_nicv3_criteria13(self, log_warning):
        """Test to create the ready open icv function."""
        criteria = 13
        trigger_number_times = 10000
        trigger_minimum_interval = ""

        self.icv_function.initials.custom_conditions = {
            ICVMethod.OPEN_READY: {
                "E": {
                    "13": """WWIR WELL1 > WUMXNG3W WELL1 AND /
    Left_x1 > Right_x1 AND /
  SFOPN WELL1 105 < 0.99 /
    """,
                    "map": {"13": {"x0": "E", "x1": "F"}},
                }
            }
        }

        open_ready = self.icv_function.create_open_ready("E", criteria, trigger_number_times, trigger_minimum_interval)

        expected_open_ready = """ACTIONX
  REDYO13E 10000 /
  FUTO_E > FUD_E AND /
  FUP_E = 2 AND /
  WWIR WELL1 > WUMXNG3W WELL1 AND /
  Left_F > Right_F AND /
  SFOPN WELL1 105 < 0.99 /
/

UDQ
  ASSIGN FUP_E 3 /
/
ENDACTIO

"""
        assert open_ready == expected_open_ready

    def test_insert_custom_conditions_open_rdy_nicv3_crit9_ICV_EE(self, log_warning):
        """Test to create the ready open icv function."""
        criteria = 9
        trigger_number_times = 10000
        trigger_minimum_interval = ""

        self.icv_function.initials.custom_conditions = {
            ICVMethod.OPEN_READY: {
                "BY": {
                    "9": """TEST_x0 < TEST_x1  /
        """,
                    "map": {"1": {"x0": "BY", "x1": "BX"}},
                }
            }
        }

        open_ready = self.icv_function.create_open_ready("BY", criteria, trigger_number_times, trigger_minimum_interval)

        expected_open_ready = """ACTIONX
  REDYO9BY 10000 /
  FUTO_BY > FUD_BY AND /
  FUP_BY = 2 AND /
  TEST_BY < TEST_BX /
/

UDQ
  ASSIGN FUP_BY 3 /
/
ENDACTIO

"""
        assert open_ready == expected_open_ready

    def test_insert_custom_conditions_open_rdy_nicv3_crit13_ICV_EE(self, log_warning):
        """Test to create the ready open icv function."""
        criteria = 13
        trigger_number_times = 10000
        trigger_minimum_interval = ""

        self.icv_function.initials.custom_conditions = {
            ICVMethod.OPEN_READY: {
                "BY": {
                    "13": """WWIR WELL1 > WUMXNG3W WELL1 /
        """,
                    "map": {"1": {"x0": "BY"}},
                }
            }
        }

        open_ready = self.icv_function.create_open_ready("BY", criteria, trigger_number_times, trigger_minimum_interval)

        expected_open_ready = """ACTIONX
  RDYO13BY 10000 /
  FUTO_BY > FUD_BY AND /
  FUP_BY = 2 AND /
  WWIR WELL1 > WUMXNG3W WELL1 /
/

UDQ
  ASSIGN FUP_BY 3 /
/
ENDACTIO

"""
        assert open_ready == expected_open_ready

    def test_insert_custom_conditions_record2_choke_nicv2(self, log_warning):
        """Test creating record 2 in the Eclipse ACTIONX keyword for icvc.
        Two ICVs."""
        step = 1
        criteria = 1
        self.icv_function.initials.custom_conditions = {
            ICVMethod.CHOKE: {"A": {"2": """ SHOULD NOT BE WRITTEN, Default output!!!""", "map": {"2": {"x0": "A"}}}}
        }

        record2 = self.icv_function.create_record2_choke("A", step, criteria)
        expected_record2 = """  FUTSTP < FUH_A AND /
  FUTSTP > FUL_A AND /
  FUTC_A > FUD_A AND /
  FUP_A = 4 /
/
"""
        assert record2 == expected_record2

    def test_insert_custom_conditions_record2_choke_nicv3_c1337(self, log_warning):
        """Test creating record 2 in the Eclipse ACTIONX keyword for icvc.
        Two ICVs."""
        step = 1
        criteria = 1337
        self.icv_function.initials.custom_conditions = {
            ICVMethod.CHOKE: {
                "E": {
                    "1337": """  WWIR WELL(x0) > WUMXNG3W WELL(x0) AND /
FURAT_x0 > FURMAX_x0 AND /
SFOPN WELL(x0) 321 > 0.01 /
""",
                    "map": {"1": {"x0": "E"}},
                }
            }
        }

        record2 = self.icv_function.create_record2_choke("E", step, criteria)
        expected_record2 = """  FUTSTP < FUH_E AND /
  FUTSTP > FUL_E AND /
  FUTC_E > FUD_E AND /
  FUP_E = 4 AND /
  WWIR 'WELL2' > WUMXNG3W 'WELL2' AND /
  FURAT_E > FURMAX_E AND /
  SFOPN 'WELL2' 321 > 0.01 /
/
"""
        assert record2 == expected_record2

    def test_insert_custom_conditions_choke_wait_nicv2(self, log_warning):
        """Test creating the wait choke function"""
        trigger_number_times = 100
        trigger_minimum_interval = 10
        actionx_repeater = 2
        criteria = 1
        self.icv_function.initials.custom_conditions = {
            ICVMethod.CHOKE_WAIT: {
                "A": {
                    "1": """    WWIR WELL(x0) > WUMXNG3W WELL(x0) AND
  FURAT_x0 > FURMAX_x0 AND
  SFOPN WELL(x0) SEG(x1) > 0.99 AND
  SFOPN 'WELL1' SEG(x0) > 0.01
  1337 x2
""",
                    "map": {"1": {"x0": "A", "x1": "B"}},
                }
            }
        }
        choke_wait = self.icv_function.create_choke_wait(
            "A", trigger_number_times, trigger_minimum_interval, actionx_repeater, criteria
        )
        expected_choke_wait = """ACTIONX
  WC1A_001 100 10 /
  FUTC_A <= FUD_A AND /
  FUP_A = 2 AND /
  FUT_A > FUFRQ_A AND /
  WWIR 'WELL1' > WUMXNG3W 'WELL1' AND /
  FURAT_A > FURMAX_A AND /
  SFOPN 'WELL1' 106 > 0.99 AND /
  SFOPN 'WELL1' 105 > 0.01 /
  1337 x2 /
/

UDQ
  DEFINE FUTC_A FUTC_A + TIMESTEP /
/
NEXTSTEP
  1.0 /

ACTIONX
  WC1A_002 1 /
  FUTSTP > FUL_A AND /
  FUTC_A <= FUD_A AND /
  FUP_A = 2 AND /
  FUT_A > FUFRQ_A AND /
  WWIR 'WELL1' > WUMXNG3W 'WELL1' AND /
  FURAT_A > FURMAX_A AND /
  SFOPN 'WELL1' 106 > 0.99 AND /
  SFOPN 'WELL1' 105 > 0.01 /
  1337 x2 /
/

UDQ
  DEFINE FUTC_A FUTC_A + TIMESTEP /
/
NEXTSTEP
  1.0 /

ENDACTIO
ENDACTIO
"""
        assert choke_wait == expected_choke_wait

    def test_insert_custom_conditions_choke_wait_nicv3_empty(self, log_warning):
        """Test creating the wait choke function, note criteria does not match"""
        trigger_number_times = 100
        trigger_minimum_interval = 10
        actionx_repeater = 1
        criteria = 1
        self.icv_function.initials.custom_conditions = {
            ICVMethod.CHOKE_WAIT: {"E": {"3": "DONT WRITE ME", "map": {"1": {"x0": "E"}}}}
        }
        choke_wait = self.icv_function.create_choke_wait(
            "E", trigger_number_times, trigger_minimum_interval, actionx_repeater, criteria
        )
        expected_choke_wait = """ACTIONX
  WC1E_001 100 10 /
  FUTC_E <= FUD_E AND /
  FUP_E = 2 AND /
  FUT_E > FUFRQ_E /
/

UDQ
  DEFINE FUTC_E FUTC_E + TIMESTEP /
/
NEXTSTEP
  1.0 /

ENDACTIO
"""
        assert choke_wait == expected_choke_wait

    def test_error_empty_custom_content(self, log_warning):
        """Test creating the wait choke function"""
        trigger_number_times = 100
        trigger_minimum_interval = 10
        actionx_repeater = 1
        criteria = 2
        self.icv_function.initials.custom_conditions = {
            ICVMethod.CHOKE_WAIT: {"E": {"2": "", "map": {"2": {"x0": "E"}}}}
        }
        with pytest.raises(ValueError) as e:
            self.icv_function.create_choke_wait(
                "E", trigger_number_times, trigger_minimum_interval, actionx_repeater, criteria
            )
        assert "Missing content in CONTROL_CRITERIA keyword!" in str(e.value)


class Test_CustomConditionCustomCase:
    CASE_CUSTOM_TEXT = """
SCHFILE
  'data/dummy_schedule_file.sch'
/

COMPLETION
--WELL Branch Start  End   Screen    Well/ Roughness Annulus Nvalve Valve Device
--     Number    mD   mD   Tubing   Casing Roughness Content /Joint  Type Number
--                       Diameter Diameter
WELL1     1    0 99999     0.10   0.2159   0.00300      GP      1  AICD      1
WELL2     1    0 99999     0.10   0.2159   0.00300      GP      1  AICD      1
/

ICVCONTROL
-- D: FUD
-- H: FUH
-- FAC: Maximum rate factor for icv-control
-- FR: ICV function repetitions
-- OSTP: OPERSTEP (NEXTSTEP in operation icv-functions)
-- WSTP: WAITSTEP (NEXTSTEP in waiting icv-functions)
--
-- WELL ICV SEGMENT AC-TABLE STEPS     ICVDATE  FREQ  MIN MAX OPENING FUD FUH FUL  OPERSTEP WAITSTEP  INIT
WELL1   A       105   0.1337   100  1.JAN.2022    30    0   1       0   5   2 0.1       0.2      1.0  0.01
WELL1   B       106   0.1337   100  1.JAN.2022    30    0   1       0   5   2 0.1       0.2      1.0  0.02
WELL2   E       142   0.1337   100  1.JAN.2022    30    0   1       0   5   2 0.1       0.2      1.0  0.07
WELL2   F       143   0.1337   100  1.JAN.2022    30    0   1       0   5   2 0.1       0.2      1.0  0.08
WELL2   G       144   0.1337   100  1.JAN.2022    30    0   1       0   5   2 0.1       0.2      1.0  0.09
WELL2   Z      1337   0.1337   100  1.JAN.2022    30    0   1       0   5   2 0.1       0.2      1.0  0.09
WELL2   D      1338   0.1337   100  1.JAN.2022    30    0   1       0   5   2 0.1       0.2      1.0  0.09
/

CONTROL_CRITERIA
  FUNCTION: [OPEN]
  CRITERIUM: 1
  ICV: [F]
  1111 OPEN WAITOPEN READYOPEN /
/

CONTROL_CRITERIA
  FUNCTION: [OPEN_STOP, OPEN_WAIT_STOP]
  CRITERIUM: [2, 3]
  ICV: [Z, A, D, F]
  2222 STOPOPEN STOPOPENWAIT
/

CONTROL_CRITERIA
  FUNCTION: [OPEN_STOP, OPEN_WAIT_STOP]
  CRITERIUM: [2, 3]
  ICV: [A, Z, D, F]
  2222 STOPOPEN STOPOPENWAIT
/

CONTROL_CRITERIA
  FUNCTION: [OPEN_STOP, OPEN_WAIT_STOP]
  CRITERIUM: [2, 3]
  ICV: [F, Z, D, A]
  2222 STOPOPEN STOPOPENWAIT
/

CONTROL_CRITERIA
  FUNCTION: [OPEN_WAIT]
  CRITERIUM: 2
  ICV: [B]
  2222 WAITOPEN
/

CONTROL_CRITERIA
  FUNCTION: [OPEN_READY]
  CRITERIUM: 3
  ICV: [E,F]
  3333 READY YO
/

CONTROL_CRITERIA
  FUNCTION: [CHOKE]
  CRITERIUM: 1
  ICV: [F]
  1111 CHOOCHOO /
/

CONTROL_CRITERIA
  FUNCTION: [CHOKE_STOP, CHOKE_WAIT_STOP]
  CRITERIUM: [2, 3]
  ICV: [Z, A, D, F]
  2222 STOPCHOOCHOO STOPCHOKEWAIT  /
/

CONTROL_CRITERIA
  FUNCTION: [CHOKE_STOP, CHOKE_WAIT_STOP]
  CRITERIUM: [2, 3]
  ICV: [A][F]
  2222 STOPCHOOCHOO STOPCHOKEWAIT  /
/

CONTROL_CRITERIA
  FUNCTION: [CHOKE_WAIT]
  CRITERIUM: 2
  ICV: [B]
  2222 WAITCHOKE
/

CONTROL_CRITERIA
  FUNCTION: [CHOKE_READY]
  CRITERIUM: 3
  ICV: [E]
  READYCHOKE 3333 /
/
---------------------- UDQ -----------------------------
CONTROL_CRITERIA
  FUNCTION: [UDQ]
  ICV: [Z, A]
  DEFINE TULL_x0 ( BUR WELL(x0) SEG(x0) / SUR WELL(x0) SEG(x1) ) / -- Ratio of tullball
/

"""

    custom_case = ICVReadCasefile(CASE_CUSTOM_TEXT)
    icv_function = IcvFunctions(Initialization(custom_case))

    def test_insert_custom_conditions_open_f(self, log_warning):
        """Open from custom conditions in case file.
        The case file includes:
        CONTROL_CRITERIA
          FUNCTION: [OPEN]
          CRITERIUM: 1
          ICV: [F]
          1111 OPEN WAITOPEN READYOPEN /"""
        trigger_number_times = 1
        trigger_minimum_interval = ""
        criteria = 1
        actionx_repeater = 2
        expected = """ACTIONX
  OP1F_001 1 /
  FUTSTP < FUH_F AND /
  FUTSTP > FUL_F AND /
  FUTO_F > FUD_F AND /
  FUP_F = 3 AND /
  1111 OPEN WAITOPEN READYOPEN /
/

UDQ
  DEFINE FUARE_F (FUARE_F / 0.6) /
  UPDATE FUARE_F NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  OP1F_002 1 /
  FUP_F = 3 /
/

WSEGVALV
  WELL2 143 1.0 FUARE_F 5* 0.1337 /
/
NEXTSTEP
  0.2 /

ENDACTIO
ENDACTIO
"""

        open = self.icv_function.create_open(
            "F", criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater
        )

        assert open == expected

    def test_insert_custom_conditions_open_stop_a_crit2(self, log_warning):
        """Open stop from custom conditions in case file.
        The case file includes:
        CONTROL_CRITERIA
          FUNCTION: [OPEN_STOP, OPEN_WAIT_STOP]
          CRITERIUM: [2, 3]
          ICV: [Z, A, D, F]
          2222 STOPOPEN STOPOPENWAIT
        /"""
        trigger_number_times = 10000
        trigger_minimum_interval = ""
        criteria = 2
        icv_name = "A"

        expected = """ACTIONX
  STOPO2A 10000 /
  FUP_A = 3 AND /
  FUTO_A != 0 AND /
  2222 STOPOPEN STOPOPENWAIT /
/

UDQ
  ASSIGN FUP_A 2 /
  ASSIGN FUTO_A 0 /
  ASSIGN FUT_A 0 /
  UPDATE FUT_A ON /
/
ENDACTIO

"""
        open_stop = self.icv_function.create_open_stop(
            icv_name, criteria, trigger_number_times, trigger_minimum_interval
        )
        assert open_stop == expected

    def test_insert_custom_conditions_open_wait_stop_f_crit3(self, log_warning):
        """Open wait stop from custom conditions in case file.
        The case file includes:
        CONTROL_CRITERIA
          FUNCTION: [OPEN_WAIT_STOP]
          CRITERIUM: [2, 3]
          ICV: [Z, A, D, F]
          2222 STOPOPEN STOPOPENWAIT
        /"""
        criteria = 3
        icv_name = "F"
        expected = """ACTIONX
  STOPOW3F 10000 10 /
  FUP_F = 2 AND /
  FUTO_F != 0 AND /
  2222 STOPOPEN STOPOPENWAIT /
/

UDQ
  ASSIGN FUTO_F 0 /
/
ENDACTIO

"""
        open_wait_stop = self.icv_function.create_open_wait_stop(icv_name, criteria)
        assert open_wait_stop == expected

    def test_insert_custom_conditions_open_wait_b_crit2(self, log_warning):
        """Open wait from custom conditions in case file.
        The case file includes:
        CONTROL_CRITERIA
          FUNCTION: [OPEN_WAIT]
          CRITERIUM: 2
          ICV: [B]
          2222 WAITOPEN
        /"""
        actionx_repeater = 4
        icv_name = "B"
        criteria = 2
        expected = """ACTIONX
  WO2B_001 10000 10 /
  FUTO_B <= FUD_B AND /
  FUP_B = 2 AND /
  FUT_B > FUFRQ_B AND /
  2222 WAITOPEN /
/

UDQ
  DEFINE FUTO_B FUTO_B + TIMESTEP /
/
NEXTSTEP
  1.0 /

ACTIONX
  WO2B_002 1 /
  FUTSTP > FUL_B AND /
  FUTO_B <= FUD_B AND /
  FUP_B = 2 AND /
  FUT_B > FUFRQ_B AND /
  2222 WAITOPEN /
/

UDQ
  DEFINE FUTO_B FUTO_B + TIMESTEP /
/
NEXTSTEP
  1.0 /

ACTIONX
  WO2B_003 1 /
  FUTSTP > FUL_B AND /
  FUTO_B <= FUD_B AND /
  FUP_B = 2 AND /
  FUT_B > FUFRQ_B AND /
  2222 WAITOPEN /
/

UDQ
  DEFINE FUTO_B FUTO_B + TIMESTEP /
/
NEXTSTEP
  1.0 /

ACTIONX
  WO2B_004 1 /
  FUTSTP > FUL_B AND /
  FUTO_B <= FUD_B AND /
  FUP_B = 2 AND /
  FUT_B > FUFRQ_B AND /
  2222 WAITOPEN /
/

UDQ
  DEFINE FUTO_B FUTO_B + TIMESTEP /
/
NEXTSTEP
  1.0 /

ENDACTIO
ENDACTIO
ENDACTIO
ENDACTIO
"""
        open_wait = self.icv_function.create_open_wait(icv_name, actionx_repeater, criteria)
        assert open_wait == expected

    def test_insert_custom_conditions_open_ready_e_crit3(self, log_warning):
        """Open ready from custom conditions in case file.
        The case file includes:
        CONTROL_CRITERIA
          FUNCTION: [OPEN_READY]
          CRITERIUM: 3
          ICV: [e]
          2222 WAITOPEN
        /"""
        trigger_number_times = 10000
        trigger_minimum_interval = ""
        criteria = 3
        icv_name = "E"
        expected = """ACTIONX
  READYO3E 10000 /
  FUTO_E > FUD_E AND /
  FUP_E = 2 AND /
  3333 READY YO /
/

UDQ
  ASSIGN FUP_E 3 /
/
ENDACTIO

"""
        open_wait_stop = self.icv_function.create_open_ready(
            icv_name, criteria, trigger_number_times, trigger_minimum_interval
        )
        assert open_wait_stop == expected

    def test_insert_custom_conditions_choke_f(self, log_warning):
        """Choke from custom conditions in case file.
        The case file includes:
        CONTROL_CRITERIA
          FUNCTION: [CHOKE]
          CRITERIUM: 1
          ICV: [F]
          1111 CHOOCHOO /"""
        trigger_number_times = 1
        trigger_minimum_interval = ""
        criteria = 1
        actionx_repeater = 4
        expected = """ACTIONX
  CH1F_001 1 /
  FUTSTP < FUH_F AND /
  FUTSTP > FUL_F AND /
  FUTC_F > FUD_F AND /
  FUP_F = 4 AND /
  1111 CHOOCHOO /
/

UDQ
  DEFINE FUARE_F (FUARE_F * 0.6) /
  UPDATE FUARE_F NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  CH1F_002 1 /
  FUP_F = 4 /
/

WSEGVALV
  WELL2 143 1.0 FUARE_F 5* 0.1337 /
/
NEXTSTEP
  0.2 /

ACTIONX
  CH1F_003 1 /
  FUTSTP < FUH_F AND /
  FUTSTP > FUL_F AND /
  FUTC_F > FUD_F AND /
  FUP_F = 4 AND /
  1111 CHOOCHOO /
/

UDQ
  DEFINE FUARE_F (FUARE_F * 0.6) /
  UPDATE FUARE_F NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  CH1F_004 1 /
  FUP_F = 4 /
/

WSEGVALV
  WELL2 143 1.0 FUARE_F 5* 0.1337 /
/
NEXTSTEP
  0.2 /

ENDACTIO
ENDACTIO
ENDACTIO
ENDACTIO
"""

        choke = self.icv_function.create_choke(
            "F", criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater
        )

        assert choke == expected

    def test_insert_custom_conditions_choke_stop_a_crit2(self, log_warning):
        """Choke stop from custom conditions in case file.
        The case file includes:
        CONTROL_CRITERIA
          FUNCTION: [OPEN_STOP, OPEN_WAIT_STOP]
          CRITERIUM: 2
          ICV: [Z, A]
          2222 STOPOPEN STOPOPENWAIT
        /"""
        trigger_number_times = 10000
        trigger_minimum_interval = ""
        criteria = 2
        icv_name = "A"
        expected = """ACTIONX
  STOPC2A 10000 /
  FUP_A = 4 AND /
  FUTC_A != 0 AND /
  2222 STOPCHOOCHOO STOPCHOKEWAIT /
/

UDQ
  ASSIGN FUP_A 2 /
  ASSIGN FUTC_A 0 /
  ASSIGN FUT_A 0 /
  UPDATE FUT_A ON /
/
ENDACTIO

"""
        choke_stop = self.icv_function.create_choke_stop(
            icv_name, criteria, trigger_number_times, trigger_minimum_interval
        )
        assert choke_stop == expected

    def test_insert_custom_conditions_choke_wait_stop_f_crit3(self, log_warning):
        """Choke wait stop from custom conditions in case file.
        The case file includes:
        CONTROL_CRITERIA
          FUNCTION: [CHOKE_WAIT_STOP]
          CRITERIUM: [2, 3]
          ICV: [Z, A, D, F]
          2222 STOPCHOOCHOO STOPCHOKEWAIT  /
        /"""
        criteria = 2
        icv_name = "F"
        expected = """ACTIONX
  STOPCW2F 10000 10 /
  FUP_F = 2 AND /
  FUTC_F != 0 AND /
  2222 STOPCHOOCHOO STOPCHOKEWAIT /
/

UDQ
  ASSIGN FUTC_F 0 /
/
ENDACTIO

"""
        choke_wait_stop = self.icv_function.create_choke_wait_stop(icv_name, criteria)
        assert choke_wait_stop == expected

    def test_insert_custom_conditions_choke_wait_b_crit2(self, log_warning):
        """Choke wait from custom conditions in case file.
        The case file includes:
        CONTROL_CRITERIA
          FUNCTION: [CHOKE_WAIT]
          CRITERIUM: 2
          ICV: [B]
          2222 WAITCHOKE
        /"""
        actionx_repeater = 4
        icv_name = "B"
        criteria = 2
        trigger_number_times = 10000
        trigger_minimum_interval = 10
        expected = """ACTIONX
  WC2B_001 10000 10 /
  FUTC_B <= FUD_B AND /
  FUP_B = 2 AND /
  FUT_B > FUFRQ_B AND /
  2222 WAITCHOKE /
/

UDQ
  DEFINE FUTC_B FUTC_B + TIMESTEP /
/
NEXTSTEP
  1.0 /

ACTIONX
  WC2B_002 1 /
  FUTSTP > FUL_B AND /
  FUTC_B <= FUD_B AND /
  FUP_B = 2 AND /
  FUT_B > FUFRQ_B AND /
  2222 WAITCHOKE /
/

UDQ
  DEFINE FUTC_B FUTC_B + TIMESTEP /
/
NEXTSTEP
  1.0 /

ACTIONX
  WC2B_003 1 /
  FUTSTP > FUL_B AND /
  FUTC_B <= FUD_B AND /
  FUP_B = 2 AND /
  FUT_B > FUFRQ_B AND /
  2222 WAITCHOKE /
/

UDQ
  DEFINE FUTC_B FUTC_B + TIMESTEP /
/
NEXTSTEP
  1.0 /

ACTIONX
  WC2B_004 1 /
  FUTSTP > FUL_B AND /
  FUTC_B <= FUD_B AND /
  FUP_B = 2 AND /
  FUT_B > FUFRQ_B AND /
  2222 WAITCHOKE /
/

UDQ
  DEFINE FUTC_B FUTC_B + TIMESTEP /
/
NEXTSTEP
  1.0 /

ENDACTIO
ENDACTIO
ENDACTIO
ENDACTIO
"""
        choke_wait = self.icv_function.create_choke_wait(
            icv_name, trigger_number_times, trigger_minimum_interval, actionx_repeater, criteria
        )
        assert choke_wait == expected

    def test_insert_custom_conditions_choke_ready_e_crit3(self, log_warning):
        """'Choke ready from custom conditions in case file.
        The case file includes:
        CONTROL_CRITERIA
          FUNCTION: [CHOKE_READY]
          CRITERIUM: 3
          ICV: [e]
         READYCHOKE 3333
        /"""
        trigger_number_times = 10000
        trigger_minimum_interval = ""
        criteria = 3
        icv_name = "E"
        expected = """ACTIONX
  READYC3E 10000 /
  FUTC_E > FUD_E AND /
  FUP_E = 2 AND /
  READYCHOKE 3333 /
/

UDQ
  ASSIGN FUP_E 4 /
/
ENDACTIO

"""
        choke_wait_stop = self.icv_function.create_choke_ready(
            icv_name, criteria, trigger_number_times, trigger_minimum_interval
        )
        assert choke_wait_stop == expected

    def test_output_input_icvcontrol(self, log_warning):
        """Read UDQ Custom content from case file."""
        expected_input_icvcontrol_output = """UDQ

-- Initialization

  ASSIGN FUFRQ_A 30 /
  ASSIGN FUFRQ_B 30 /
  ASSIGN FUFRQ_E 30 /
  ASSIGN FUFRQ_F 30 /
  ASSIGN FUFRQ_G 30 /
  ASSIGN FUFRQ_Z 30 /
  ASSIGN FUFRQ_D 30 /

  ASSIGN FUT_A 30 /
  ASSIGN FUT_B 30 /
  ASSIGN FUT_E 30 /
  ASSIGN FUT_F 30 /
  ASSIGN FUT_G 30 /
  ASSIGN FUT_Z 30 /
  ASSIGN FUT_D 30 /

  ASSIGN FUCH_A 0.0 /
  ASSIGN FUOP_A 1.0 /

  ASSIGN FUCH_B 0.0 /
  ASSIGN FUOP_B 1.0 /

  ASSIGN FUCH_E 0.0 /
  ASSIGN FUOP_E 1.0 /

  ASSIGN FUCH_F 0.0 /
  ASSIGN FUOP_F 1.0 /

  ASSIGN FUCH_G 0.0 /
  ASSIGN FUOP_G 1.0 /

  ASSIGN FUCH_Z 0.0 /
  ASSIGN FUOP_Z 1.0 /

  ASSIGN FUCH_D 0.0 /
  ASSIGN FUOP_D 1.0 /

  ASSIGN FUTSTP 0 /

  ASSIGN TULL_Z 0.09 /

-- Definition of parameters,
-- continuously updated:

  DEFINE FUTSTP TIMESTEP /
  DEFINE FUT_A FUT_A + TIMESTEP /
  DEFINE FUT_B FUT_B + TIMESTEP /
  DEFINE FUT_E FUT_E + TIMESTEP /
  DEFINE FUT_F FUT_F + TIMESTEP /
  DEFINE FUT_G FUT_G + TIMESTEP /
  DEFINE FUT_Z FUT_Z + TIMESTEP /
  DEFINE FUT_D FUT_D + TIMESTEP /

  DEFINE TULL_Z ( BUR 'WELL2' 1337 / SUR 'WELL2' 105 ) /

  ASSIGN FUARE_A 0.1337 /
  ASSIGN FUARE_B 0.1337 /
  ASSIGN FUARE_E 0.1337 /
  ASSIGN FUARE_F 0.1337 /
  ASSIGN FUARE_G 0.1337 /
  ASSIGN FUARE_Z 0.1337 /
  ASSIGN FUARE_D 0.1337 /
/"""
        initialization = Initialization(ICVReadCasefile(self.CASE_CUSTOM_TEXT))
        assert initialization.input_icvcontrol == expected_input_icvcontrol_output


class TestCustomConditionCustomCase3ICV:
    CASE_CUSTOM_TEXT_3_ICV = """
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
-- WELL ICV SEGMENT AC-TABLE STEPS     ICVDATE  FREQ  MIN MAX OPENING FUD FUH FUL OPERSTEP WAITSTEP  INIT
WELL1     A 105       0.1337   100  1.JAN.2022    30    0   1       0   5   2 0.1      0.2      1.0  0.01
WELL1     B 106       0.1337   100  1.JAN.2022    30    0   1       0   5   2 0.1      0.2      1.0  0.01
WELL2     E 142       0.1337   100  1.JAN.2022    30    0   1       0   5   2 0.1      0.2      1.0  0.01
WELL2     F 143       0.1337   100  1.JAN.2022    30    0   1       0   5   2 0.1      0.2      1.0  0.01
WELL2     G 144       0.1337   100  1.JAN.2022    30    0   1       0   5   2 0.1      0.2      1.0  0.01
/

CONTROL_CRITERIA
  FUNCTION: [OPEN]
  CRITERIUM: 1
  ICV: [G]
  1111 OPEN WAITOPEN READYOPEN /
/

---------------------- UDQ -----------------------------
CONTROL_CRITERIA
  FUNCTION: [UDQ]
  ICV: [A, B, E, F, G]
  DEFINE TULL_x0 ( BUR WELL(x0) SEG(x0) / SUR WELL(x0) SEG(x1) ) / -- Ratio of tullball
/

"""

    custom_case = ICVReadCasefile(CASE_CUSTOM_TEXT_3_ICV)
    icv_function = IcvFunctions(Initialization(custom_case))

    def test_insert_custom_conditions_open_3ICV(self, log_warning):
        """Open from custom conditions in case file.
        The case file includes:
        CONTROL_CRITERIA
          FUNCTION: [OPEN]
          CRITERIUM: 1
          ICV: [G]
          1111 OPEN WAITOPEN READYOPEN /"""
        trigger_number_times = 1
        trigger_minimum_interval = ""
        criteria = 1
        actionx_repeater = 2
        expected = """ACTIONX
  OP1G_001 1 /
  FUTSTP < FUH_G AND /
  FUTSTP > FUL_G AND /
  FUTO_G > FUD_G AND /
  FUP_G = 3 AND /
  1111 OPEN WAITOPEN READYOPEN /
/

UDQ
  DEFINE FUARE_G (FUARE_G / 0.6) /
  UPDATE FUARE_G NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  OP1G_002 1 /
  FUP_G = 3 /
/

WSEGVALV
  WELL2 144 1.0 FUARE_G 5* 0.1337 /
/
NEXTSTEP
  0.2 /

ENDACTIO
ENDACTIO
"""

        open = self.icv_function.create_open(
            "G", criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater
        )

        assert open == expected


class TestCustomConditionCustomCase10ICV:
    CASE_CUSTOM_TEXT_10_ICV = """
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
-- WELL ICV SEGMENT AC-TABLE  STEPS     ICVDATE    FREQ  MIN MAX OPENING  FUD FUH FUL OPERSTEP WAITSTEP  INIT
WELL2   A     141 0.1337        100  1.JAN.2022      30    0   1       0    5   2 0.1      0.2      1.0  0.01
WELL2   B     142 0.1337        100  1.JAN.2022      30    0   1       0    5   2 0.1      0.2      1.0  0.02
WELL2   C     143 0.1337        100  1.JAN.2022      30    0   1       0    5   2 0.1      0.2      1.0  0.03
WELL2   D     144 0.1337        100  1.JAN.2022      30    0   1       0    5   2 0.1      0.2      1.0  0.04
WELL2   E     145 0.1337        100  1.JAN.2022      30    0   1       0    5   2 0.1      0.2      1.0  0.05
WELL2   F     146 0.1337        100  1.JAN.2022      30    0   1       0    5   2 0.1      0.2      1.0  0.06
WELL2   G     147 0.1337        100  1.JAN.2022      30    0   1       0    5   2 0.1      0.2      1.0  0.07
WELL2   H     148 0.1337        100  1.JAN.2022      30    0   1       0    5   2 0.1      0.2      1.0  0.08
WELL2   I     149 0.1337        100  1.JAN.2022      30    0   1       0    5   2 0.1      0.2      1.0  0.09
WELL2   J     150 0.1337        100  1.JAN.2022      30    0   1       0    5   2 0.1      0.2      1.0  0.09
/

CONTROL_CRITERIA
  FUNCTION: [OPEN_STOP, OPEN_WAIT_STOP]
  CRITERIUM: [2, 3]
  ICV: [A]
  2222 STOPOPEN STOPOPENWAIT
/

CONTROL_CRITERIA
  FUNCTION: [OPEN_WAIT]
  CRITERIUM: 2
  ICV: [B]
  2222 WAITOPEN
/

CONTROL_CRITERIA
  FUNCTION: [OPEN_READY]
  CRITERIUM: 3
  ICV: [I]
  3333 READY YO
/

CONTROL_CRITERIA
  FUNCTION: [CHOKE]
  CRITERIUM: 1
  ICV: [D]
  1111 CHOOCHOO /
/

CONTROL_CRITERIA
  FUNCTION: [CHOKE_STOP, CHOKE_WAIT_STOP]
  CRITERIUM: [2, 3]
  ICV: [E]
  2222 STOPCHOOCHOO STOPCHOKEWAIT  /
/

CONTROL_CRITERIA
  FUNCTION: [CHOKE_WAIT]
  CRITERIUM: 2
  ICV: [F]
  2222 WAITCHOKE
/

CONTROL_CRITERIA
  FUNCTION: [OPEN]
  CRITERIUM: 1
  ICV: [G]
  1111 OPEN WAITOPEN READYOPEN /
/

CONTROL_CRITERIA
  FUNCTION: [CHOKE_READY]
  CRITERIUM: 3
  ICV: [H]
  READYCHOKE 3333 /
/

"""

    custom_case = ICVReadCasefile(CASE_CUSTOM_TEXT_10_ICV)
    icv_function = IcvFunctions(Initialization(custom_case))

    def test_insert_custom_conditions_open_10ICV(self, log_warning):
        """Open from custom conditions in case file.
        The case file includes:
        CONTROL_CRITERIA
          FUNCTION: [OPEN]
          CRITERIUM: 1
          ICV: [G]
          1111 OPEN WAITOPEN READYOPEN /"""
        trigger_number_times = 1
        trigger_minimum_interval = ""
        criteria = 1
        actionx_repeater = 2
        expected = """ACTIONX
  OP1G_001 1 /
  FUTSTP < FUH_G AND /
  FUTSTP > FUL_G AND /
  FUTO_G > FUD_G AND /
  FUP_G = 3 AND /
  1111 OPEN WAITOPEN READYOPEN /
/

UDQ
  DEFINE FUARE_G (FUARE_G / 0.6) /
  UPDATE FUARE_G NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  OP1G_002 1 /
  FUP_G = 3 /
/

WSEGVALV
  WELL2 147 1.0 FUARE_G 5* 0.1337 /
/
NEXTSTEP
  0.2 /

ENDACTIO
ENDACTIO
"""

        open = self.icv_function.create_open(
            "G", criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater
        )

        assert open == expected

    def test_insert_custom_conditions_open_stop_a_crit2_10ICV(self, log_warning):
        """Open stop from custom conditions in case file.
        The case file includes:
        CONTROL_CRITERIA
          FUNCTION: [OPEN_STOP, OPEN_WAIT_STOP]
          CRITERIUM: [2, 3]
          ICV: [A]
          2222 STOPOPEN STOPOPENWAIT
        /"""
        trigger_number_times = 10000
        trigger_minimum_interval = ""
        criteria = 2
        icv_name = "A"

        expected = """ACTIONX
  STOPO2A 10000 /
  FUP_A = 3 AND /
  FUTO_A != 0 AND /
  2222 STOPOPEN STOPOPENWAIT /
/

UDQ
  ASSIGN FUP_A 2 /
  ASSIGN FUTO_A 0 /
  ASSIGN FUT_A 0 /
  UPDATE FUT_A ON /
/
ENDACTIO

"""
        open_stop = self.icv_function.create_open_stop(
            icv_name, criteria, trigger_number_times, trigger_minimum_interval
        )
        assert open_stop == expected

    def test_insert_custom_conditions_open_wait_b_ICV10(self, log_warning):
        """Open wait from custom conditions in case file.
        The case file includes:
        CONTROL_CRITERIA
          FUNCTION: [OPEN_WAIT]
          CRITERIUM: 2
          ICV: [B]
          2222 WAITOPEN
        /"""
        actionx_repeater = 4
        icv_name = "B"
        criteria = 2
        expected = """ACTIONX
  WO2B_001 10000 10 /
  FUTO_B <= FUD_B AND /
  FUP_B = 2 AND /
  FUT_B > FUFRQ_B AND /
  2222 WAITOPEN /
/

UDQ
  DEFINE FUTO_B FUTO_B + TIMESTEP /
/
NEXTSTEP
  1.0 /

ACTIONX
  WO2B_002 1 /
  FUTSTP > FUL_B AND /
  FUTO_B <= FUD_B AND /
  FUP_B = 2 AND /
  FUT_B > FUFRQ_B AND /
  2222 WAITOPEN /
/

UDQ
  DEFINE FUTO_B FUTO_B + TIMESTEP /
/
NEXTSTEP
  1.0 /

ACTIONX
  WO2B_003 1 /
  FUTSTP > FUL_B AND /
  FUTO_B <= FUD_B AND /
  FUP_B = 2 AND /
  FUT_B > FUFRQ_B AND /
  2222 WAITOPEN /
/

UDQ
  DEFINE FUTO_B FUTO_B + TIMESTEP /
/
NEXTSTEP
  1.0 /

ACTIONX
  WO2B_004 1 /
  FUTSTP > FUL_B AND /
  FUTO_B <= FUD_B AND /
  FUP_B = 2 AND /
  FUT_B > FUFRQ_B AND /
  2222 WAITOPEN /
/

UDQ
  DEFINE FUTO_B FUTO_B + TIMESTEP /
/
NEXTSTEP
  1.0 /

ENDACTIO
ENDACTIO
ENDACTIO
ENDACTIO
"""
        open_wait = self.icv_function.create_open_wait(icv_name, actionx_repeater, criteria)
        assert open_wait == expected

    def test_insert_custom_conditions_open_ready_e_crit3_10ICV(self, log_warning):
        """Open ready from custom conditions in case file.
        The case file includes:
        CONTROL_CRITERIA
          FUNCTION: [OPEN_READY]
          CRITERIUM: 3
          ICV: [I]
          2222 WAITOPEN
        /"""
        trigger_number_times = 10000
        trigger_minimum_interval = ""
        criteria = 3
        icv_name = "I"
        expected = """ACTIONX
  READYO3I 10000 /
  FUTO_I > FUD_I AND /
  FUP_I = 2 AND /
  3333 READY YO /
/

UDQ
  ASSIGN FUP_I 3 /
/
ENDACTIO

"""
        open_wait_stop = self.icv_function.create_open_ready(
            icv_name, criteria, trigger_number_times, trigger_minimum_interval
        )
        assert open_wait_stop == expected

    def test_insert_custom_conditions_choke_d_10ICV(self, log_warning):
        """Choke from custom conditions in case file.
        The case file includes:
        CONTROL_CRITERIA
          FUNCTION: [CHOKE]
          CRITERIUM: 1
          ICV: [D]
          1111 CHOOCHOO /"""
        trigger_number_times = 1
        trigger_minimum_interval = ""
        criteria = 1
        actionx_repeater = 4
        expected = """ACTIONX
  CH1D_001 1 /
  FUTSTP < FUH_D AND /
  FUTSTP > FUL_D AND /
  FUTC_D > FUD_D AND /
  FUP_D = 4 AND /
  1111 CHOOCHOO /
/

UDQ
  DEFINE FUARE_D (FUARE_D * 0.6) /
  UPDATE FUARE_D NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  CH1D_002 1 /
  FUP_D = 4 /
/

WSEGVALV
  WELL2 144 1.0 FUARE_D 5* 0.1337 /
/
NEXTSTEP
  0.2 /

ACTIONX
  CH1D_003 1 /
  FUTSTP < FUH_D AND /
  FUTSTP > FUL_D AND /
  FUTC_D > FUD_D AND /
  FUP_D = 4 AND /
  1111 CHOOCHOO /
/

UDQ
  DEFINE FUARE_D (FUARE_D * 0.6) /
  UPDATE FUARE_D NEXT /
/
NEXTSTEP
  0.1 /

ACTIONX
  CH1D_004 1 /
  FUP_D = 4 /
/

WSEGVALV
  WELL2 144 1.0 FUARE_D 5* 0.1337 /
/
NEXTSTEP
  0.2 /

ENDACTIO
ENDACTIO
ENDACTIO
ENDACTIO
"""

        choke = self.icv_function.create_choke(
            "D", criteria, trigger_number_times, trigger_minimum_interval, actionx_repeater
        )

        assert choke == expected

    def test_insert_custom_conditions_record2_choke_10icv(self, log_warning):
        """Test creating record 2 in the Eclipse ACTIONX keyword for icvc.
        Two ICVs."""
        step = 1
        criteria = 1337
        self.icv_function.initials.custom_conditions = {
            ICVMethod.CHOKE: {
                "E": {
                    "1337": """  WELL(x0) > WELL(x0) AND /
  T_x0 > X_x9 AND /
  WELL(x0) 321 > 0.01 /
""",
                    "map": {"1337": {"x0": "E", "x9": "J"}},
                }
            }
        }

        record2 = self.icv_function.create_record2_choke("E", step, criteria)
        expected_record2 = """  FUTSTP < FUH_E AND /
  FUTSTP > FUL_E AND /
  FUTC_E > FUD_E AND /
  FUP_E = 4 AND /
  'WELL2' > 'WELL2' AND /
  T_E > X_J AND /
  'WELL2' 321 > 0.01 /
/
"""
        assert record2 == expected_record2
