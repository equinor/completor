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
