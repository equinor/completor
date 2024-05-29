"""Test functions for the Completor read_schedule module"""

from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

import completor.parse as fr
from completor import utils
from completor.read_schedule import ReadSchedule, fix_compsegs, fix_welsegs

_TESTDIR = Path(__file__).absolute().parent / "data"
with open(Path(_TESTDIR / "schedule.testfile"), encoding="utf-8") as file:
    _SCHEDULE = ReadSchedule(file.read())


def test_reading_welspecs():
    """Test the functions which read the WELSPECS keyword."""
    true_welspecs = StringIO(
        """
WELL,GROUP,I,J,BHP_DEPTH,PHASE,DR,FLAG,SHUT,CROSS,PRESSURETABLE,DENSCAL,REGION,ITEM14,\
ITEM15,ITEM16,ITEM17
'WELL1','GROUP1',13,75,1200,GAS,1*,1*,SHUT,1*,1*,1*,1*,1*,1*,1*,1*
'WELL2','GROUP1',18,37,1200,GAS,1*,1*,SHUT,1*,1*,1*,1*,1*,1*,1*,1*
'WELL3','GROUP1',23,40,1200,OIL,1*,1*,SHUT,1*,1*,1*,1*,1*,1*,1*,1*
'WELL4','GROUP1',18,32,1200,OIL,1*,1*,SHUT,1*,1*,1*,1*,1*,1*,1*,1*
'WELL5','GROUP1',16,47,1200,OIL,1*,1*,SHUT,1*,1*,1*,1*,1*,1*,1*,1*
'WELL6','GROUP1',20,91,1200,OIL,1*,1*,SHUT,1*,1*,1*,1*,1*,1*,1*,1*
'WELL7','GROUP2',12,75,1200,OIL,1*,1*,SHUT,1*,1*,1*,1*,1*,1*,1*,1*
'WELL8','GROUP2',16,73,1200,OIL,1*,1*,SHUT,1*,1*,1*,1*,1*,1*,1*,1*
'WELL9','GROUP2',17,102,1200,OIL,1*,1*,SHUT,1*,1*,1*,1*,1*,1*,1*,1*
'WELL10','GROUP2',20,31,1200,OIL,1*,1*,SHUT,1*,1*,1*,1*,1*,1*,1*,1*
'WELL11','GROUP2',12,44,1200,OIL,1*,1*,SHUT,1*,1*,1*,1*,1*,1*,1*,1*
'WELL12','GROUP2',9,41,1200,OIL,1*,1*,SHUT,1*,1*,1*,1*,1*,1*,1*,1*
    """
    )
    df_true = pd.read_csv(true_welspecs, sep=",")
    df_true = fr.remove_string_characters(df_true)
    df_true = df_true.astype(str)
    pd.testing.assert_frame_equal(df_true, _SCHEDULE.welspecs)


def test_reading_unused_keywords():
    """Test the function which reads the unused keywords."""
    true_unused = """
GRUPTREE
'GROUP1' 'MYGRP' /
'GROUP2' 'MYGRP' /
/
COMPORD
 'WELL1'  INPUT /
 'WELL2'  INPUT /
 'WELL3'  INPUT /
 'WELL4'  INPUT /
 'WELL5'  INPUT /
 'WELL6'  INPUT /
 'WELL7'  INPUT /
 'WELL8'  INPUT /
 'WELL9'  INPUT /
 'WELL10' INPUT /
 'WELL11' INPUT /
 'WELL12' INPUT /
/
    """
    true_unused = utils.clean_file_lines(true_unused.splitlines())
    np.testing.assert_array_equal(true_unused, _SCHEDULE.unused_keywords, "Failed reading unused keywords")


def test_reading_compdat():
    """
    Test the functions which read COMPDAT keywords.

    Test the whole COMPDAT and spesific on WELL10
    """
    true_compdat = Path(_TESTDIR / "compdat.true")
    df_true = pd.read_csv(true_compdat, sep=",", dtype=object)
    df_true = fr.remove_string_characters(df_true)
    columns1 = ["I", "J", "K", "K2"]
    columns2 = ["CF", "KH", "SKIN"]
    df_true[columns1] = df_true[columns1].astype(np.int64)
    df_true[columns2] = df_true[columns2].astype(np.float64)
    df_well10 = df_true[df_true["WELL"] == "WELL10"]
    df_well10.reset_index(drop=True, inplace=True)
    pd.testing.assert_frame_equal(df_true, _SCHEDULE.compdat)
    pd.testing.assert_frame_equal(df_well10, _SCHEDULE.get_compdat("WELL10"))


