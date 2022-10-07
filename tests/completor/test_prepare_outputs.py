"""Test functions for the Completor prepare_outputs module."""

import re
from pathlib import Path

import common
import numpy as np
import pandas as pd

from completor import completion, prepare_outputs, read_casefile  # type:ignore

_TESTDIR = Path(__file__).absolute().parent / "data"
_TEST_FILE = "test.sch"


def test_trim_pandas():
    """Test the function to trim pandas data frames with default values."""
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
        columns=["--", "A", "B", "C", "D", "E", "F", ""],
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
    df_test_common = pd.DataFrame(
        [[1, 2, 3, "1*", 5, 6], [1, 2, "5*", 3, 4, 5]], columns=["A", "B", "C", "D", "E", "F"]
    )
    df_true_common = pd.DataFrame(
        [[" ", 1, 2, 3, "1*", 5, 6, "/"], [" ", 1, 2, "5*", 3, 4, 5, "/"]],
        columns=["--", "A", "B", "C", "D", "E", "F", ""],
    )

    df_test_default = prepare_outputs.dataframe_tostring(df_test_common)
    df_true_default = df_true_common.to_string(index=False, justify="justify")
    # with formatters
    formatters = {"A": "{:.3f}".format}
    df_test_with_formatter = prepare_outputs.dataframe_tostring(df_test_common, True, True, True, formatters)
    df_true_with_formatter = df_true_common.to_string(index=False, justify="justify", formatters=formatters)
    assert df_test_default == df_true_default
    assert df_test_with_formatter == df_true_with_formatter


def test_outlet_segment_1():
    """
    Test outlet_segment find the outlet segments closest to target measured depths.
    """
    target_md = [1, 2, 3, 4.0]
    reference_md = [0.5, 1.0, 2.0, 4.0, 5.0]
    reference_segment_number = [1, 2, 3, 4, 5]

    test_segment = prepare_outputs.get_outlet_segment(target_md, reference_md, reference_segment_number)
    np.testing.assert_equal(test_segment, [2, 3, 3, 4])


def test_outlet_segment_2():
    """
    Test outlet_segment find the outlet segments closest to target measured depths.
    """
    target_md = [1, 2, 4.0, 5.0]
    reference_md = [0.5, 1.0, 2.0, 4.0, 5.0]
    reference_segement = [1, 2, 3, 4, 5]

    test_segment = prepare_outputs.get_outlet_segment(target_md, reference_md, reference_segement)
    np.testing.assert_equal(test_segment, [2, 3, 4, 5])


def test_prepare_tubing_layer():
    """Test that the function does not create duplicate tubing segments."""
    schedule_obj = completion.WellSchedule(["A1"])
    schedule_obj.set_welsegs(
        [
            ["A1", "2148.00", "3422", "1*", "ABS", "HFA", "HO"],
            ["2", "2", "1", "1", "3428.66288", "2247.36764", "0.1242", "0.0123"],
            ["3", "3", "1", "2", "3445.89648", "2249.14115", "0.1242", "0.0123"],
            ["4", "4", "1", "3", "3471.06249", "2251.62048", "0.1242", "0.0123"],
            ["5", "5", "1", "4", "3516.04433", "2255.62756", "0.1242", "0.0123"],
        ]
    )
    df_test, _ = prepare_outputs.prepare_tubing_layer(
        schedule=schedule_obj,
        well_name="A1",
        lateral=1,
        df_well=pd.DataFrame(
            [
                ["A1", 3428.662885, 2247.367641, 0.1, 0.1, 1],
                ["A1", 3445.896480, 2249.141150, 0.1, 0.1, 1],
                ["A1", 3471.062485, 2251.620480, 0.1, 0.1, 1],
                ["A1", 3516.044325, 2255.627560, 0.1, 0.1, 1],
            ],
            columns=["WELL", "TUB_MD", "TUB_TVD", "INNER_DIAMETER", "ROUGHNESS", "LATERAL"],
        ),
        start_segment=1,
        branch_no=1,
        completion_table=pd.DataFrame(
            [
                ["A1", 1, 0.00000000, 3417.52493, 0.1, 0.2, 6, "GP", 0],
                ["A1", 1, 3417.52493, 4593.87272, 0.1, 0.2, 6, "GP", 3],
                ["A1", 1, 4593.87272, 99999.0000, 0.1, 0.2, 6, "GP", 0],
            ],
            columns=[
                "WELL",
                "BRANCH",
                "STARTMD",
                "ENDMD",
                "INNER_ID",
                "OUTER_ID",
                "ROUGHNESS",
                "ANNULUS",
                "NVALVEPERJOINT",
            ],
        ),
    )

    df_true = pd.DataFrame(
        [
            ["A1", 3428.662885, 2247.367641, 0.1, 0.1, 1],
            ["A1", 3445.896480, 2249.141150, 0.1, 0.1, 1],
            ["A1", 3471.062485, 2251.620480, 0.1, 0.1, 1],
            ["A1", 3516.044325, 2255.627560, 0.1, 0.1, 1],
        ],
        columns=["WELL", "MD", "TVD", "DIAM", "ROUGHNESS", "LATERAL"],
    )

    pd.testing.assert_frame_equal(
        df_test[["MD", "TVD", "DIAM", "ROUGHNESS"]], df_true[["MD", "TVD", "DIAM", "ROUGHNESS"]]
    )


