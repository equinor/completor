"""Test functions for the Completor prepare_outputs module."""

import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import utils_for_tests

from completor import prepare_outputs
from completor.constants import Content, Headers, Keywords

_TESTDIR = Path(__file__).absolute().parent / "data"
_TEST_FILE = "test.sch"


def test_trim_pandas():
    """Test the function to trim DataFrames with default values."""
    df_test = pd.DataFrame([[1, 2, 3, "1*", 5, 6], [1, 2, "5*", 3, 4, 5]])
    df_true = pd.DataFrame(
        [
            [1, 2, 3, "1*", 5, 6],
            [1, 2, "5*", 3, 4, 5],
        ]
    )
    df_test = prepare_outputs.trim_pandas(df_test)
    pd.testing.assert_frame_equal(df_test, df_true)

    df_test = pd.DataFrame(
        [
            ["1*", 2, 3, "1*", 5, "5*"],
            [1, 2, "5*", 3, 4, "20*"],
        ]
    )
    df_true = pd.DataFrame(
        [
            ["1*", 2, 3, "1*", 5],
            [1, 2, "5*", 3, 4],
        ]
    )
    df_test = prepare_outputs.trim_pandas(df_test)
    pd.testing.assert_frame_equal(df_test, df_true)

    df_test = pd.DataFrame([["1*", 2, 3, "1*", "2*", "5*"], [1, 2, "5*", 3, "1*", "20*"]])
    df_true = pd.DataFrame([["1*", 2, 3, "1*"], [1, 2, "5*", 3]])
    df_test = prepare_outputs.trim_pandas(df_test)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_add_columns_first_last():
    """Test the function which adds first and last column."""
    df_test = pd.DataFrame([[1, 2, 3, "1*", 5, 6], [1, 2, "5*", 3, 4, 5]], columns=["A", "B", "C", "D", "E", "F"])
    df_true_first_last = pd.DataFrame(
        [[" ", 1, 2, 3, "1*", 5, 6, "/"], [" ", 1, 2, "5*", 3, 4, 5, "/"]],
        columns=["--", "A", "B", "C", "D", "E", "F", Headers.EMPTY],
    )
    df_true_only_first = pd.DataFrame(
        [[" ", 1, 2, 3, "1*", 5, 6], [" ", 1, 2, "5*", 3, 4, 5]], columns=["--", "A", "B", "C", "D", "E", "F"]
    )

    df_test_first_last = prepare_outputs.add_columns_first_last(df_test, True, True)
    df_test_only_first = prepare_outputs.add_columns_first_last(df_test, True, False)
    pd.testing.assert_frame_equal(df_test_first_last, df_true_first_last)
    pd.testing.assert_frame_equal(df_test_only_first, df_true_only_first)


def test_dataframe_to_string():
    """Test the function which converts data frame to string."""
    df_test_utils = pd.DataFrame([[1, 2, 3, "1*", 5, 6], [1, 2, "5*", 3, 4, 5]], columns=["A", "B", "C", "D", "E", "F"])
    df_true_utils = pd.DataFrame(
        [[" ", 1, 2, 3, "1*", 5, 6, "/"], [" ", 1, 2, "5*", 3, 4, 5, "/"]],
        columns=["--", "A", "B", "C", "D", "E", "F", Headers.EMPTY],
    )

    df_test_default = prepare_outputs.dataframe_tostring(df_test_utils)
    df_true_default = df_true_utils.to_string(index=False, justify="justify")
    assert df_test_default == df_true_default


def test_outlet_segment_1():
    """Test outlet_segment find the outlet segments closest to target measured depths."""
    target_md = [1, 2, 3, 4.0]
    reference_md = [0.5, 1.0, 2.0, 4.0, 5.0]
    reference_segment_number = [1, 2, 3, 4, 5]

    test_segment = prepare_outputs.get_outlet_segment(target_md, reference_md, reference_segment_number)
    np.testing.assert_equal(test_segment, [2, 3, 3, 4])


def test_outlet_segment_2():
    """Test outlet_segment find the outlet segments closest to target measured depths."""
    target_md = [1, 2, 4.0, 5.0]
    reference_md = [0.5, 1.0, 2.0, 4.0, 5.0]
    reference_segment = [1, 2, 3, 4, 5]

    test_segment = prepare_outputs.get_outlet_segment(target_md, reference_md, reference_segment)
    np.testing.assert_equal(test_segment, [2, 3, 4, 5])