def test_reading_compsegs():
    """
    Test the functions which read the COMPSEGS keywords.

    Test it on WELL12 branch 1
    """
    true_compsegs = Path(_TESTDIR / "compsegs_well12.true")
    df_true = pd.read_csv(true_compsegs, sep=",", dtype=object)
    columns1 = ["I", "J", "K", "BRANCH"]
    columns2 = ["STARTMD", "ENDMD"]
    df_true[columns1] = df_true[columns1].astype(np.int64)
    df_true[columns2] = df_true[columns2].astype(np.float64)
    pd.testing.assert_frame_equal(df_true, _SCHEDULE.get_compsegs("WELL12", 1))


def test_reading_welsegs():
    """
    Test the functions which read WELSEGS keywords.

    Both the first and the second record
    check WELL4 for the second record
    """
    true_welsegs1 = StringIO(
        """
WELL,SEGMENTTVD,SEGMENTMD,WBVOLUME,INFOTYPE,PDROPCOMP,MPMODEL,ITEM8,ITEM9,ITEM10,\
ITEM11,ITEM12
'WELL3',1328,1328,1*,ABS,HFA,1*,1*,1*,1*,1*,1*
'WELL4',1316,1316,1*,ABS,HFA,1*,1*,1*,1*,1*,1*
'WELL5',1326.8,1326.8,1*,ABS,HFA,1*,1*,1*,1*,1*,1*
'WELL6',1350,1350,1*,ABS,HFA,1*,1*,1*,1*,1*,1*
'WELL7',1342.49,1342.49,1*,ABS,HFA,1*,1*,1*,1*,1*,1*
'WELL8',1340.6,1340.6,1*,ABS,HFA,1*,1*,1*,1*,1*,1*
'WELL9',1336,1336,1*,ABS,HFA,1*,1*,1*,1*,1*,1*
'WELL10',1331,1331,1*,ABS,HFA,1*,1*,1*,1*,1*,1*
'WELL11',1325,1325,1*,ABS,HFA,1*,1*,1*,1*,1*,1*
'WELL12',1335,1335,1*,ABS,HFA,1*,1*,1*,1*,1*,1*
    """
    )
    true_well4 = Path(_TESTDIR / "welsegs_well4.true")
    true_welsegs1 = pd.read_csv(true_welsegs1, sep=",", dtype=object)
    true_welsegs1 = fr.remove_string_characters(true_welsegs1)
    true_welsegs1 = true_welsegs1.astype({"SEGMENTTVD": np.float64, "SEGMENTMD": np.float64})
    true_well4 = str(_TESTDIR / "welsegs_well4.true")
    true_well4 = pd.read_csv(true_well4, sep=",", dtype=object)
    true_well4 = fr.remove_string_characters(true_well4)
    true_well4 = true_well4.astype(
        {
            "TUBINGSEGMENT": np.int64,
            "TUBINGSEGMENT2": np.int64,
            "TUBINGBRANCH": np.int64,
            "TUBINGOUTLET": np.int64,
            "TUBINGMD": np.float64,
            "TUBINGTVD": np.float64,
            "TUBINGROUGHNESS": np.float64,
        }
    )
    true_welsegs1_well4 = true_welsegs1[true_welsegs1["WELL"] == "WELL4"]
    true_welsegs1_well4.reset_index(drop=True, inplace=True)

    # get the program reading
    well4_first, well4_second = _SCHEDULE.get_welsegs("WELL4", 1)

    pd.testing.assert_frame_equal(true_welsegs1, _SCHEDULE.welsegs_header)
    pd.testing.assert_frame_equal(true_welsegs1_well4, well4_first)
    pd.testing.assert_frame_equal(true_well4, well4_second)


