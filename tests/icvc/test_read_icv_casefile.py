"""Test reading of casefile, loading tables."""

import pandas as pd
import pytest

from completor import read_casefile
from completor.constants import ICVMethod

BASE_CASE = """
COMPLETION
--WELL  Branch  Start    End   Screen     Well/  Roughness  Annulus  Nvalve  Valve  Device
--      Number     mD     mD   Tubing    Casing  Roughness  Content  /Joint   Type  Number
--                           Diameter  Diameter
WELL1       1      0  99999     0.10    0.2159    0.00300       GP       1   AICD       1
/

ICVCONTROL
-- WELL ICV SEGMENT AC-TABLE STEPS     ICVDATE  FREQ   MIN MAX OPENING
  WELL1   A     105 0.1337      80  1.JAN.2033    90     0   1      T1
  WELL1   B     106 0.1337      30  1.JAN.2033    90     0   1      T2
WELL-N1   C     181 0.1337      150 1.JAN.2033    90     0   1      T3
WELL-N1   D     182 0.1337      20  1.JAN.2033    90     0   1      T4
WELL-F2   H      39 0.1337      80  1.JAN.2033    90     0   1      T5
WELL-F2   I      40 0.1337      20  1.JAN.2033    90     0   1      T6
  WELL2   E     142 0.1337      50  1.JAN.2033    90     0   1      T7
  WELL2   F     143 0.1337      50  1.JAN.2033    90     0   1      T8
  WELL2   G     144 0.1337      50  1.JAN.2033    90     0   1      T9
/
"""

BASE_CASE_EXTENDED = """
COMPLETION
--WELL  Branch  Start    End   Screen     Well/  Roughness  Annulus  Nvalve  Valve  Device
--      Number     mD     mD   Tubing    Casing  Roughness  Content  /Joint   Type  Number
--                           Diameter  Diameter
WELL1       1      0  99999     0.10    0.2159    0.00300       GP       1   AICD       1
/

ICVCONTROL
-- WELL ICV SEGMENT AC-TABLE STEPS     ICVDATE  FREQ   MIN MAX OPENING  FUD FUH FUL  OPERSTEP WAITSTEP  INIT
  WELL1   A     105 0.1337      80  1.JAN.2033    90     0   1      T1    5   2 0.1       0.2      1.0  0.01
  WELL1   B     106 0.1337      30  1.JAN.2033    90     0   1      T2    5   2 0.1       0.2      1.0  0.02
WELL-N1   C     181 0.1337      150 1.JAN.2033    90     0   1      T3    5   2 0.1       0.2      1.0  0.03
WELL-N1   D     182 0.1337      20  1.JAN.2033    90     0   1      T4    5   2 0.1       0.2      1.0  0.04
WELL-F2   H      39 0.1337      80  1.JAN.2033    90     0   1      T5    5   2 0.1       0.2      1.0  0.05
WELL-F2   I      40 0.1337      20  1.JAN.2033    90     0   1      T6    5   2 0.1       0.2      1.0  0.06
  WELL2   E     142 0.1337      50  1.JAN.2033    90     0   1      T7    5   2 0.1       0.2      1.0  0.07
  WELL2   F     143 0.1337      50  1.JAN.2033    90     0   1      T8    5   2 0.1       0.2      1.0  0.08
  WELL2   G     144 0.1337      50  1.JAN.2033    90     0   1      T9    5   2 0.1       0.2      1.0  0.09
/
"""

ICV_TABLE_A_H = """
ICVTABLE
-- Valve name
A B C D E F G H /
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

ICV_TABLE_I = """
ICVTABLE
-- Valve name
I /
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

ICV_TABLE_A_AND_H = """
ICVTABLE
-- Valve name
A H /
-- Position  Cv     Area
1           1.0  0.0001403
2           1.0  0.0001442
3           1.0  0.0001475
4           1.0  0.0001604
5           1.0  0.0001312
6           1.0  0.0001161
7           1.0  0.0011060
8           1.0  0.0011375
9           1.0  0.0021354
10          1.0  0.0041550
/"""

