"""Test functions for the Completor read_schedule module."""

from pathlib import Path

import numpy as np
import pandas as pd
from utils_for_tests import ReadSchedule

from completor import parse, utils
from completor.constants import Headers
from completor.read_schedule import fix_compsegs, fix_welsegs

_TESTDIR = Path(__file__).absolute().parent / "data"
with open(Path(_TESTDIR / "schedule.testfile"), encoding="utf-8") as file:
    _SCHEDULE = ReadSchedule(file.read())


def test_reading_welspecs():
    """Test the functions which read the WELL_SPECIFICATION keyword."""
    data = [
        ["WELL1", "GROUP1", 13, 75, 1200, "GAS", "1*", "1*", "SHUT", "1*", "1*", "1*", "1*", "1*", "1*", "1*", "1*"],
        ["WELL2", "GROUP1", 18, 37, 1200, "GAS", "1*", "1*", "SHUT", "1*", "1*", "1*", "1*", "1*", "1*", "1*", "1*"],
        ["WELL3", "GROUP1", 23, 40, 1200, "OIL", "1*", "1*", "SHUT", "1*", "1*", "1*", "1*", "1*", "1*", "1*", "1*"],
        ["WELL4", "GROUP1", 18, 32, 1200, "OIL", "1*", "1*", "SHUT", "1*", "1*", "1*", "1*", "1*", "1*", "1*", "1*"],
        ["WELL5", "GROUP1", 16, 47, 1200, "OIL", "1*", "1*", "SHUT", "1*", "1*", "1*", "1*", "1*", "1*", "1*", "1*"],
        ["WELL6", "GROUP1", 20, 91, 1200, "OIL", "1*", "1*", "SHUT", "1*", "1*", "1*", "1*", "1*", "1*", "1*", "1*"],
        ["WELL7", "GROUP2", 12, 75, 1200, "OIL", "1*", "1*", "SHUT", "1*", "1*", "1*", "1*", "1*", "1*", "1*", "1*"],
        ["WELL8", "GROUP2", 16, 73, 1200, "OIL", "1*", "1*", "SHUT", "1*", "1*", "1*", "1*", "1*", "1*", "1*", "1*"],
        ["WELL9", "GROUP2", 17, 102, 1200, "OIL", "1*", "1*", "SHUT", "1*", "1*", "1*", "1*", "1*", "1*", "1*", "1*"],
        ["WELL10", "GROUP2", 20, 31, 1200, "OIL", "1*", "1*", "SHUT", "1*", "1*", "1*", "1*", "1*", "1*", "1*", "1*"],
        ["WELL11", "GROUP2", 12, 44, 1200, "OIL", "1*", "1*", "SHUT", "1*", "1*", "1*", "1*", "1*", "1*", "1*", "1*"],
        ["WELL12", "GROUP2", 9, 41, 1200, "OIL", "1*", "1*", "SHUT", "1*", "1*", "1*", "1*", "1*", "1*", "1*", "1*"],
    ]
    df_true = pd.DataFrame(
        data=data,
        columns=[
            Headers.WELL,
            Headers.GROUP,
            Headers.I,
            Headers.J,
            Headers.BHP_DEPTH,
            Headers.PHASE,
            Headers.DR,
            Headers.FLAG,
            Headers.SHUT,
            Headers.FLOW_CROSS_SECTIONAL_AREA,
            Headers.PRESSURE_TABLE,
            Headers.DENSITY_CALCULATION_TYPE,
            Headers.REGION,
            Headers.RESERVED_HEADER_1,
            Headers.RESERVED_HEADER_2,
            Headers.WELL_MODEL_TYPE,
            Headers.POLYMER_MIXING_TABLE_NUMBER,
        ],
    )
    df_true = parse.remove_string_characters(df_true)
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
    """Test the functions which read COMPLETION_DATA keywords.

    Test the whole COMPLETION_DATA and specific on WELL10.
    """
    true_compdat = Path(_TESTDIR / "compdat.true")
    df_true = pd.read_csv(true_compdat, sep=",", dtype=object)
    df_true = parse.remove_string_characters(df_true)
    columns1 = [Headers.I, Headers.J, Headers.K, Headers.K2]
    columns2 = [Headers.CONNECTION_FACTOR, Headers.FORMATION_PERMEABILITY_THICKNESS, Headers.SKIN]
    df_true[columns1] = df_true[columns1].astype(np.int64)
    df_true[columns2] = df_true[columns2].astype(np.float64)
    df_well10 = df_true[df_true[Headers.WELL] == "WELL10"]
    df_well10.reset_index(drop=True, inplace=True)
    pd.testing.assert_frame_equal(df_true, _SCHEDULE.compdat)
    pd.testing.assert_frame_equal(df_well10, _SCHEDULE.get_compdat("WELL10"))