def test_reading_wsegvalv():
    """Test the functions which read the WSEGVALV keyword."""
    true_wsegvalv = StringIO(
        """
WELL,SEGMENT,CD,AC,DEFAULT_1,DEFAULT_2,DEFAULT_3,DEFAULT_4,STATE,AC_MAX
WELL1,0,0.830,1.0000E-03,1*,1*,1*,1*,OPEN,1.0000E-03
WELL1,1,0.830,1.0000E-02,1*,1*,1*,1*,SHUT,2.0000E-02
WELL2,5,1,5e-3,1*,1*,1*,1*,OPEN,6e-3
WELL2,56,1,5e-4,1*,1*,1*,1*,OPEN,7e-4
WELL3,12,0.830,1.2E-03,1*,1*,1*,1*,OPEN,1.2E-03
WELL3,87,0.830,1.2E-03,1*,1*,1*,1*,OPEN,1.2E-03
WELL3,145,0.830,6.0E-03,1*,1*,1*,1*,OPEN,6E-03
        """
    )
    df_true = pd.read_csv(true_wsegvalv, sep=",")
    df_true = fr.remove_string_characters(df_true)
    df_true = df_true.astype(
        {
            "WELL": "string",
            "SEGMENT": "int",
            "CD": "float",
            "AC": "float",
            "DEFAULT_1": "string",
            "DEFAULT_2": "string",
            "DEFAULT_3": "string",
            "DEFAULT_4": "string",
            "STATE": "string",
            "AC_MAX": "float",
        }
    )
    pd.testing.assert_frame_equal(df_true, _SCHEDULE.wsegvalv)


def test_fix_compsegs():
    """
    Test that fix_compsegs correctly assigns start and end measured depths.

    In cases where there are overlapping segments in compsegs, also test zero
    length segments.
    """
    df_test = pd.DataFrame(
        [
            [3000.82607, 3026.67405],
            [2984.458, 3006.55],
            [3006.55, 3013.000],
            [3013.147, 3013.147],
            [3014.000, 3019.764],
            [3019.764, 3039.297],
            [3039.297, 3041.915],
        ],
        columns=["STARTMD", "ENDMD"],
    )

    df_true = pd.DataFrame(
        [
            [2984.458, 3000.82607],
            [3000.82607, 3013],
            [3013, 3013.147],
            [3013.147, 3014],
            [3014, 3026.67405],
            [3026.67405, 3039.297],
            [3039.297, 3041.915],
        ],
        columns=["STARTMD", "ENDMD"],
    )
    df_test = fix_compsegs(df_test, "")
    pd.testing.assert_frame_equal(df_true, df_test)


def test_fix_welsegs():
    """
    Test that fix_welsegs correctly converts WELSEGS from INC to ABS.

    Completor works with ABS in the WELSEGS.
    So if the users have WELSEGS defined in INC then it must be converted first.
    """
    df_header = pd.DataFrame(
        [[1000.0, 1500.0, "INC"]],
        columns=["SEGMENTTVD", "SEGMENTMD", "INFOTYPE"],
    )
    df_content = pd.DataFrame(
        [
            [2, 1, 10.0, 50.0],
            [3, 2, 20.0, 20.0],
            [4, 3, 30.0, 30.0],
            [5, 4, 40.0, 40.0],
        ],
        columns=["TUBINGSEGMENT", "TUBINGOUTLET", "TUBINGTVD", "TUBINGMD"],
    )

    df_header_true = pd.DataFrame(
        [[1000.0, 1500.0, "ABS"]],
        columns=["SEGMENTTVD", "SEGMENTMD", "INFOTYPE"],
    )
    df_content_true = pd.DataFrame(
        [
            [2, 1, 1010.0, 1550.0],
            [3, 2, 1030.0, 1570.0],
            [4, 3, 1060.0, 1600.0],
            [5, 4, 1100.0, 1640.0],
        ],
        columns=["TUBINGSEGMENT", "TUBINGOUTLET", "TUBINGTVD", "TUBINGMD"],
    )

    df_header, df_content = fix_welsegs(df_header, df_content)
    pd.testing.assert_frame_equal(df_header_true, df_header)
    pd.testing.assert_frame_equal(df_content_true, df_content)