ICV_TABLE_B = """
ICVTABLE
-- Valve name
B /
-- Position  Cv     Area
1           1.0  0.0021337
2           1.0  0.0031340
3           1.0  0.0041341
4           1.0  0.0051341
5           1.0  0.0061373
6           1.0  0.0071400
7           1.0  0.0081377
8           1.0  0.0091402
9           1.0  0.0011412
10          1.0  0.0021422
/
"""

ICV_TABLE_C_G = """
ICVTABLE
-- Valve name
C D E F G/
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

BASE_CONTENT = [
    [1, 1.0, 0.0000474],
    [2, 1.0, 0.0000790],
    [3, 1.0, 0.0001317],
    [4, 1.0, 0.0002195],
    [5, 1.0, 0.0003659],
    [6, 1.0, 0.0006098],
    [7, 1.0, 0.0010160],
    [8, 1.0, 0.0016938],
    [9, 1.0, 0.0028230],
    [10, 1.0, 0.13370],
]

BASE_C_H = [
    [1, 1.0, 0.0001337],
    [2, 1.0, 0.0001340],
    [3, 1.0, 0.0001341],
    [4, 1.0, 0.0001341],
    [5, 1.0, 0.0001373],
    [6, 1.0, 0.0001400],
    [7, 1.0, 0.0011377],
    [8, 1.0, 0.0011402],
    [9, 1.0, 0.0021412],
    [10, 1.0, 0.0041422],
]


UPDATE_SEGMENT = """
UPDATE_SEGMENT_NUMBER
True
/
"""


def test_read_steps_extended():
    """Test reading of steps from case file."""
    expected = pd.DataFrame(
        [
            ["WELL1", "A", 105, "0.1337", 80, "1.JAN.2033", 90, 0.0, 1.0, "T1", 5.0, 2.0, 0.1, 0.2, 1.0, 0.01],
            ["WELL1", "B", 106, "0.1337", 30, "1.JAN.2033", 90, 0.0, 1.0, "T2", 5.0, 2.0, 0.1, 0.2, 1.0, 0.02],
            ["WELL-N1", "C", 181, "0.1337", 150, "1.JAN.2033", 90, 0.0, 1.0, "T3", 5.0, 2.0, 0.1, 0.2, 1.0, 0.03],
            ["WELL-N1", "D", 182, "0.1337", 20, "1.JAN.2033", 90, 0.0, 1.0, "T4", 5.0, 2.0, 0.1, 0.2, 1.0, 0.04],
            ["WELL-F2", "H", 39, "0.1337", 80, "1.JAN.2033", 90, 0.0, 1.0, "T5", 5.0, 2.0, 0.1, 0.2, 1.0, 0.05],
            ["WELL-F2", "I", 40, "0.1337", 20, "1.JAN.2033", 90, 0.0, 1.0, "T6", 5.0, 2.0, 0.1, 0.2, 1.0, 0.06],
            ["WELL2", "E", 142, "0.1337", 50, "1.JAN.2033", 90, 0.0, 1.0, "T7", 5.0, 2.0, 0.1, 0.2, 1.0, 0.07],
            ["WELL2", "F", 143, "0.1337", 50, "1.JAN.2033", 90, 0.0, 1.0, "T8", 5.0, 2.0, 0.1, 0.2, 1.0, 0.08],
            ["WELL2", "G", 144, "0.1337", 50, "1.JAN.2033", 90, 0.0, 1.0, "T9", 5.0, 2.0, 0.1, 0.2, 1.0, 0.09],
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
    result = read_casefile.ICVReadCasefile(BASE_CASE_EXTENDED).icv_control_table

    pd.testing.assert_frame_equal(result, expected, check_dtype=False)


def test_read_steps():
    """Test reading of steps from case file."""
    expected = pd.DataFrame(
        [
            ["WELL1", "A", 105, "0.1337", 80, "1.JAN.2033", 90, 0.0, 1.0, "T1", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["WELL1", "B", 106, "0.1337", 30, "1.JAN.2033", 90, 0.0, 1.0, "T2", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["WELL-N1", "C", 181, "0.1337", 150, "1.JAN.2033", 90, 0.0, 1.0, "T3", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["WELL-N1", "D", 182, "0.1337", 20, "1.JAN.2033", 90, 0.0, 1.0, "T4", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["WELL-F2", "H", 39, "0.1337", 80, "1.JAN.2033", 90, 0.0, 1.0, "T5", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["WELL-F2", "I", 40, "0.1337", 20, "1.JAN.2033", 90, 0.0, 1.0, "T6", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["WELL2", "E", 142, "0.1337", 50, "1.JAN.2033", 90, 0.0, 1.0, "T7", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["WELL2", "F", 143, "0.1337", 50, "1.JAN.2033", 90, 0.0, 1.0, "T8", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
            ["WELL2", "G", 144, "0.1337", 50, "1.JAN.2033", 90, 0.0, 1.0, "T9", 1.0, 10.0, 0.1, 2.0, 1.0, 0.01],
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
    result = read_casefile.ICVReadCasefile(BASE_CASE).icv_control_table

    pd.testing.assert_frame_equal(result, expected, check_dtype=False)


@pytest.mark.parametrize(
    "input_variation, expected",
    [
        (
            ICV_TABLE_A_H + ICV_TABLE_I,
            {
                "A": pd.DataFrame(BASE_CONTENT, columns=["POSITION", "CV", "AREA"]),
                "B": pd.DataFrame(BASE_CONTENT, columns=["POSITION", "CV", "AREA"]),
                "C": pd.DataFrame(BASE_CONTENT, columns=["POSITION", "CV", "AREA"]),
                "D": pd.DataFrame(BASE_CONTENT, columns=["POSITION", "CV", "AREA"]),
                "E": pd.DataFrame(BASE_CONTENT, columns=["POSITION", "CV", "AREA"]),
                "F": pd.DataFrame(BASE_CONTENT, columns=["POSITION", "CV", "AREA"]),
                "G": pd.DataFrame(BASE_CONTENT, columns=["POSITION", "CV", "AREA"]),
                "H": pd.DataFrame(BASE_CONTENT, columns=["POSITION", "CV", "AREA"]),
                "I": pd.DataFrame(
                    [
                        [1, 1.0, 0.0001337],
                        [2, 1.0, 0.0001340],
                        [3, 1.0, 0.0001341],
                        [4, 1.0, 0.0001341],
                        [5, 1.0, 0.0001373],
                        [6, 1.0, 0.0001400],
                        [7, 1.0, 0.0011377],
                        [8, 1.0, 0.0011402],
                        [9, 1.0, 0.0021412],
                        [10, 1.0, 0.0041422],
                    ],
                    columns=["POSITION", "CV", "AREA"],
                ),
            },
        ),
        (
            ICV_TABLE_A_AND_H + ICV_TABLE_B + ICV_TABLE_C_G + ICV_TABLE_I,
            {
                "A": pd.DataFrame(
                    [
                        [1, 1.0, 0.0001403],
                        [2, 1.0, 0.0001442],
                        [3, 1.0, 0.0001475],
                        [4, 1.0, 0.0001604],
                        [5, 1.0, 0.0001312],
                        [6, 1.0, 0.0001161],
                        [7, 1.0, 0.0011060],
                        [8, 1.0, 0.0011375],
                        [9, 1.0, 0.0021354],
                        [10, 1.0, 0.0041550],
                    ],
                    columns=["POSITION", "CV", "AREA"],
                ),
                "B": pd.DataFrame(
                    [
                        [1, 1.0, 0.0021337],
                        [2, 1.0, 0.0031340],
                        [3, 1.0, 0.0041341],
                        [4, 1.0, 0.0051341],
                        [5, 1.0, 0.0061373],
                        [6, 1.0, 0.0071400],
                        [7, 1.0, 0.0081377],
                        [8, 1.0, 0.0091402],
                        [9, 1.0, 0.0011412],
                        [10, 1.0, 0.0021422],
                    ],
                    columns=["POSITION", "CV", "AREA"],
                ),
                "C": pd.DataFrame(BASE_C_H, columns=["POSITION", "CV", "AREA"]),
                "D": pd.DataFrame(BASE_C_H, columns=["POSITION", "CV", "AREA"]),
                "E": pd.DataFrame(BASE_C_H, columns=["POSITION", "CV", "AREA"]),
                "F": pd.DataFrame(BASE_C_H, columns=["POSITION", "CV", "AREA"]),
                "G": pd.DataFrame(BASE_C_H, columns=["POSITION", "CV", "AREA"]),
                "H": pd.DataFrame(
                    [
                        [1, 1.0, 0.0001403],
                        [2, 1.0, 0.0001442],
                        [3, 1.0, 0.0001475],
                        [4, 1.0, 0.0001604],
                        [5, 1.0, 0.0001312],
                        [6, 1.0, 0.0001161],
                        [7, 1.0, 0.0011060],
                        [8, 1.0, 0.0011375],
                        [9, 1.0, 0.0021354],
                        [10, 1.0, 0.0041550],
                    ],
                    columns=["POSITION", "CV", "AREA"],
                ),
                "I": pd.DataFrame(
                    [
                        [1, 1.0, 0.0001337],
                        [2, 1.0, 0.0001340],
                        [3, 1.0, 0.0001341],
                        [4, 1.0, 0.0001341],
                        [5, 1.0, 0.0001373],
                        [6, 1.0, 0.0001400],
                        [7, 1.0, 0.0011377],
                        [8, 1.0, 0.0011402],
                        [9, 1.0, 0.0021412],
                        [10, 1.0, 0.0041422],
                    ],
                    columns=["POSITION", "CV", "AREA"],
                ),
            },
        ),
    ],
)
def test_read_casefile(input_variation, expected):
    """Test creation of icv tables."""
    test_input = BASE_CASE + input_variation
    reader = read_casefile.ICVReadCasefile(test_input)

    for key in reader.icv_table.keys():
        pd.testing.assert_frame_equal(reader.icv_table[key], expected[key], check_dtype=False)


@pytest.mark.parametrize(
    "condition, expected",
    [
        (
            """ \t CONTROL_CRITERIA
  FUNCTION: [OPEN] -- A Dummy comment
    CRITERIUM: 1
  ICV: [A, F]
    WWIR WELL(X1) > WUMXVDJ2 WELL(X1) AND /

  FURATE_X1 < FURATE_X2 AND /
  FURATE_G > FURMAX_G /


  SFOPN WELL(X1) SEG(X1) < 0.99 AND /