@pytest.mark.parametrize(
    "segment_length,df_device,df_annulus,df_completion,expected",
    [
        pytest.param(
            1.0,
            pd.DataFrame(
                [
                    [4, 4, 1, 2, 1500.0, 1500.0, 0.15, 0.00065],
                    [5, 5, 1, 3, 2500.0, 2500.0, 0.15, 0.00065],
                ],
                columns=[
                    Headers.START_SEGMENT_NUMBER,
                    Headers.END_SEGMENT_NUMBER,
                    Headers.BRANCH,
                    Headers.OUT,
                    Headers.MEASURED_DEPTH,
                    Headers.TRUE_VERTICAL_DEPTH,
                    Headers.WELL_BORE_DIAMETER,
                    Headers.ROUGHNESS,
                ],
            ),
            pd.DataFrame([], columns=[]),
            pd.DataFrame(
                [
                    [1000.0, 2000.0, 1500.0, 1500.0, Headers.ORIGINAL_SEGMENT, 1, Content.PERFORATED, "GP"],
                    [2000.0, 3000.0, 2500.0, 2500.0, Headers.ORIGINAL_SEGMENT, 1, Content.PERFORATED, "GP"],
                ],
                columns=[
                    Headers.START_MEASURED_DEPTH,
                    Headers.END_MEASURED_DEPTH,
                    Headers.TUBING_MEASURED_DEPTH,
                    Headers.TRUE_VERTICAL_DEPTH,
                    Headers.SEGMENT_DESC,
                    Headers.VALVES_PER_JOINT,
                    Headers.DEVICE_TYPE,
                    Headers.ANNULUS,
                ],
            ),
            pd.DataFrame(
                [
                    [1, 1, 1, 1, 1000.0, 1500.0, "1*", "3*", 4, "/"],
                    [1, 1, 2, 1, 1500.0, 2000.0, "1*", "3*", 4, "/"],
                    [1, 1, 3, 1, 2000.0, 2500.0, "1*", "3*", 5, "/"],
                    [1, 1, 4, 1, 2500.0, 3000.0, "1*", "3*", 5, "/"],
                ],
                columns=[
                    Headers.I,
                    Headers.J,
                    Headers.K,
                    Headers.BRANCH,
                    Headers.START_MEASURED_DEPTH,
                    Headers.END_MEASURED_DEPTH,
                    Headers.COMPSEGS_DIRECTION,
                    Headers.DEF,
                    Headers.START_SEGMENT_NUMBER,
                    Headers.EMPTY,
                ],
            ),
            id="Positive segment length, no annulus zone",
        ),
        pytest.param(
            -1.0,
            pd.DataFrame(
                [
                    [4, 4, 1, 2, 1250.0, 1250.0, 0.15, 0.00065],
                    [5, 5, 1, 3, 2250.0, 2250.0, 0.15, 0.00065],
                ],
                columns=[
                    Headers.START_SEGMENT_NUMBER,
                    Headers.END_SEGMENT_NUMBER,
                    Headers.BRANCH,
                    Headers.OUT,
                    Headers.MEASURED_DEPTH,
                    Headers.TRUE_VERTICAL_DEPTH,
                    Headers.WELL_BORE_DIAMETER,
                    Headers.ROUGHNESS,
                ],
            ),
            pd.DataFrame([], columns=[]),
            pd.DataFrame(
                [
                    [1000.0, 1500.0, 1250.0, 1250.0, Headers.ORIGINAL_SEGMENT, "GP", 1, Content.PERFORATED],
                    [1500.0, 3000.0, 2250.0, 2250.0, Headers.ORIGINAL_SEGMENT, "GP", 1, Content.PERFORATED],
                ],
                columns=[
                    Headers.START_MEASURED_DEPTH,
                    Headers.END_MEASURED_DEPTH,
                    Headers.TUBING_MEASURED_DEPTH,
                    Headers.TRUE_VERTICAL_DEPTH,
                    Headers.SEGMENT_DESC,
                    Headers.ANNULUS,
                    Headers.VALVES_PER_JOINT,
                    Headers.DEVICE_TYPE,
                ],
            ),
            pd.DataFrame(
                [
                    [1, 1, 1, 1, 1000.0, 1500.0, "1*", "3*", 4, "/"],
                    [1, 1, 2, 1, 1500.0, 2000.0, "1*", "3*", 5, "/"],
                    [1, 1, 3, 1, 2000.0, 2500.0, "1*", "3*", 5, "/"],
                    [1, 1, 4, 1, 2500.0, 3000.0, "1*", "3*", 5, "/"],
                ],
                columns=[
                    Headers.I,
                    Headers.J,
                    Headers.K,
                    Headers.BRANCH,
                    Headers.START_MEASURED_DEPTH,
                    Headers.END_MEASURED_DEPTH,
                    Headers.COMPSEGS_DIRECTION,
                    Headers.DEF,
                    Headers.START_SEGMENT_NUMBER,
                    Headers.EMPTY,
                ],
            ),
            id="Negative segment length, no annulus zone",
        ),
        pytest.param(
            1.0,
            pd.DataFrame(
                [
                    [4, 4, 1, 2, 1500.0, 1500.0, 0.15, 0.00065],
                    [5, 5, 1, 3, 2500.0, 2500.0, 0.15, 0.00065],
                ],
                columns=[
                    Headers.START_SEGMENT_NUMBER,
                    Headers.END_SEGMENT_NUMBER,
                    Headers.BRANCH,
                    Headers.OUT,
                    Headers.MEASURED_DEPTH,
                    Headers.TRUE_VERTICAL_DEPTH,
                    Headers.WELL_BORE_DIAMETER,
                    Headers.ROUGHNESS,
                ],
            ),
            pd.DataFrame(
                [
                    [6, 6, 1, 2, 1500.0, 1500.0, 0.15, 0.0001, "/"],
                    [7, 7, 1, 3, 2500.0, 2500.0, 0.15, 0.0001, "/"],
                ],
                columns=[
                    Headers.START_SEGMENT_NUMBER,
                    Headers.END_SEGMENT_NUMBER,
                    Headers.BRANCH,
                    Headers.OUT,
                    Headers.MEASURED_DEPTH,
                    Headers.TRUE_VERTICAL_DEPTH,
                    Headers.WELL_BORE_DIAMETER,
                    Headers.ROUGHNESS,
                    Headers.EMPTY,
                ],
            ),
            pd.DataFrame(
                [
                    [1000.0, 2000.0, 1500.0, 1500.0, Headers.ORIGINAL_SEGMENT, 1, "GP", Content.INFLOW_CONTROL_DEVICE],
                    [2000.0, 3000.0, 2500.0, 2500.0, Headers.ORIGINAL_SEGMENT, 1, "GP", Content.INFLOW_CONTROL_DEVICE],
                ],
                columns=[
                    Headers.START_MEASURED_DEPTH,
                    Headers.END_MEASURED_DEPTH,
                    Headers.TUBING_MEASURED_DEPTH,
                    Headers.TRUE_VERTICAL_DEPTH,
                    Headers.SEGMENT_DESC,
                    Headers.VALVES_PER_JOINT,
                    Headers.ANNULUS,
                    Headers.DEVICE_TYPE,
                ],
            ),
            pd.DataFrame(
                [
                    [1, 1, 1, 1, 1000.0, 1500.0, "1*", "3*", 4, "/"],
                    [1, 1, 2, 1, 1500.0, 2000.0, "1*", "3*", 4, "/"],
                    [1, 1, 3, 1, 2000.0, 2500.0, "1*", "3*", 5, "/"],
                    [1, 1, 4, 1, 2500.0, 3000.0, "1*", "3*", 5, "/"],
                ],
                columns=[
                    Headers.I,
                    Headers.J,
                    Headers.K,
                    Headers.BRANCH,
                    Headers.START_MEASURED_DEPTH,
                    Headers.END_MEASURED_DEPTH,
                    Headers.COMPSEGS_DIRECTION,
                    Headers.DEF,
                    Headers.START_SEGMENT_NUMBER,
                    Headers.EMPTY,
                ],
            ),
            id="Positive segment length with annulus zone",
        ),
        pytest.param(
            -1.0,
            pd.DataFrame(
                [
                    [4, 4, 1, 2, 1250.0, 1250.0, 0.15, 0.00065],
                    [5, 5, 1, 3, 2250.0, 2250.0, 0.15, 0.00065],
                ],
                columns=[
                    Headers.START_SEGMENT_NUMBER,
                    Headers.END_SEGMENT_NUMBER,
                    Headers.BRANCH,
                    Headers.OUT,
                    Headers.MEASURED_DEPTH,
                    Headers.TRUE_VERTICAL_DEPTH,
                    Headers.WELL_BORE_DIAMETER,
                    Headers.ROUGHNESS,
                ],
            ),
            pd.DataFrame(
                [
                    [6, 6, 1, 2, 1250.0, 1250.0, 0.15, 0.0001, "/"],
                    [7, 7, 1, 3, 2250.0, 2250.0, 0.15, 0.0001, "/"],
                ],
                columns=[
                    Headers.START_SEGMENT_NUMBER,
                    Headers.END_SEGMENT_NUMBER,
                    Headers.BRANCH,
                    Headers.OUT,
                    Headers.MEASURED_DEPTH,
                    Headers.TRUE_VERTICAL_DEPTH,
                    Headers.WELL_BORE_DIAMETER,
                    Headers.ROUGHNESS,
                    Headers.EMPTY,
                ],
            ),
            pd.DataFrame(
                [
                    [
                        1000.0,
                        1500.0,
                        1300.0,
                        1300.0,
                        Headers.ORIGINAL_SEGMENT,
                        Content.OPEN_ANNULUS,
                        1,
                        Content.PERFORATED,
                    ],
                    [
                        1500.0,
                        3000.0,
                        2250.0,
                        2250.0,
                        Headers.ORIGINAL_SEGMENT,
                        Content.OPEN_ANNULUS,
                        1,
                        Content.PERFORATED,
                    ],
                ],
                columns=[
                    Headers.START_MEASURED_DEPTH,
                    Headers.END_MEASURED_DEPTH,
                    Headers.TUBING_MEASURED_DEPTH,
                    Headers.TRUE_VERTICAL_DEPTH,
                    Headers.SEGMENT_DESC,
                    Headers.ANNULUS,
                    Headers.VALVES_PER_JOINT,
                    Headers.DEVICE_TYPE,
                ],
            ),
            pd.DataFrame(
                [
                    [1, 1, 1, 1, 1000.0, 1500.0, "1*", "3*", 4, "/"],
                    [1, 1, 2, 1, 1500.0, 2000.0, "1*", "3*", 5, "/"],
                    [1, 1, 3, 1, 2000.0, 2500.0, "1*", "3*", 5, "/"],
                    [1, 1, 4, 1, 2500.0, 3000.0, "1*", "3*", 5, "/"],
                ],
                columns=[
                    Headers.I,
                    Headers.J,
                    Headers.K,
                    Headers.BRANCH,
                    Headers.START_MEASURED_DEPTH,
                    Headers.END_MEASURED_DEPTH,
                    Headers.COMPSEGS_DIRECTION,
                    Headers.DEF,
                    Headers.START_SEGMENT_NUMBER,
                    Headers.EMPTY,
                ],
            ),
            id="Negative segment length with annulus zone",
        ),
        pytest.param(
            Keywords.WELL_SEGMENTS,
            pd.DataFrame(
                [
                    [4, 4, 1, 2, 1500.0, 1500.0, 0.15, 0.00065],
                    [5, 5, 1, 3, 2500.0, 2500.0, 0.15, 0.00065],
                ],
                columns=[
                    Headers.START_SEGMENT_NUMBER,
                    Headers.END_SEGMENT_NUMBER,
                    Headers.BRANCH,
                    Headers.OUT,
                    Headers.MEASURED_DEPTH,
                    Headers.TRUE_VERTICAL_DEPTH,
                    Headers.WELL_BORE_DIAMETER,
                    Headers.ROUGHNESS,
                ],
            ),
            pd.DataFrame(
                [
                    [6, 6, 1, 2, 1500.0, 1500.0, 0.15, 0.0001, "/"],
                    [7, 7, 1, 3, 2500.0, 2500.0, 0.15, 0.0001, "/"],
                ],
                columns=[
                    Headers.START_SEGMENT_NUMBER,
                    Headers.END_SEGMENT_NUMBER,
                    Headers.BRANCH,
                    Headers.OUT,
                    Headers.MEASURED_DEPTH,
                    Headers.TRUE_VERTICAL_DEPTH,
                    Headers.WELL_BORE_DIAMETER,
                    Headers.ROUGHNESS,
                    Headers.EMPTY,
                ],
            ),
            pd.DataFrame(
                [
                    [1000.0, 2000.0, 1500.0, 1500.0, Headers.ORIGINAL_SEGMENT, "GP", 1, Content.INFLOW_CONTROL_DEVICE],
                    [2000.0, 3000.0, 2500.0, 2500.0, Headers.ORIGINAL_SEGMENT, "GP", 1, Content.INFLOW_CONTROL_DEVICE],
                ],
                columns=[
                    Headers.START_MEASURED_DEPTH,
                    Headers.END_MEASURED_DEPTH,
                    Headers.TUBING_MEASURED_DEPTH,
                    Headers.TRUE_VERTICAL_DEPTH,
                    Headers.SEGMENT_DESC,
                    Headers.ANNULUS,
                    Headers.VALVES_PER_JOINT,
                    Headers.DEVICE_TYPE,
                ],
            ),
            pd.DataFrame(
                [
                    [1, 1, 1, 1, 1000.0, 1500.0, "1*", "3*", 4, "/"],
                    [1, 1, 2, 1, 1500.0, 2000.0, "1*", "3*", 4, "/"],
                    [1, 1, 3, 1, 2000.0, 2500.0, "1*", "3*", 5, "/"],
                    [1, 1, 4, 1, 2500.0, 3000.0, "1*", "3*", 5, "/"],
                ],
                columns=[
                    Headers.I,
                    Headers.J,
                    Headers.K,
                    Headers.BRANCH,
                    Headers.START_MEASURED_DEPTH,
                    Headers.END_MEASURED_DEPTH,
                    Headers.COMPSEGS_DIRECTION,
                    Headers.DEF,
                    Headers.START_SEGMENT_NUMBER,
                    Headers.EMPTY,
                ],
            ),
            id="WELL_SEGMENTS segment length with annulus",
        ),
    ],
)
def test_prepare_compsegs(segment_length, df_device, df_annulus, df_completion, expected):
    """Tests the function prepare_outputs.py::prepare_compsegs."""
    well_name = "A1"
    lateral = 1
    df_reservoir = pd.DataFrame(
        [
            [1, 1, 1, 1000.0, 1500.0, "1*", 1, 100, 0.15, 1300.0, 1300.0, 0, Content.PERFORATED, 0, "A1", 1],
            [1, 1, 2, 1500.0, 2000.0, "1*", 1, 200, 0.20, 1750.0, 1750.0, 0, Content.PERFORATED, 0, "A1", 1],
            [1, 1, 3, 2000.0, 2500.0, "1*", 1, 100, 0.15, 2300.0, 2300.0, 0, Content.PERFORATED, 0, "A1", 1],
            [1, 1, 4, 2500.0, 3000.0, "1*", 1, 200, 0.20, 2750.0, 2750.0, 0, Content.PERFORATED, 0, "A1", 1],
        ],
        columns=[
            Headers.I,
            Headers.J,
            Headers.K,
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.COMPSEGS_DIRECTION,
            Headers.K2,
            Headers.CONNECTION_FACTOR,
            Headers.WELL_BORE_DIAMETER,
            Headers.MEASURED_DEPTH,
            Headers.TUBING_MEASURED_DEPTH,
            Headers.NUMBER_OF_DEVICES,
            Headers.DEVICE_TYPE,
            Headers.ANNULUS_ZONE,
            Headers.WELL,
            Headers.LATERAL,
        ],
    )

    test_compsegs = prepare_outputs.prepare_completion_segments(
        well_name, lateral, df_reservoir, df_device, df_annulus, df_completion, segment_length
    )
    pd.testing.assert_frame_equal(test_compsegs, expected)