def test_reading_compsegs():
    """Test the functions which read the COMPLETION_SEGMENTS keywords.

    Test it on WELL12 branch 1.
    """
    true_compsegs = Path(_TESTDIR / "compsegs_well12.true")
    df_true = pd.read_csv(true_compsegs, sep=",", dtype=object)
    columns1 = [Headers.I, Headers.J, Headers.K, Headers.BRANCH]
    columns2 = [Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH]
    df_true[columns1] = df_true[columns1].astype(np.int64)
    df_true[columns2] = df_true[columns2].astype(np.float64)
    pd.testing.assert_frame_equal(df_true, _SCHEDULE.get_compsegs("WELL12", 1))


def test_reading_welsegs():
    """Test the functions which read WELL_SEGMENTS keywords.

    Both the first and the second record.
    Check WELL4 for the second record.
    """
    true_welsegs1 = pd.DataFrame(
        [
            ["WELL3", 1328, 1328, "1*", "ABS", "HFA", "1*", "1*", "1*", "1*", "1*", "1*"],
            ["WELL4", 1316, 1316, "1*", "ABS", "HFA", "1*", "1*", "1*", "1*", "1*", "1*"],
            ["WELL5", 1326.8, 1326.8, "1*", "ABS", "HFA", "1*", "1*", "1*", "1*", "1*", "1*"],
            ["WELL6", 1350, 1350, "1*", "ABS", "HFA", "1*", "1*", "1*", "1*", "1*", "1*"],
            ["WELL7", 1342.49, 1342.49, "1*", "ABS", "HFA", "1*", "1*", "1*", "1*", "1*", "1*"],
            ["WELL8", 1340.6, 1340.6, "1*", "ABS", "HFA", "1*", "1*", "1*", "1*", "1*", "1*"],
            ["WELL9", 1336, 1336, "1*", "ABS", "HFA", "1*", "1*", "1*", "1*", "1*", "1*"],
            ["WELL10", 1331, 1331, "1*", "ABS", "HFA", "1*", "1*", "1*", "1*", "1*", "1*"],
            ["WELL11", 1325, 1325, "1*", "ABS", "HFA", "1*", "1*", "1*", "1*", "1*", "1*"],
            ["WELL12", 1335, 1335, "1*", "ABS", "HFA", "1*", "1*", "1*", "1*", "1*", "1*"],
        ],
        columns=[
            Headers.WELL,
            Headers.TRUE_VERTICAL_DEPTH,
            Headers.MEASURED_DEPTH,
            Headers.WELLBORE_VOLUME,
            Headers.INFO_TYPE,
            Headers.PRESSURE_DROP_COMPLETION,
            Headers.MULTIPHASE_FLOW_MODEL,
            Headers.X_COORDINATE_TOP_SEGMENT,
            Headers.Y_COORDINATE_TOP_SEGMENT,
            Headers.THERMAL_CONDUCTIVITY_CROSS_SECTIONAL_AREA,
            Headers.VOLUMETRIC_HEAT_CAPACITY_PIPE_WALL,
            Headers.THERMAL_CONDUCTIVITY_PIPE_WALL,
        ],
    )
    true_welsegs1 = parse.remove_string_characters(true_welsegs1)
    true_welsegs1 = true_welsegs1.astype({Headers.TRUE_VERTICAL_DEPTH: np.float64, Headers.MEASURED_DEPTH: np.float64})
    true_well4 = Path(_TESTDIR / "welsegs_well4.true")
    true_well4 = pd.read_csv(true_well4, sep=",", dtype=object)
    true_well4 = parse.remove_string_characters(true_well4)
    true_well4 = true_well4.astype(
        {
            Headers.TUBING_SEGMENT: np.int64,
            Headers.TUBING_SEGMENT_2: np.int64,
            Headers.TUBING_BRANCH: np.int64,
            Headers.TUBING_OUTLET: np.int64,
            Headers.TUBING_MEASURED_DEPTH: np.float64,
            Headers.TRUE_VERTICAL_DEPTH: np.float64,
            Headers.TUBING_ROUGHNESS: np.float64,
        }
    )
    true_welsegs1_well4 = true_welsegs1[true_welsegs1[Headers.WELL] == "WELL4"]
    true_welsegs1_well4 = true_welsegs1_well4.reset_index(drop=True)

    # get the program reading
    well4_first, well4_second = _SCHEDULE.get_welsegs("WELL4", 1)

    pd.testing.assert_frame_equal(true_welsegs1, _SCHEDULE.welsegs_header)
    pd.testing.assert_frame_equal(true_welsegs1_well4, well4_first)
    pd.testing.assert_frame_equal(true_well4, well4_second)