/
\t CONTROL_CRITERIA
  FUNCTION: [CHOKE]
    CRITERIA: 1,3
  ICV: [A, F]
  Testerino /

/ \t

""",
            {
                ICVMethod.OPEN: {
                    "A": {
                        "1": """WWIR WELL(X1) > WUMXVDJ2 WELL(X1) AND /
FURATE_X1 < FURATE_X2 AND /
FURATE_G > FURMAX_G AND /
SFOPN WELL(X1) SEG(X1) < 0.99 /""",
                        "map": {"1": {"X0": "A", "X1": "F"}},
                    }
                },
                ICVMethod.CHOKE: {
                    "A": {
                        "1": "TESTERINO /",
                        "3": "TESTERINO /",
                        "map": {"1": {"X0": "A", "X1": "F"}, "3": {"X0": "A", "X1": "F"}},
                    }
                },
            },
        ),
        (
            """ \t CONTROL_CRITERIA
  FUNCTION: [UDQ] -- A Dummy comment
  ICV: [B, E]
    TEST COND TO INSERT IN POS 1 UDQ REPLACEMENT /
    TEST COND TO INSERT IN POS 2 /
/
\t CONTROL_CRITERIA
  FUNCTION: [UDQ] -- A Dummy comment
  ICV: [H, J]
 POS1 H, J ICV /
 POS2 H, J ICV