def test_user_segment_lumping_oa(tmpdir):
    """Test completor case with user defined segment lumping.

    The keyword SEGMENTLENGTH is set to -1 in the case file.
    The completion has an open annulus interspersed with packers.
    """
    tmpdir.chdir()
    case_file = Path(_TESTDIR / "well_4_lumping_tests_oa.case")
    schedule_file = Path(_TESTDIR / "drogon" / "drogon_input.sch")
    true_file = Path(_TESTDIR / "user_created_lumping_oa.true")
    utils_for_tests.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_user_segment_lumping_gp(tmpdir):
    """Test completor case with user defined segment lumping.

    The keyword SEGMENTLENGTH is set to -1 in the case file.
    The completion has a gravel packed annulus interspersed with packers.
    """
    tmpdir.chdir()
    case_file = Path(_TESTDIR / "well_4_lumping_tests_gp.case")
    schedule_file = Path(_TESTDIR / "drogon" / "drogon_input.sch")
    true_file = Path(_TESTDIR / "user_created_lumping_gp.true")
    utils_for_tests.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)


def test_print_wsegdar(tmpdir):
    tmpdir.chdir()
    true_wsegdar_printout = """UDQ
  ASSIGN SUVTRIG WELL 3 0 /
/

WSEGVALV
--  WELL  START_SEGMENT_NUMBER  FLOW_COEFFICIENT  OIL_FLOW_CROSS_SECTIONAL_AREA  DEFAULTS  MAX_FLOW_CROSS_SECTIONAL_AREA
  'WELL' 3 1 7.852e-06  5* 7.852e-06 /
/

ACTIONX
D0010031 1000000 /
SWHF 'WELL' 3 <= 0.8 AND /
SGHF 'WELL' 3 > 0.99 AND /
SUVTRIG 'WELL' 3 = 0 /
/

WSEGVALV
--  WELL  START_SEGMENT_NUMBER  FLOW_COEFFICIENT  GAS_FLOW_CROSS_SECTIONAL_AREA  DEFAULTS  MAX_FLOW_CROSS_SECTIONAL_AREA
  'WELL' 3 1 2.590e-06  5* 7.852e-06 /
/

UDQ
  ASSIGN SUVTRIG 'WELL' 3 1 /
/

ENDACTIO

ACTIONX
D0010032 1000000 /
SWHF 'WELL' 3 > 0.8 AND /
SGHF 'WELL' 3 <= 0.99 AND /
SUVTRIG 'WELL' 3 = 0 /
/

WSEGVALV
--  WELL  START_SEGMENT_NUMBER  FLOW_COEFFICIENT  WATER_FLOW_CROSS_SECTIONAL_AREA  DEFAULTS  MAX_FLOW_CROSS_SECTIONAL_AREA
  'WELL' 3 1 1.590e-06  5* 7.852e-06 /
/

UDQ
  ASSIGN SUVTRIG 'WELL' 3 2 /
/

ENDACTIO

ACTIONX
D0010033 1000000 /
SGHF 'WELL' 3 < 0.9 AND /
SUVTRIG 'WELL' 3 = 1 /
/

WSEGVALV
--  WELL  START_SEGMENT_NUMBER  FLOW_COEFFICIENT  OIL_FLOW_CROSS_SECTIONAL_AREA  DEFAULTS  MAX_FLOW_CROSS_SECTIONAL_AREA
  'WELL' 3 1 7.852e-06  5* 7.852e-06 /
/

UDQ
  ASSIGN SUVTRIG WELL 3 0 /
/

ENDACTIO

ACTIONX
D0010034 1000000 /
SWHF 'WELL' 3 < 0.7 AND /
SUVTRIG 'WELL' 3 = 2 /
/

WSEGVALV
--  WELL  START_SEGMENT_NUMBER  FLOW_COEFFICIENT  OIL_FLOW_CROSS_SECTIONAL_AREA  DEFAULTS  MAX_FLOW_CROSS_SECTIONAL_AREA
  'WELL' 3 1 7.852e-06  5* 7.852e-06 /
/
UDQ
  ASSIGN SUVTRIG WELL 3 0 /
/

ENDACTIO

"""
    df_wsegdar = pd.DataFrame(
        [[Headers.WELL, 3, 1.0, 7.852e-6, 2.590e-06, 1.590e-06, 0.7, 0.8, 0.9, 0.99, "5*", 7.852e-6]],
        columns=[
            Headers.WELL,
            Headers.START_SEGMENT_NUMBER,
            Headers.FLOW_COEFFICIENT,
            Headers.OIL_FLOW_CROSS_SECTIONAL_AREA,
            Headers.GAS_FLOW_CROSS_SECTIONAL_AREA,
            Headers.WATER_FLOW_CROSS_SECTIONAL_AREA,
            Headers.WATER_HOLDUP_FRACTION_LOW_CUTOFF,
            Headers.WATER_HOLDUP_FRACTION_HIGH_CUTOFF,
            Headers.GAS_HOLDUP_FRACTION_LOW_CUTOFF,
            Headers.GAS_HOLDUP_FRACTION_HIGH_CUTOFF,
            Headers.DEFAULTS,
            Headers.MAX_FLOW_CROSS_SECTIONAL_AREA,
        ],
    )
    well_number = 1
    wsegdar_printout = prepare_outputs.print_wsegdar(df_wsegdar, well_number)
    wsegdar_printout = wsegdar_printout.strip()
    true_wsegdar_printout = true_wsegdar_printout.strip()
    wsegdar_printout = re.sub(r"[^\S\r\n]+", " ", wsegdar_printout)
    true_wsegdar_printout = re.sub(r"[^\S\r\n]+", " ", true_wsegdar_printout)
    assert wsegdar_printout == true_wsegdar_printout