def test_prepare_compsegs():
    """Tests the function prepare_outputs.py::prepare_compsegs()."""
    well_name = "A1"
    lateral = 1
    df_reservoir = pd.DataFrame(
        [
            [1, 1, 1, 1000.0, 1500.0, "1*", 1, 100, 0.15, 1300.0, 1300.0, 0, "PERF", 0, "A1", 1],
            [1, 1, 2, 1500.0, 2000.0, "1*", 1, 200, 0.20, 1750.0, 1750.0, 0, "PERF", 0, "A1", 1],
            [1, 1, 3, 2000.0, 2500.0, "1*", 1, 100, 0.15, 2300.0, 2300.0, 0, "PERF", 0, "A1", 1],
            [1, 1, 4, 2500.0, 3000.0, "1*", 1, 200, 0.20, 2750.0, 2750.0, 0, "PERF", 0, "A1", 1],
        ],
        columns=[
            "I",
            "J",
            "K",
            "STARTMD",
            "ENDMD",
            "COMPSEGS_DIRECTION",
            "K2",
            "CF",
            "DIAM",
            "MD",
            "TUB_MD",
            "NDEVICES",
            "DEVICETYPE",
            "ANNULUS_ZONE",
            "WELL",
            "LATERAL",
        ],
    )
    df_device = pd.DataFrame(
        [
            [4, 4, 1, 2, 1500.0, 1500.0, 0.15, 0.00065],
            [5, 5, 1, 3, 2500.0, 2500.0, 0.15, 0.00065],
        ],
        columns=["SEG", "SEG2", "BRANCH", "OUT", "MD", "TVD", "DIAM", "ROUGHNESS"],
    )
    df_annulus = pd.DataFrame([], columns=[])
    df_tubing_segments = pd.DataFrame(
        [
            [1000.0, 2000.0, 1500.0, 1500.0, "OriginalSegment", 1, "PERF", "GP"],
            [2000.0, 3000.0, 2500.0, 2500.0, "OriginalSegment", 1, "PERF", "GP"],
        ],
        columns=["STARTMD", "ENDMD", "TUB_MD", "TUB_TVD", "SEGMENT_DESC", "NVALVEPERJOINT", "DEVICETYPE", "ANNULUS"],
    )

    # Test1: Positive segment length and no annulus zone
    segment_length = 1.0
    true_compsegs = pd.DataFrame(
        [
            [1, 1, 1, 1, 1000.0, 1500.0, "1*", "3*", 4, "/"],
            [1, 1, 2, 1, 1500.0, 2000.0, "1*", "3*", 4, "/"],
            [1, 1, 3, 1, 2000.0, 2500.0, "1*", "3*", 5, "/"],
            [1, 1, 4, 1, 2500.0, 3000.0, "1*", "3*", 5, "/"],
        ],
        columns=["I", "J", "K", "BRANCH", "STARTMD", "ENDMD", "DIR", "DEF", "SEG", ""],
    )
    test_compsegs = prepare_outputs.prepare_compsegs(
        well_name, lateral, df_reservoir, df_device, df_annulus, df_tubing_segments, segment_length
    )
    pd.testing.assert_frame_equal(test_compsegs, true_compsegs)

    # Test2: Negative segment length and no annulus zone
    segment_length = -1.0
    df_device = pd.DataFrame(
        [
            [4, 4, 1, 2, 1250.0, 1250.0, 0.15, 0.00065],
            [5, 5, 1, 3, 2250.0, 2250.0, 0.15, 0.00065],
        ],
        columns=["SEG", "SEG2", "BRANCH", "OUT", "MD", "TVD", "DIAM", "ROUGHNESS"],
    )
    df_completion_table = pd.DataFrame(
        [
            [1000.0, 1500.0, 1250.0, 1250.0, "OriginalSegment", "GP", 1, "PERF"],
            [1500.0, 3000.0, 2250.0, 2250.0, "OriginalSegment", "GP", 1, "PERF"],
        ],
        columns=["STARTMD", "ENDMD", "TUB_MD", "TUB_TVD", "SEGMENT_DESC", "ANNULUS", "NVALVEPERJOINT", "DEVICETYPE"],
    )
    true_compsegs = pd.DataFrame(
        [
            [1, 1, 1, 1, 1000.0, 1500.0, "1*", "3*", 4, "/"],
            [1, 1, 2, 1, 1500.0, 2000.0, "1*", "3*", 5, "/"],
            [1, 1, 3, 1, 2000.0, 2500.0, "1*", "3*", 5, "/"],
            [1, 1, 4, 1, 2500.0, 3000.0, "1*", "3*", 5, "/"],
        ],
        columns=["I", "J", "K", "BRANCH", "STARTMD", "ENDMD", "DIR", "DEF", "SEG", ""],
    )
    test_compsegs = prepare_outputs.prepare_compsegs(
        well_name, lateral, df_reservoir, df_device, df_annulus, df_completion_table, segment_length
    )
    pd.testing.assert_frame_equal(test_compsegs, true_compsegs)

    # Test3: Positive segment length and annulus zone
    segment_length = 1.0
    df_device = pd.DataFrame(
        [
            [4, 4, 1, 2, 1500.0, 1500.0, 0.15, 0.00065],
            [5, 5, 1, 3, 2500.0, 2500.0, 0.15, 0.00065],
        ],
        columns=["SEG", "SEG2", "BRANCH", "OUT", "MD", "TVD", "DIAM", "ROUGHNESS"],
    )
    df_annulus = pd.DataFrame(
        [
            [6, 6, 1, 2, 1500.0, 1500.0, 0.15, 0.0001, "/"],
            [7, 7, 1, 3, 2500.0, 2500.0, 0.15, 0.0001, "/"],
        ],
        columns=["SEG", "SEG2", "BRANCH", "OUT", "MD", "TVD", "DIAM", "ROUGHNESS", ""],
    )
    df_tubing_segments = pd.DataFrame(
        [
            [1000.0, 2000.0, 1500.0, 1500.0, "OriginalSegment", 1, "GP", "ICD"],
            [2000.0, 3000.0, 2500.0, 2500.0, "OriginalSegment", 1, "GP", "ICD"],
        ],
        columns=["STARTMD", "ENDMD", "TUB_MD", "TUB_TVD", "SEGMENT_DESC", "NVALVEPERJOINT", "ANNULUS", "DEVICETYPE"],
    )
    true_compsegs = pd.DataFrame(
        [
            [1, 1, 1, 1, 1000.0, 1500.0, "1*", "3*", 4, "/"],
            [1, 1, 2, 1, 1500.0, 2000.0, "1*", "3*", 4, "/"],
            [1, 1, 3, 1, 2000.0, 2500.0, "1*", "3*", 5, "/"],
            [1, 1, 4, 1, 2500.0, 3000.0, "1*", "3*", 5, "/"],
        ],
        columns=["I", "J", "K", "BRANCH", "STARTMD", "ENDMD", "DIR", "DEF", "SEG", ""],
    )
    test_compsegs = prepare_outputs.prepare_compsegs(
        well_name, lateral, df_reservoir, df_device, df_annulus, df_tubing_segments, segment_length
    )
    pd.testing.assert_frame_equal(test_compsegs, true_compsegs)

    # Test4: Negative segment length and annulus zone
    segment_length = -1.0
    df_device = pd.DataFrame(
        [
            [4, 4, 1, 2, 1250.0, 1250.0, 0.15, 0.00065],
            [5, 5, 1, 3, 2250.0, 2250.0, 0.15, 0.00065],
        ],
        columns=["SEG", "SEG2", "BRANCH", "OUT", "MD", "TVD", "DIAM", "ROUGHNESS"],
    )
    df_annulus = pd.DataFrame(
        [
            [6, 6, 1, 2, 1250.0, 1250.0, 0.15, 0.0001, "/"],
            [7, 7, 1, 3, 2250.0, 2250.0, 0.15, 0.0001, "/"],
        ],
        columns=["SEG", "SEG2", "BRANCH", "OUT", "MD", "TVD", "DIAM", "ROUGHNESS", ""],
    )
    df_completion_table = pd.DataFrame(
        [
            [1000.0, 1500.0, 1300.0, 1300.0, "OriginalSegment", "OA", 1, "PERF"],
            [1500.0, 3000.0, 2250.0, 2250.0, "OriginalSegment", "OA", 1, "PERF"],
        ],
        columns=["STARTMD", "ENDMD", "TUB_MD", "TUB_TVD", "SEGMENT_DESC", "ANNULUS", "NVALVEPERJOINT", "DEVICETYPE"],
    )
    true_compsegs = pd.DataFrame(
        [
            [1, 1, 1, 1, 1000.0, 1500.0, "1*", "3*", 4, "/"],
            [1, 1, 2, 1, 1500.0, 2000.0, "1*", "3*", 5, "/"],
            [1, 1, 3, 1, 2000.0, 2500.0, "1*", "3*", 5, "/"],
            [1, 1, 4, 1, 2500.0, 3000.0, "1*", "3*", 5, "/"],
        ],
        columns=["I", "J", "K", "BRANCH", "STARTMD", "ENDMD", "DIR", "DEF", "SEG", ""],
    )
    test_compsegs = prepare_outputs.prepare_compsegs(
        well_name, lateral, df_reservoir, df_device, df_annulus, df_completion_table, segment_length
    )
    pd.testing.assert_frame_equal(test_compsegs, true_compsegs)

    # Test5: WELSEGS segment length with annulus
    segment_length = "WELSEGS"
    df_device = pd.DataFrame(
        [
            [4, 4, 1, 2, 1500.0, 1500.0, 0.15, 0.00065],
            [5, 5, 1, 3, 2500.0, 2500.0, 0.15, 0.00065],
        ],
        columns=["SEG", "SEG2", "BRANCH", "OUT", "MD", "TVD", "DIAM", "ROUGHNESS"],
    )
    df_annulus = pd.DataFrame(
        [
            [6, 6, 1, 2, 1500.0, 1500.0, 0.15, 0.0001, "/"],
            [7, 7, 1, 3, 2500.0, 2500.0, 0.15, 0.0001, "/"],
        ],
        columns=["SEG", "SEG2", "BRANCH", "OUT", "MD", "TVD", "DIAM", "ROUGHNESS", ""],
    )
    df_tubing_segments = pd.DataFrame(
        [
            [1000.0, 2000.0, 1500.0, 1500.0, "OriginalSegment", "GP", 1, "ICD"],
            [2000.0, 3000.0, 2500.0, 2500.0, "OriginalSegment", "GP", 1, "ICD"],
        ],
        columns=["STARTMD", "ENDMD", "TUB_MD", "TUB_TVD", "SEGMENT_DESC", "ANNULUS", "NVALVEPERJOINT", "DEVICETYPE"],
    )
    true_compsegs = pd.DataFrame(
        [
            [1, 1, 1, 1, 1000.0, 1500.0, "1*", "3*", 4, "/"],
            [1, 1, 2, 1, 1500.0, 2000.0, "1*", "3*", 4, "/"],
            [1, 1, 3, 1, 2000.0, 2500.0, "1*", "3*", 5, "/"],
            [1, 1, 4, 1, 2500.0, 3000.0, "1*", "3*", 5, "/"],
        ],
        columns=["I", "J", "K", "BRANCH", "STARTMD", "ENDMD", "DIR", "DEF", "SEG", ""],
    )
    test_compsegs = prepare_outputs.prepare_compsegs(
        well_name, lateral, df_reservoir, df_device, df_annulus, df_tubing_segments, segment_length
    )
    pd.testing.assert_frame_equal(test_compsegs, true_compsegs)