def test_reading_wsegvalv():
    """Test the functions which read the WELL_SEGMENTS_VALVE keyword."""
    df_true = pd.DataFrame(
        [
            ["WELL1", 0, 0.830, 1.0000e-03, "1*", "1*", "1*", "1*", "OPEN", 1.0000e-03],
            ["WELL1", 1, 0.830, 1.0000e-02, "1*", "1*", "1*", "1*", "SHUT", 2.0000e-02],
            ["WELL2", 5, 1, 5e-3, "1*", "1*", "1*", "1*", "OPEN", 6e-3],
            ["WELL2", 56, 1, 5e-4, "1*", "1*", "1*", "1*", "OPEN", 7e-4],
            ["WELL3", 12, 0.830, 1.2e-03, "1*", "1*", "1*", "1*", "OPEN", 1.2e-03],
            ["WELL3", 87, 0.830, 1.2e-03, "1*", "1*", "1*", "1*", "OPEN", 1.2e-03],
            ["WELL3", 145, 0.830, 6.0e-03, "1*", "1*", "1*", "1*", "OPEN", 6e-03],
        ],
        columns=[
            Headers.WELL,
            Headers.SEGMENT,
            Headers.FLOW_COEFFICIENT,
            Headers.FLOW_CROSS_SECTIONAL_AREA,
            Headers.ADDITIONAL_PIPE_LENGTH_FRICTION_PRESSURE_DROP,
            Headers.PIPE_DIAMETER,
            Headers.ABSOLUTE_PIPE_ROUGHNESS,
            Headers.PIPE_CROSS_SECTION_AREA,
            Headers.FLAG,
            Headers.MAX_FLOW_CROSS_SECTIONAL_AREA,
        ],
    )
    df_true = parse.remove_string_characters(df_true)
    df_true = df_true.astype(
        {
            Headers.WELL: "string",
            Headers.SEGMENT: "int",
            Headers.FLOW_COEFFICIENT: "float",
            Headers.FLOW_CROSS_SECTIONAL_AREA: "float",
            Headers.ADDITIONAL_PIPE_LENGTH_FRICTION_PRESSURE_DROP: "string",
            Headers.PIPE_DIAMETER: "string",
            Headers.ABSOLUTE_PIPE_ROUGHNESS: "string",
            Headers.PIPE_CROSS_SECTION_AREA: "string",
            Headers.FLAG: "string",
            Headers.MAX_FLOW_CROSS_SECTIONAL_AREA: "float",
        }
    )
    pd.testing.assert_frame_equal(df_true, _SCHEDULE.wsegvalv)


def test_fix_compsegs():
    """Test that fix_compsegs correctly assigns start and end measured depths.

    In cases where there are overlapping segments in compsegs, also test zero length segments.
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
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
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
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
    )
    df_test = fix_compsegs(df_test, "")
    pd.testing.assert_frame_equal(df_true, df_test)


def test_fix_welsegs():
    """Test that fix_welsegs correctly converts WELL_SEGMENTS from INC to ABS.

    Completor works with ABS in the WELL_SEGMENTS.
    So if the users have WELL_SEGMENTS defined in INC then it must be converted first.
    """
    df_header = pd.DataFrame(
        [[1000.0, 1500.0, "INC"]],
        columns=[Headers.TRUE_VERTICAL_DEPTH, Headers.MEASURED_DEPTH, Headers.INFO_TYPE],
    )
    df_content = pd.DataFrame(
        [
            [2, 1, 10.0, 50.0],
            [3, 2, 20.0, 20.0],
            [4, 3, 30.0, 30.0],
            [5, 4, 40.0, 40.0],
        ],
        columns=[
            Headers.TUBING_SEGMENT,
            Headers.TUBING_OUTLET,
            Headers.TRUE_VERTICAL_DEPTH,
            Headers.TUBING_MEASURED_DEPTH,
        ],
    )

    df_header_true = pd.DataFrame(
        [[1000.0, 1500.0, "ABS"]],
        columns=[Headers.TRUE_VERTICAL_DEPTH, Headers.MEASURED_DEPTH, Headers.INFO_TYPE],
    )
    df_content_true = pd.DataFrame(
        [
            [2, 1, 1010.0, 1550.0],
            [3, 2, 1030.0, 1570.0],
            [4, 3, 1060.0, 1600.0],
            [5, 4, 1100.0, 1640.0],
        ],
        columns=[
            Headers.TUBING_SEGMENT,
            Headers.TUBING_OUTLET,
            Headers.TRUE_VERTICAL_DEPTH,
            Headers.TUBING_MEASURED_DEPTH,
        ],
    )

    df_header, df_content = fix_welsegs(df_header, df_content)
    pd.testing.assert_frame_equal(df_header_true, df_header)
    pd.testing.assert_frame_equal(df_content_true, df_content)