def test_prepare_wsegvalv():
    df_well = pd.DataFrame(
        [
            ["'WELL'", 1250.0, 1250.0, 0.1, 0.1, 1, 1, 1.0, 1.2, "5*", 2.1, Content.VALVE, 1, 1],
            ["'WELL'", 1260.0, 1260.0, 0.1, 0.1, 1, 1, 1.0, 1.2, "5*", np.nan, Content.VALVE, 1, 1],
        ],
        columns=[
            Headers.WELL,
            Headers.TUBING_MEASURED_DEPTH,
            Headers.TRUE_VERTICAL_DEPTH,
            Headers.INNER_DIAMETER,
            Headers.ROUGHNESS,
            Headers.LATERAL,
            Headers.ANNULUS,
            Headers.FLOW_COEFFICIENT,
            Headers.FLOW_CROSS_SECTIONAL_AREA,
            Headers.ADDITIONAL_PIPE_LENGTH_FRICTION_PRESSURE_DROP,
            Headers.MAX_FLOW_CROSS_SECTIONAL_AREA,
            Headers.DEVICE_TYPE,
            Headers.NUMBER_OF_DEVICES,
            Headers.DEVICE_NUMBER,
        ],
    )
    df_device = pd.DataFrame(
        [
            [3, 3, 1, 2, 1250.0, 1250.0, 0.1, 0.1],
            [4, 4, 1, 3, 1260.0, 1260.0, 0.1, 0.1],
        ],
        columns=[
            Headers.START_SEGMENT_NUMBER,
            Headers.END_SEGMENT_NUMBER,
            Headers.BRANCH,
            Headers.OUT,
            Headers.MEASURED_DEPTH,
            Headers.TRUE_VERTICAL_DEPTH,
            Headers.WELL_BORE_DIAMETER,
            Headers.ROUGHNESS,
        ],
    )
    true_wsegvalv_output = pd.DataFrame(
        [
            ["'WELL'", 3, 1.0, 1.2, "5*", 2.1, "/"],
            ["'WELL'", 4, 1.0, 1.2, "5*", 1.2, "/"],
        ],
        columns=[
            Headers.WELL,
            Headers.START_SEGMENT_NUMBER,
            Headers.FLOW_COEFFICIENT,
            Headers.FLOW_CROSS_SECTIONAL_AREA,
            Headers.ADDITIONAL_PIPE_LENGTH_FRICTION_PRESSURE_DROP,
            Headers.MAX_FLOW_CROSS_SECTIONAL_AREA,
            Headers.EMPTY,
        ],
    )
    wsegvalv_output = prepare_outputs.prepare_valve("'WELL'", df_well, df_device)
    pd.testing.assert_frame_equal(wsegvalv_output, true_wsegvalv_output)