def test_connect_lateral_logs_warning(caplog):
    """
    Test the warning occurs in connect_lateral when given segments with negative length.

    Segments with negative lengths can occur when trying to connect a lateral to it's
    main bore/mother branch. They are caused by an error in the input,
    so the user must be warned about this.
    """

    df_tubing_lat_1 = pd.DataFrame(
        [
            [2, 2, 1, 1, 2219.76749],
            [3, 3, 1, 2, 2200.73413],
            [4, 4, 1, 3, 2202.75139],
        ],
        columns=["SEG", "SEG2", "BRANCH", "OUT", "MD"],
    )
    df_tubing_lat_2 = pd.DataFrame(
        [
            [16, 16, 5, 15, 2179.9725],
            [17, 17, 5, 16, 2195.5],
        ],
        columns=["SEG", "SEG2", "BRANCH", "OUT", "MD"],
    )
    df_top = pd.DataFrame(
        [[1, 2188.76261]],
        columns=["TUBINGBRANCH", "TUBINGMD"],
    )
    empty_df = pd.DataFrame()

    data = {
        1: (df_tubing_lat_1, empty_df, empty_df, empty_df, empty_df),
        2: (df_tubing_lat_2, empty_df, empty_df, empty_df, df_top),
    }
    case = read_casefile.ReadCasefile(
        (
            """
COMPLETION
--Well Branch Start End Screen   Well/   Roughness Annulus Nvalve/ Valve Device
--     Number  MD   MD  Tubing   Casing            Content Joint   Type  Number
--                      Diameter Diameter
  A1     1   0.0  2451.78 0.15   0.19    0.00035     GP      1     PERF    1
  A1     2   0.0  2450.0  0.15   0.19    0.00035     GP      1     PERF    1
/
SEGMENTLENGTH
 0
/
GP_PERF_DEVICELAYER
 TRUE
/"""
        ),
        "dummy_schedule",
    )

    prepare_outputs.connect_lateral("A1", 2, data, case)
    assert len(caplog.text) > 0
    assert "WARNING" in caplog.text