/ \t

""",
            {
                ICVMethod.UDQ: {
                    "B": {
                        "1": """TEST COND TO INSERT IN POS 1 UDQ REPLACEMENT /
TEST COND TO INSERT IN POS 2 /\n""",
                        "map": {"1": {"X0": "B", "X1": "E"}},
                    },
                    "H": {"1": "POS1 H, J ICV /\nPOS2 H, J ICV\n", "map": {"1": {"X0": "H", "X1": "J"}}},
                }
            },
        ),
        (
            """ \t CONTROL_CRITERIA
  FUNCTION: [UDQ] /
  ICV: [A, G]
    TEST COND TO ONLY REPLACE POS 1 /
    /""",
            {ICVMethod.UDQ: {"A": {"1": "TEST COND TO ONLY REPLACE POS 1 /\n", "map": {"1": {"X0": "A", "X1": "G"}}}}},
        ),
        (
            """ \t CONTROL_CRITERIA
  FUNCTION: [CHOKE] -- A Dummy comment
  CRITERIA: [1, 2]
  ICV: [E]
    The crit 1 & 2 icv e test_x
/
\t CONTROL_CRITERIA
  FUNCTION: [CHOKE] -- A Dummy comment
  CRITERIA: 3
  ICV: [E]
    The crit 3 icv e test_x /