def test_prepare_compdat(tmpdir):
    """Test function for prepare_compdat including change of well/casing ID from
    input schedule values to completion table values.
    """
    tmpdir.chdir()
    well_name = Headers.WELL
    lateral = 1
    df_reservoir = pd.DataFrame(
        [
            [
                Headers.WELL,
                1,
                5,
                10,
                15,
                15,
                Headers.OPEN,
                "1*",
                100.0,
                0.216,
                50.0,
                2.5,
                "1*",
                "Y",
                12.25,
                1000.0,
                1,
                1,
                Content.INFLOW_CONTROL_DEVICE,
            ]
        ],
        columns=[
            Headers.WELL,
            Headers.LATERAL,
            Headers.I,
            Headers.J,
            Headers.K,
            Headers.K2,
            Headers.STATUS,
            Headers.SATURATION_FUNCTION_REGION_NUMBERS,
            Headers.CONNECTION_FACTOR,
            Headers.WELL_BORE_DIAMETER,
            Headers.FORMATION_PERMEABILITY_THICKNESS,
            Headers.SKIN,
            Headers.D_FACTOR,
            Headers.COMPDAT_DIRECTION,
            Headers.RO,
            Headers.MEASURED_DEPTH,
            Headers.ANNULUS_ZONE,
            Headers.NUMBER_OF_DEVICES,
            Headers.DEVICE_TYPE,
        ],
    )

    df_completion_table = pd.DataFrame(
        [
            [
                500.0,
                1500.0,
                500.0,
                1500.0,
                Headers.ORIGINAL_SEGMENT,
                Content.OPEN_ANNULUS,
                1,
                Content.INFLOW_CONTROL_DEVICE,
                0.15,
                0.311,
            ]
        ],
        columns=[
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.TUBING_MEASURED_DEPTH,
            Headers.TRUE_VERTICAL_DEPTH,
            Headers.SEGMENT_DESC,
            Headers.ANNULUS,
            Headers.VALVES_PER_JOINT,
            Headers.DEVICE_TYPE,
            Headers.INNER_DIAMETER,
            Headers.OUTER_DIAMETER,
        ],
    )

    prepare_compdat_out = prepare_outputs.prepare_completion_data(well_name, lateral, df_reservoir, df_completion_table)
    prepare_compdat_true = pd.DataFrame(
        [[Headers.WELL, 5, 10, 15, 15, Headers.OPEN, "1*", 100.0, 0.311, 50.0, 2.5, "1*", "Y", 12.25, "/"]],
        columns=[
            Headers.WELL,
            Headers.I,
            Headers.J,
            Headers.K,
            Headers.K2,
            Headers.FLAG,
            Headers.SATURATION_FUNCTION_REGION_NUMBERS,
            Headers.CONNECTION_FACTOR,
            Headers.WELL_BORE_DIAMETER,
            Headers.FORMATION_PERMEABILITY_THICKNESS,
            Headers.SKIN,
            Headers.D_FACTOR,
            Headers.COMPDAT_DIRECTION,
            Headers.RO,
            Headers.EMPTY,
        ],
    )
    pd.testing.assert_frame_equal(prepare_compdat_out, prepare_compdat_true)