def test_user_segment_lumping_oa(tmpdir):
    """
    Test completor case with user defined segment lumping.
    The keyword SEGMENTLENGTH is set to -1 in the case file.
    The completion has an open annulus interspersed with packers.
    """
    tmpdir.chdir()
    case_file = Path(_TESTDIR / "well_4_lumping_tests_oa.case")
    schedule_file = Path(_TESTDIR / "drogon" / "drogon_input.sch")
    true_file = Path(_TESTDIR / "user_created_lumping_oa.true")
    common.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_user_segment_lumping_gp(tmpdir):
    """
    Test completor case with user defined segment lumping.
    The keyword SEGMENTLENGTH is set to -1 in the case file.
    The completion has a gravel packed annulus interspersed with packers.
    """
    tmpdir.chdir()
    case_file = Path(_TESTDIR / "well_4_lumping_tests_gp.case")
    schedule_file = Path(_TESTDIR / "drogon" / "drogon_input.sch")
    true_file = Path(_TESTDIR / "user_created_lumping_gp.true")
    common.open_files_run_create(case_file, schedule_file, _TEST_FILE)
    common.assert_results(true_file, _TEST_FILE)


def test_print_wsegdar(tmpdir):
    tmpdir.chdir()
    df_wsegdar = pd.DataFrame(
        [["WELL", 3, 1.0, 7.852e-6, 2.590e-06, 1.590e-06, 0.7, 0.8, 0.9, 0.99, "5*", 7.852e-6]],
        columns=[
            "WELL",
            "SEG",
            "CV_DAR",
            "AC_OIL",
            "AC_GAS",
            "AC_WATER",
            "WHF_LCF_DAR",
            "WHF_HCF_DAR",
            "GHF_LCF_DAR",
            "GHF_HCF_DAR",
            "DEFAULTS",
            "AC_MAX",
        ],
    )
    well_number = 1
    wsegdar_printout = prepare_outputs.print_wsegdar(df_wsegdar, well_number)
    true_wsegdar_printout = """UDQ
  ASSIGN SUVTRIG WELL 3 0 /
/

WSEGVALV
--  WELL  SEG  CV_DAR  AC_OIL  DEFAULTS  AC_MAX
  'WELL' 3 1 7.852e-06  5* 7.852e-06 /
/

ACTIONX
D0010031 1000000 /
SWHF 'WELL' 3 <= 0.8 AND /
SGHF 'WELL' 3 > 0.99 AND /
SUVTRIG 'WELL' 3 = 0 /
/

WSEGVALV
--  WELL  SEG  CV_DAR  AC_GAS  DEFAULTS  AC_MAX
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
--  WELL  SEG  CV_DAR  AC_WATER  DEFAULTS  AC_MAX
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
--  WELL  SEG  CV_DAR  AC_OIL  DEFAULTS  AC_MAX
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
--  WELL  SEG  CV_DAR  AC_OIL  DEFAULTS  AC_MAX
  'WELL' 3 1 7.852e-06  5* 7.852e-06 /
/
UDQ
  ASSIGN SUVTRIG WELL 3 0 /
/

ENDACTIO

"""
    wsegdar_printout = wsegdar_printout.strip()
    true_wsegdar_printout = true_wsegdar_printout.strip()
    wsegdar_printout = re.sub(r"[^\S\r\n]+", " ", wsegdar_printout)
    true_wsegdar_printout = re.sub(r"[^\S\r\n]+", " ", true_wsegdar_printout)
    assert wsegdar_printout == true_wsegdar_printout