/ \t
CONTROL_CRITERIA
  FUNCTION: [OPEN] -- A Dummy comment
  CRITERIA: 2,3
  ICV: [A]
    Nr 2 and 3 crit for open
/ \t
CONTROL_CRITERIA
  FUNCTION: [UDQ] -- A Dummy comment
  ICV: [A]
    UDQ
/ \t

""",
            {
                ICVMethod.CHOKE: {
                    "E": {
                        "1": "THE CRIT 1 & 2 ICV E TEST_X /",
                        "2": "THE CRIT 1 & 2 ICV E TEST_X /",
                        "3": "THE CRIT 3 ICV E TEST_X /",
                        "map": {"1": {"X0": "E"}, "2": {"X0": "E"}, "3": {"X0": "E"}},
                    }
                },
                ICVMethod.OPEN: {
                    "A": {
                        "2": "NR 2 AND 3 CRIT FOR OPEN /",
                        "3": "NR 2 AND 3 CRIT FOR OPEN /",
                        "map": {"2": {"X0": "A"}, "3": {"X0": "A"}},
                    }
                },
                ICVMethod.UDQ: {"A": {"1": "UDQ\n", "map": {"1": {"X0": "A"}}}},
            },
        ),
    ],
)
def test_read_custom_conditions(condition, expected):
    """Check reading and parsing of CONTROL_CRITERIA keyword."""
    case = BASE_CASE + condition
    result = read_casefile.ICVReadCasefile(case).custom_conditions
    for key in expected.keys():
        assert result[key] == expected[key]


@pytest.mark.parametrize(
    "condition, expected",
    [
        (
            """ \t CONTROL_CRITERIA
  FUNCTION: [OPEN] -- A Dummy comment
    CRITERIUM: 1
  ICV: [A, F], [F, A]
    WWIR WELL(x1) > WUMXVDJ2 WELL(x1) /

  FURATE_x1 < FURATE_x2 /
  FURATE_G > FURMAX_G /


  SFOPN WELL(x1) SEG(x1) < 0.99 /
/
""",
            {
                ICVMethod.OPEN: {
                    "A": {
                        "1": """WWIR WELL(X1) > WUMXVDJ2 WELL(X1) AND /
FURATE_X1 < FURATE_X2 AND /
FURATE_G > FURMAX_G AND /
SFOPN WELL(X1) SEG(X1) < 0.99 /""",
                        "map": {"1": {"X0": "A", "X1": "F"}},
                    },
                    "F": {
                        "1": """WWIR WELL(X1) > WUMXVDJ2 WELL(X1) AND /