def test_prepare_wsegicv(tmpdir):
    """Test function for prepare_wsegicv including use of tubing layer as ICV placement in tubing,
    and ICV placement in device, going as a fully lumped segment.
    """
    tmpdir.chdir()
    well_name = "'WELL'"
    lateral = 1
    df_well = pd.DataFrame(
        [
            ["'WELL'", 2030.0, 2000.0, 0.1, 0.1, 1, 1, 1.2, 4.1, "5*", 5.1, Content.INFLOW_CONTROL_VALVE, 1, 1],
            ["'WELL'", 2050.0, 2000.0, 0.1, 0.1, 1, 1, 3.5, 3.2, "5*", 6.1, Content.INFLOW_CONTROL_VALVE, 1, 2],
        ],
        columns=[
            Headers.WELL,
            Headers.TUBING_MEASURED_DEPTH,
            Headers.TRUE_VERTICAL_DEPTH,
            Headers.INNER_DIAMETER,
            Headers.ROUGHNESS,
            Headers.LATERAL,
            Headers.ANNULUS,
            Headers.FLOW_COEFFICIENT,
            Headers.FLOW_CROSS_SECTIONAL_AREA,
            Headers.ADDITIONAL_PIPE_LENGTH_FRICTION_PRESSURE_DROP,
            Headers.MAX_FLOW_CROSS_SECTIONAL_AREA,
            Headers.DEVICE_TYPE,
            Headers.NUMBER_OF_DEVICES,
            Headers.DEVICE_NUMBER,
        ],
    )
    df_device = pd.DataFrame(
        [
            [4, 4, 1, 3, 2030.0, 2000.0, 0.1, 0.1],
            [5, 5, 1, 4, 2050.0, 2000.0, 0.1, 0.1],
        ],
        columns=[
            Headers.START_SEGMENT_NUMBER,
            Headers.END_SEGMENT_NUMBER,
            Headers.BRANCH,
            Headers.OUT,
            Headers.MEASURED_DEPTH,
            Headers.TRUE_VERTICAL_DEPTH,
            Headers.WELL_BORE_DIAMETER,
            Headers.ROUGHNESS,
        ],
    )
    df_tubing = pd.DataFrame(
        [
            [2, 2, 1, 1, 2000, 2000, 0.1, 0.1],
            [3, 3, 1, 2, 2010, 2000, 0.1, 0.1],
            [4, 4, 1, 3, 2015, 2000, 0.1, 0.1],
        ],
        columns=[
            Headers.START_SEGMENT_NUMBER,
            Headers.END_SEGMENT_NUMBER,
            Headers.BRANCH,
            Headers.OUT,
            Headers.MEASURED_DEPTH,
            Headers.TRUE_VERTICAL_DEPTH,
            Headers.WELL_BORE_DIAMETER,
            Headers.ROUGHNESS,
        ],
    )
    df_icv_tubing = pd.DataFrame(
        [
            ["'WELL'", 1, 2005, 2000, 1, 1, Content.INFLOW_CONTROL_VALVE, 1],
            ["'WELL'", 1, 2012, 2000, 1, 1, Content.INFLOW_CONTROL_VALVE, 1],
            ["'WELL'", 1, 2015, 2000, 1, 1, Content.INFLOW_CONTROL_VALVE, 2],
            ["WELL", 1, 2008, 2008, 1, 1, Content.INFLOW_CONTROL_VALVE, 1],
        ],
        columns=[
            Headers.WELL,
            Headers.BRANCH,
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.ANNULUS,
            Headers.VALVES_PER_JOINT,
            Headers.DEVICE_TYPE,
            Headers.DEVICE_NUMBER,
        ],
    )
    df_icv = pd.DataFrame(
        [
            [Content.INFLOW_CONTROL_VALVE, 1, 1.2, 4.1, "5*", 5.1],
            [Content.INFLOW_CONTROL_VALVE, 2, 3.5, 3.2, "5*", 6.1],
        ],
        columns=[
            Headers.DEVICE_TYPE,
            Headers.DEVICE_NUMBER,
            Headers.FLOW_COEFFICIENT,
            Headers.FLOW_CROSS_SECTIONAL_AREA,
            Headers.DEFAULTS,
            Headers.MAX_FLOW_CROSS_SECTIONAL_AREA,
        ],
    )
    wsegicv_output = prepare_outputs.prepare_inflow_control_valve(
        well_name, lateral, df_well, df_device, df_tubing, df_icv_tubing, df_icv
    )
    true_wsegicv_output = pd.DataFrame(
        [
            ["'WELL'", 4, 1.2, 4.1, "5*", 5.1, "/"],
            ["'WELL'", 5, 3.5, 3.2, "5*", 6.1, "/"],
            ["'WELL'", 2, 1.2, 4.1, "5*", 5.1, "/"],
            ["'WELL'", 3, 1.2, 4.1, "5*", 5.1, "/"],
            ["'WELL'", 4, 3.5, 3.2, "5*", 6.1, "/"],
        ],
        columns=[
            Headers.WELL,
            Headers.START_SEGMENT_NUMBER,
            Headers.FLOW_COEFFICIENT,
            Headers.FLOW_CROSS_SECTIONAL_AREA,
            Headers.DEFAULTS,
            Headers.MAX_FLOW_CROSS_SECTIONAL_AREA,
            Headers.EMPTY,
        ],
    )
    pd.testing.assert_frame_equal(wsegicv_output, true_wsegicv_output)