FURATE_X1 < FURATE_X2 AND /
FURATE_G > FURMAX_G AND /
SFOPN WELL(X1) SEG(X1) < 0.99 /""",
                        "map": {"1": {"X0": "F", "X1": "A"}},
                    },
                }
            },
        ),
        (
            """ \t CONTROL_CRITERIA
  FUNCTION: [OPEN] -- A Dummy comment
    CRITERIUM: [1,2]
  ICV: [A                ]
    WWIR WELL(x1) > WUMXVDJ2 WELL(x1) AND /

  FURATE_x1 < FURATE_x2 AND /
  FURATE_G > FURMAX_G AND /


  SFOPN WELL(x1) SEG(x1) < 0.99 /
/
""",
            {
                ICVMethod.OPEN: {
                    "A": {
                        "2": """WWIR WELL(X1) > WUMXVDJ2 WELL(X1) AND /
FURATE_X1 < FURATE_X2 AND /
FURATE_G > FURMAX_G AND /
SFOPN WELL(X1) SEG(X1) < 0.99 /""",
                        "1": """WWIR WELL(X1) > WUMXVDJ2 WELL(X1) AND /
FURATE_X1 < FURATE_X2 AND /
FURATE_G > FURMAX_G AND /
SFOPN WELL(X1) SEG(X1) < 0.99 /""",
                        "map": {"1": {"X0": "A"}, "2": {"X0": "A"}},
                    }
                }
            },
        ),
    ],
)
def test_read_custom_conditions_2(condition, expected):
    """Check reading and parsing of CONTROL_CRITERIA keyword."""
    case = BASE_CASE + condition
    result = read_casefile.ICVReadCasefile(case).custom_conditions
    for key in expected.keys():
        assert result[key] == expected[key]


@pytest.mark.parametrize(
    "condition, expected_err",
    [
        (
            """
CONTROL_CRITERIA
  FUNCTION: DA_WO, NOT_METHOD -- malformed list + unknown method
  CRITERIA: not_a_number
  ICV: [A, F -- malformed list
  WWIR WELL(test) = WUMXVDJ2 WELL(test) AND /
/""",
            ValueError("Expected the value in criteria to be an integer, or a list of integers, got 'not_a_number'."),
        ),
        (
            """
CONTROL_CRITERIA
  FUNCTION: OPEN
  WWIR WELL(test) = WUMXVDJ2 WELL(test) AND /
/""",
            ValueError("The contents of CONTROL_CRITERIA was malformed. Missing information in the 'ICVS' field!"),
        ),
        (
            """
CONTROL_CRITERIA
/""",
            ValueError("The contents of CONTROL_CRITERIA was malformed. Missing information in the 'FUNCTION' field!"),
        ),
        (
            """ \t CONTROL_CRITERIA
  FUNCTION: [UDQ, OPEN] /
  ICV: [A, G]
    TEST COND TO ONLY REPLACE POS 1 /
    /""",
            ValueError("UDQ field needs a seperate CONTROL_CRITERIA keyword."),
        ),
    ],
)
def test_error_read_custom_conditions(condition, expected_err):
    """Check it covers the warnings when reading
    and parsing CONTROL_CRITERIA keyword."""
    case = BASE_CASE + condition
    with pytest.raises(ValueError) as e:
        read_casefile.ICVReadCasefile(case).custom_conditions
    assert str(expected_err) == str(e.value)


def test_create_step_table():
    """Test that the data from STEPS keyword in case file
    matches in icv_functions"""
    expected = pd.DataFrame(
        [[80, 30, 150, 20, 80, 20, 50, 50, 50]],
        columns=["A", "B", "C", "D", "H", "I", "E", "F", "G"],
    )

    result = read_casefile.ICVReadCasefile(BASE_CASE).step_table

    pd.testing.assert_frame_equal(result, expected, check_names=False, check_dtype=False)


def test_create_init_table():
    """Test that the data from STEPS keyword in case file
    matches in icv_functions"""
    expected = pd.DataFrame(
        [[0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09]],
        columns=["A", "B", "C", "D", "H", "I", "E", "F", "G"],
    )

    result = read_casefile.ICVReadCasefile(BASE_CASE_EXTENDED).init_table

    pd.testing.assert_frame_equal(result, expected, check_names=False)