def test_prepare_icv_compseg(tmpdir):
    """Test function for compseg preparation in accordance with ICV placement in well segmentation."""
    df_reservoir = pd.DataFrame(
        [
            [
                33,
                42,
                29,
                3778.0,
                3932,
                "1*",
                29,
                100.0,
                0.2159,
                3855.0,
                3855.0,
                10,
                Content.AUTONOMOUS_INFLOW_CONTROL_DEVICE,
                1,
                "OP5",
                1,
            ],
            [
                33,
                41,
                29,
                3932.0,
                4088,
                "1*",
                29,
                100.0,
                0.2159,
                4010.0,
                4125.0,
                10,
                Content.INFLOW_CONTROL_VALVE,
                0,
                "OP5",
                1,
            ],
            [
                33,
                40,
                29,
                4088.0,
                4108,
                "1*",
                29,
                100.0,
                0.2159,
                4098.0,
                4125.0,
                10,
                Content.INFLOW_CONTROL_VALVE,
                0,
                "OP5",
                1,
            ],
            [
                33,
                40,
                28,
                4108.0,
                4143,
                "1*",
                28,
                100.0,
                0.2159,
                4125.0,
                4125.0,
                10,
                Content.INFLOW_CONTROL_VALVE,
                0,
                "OP5",
                1,
            ],
            [
                32,
                40,
                28,
                4143.0,
                4246,
                "1*",
                28,
                100.0,
                0.2159,
                4194.0,
                4125.0,
                10,
                Content.INFLOW_CONTROL_VALVE,
                0,
                "OP5",
                1,
            ],
            [
                32,
                39,
                28,
                4246.0,
                4287,
                "1*",
                28,
                100.0,
                0.2159,
                4266.0,
                4266.0,
                10,
                Content.AUTONOMOUS_INFLOW_CONTROL_DEVICE,
                1,
                "OP5",
                1,
            ],
        ],
        columns=[
            Headers.I,
            Headers.J,
            Headers.K,
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.COMPSEGS_DIRECTION,
            Headers.K2,
            Headers.CONNECTION_FACTOR,
            Headers.WELL_BORE_DIAMETER,
            Headers.MEASURED_DEPTH,
            Headers.TUBING_MEASURED_DEPTH,
            Headers.NUMBER_OF_DEVICES,
            Headers.DEVICE_TYPE,
            Headers.ANNULUS_ZONE,
            Headers.WELL,
            Headers.LATERAL,
        ],
    )
    df_device = pd.DataFrame(
        [
            [20, 20, 4, 6, 4010.0, 1609.0, 0.15, 0.00065],
            [21, 21, 5, 7, 4125.0, 1611.0, 0.15, 0.00065],
            [22, 22, 6, 8, 4266.0, 1613.0, 0.15, 0.00065],
        ],
        columns=[
            Headers.START_SEGMENT_NUMBER,
            Headers.END_SEGMENT_NUMBER,
            Headers.BRANCH,
            Headers.OUT,
            Headers.MEASURED_DEPTH,
            Headers.TRUE_VERTICAL_DEPTH,
            Headers.WELL_BORE_DIAMETER,
            Headers.ROUGHNESS,
        ],
    )
    df_annulus = pd.DataFrame(
        [
            [33, 33, 17, 32, 3855.0, 1609.0, 0.2724, 0.00065],
            [34, 34, 17, 33, 4010.0, 1609.0, 0.2724, 0.00065],
            [35, 35, 18, 34, 4266.0, 1613.0, 0.2724, 0.00065],
        ],
        columns=[
            Headers.START_SEGMENT_NUMBER,
            Headers.END_SEGMENT_NUMBER,
            Headers.BRANCH,
            Headers.OUT,
            Headers.MEASURED_DEPTH,
            Headers.TRUE_VERTICAL_DEPTH,
            Headers.WELL_BORE_DIAMETER,
            Headers.ROUGHNESS,
        ],
    )
    df_completion_table = pd.DataFrame(
        [
            [
                "OP5",
                1,
                3778.0,
                4000.0,
                0.15,
                0.311,
                0.00065,
                Content.OPEN_ANNULUS,
                6.0,
                Content.AUTONOMOUS_INFLOW_CONTROL_DEVICE,
                1,
            ],
            ["OP5", 1, 4000.0, 4250.0, 0.15, 0.311, 0.00065, "GP", 6.0, Content.INFLOW_CONTROL_VALVE, 1],
            [
                "OP5",
                1,
                4250.0,
                4900.0,
                0.15,
                0.311,
                0.00065,
                Content.OPEN_ANNULUS,
                6.0,
                Content.AUTONOMOUS_INFLOW_CONTROL_DEVICE,
                1,
            ],
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
    compseg_icv_output_tubing, compseg_icv_output_annulus = prepare_outputs.connect_compseg_icv(
        df_reservoir, df_device, df_annulus, df_completion_table
    )

    compseg_tubing_true = pd.DataFrame(
        [
            [33, 42, 29, 4, 3778.0, 3932, 20],
            [33, 41, 29, 5, 3932.0, 4088, 21],
            [33, 40, 29, 5, 4088.0, 4108, 21],
            [33, 40, 28, 5, 4108.0, 4143, 21],
            [32, 40, 28, 5, 4143.0, 4246, 21],
            [32, 39, 28, 6, 4246.0, 4287, 22],
        ],
        columns=[
            Headers.I,
            Headers.J,
            Headers.K,
            Headers.BRANCH,
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.START_SEGMENT_NUMBER,
        ],
    )
    compseg_annulus_true = pd.DataFrame(
        [
            [33, 42, 29, 17, 3778.0, 3932, 33],
            [33, 41, 29, 17, 3932.0, 4088, 34],
            [33, 40, 29, 17, 4088.0, 4108, 34],
            [33, 40, 28, 17, 4108.0, 4143, 34],
            [32, 40, 28, 17, 4143.0, 4246, 34],
            [32, 39, 28, 18, 4246.0, 4287, 35],
        ],
        columns=[
            Headers.I,
            Headers.J,
            Headers.K,
            Headers.BRANCH,
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.START_SEGMENT_NUMBER,
        ],
    )
    compseg_icv_output_tubing = compseg_icv_output_tubing[
        [
            Headers.I,
            Headers.J,
            Headers.K,
            Headers.BRANCH,
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.START_SEGMENT_NUMBER,
        ]
    ]
    compseg_icv_output_annulus = compseg_icv_output_annulus[
        [
            Headers.I,
            Headers.J,
            Headers.K,
            Headers.BRANCH,
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.START_SEGMENT_NUMBER,
        ]
    ]
    pd.testing.assert_frame_equal(compseg_icv_output_tubing, compseg_tubing_true)
    pd.testing.assert_frame_equal(compseg_icv_output_annulus, compseg_annulus_true)


def test_user_segment_lumping_oa_overlap(tmpdir):
    """Test completor case with user defined segment lumping and overlapping case.

    The keyword SEGMENTLENGTH is set to -1 in the case file.
    The completion has an open annulus interspersed with packers.
    """
    tmpdir.chdir()
    case_file = Path(_TESTDIR / "well_4_lumping_overlap_tests_oa.case")
    schedule_file = Path(_TESTDIR / "improved_input_4_lumping_tests.sch")
    true_file = Path(_TESTDIR / "user_created_lumping_oa_overlap.true")
    utils_for_tests.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    utils_for_tests.assert_results(true_file, _TEST_FILE)
