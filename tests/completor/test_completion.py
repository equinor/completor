"""Test functions for the completion module."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import completor.read_schedule
from completor import completion
from completor.constants import Headers, Keywords, Method
from completor.exceptions import CompletorError


def test_completion_index():
    """Test completion_index gives correct indexes for start and end measured depth."""
    df_tubing_segments = pd.DataFrame(
        [[1000, 2000], [2000, 3000], [3000, 4000]], columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH]
    )
    assert (completion.completion_index(df_tubing_segments, 1000, 2001)) == (0, 1)
    assert (completion.completion_index(df_tubing_segments, 1000, 2000)) == (0, 0)
    assert (completion.completion_index(df_tubing_segments, 1000, 3000)) == (0, 1)
    assert (completion.completion_index(df_tubing_segments, 999.99, 3000)) == (-1, -1)
    assert (completion.completion_index(df_tubing_segments, 2000, 4000)) == (1, 2)
    assert (completion.completion_index(df_tubing_segments, 2000, 4001)) == (-1, -1)
    assert (completion.completion_index(df_tubing_segments, 2000, 3000.001)) == (1, 2)


def test_connect_cells_segment_cells():
    """Test connect_cells_segment connects cells to segment using method 'cells'."""
    df_segment = pd.DataFrame(
        [
            [1.0],
            [5.0],
            [8.0],
        ],
        columns=[Headers.TUBING_MEASURED_DEPTH],
    )
    df_tubing_segments = pd.DataFrame(
        [
            [0.5, 1.5],
            [4.5, 5.5],
            [7.5, 8.5],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
    )
    df_compsegs = pd.DataFrame(
        [[0.0, 3.00], [3.0, 10.0], [10.0, 20.0]],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
    )
    df_merge = pd.DataFrame(
        [
            [0.0, 3.0, 1.5, 1.0],
            [3.0, 10.0, 6.5, 5.0],
            [10.0, 20.0, 15.0, 8.0],
        ],
        columns=[
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.MEASURED_DEPTH,
            Headers.TUBING_MEASURED_DEPTH,
        ],
    )

    df_test = completion.connect_cells_to_segments(df_segment, df_compsegs, df_tubing_segments, method="cells")
    pd.testing.assert_frame_equal(df_test, df_merge)


def test_connect_cells_segment_cells_2():
    """Test connect_cells_segment connects cells to segment using method 'cells'."""
    df_segment = pd.DataFrame(
        [
            [1.0],
            [15.0],
            [18.0],
        ],
        columns=[Headers.TUBING_MEASURED_DEPTH],
    )
    df_tubing_segments = pd.DataFrame(
        [
            [0.5, 1.5],
            [14.5, 15.5],
            [17.5, 18.5],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
    )
    df_compsegs = pd.DataFrame(
        [
            [0.0, 3.00],
            [3.0, 10.0],
            [10.0, 20.0],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
    )

    df_merge = pd.DataFrame(
        [
            [0.0, 3.0, 1.5, 1.0],
            [3.0, 10.0, 6.5, 1.0],
            [10.0, 20.0, 15.0, 15.0],
        ],
        columns=[
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.MEASURED_DEPTH,
            Headers.TUBING_MEASURED_DEPTH,
        ],
    )

    df_test = completion.connect_cells_to_segments(df_segment, df_compsegs, df_tubing_segments, method="cells")
    pd.testing.assert_frame_equal(df_test, df_merge)


def test_connect_cells_segment_user():
    """Test connect_cells_segment connects cells to segment using method 'user'."""
    df_segment = pd.DataFrame(
        [
            [2.5],
            [5.0],
            [10.0],
        ],
        columns=[Headers.TUBING_MEASURED_DEPTH],
    )
    df_tubing_segments = pd.DataFrame(
        [
            [0.0, 5.0],
            [2.6, 7.5],
            [7.5, 20.0],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
    )
    df_compsegs = pd.DataFrame(
        [
            [0.0, 3.00],
            [3.0, 10.0],
            [10.0, 20.0],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
    )
    df_merge = pd.DataFrame(
        [
            [0.0, 3.0, 1.5, 2.5],
            [3.0, 10.0, 6.5, 5.0],
            [10.0, 20.0, 15.0, 10.0],
        ],
        columns=[
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.MEASURED_DEPTH,
            Headers.TUBING_MEASURED_DEPTH,
        ],
    )

    df_test = completion.connect_cells_to_segments(df_segment, df_compsegs, df_tubing_segments, method=Method.USER)
    pd.testing.assert_frame_equal(df_test, df_merge)


def test_insert_missing_segments_no_gap():
    """Test insert_missing_segments does not insert dummy segments when there are no inactive cells."""
    df_tubing_segments = pd.DataFrame(
        [
            [1000, 2000],
            [2000, 3000],
            [3000, 4000],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
    )
    df_true = pd.DataFrame(
        [
            [1000, 2000, Headers.ORIGINAL_SEGMENT],
            [2000, 3000, Headers.ORIGINAL_SEGMENT],
            [3000, 4000, Headers.ORIGINAL_SEGMENT],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH, Headers.SEGMENT_DESC],
    )

    df_test = completion.insert_missing_segments(df_tubing_segments, "A1")
    pd.testing.assert_frame_equal(df_test, df_true)


def test_insert_missing_segments_one_gap():
    """Test insert_missing_segments inserts one dummy segment due to inactive cells."""
    df_tubing_segments = pd.DataFrame(
        [
            [1000, 2000],
            [2500, 3000],
            [3000, 4000],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
    )
    df_true = pd.DataFrame(
        [
            [1000, 2000, Headers.ORIGINAL_SEGMENT],
            [2000, 2500, Headers.ADDITIONAL_SEGMENT],
            [2500, 3000, Headers.ORIGINAL_SEGMENT],
            [3000, 4000, Headers.ORIGINAL_SEGMENT],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH, Headers.SEGMENT_DESC],
    )

    df_test = completion.insert_missing_segments(df_tubing_segments, "A1")
    pd.testing.assert_frame_equal(df_test, df_true)


def test_insert_missing_segments_two_gaps():
    """Test insert_missing_segments inserts two dummy segments due to inactive cells."""
    df_tubing_segments = pd.DataFrame(
        [
            [1000, 2000],
            [2500, 3000],
            [3005, 4000],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
    )
    df_true = pd.DataFrame(
        [
            [1000, 2000, Headers.ORIGINAL_SEGMENT],
            [2000, 2500, Headers.ADDITIONAL_SEGMENT],
            [2500, 3000, Headers.ORIGINAL_SEGMENT],
            [3000, 3005, Headers.ADDITIONAL_SEGMENT],
            [3005, 4000, Headers.ORIGINAL_SEGMENT],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH, Headers.SEGMENT_DESC],
    )

    df_test = completion.insert_missing_segments(df_tubing_segments, "A1")
    pd.testing.assert_frame_equal(df_test, df_true)


def test_insert_missing_segments_raise_error():
    """Test that an error is raised when there is no data in df_tubing."""
    df_tubing_segments = pd.DataFrame([], columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH])

    with pytest.raises(CompletorError):
        completion.insert_missing_segments(df_tubing_segments, "A1")


def test_well_trajectory():
    """Test well_trajectory creates the correct relation (sorted by measured depth) between well segments'
    (welsegs) header and content.
    """
    df_welsegs_header = pd.DataFrame(
        [
            [2.0, 1.0],
        ],
        columns=[Headers.MEASURED_DEPTH, Headers.TRUE_VERTICAL_DEPTH],
    )
    df_welsegs_content = pd.DataFrame(
        [
            [5.0, 1.0],
            [4.0, 3.0],
        ],
        columns=[Headers.TUBING_MEASURED_DEPTH, Headers.TRUE_VERTICAL_DEPTH],
    )
    df_true = pd.DataFrame(
        [
            [2.0, 1.0],
            [4.0, 3.0],
            [5.0, 1.0],
        ],
        columns=[Headers.MEASURED_DEPTH, Headers.TRUE_VERTICAL_DEPTH],
    )

    df_test = completion.well_trajectory(df_welsegs_header, df_welsegs_content)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_define_annulus_zone_keep_gravel_pack_1():
    """Test define_annulus_zone gives open annulus segment when interrupted by packer segments and gravel packs.

    Also check packer are removed, while gravel pack segments are kept.
    """
    df_completion = pd.DataFrame(
        [
            [1.0, 2.0, "OA"],
            [2.0, 3.0, "GP"],
            [3.0, 4.0, "OA"],
            [4.0, 5.0, "GP"],
            [5.0, 5.0, "PA"],
            [5.0, 6.0, "OA"],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH, Headers.ANNULUS],
    )
    df_completion_before = df_completion.copy(deep=True)
    df_true = pd.DataFrame(
        [
            [1.0, 2.0, "OA", 1],
            [2.0, 3.0, "GP", 0],
            [3.0, 4.0, "OA", 2],
            [4.0, 5.0, "GP", 0],
            [5.0, 6.0, "OA", 3],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH, Headers.ANNULUS, Headers.ANNULUS_ZONE],
    )

    df_test = completion.define_annulus_zone(df_completion)
    pd.testing.assert_frame_equal(df_completion_before, df_completion)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_define_annulus_zone_keep_gravel_pack_2():
    """Test define_annulus_zone gives open annulus segment when interrupted by packer segments and gravel packs.

    Also check packer are removed, while gravel pack segments are kept.
    """
    df_completion = pd.DataFrame(
        [
            [1.0, 2.0, "OA"],
            [2.0, 3.0, "GP"],
            [3.0, 4.0, "OA"],
            [4.0, 4.0, "PA"],
            [4.0, 5.0, "OA"],
            [5.0, 5.0, "PA"],
            [5.0, 6.0, "OA"],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH, Headers.ANNULUS],
    )
    df_completion_before = df_completion.copy(deep=True)
    df_true = pd.DataFrame(
        [
            [1.0, 2.0, "OA", 1],
            [2.0, 3.0, "GP", 0],
            [3.0, 4.0, "OA", 2],
            [4.0, 5.0, "OA", 3],
            [5.0, 6.0, "OA", 4],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH, Headers.ANNULUS, Headers.ANNULUS_ZONE],
    )

    df_test = completion.define_annulus_zone(df_completion)
    pd.testing.assert_frame_equal(df_completion_before, df_completion)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_define_annulus_zone_packer_segments():
    """Test define_annulus_zone gives three open annulus segment when interrupted by packer segments.

    Also check packer are removed.
    """
    df_completion = pd.DataFrame(
        [
            [1.0, 2.0, "OA"],
            [2.0, 3.0, "OA"],
            [3.0, 4.0, "OA"],
            [4.0, 4.0, "PA"],
            [4.0, 5.0, "OA"],
            [5.0, 5.0, "PA"],
            [5.0, 6.0, "OA"],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH, Headers.ANNULUS],
    )
    df_completion_before = df_completion.copy(deep=True)
    df_true = pd.DataFrame(
        [
            [1.0, 2.0, "OA", 1],
            [2.0, 3.0, "OA", 1],
            [3.0, 4.0, "OA", 1],
            [4.0, 5.0, "OA", 2],
            [5.0, 6.0, "OA", 3],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH, Headers.ANNULUS, Headers.ANNULUS_ZONE],
    )

    df_test = completion.define_annulus_zone(df_completion)
    pd.testing.assert_frame_equal(df_completion_before, df_completion)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_define_annulus_zone_continuous_annulus_1():
    """Test define_annulus_zone gives one continuous open annulus segment when all segment are open annulus."""
    df_completion = pd.DataFrame(
        [
            [1.0, 2.0, "OA"],
            [2.0, 3.0, "OA"],
            [3.0, 4.0, "OA"],
            [4.0, 5.0, "OA"],
            [5.0, 6.0, "OA"],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH, Headers.ANNULUS],
    )
    df_completion_before = df_completion.copy(deep=True)
    df_true = pd.DataFrame(
        [
            [1.0, 2.0, "OA", 1],
            [2.0, 3.0, "OA", 1],
            [3.0, 4.0, "OA", 1],
            [4.0, 5.0, "OA", 1],
            [5.0, 6.0, "OA", 1],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH, Headers.ANNULUS, Headers.ANNULUS_ZONE],
    )

    df_test = completion.define_annulus_zone(df_completion)
    pd.testing.assert_frame_equal(df_completion_before, df_completion)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_define_annulus_zone_continuous_annulus_2():
    """Test define_annulus_zone gives one continuous open annulus segment
    when they are not interrupted by packers or gravel packs.
    """
    df_completion = pd.DataFrame(
        [
            [1.0, 2.0, "GP"],
            [2.0, 3.0, "GP"],
            [3.0, 4.0, "OA"],
            [4.0, 5.0, "OA"],
            [5.0, 6.0, "GP"],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH, Headers.ANNULUS],
    )
    df_completion_before = df_completion.copy(deep=True)
    df_true = pd.DataFrame(
        [
            [1.0, 2.0, "GP", 0],
            [2.0, 3.0, "GP", 0],
            [3.0, 4.0, "OA", 1],
            [4.0, 5.0, "OA", 1],
            [5.0, 6.0, "GP", 0],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH, Headers.ANNULUS, Headers.ANNULUS_ZONE],
    )

    df_test = completion.define_annulus_zone(df_completion)
    pd.testing.assert_frame_equal(df_completion_before, df_completion)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_define_annulus_zone_no_open_annulus():
    """Test define_annulus_zone gives no open annulus segments when all segments are gravel packs."""
    df_completion = pd.DataFrame(
        [
            [1.0, 2.0, "GP"],
            [2.0, 3.0, "GP"],
            [3.0, 4.0, "GP"],
            [4.0, 5.0, "GP"],
            [5.0, 6.0, "GP"],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH, Headers.ANNULUS],
    )
    df_completion_before = df_completion.copy(deep=True)
    df_true = pd.DataFrame(
        [
            [1.0, 2.0, "GP", 0],
            [2.0, 3.0, "GP", 0],
            [3.0, 4.0, "GP", 0],
            [4.0, 5.0, "GP", 0],
            [5.0, 6.0, "GP", 0],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH, Headers.ANNULUS, Headers.ANNULUS_ZONE],
    )

    df_test = completion.define_annulus_zone(df_completion)
    pd.testing.assert_frame_equal(df_completion_before, df_completion)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_create_tubing_segments_cells():
    """Test create_tubing_segment with the cells option."""
    df_completion = pd.DataFrame(
        [
            [1.0, 2.0],
            [2.0, 3.0],
            [3.0, 4.0],
            [4.0, 5.0],
            [5.0, 6.0],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
    )
    df_reservoir = df_completion.copy()
    df_mdtvd = pd.DataFrame(
        [
            [0, 0],
            [10, 10],
        ],
        columns=[Headers.MEASURED_DEPTH, Headers.TRUE_VERTICAL_DEPTH],
    )
    df_true = pd.DataFrame(
        [
            [1.0, 2.0, 1.5, 1.5],
            [2.0, 3.0, 2.5, 2.5],
            [3.0, 4.0, 3.5, 3.5],
            [4.0, 5.0, 4.5, 4.5],
            [5.0, 6.0, 5.5, 5.5],
        ],
        columns=[
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.TUBING_MEASURED_DEPTH,
            Headers.TRUE_VERTICAL_DEPTH,
        ],
    )

    df_test = completion.create_tubing_segments(df_reservoir, df_completion, df_mdtvd, method="CELLS")
    pd.testing.assert_frame_equal(df_test, df_true)


def test_create_tubing_segments_cells_with_input_lumping():
    """Test create_tubing_segment with the cells option with lumping."""
    df_completion = pd.DataFrame(
        [
            [1.0, 2.0],
            [2.0, 3.0],
            [3.0, 4.0],
            [4.0, 5.0],
            [5.0, 6.0],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
    )
    df_reservoir = pd.DataFrame(
        [
            [1.0, 2.0, 1],
            [2.0, 3.0, 1],
            [3.0, 4.0, 2],
            [4.0, 5.0, 2],
            [5.0, 6.0, 2],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH, Headers.SEGMENT],
    )
    df_mdtvd = pd.DataFrame(
        [
            [0, 0],
            [10, 10],
        ],
        columns=[Headers.MEASURED_DEPTH, Headers.TRUE_VERTICAL_DEPTH],
    )
    df_true = pd.DataFrame(
        [
            [1.0, 3.0, 2.0, 2.0],
            [3.0, 6.0, 4.5, 4.5],
        ],
        columns=[
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.TUBING_MEASURED_DEPTH,
            Headers.TRUE_VERTICAL_DEPTH,
        ],
    )

    df_test = completion.create_tubing_segments(df_reservoir, df_completion, df_mdtvd, method="CELLS")
    pd.testing.assert_frame_equal(df_test, df_true)


def test_minimum_segment_length_gt_zero():
    """Test create_tubing_segment, cells option, user defined minimum segment length."""
    minimum_segment_length = 12.0
    df_completion = pd.DataFrame(
        [
            [0.0, 12.0],
            [12.0, 13.0],
            [13.0, 20.0],
            [20.0, 29.0],
            [29.0, 30.0],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
    )
    df_reservoir = df_completion.copy()
    df_mdtvd = pd.DataFrame(
        [
            [0, 0],
            [30, 30],
        ],
        columns=[Headers.MEASURED_DEPTH, Headers.TRUE_VERTICAL_DEPTH],
    )
    df_true = pd.DataFrame(
        [
            [0.0, 12.0, 6.0, 6.0],
            [12.0, 29.0, 20.5, 20.5],
            [29.0, 30.0, 29.5, 29.5],
        ],
        columns=[
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.TUBING_MEASURED_DEPTH,
            Headers.TRUE_VERTICAL_DEPTH,
        ],
    )

    df_test = completion.create_tubing_segments(
        df_reservoir,
        df_completion,
        df_mdtvd,
        method="CELLS",
        minimum_segment_length=minimum_segment_length,
    )
    pd.testing.assert_frame_equal(df_test, df_true)


def test_minimum_segment_length_eq_zero():
    """Test create_tubing_segment, cells option, user defined minimum segment length."""
    minimum_segment_length = 0.0
    df_completion = pd.DataFrame(
        [
            [0.0, 12.0],
            [12.0, 13.0],
            [13.0, 20.0],
            [20.0, 29.0],
            [29.0, 30.0],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
    )
    df_reservoir = df_completion.copy()
    df_mdtvd = pd.DataFrame(
        [
            [0, 0],
            [30, 30],
        ],
        columns=[Headers.MEASURED_DEPTH, Headers.TRUE_VERTICAL_DEPTH],
    )
    df_true = pd.DataFrame(
        [
            [0.0, 12.0, 6.0, 6.0],
            [12.0, 13.0, 12.5, 12.5],
            [13.0, 20.0, 16.5, 16.5],
            [20.0, 29.0, 24.5, 24.5],
            [29.0, 30.0, 29.5, 29.5],
        ],
        columns=[
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.TUBING_MEASURED_DEPTH,
            Headers.TRUE_VERTICAL_DEPTH,
        ],
    )

    df_test = completion.create_tubing_segments(
        df_reservoir, df_completion, df_mdtvd, method="CELLS", minimum_segment_length=minimum_segment_length
    )
    pd.testing.assert_frame_equal(df_test, df_true)


def test_minimum_segment_length_default():
    """Test create_tubing_segment, cells option, user defined minimum segment length."""
    df_completion = pd.DataFrame(
        [
            [0.0, 12.0],
            [12.0, 13.0],
            [13.0, 20.0],
            [20.0, 29.0],
            [29.0, 30.0],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
    )
    df_reservoir = df_completion.copy()
    df_mdtvd = pd.DataFrame(
        [
            [0, 0],
            [30, 30],
        ],
        columns=[Headers.MEASURED_DEPTH, Headers.TRUE_VERTICAL_DEPTH],
    )
    df_true = pd.DataFrame(
        [
            [0.0, 12.0, 6.0, 6.0],
            [12.0, 13.0, 12.5, 12.5],
            [13.0, 20.0, 16.5, 16.5],
            [20.0, 29.0, 24.5, 24.5],
            [29.0, 30.0, 29.5, 29.5],
        ],
        columns=[
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.TUBING_MEASURED_DEPTH,
            Headers.TRUE_VERTICAL_DEPTH,
        ],
    )
    df_test = completion.create_tubing_segments(
        df_reservoir,
        df_completion,
        df_mdtvd,
        method="CELLS",
    )
    pd.testing.assert_frame_equal(df_test, df_true)


def test_create_tubing_segments_user():
    """Test create_tubing_segment with the user option."""
    df_completion = pd.DataFrame(
        [
            [1.0, 2.0],
            [5.0, 6.0],
            [6.5, 7.0],
            [8.1, 8.7],
            [9.0, 9.5],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
    )
    df_reservoir = df_completion.copy()
    df_mdtvd = pd.DataFrame(
        [
            [0, 0],
            [10, 10],
        ],
        columns=[Headers.MEASURED_DEPTH, Headers.TRUE_VERTICAL_DEPTH],
    )
    df_true = pd.DataFrame(
        [
            [1.0, 2.0, 1.5, 1.5],
            [5.0, 6.0, 5.5, 5.5],
            [6.5, 7.0, 6.75, 6.75],
            [8.1, 8.7, 8.399999999999999, 8.399999999999999],
            [9.0, 9.5, 9.25, 9.25],
        ],
        columns=[
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.TUBING_MEASURED_DEPTH,
            Headers.TRUE_VERTICAL_DEPTH,
        ],
    )

    df_test = completion.create_tubing_segments(df_reservoir, df_completion, df_mdtvd, "USER")
    pd.testing.assert_frame_equal(df_test, df_true)


def test_create_tubing_segments_fix_15():
    """Test create_tubing_segment with fixed segment length of 1.5."""
    df_completion = pd.DataFrame(
        [
            [1.0, 2.0],
            [2.0, 3.0],
            [3.0, 4.0],
            [4.0, 5.0],
            [5.0, 6.0],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
    )
    df_reservoir = df_completion.copy()
    df_mdtvd = pd.DataFrame(
        [
            [0, 0],
            [10, 10],
        ],
        columns=[Headers.MEASURED_DEPTH, Headers.TRUE_VERTICAL_DEPTH],
    )
    df_true = pd.DataFrame(
        [
            [1.0, 2.5, 1.75, 1.75],
            [2.5, 4.0, 3.25, 3.25],
            [4.0, 5.5, 4.75, 4.75],
            [5.5, 6.0, 5.75, 5.75],
        ],
        columns=[
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.TUBING_MEASURED_DEPTH,
            Headers.TRUE_VERTICAL_DEPTH,
        ],
    )

    df_test = completion.create_tubing_segments(df_reservoir, df_completion, df_mdtvd, "FIX", 1.5)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_create_tubing_segments_fix_1():
    """Test create_tubing_segment with fixed segment length of 1.0."""
    df_completion = pd.DataFrame(
        [
            [1.0, 2.0],
            [2.0, 3.0],
            [3.0, 4.0],
            [4.0, 5.0],
            [5.0, 6.0],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
    )
    df_reservoir = df_completion.copy()
    df_mdtvd = pd.DataFrame(
        [
            [0, 0],
            [10, 10],
        ],
        columns=[Headers.MEASURED_DEPTH, Headers.TRUE_VERTICAL_DEPTH],
    )
    df_true = pd.DataFrame(
        [
            [1.0, 2.0, 1.5, 1.5],
            [2.0, 3.0, 2.5, 2.5],
            [3.0, 4.0, 3.5, 3.5],
            [4.0, 5.0, 4.5, 4.5],
            [5.0, 6.0, 5.5, 5.5],
        ],
        columns=[
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.TUBING_MEASURED_DEPTH,
            Headers.TRUE_VERTICAL_DEPTH,
        ],
    )

    df_test = completion.create_tubing_segments(df_reservoir, df_completion, df_mdtvd, "FIX", 1.0)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_create_tubing_segment_welsegs():
    """Test creating_tubing_segments with the welsegs option."""
    df_completion = pd.DataFrame(
        [
            [1.0, 2.0],
            [5.0, 6.0],
        ],
        columns=[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH],
    )
    df_reservoir = df_completion.copy()
    df_mdtvd = pd.DataFrame(
        [
            [0.0, 0.0],
            [3.0, 3.0],
            [4.0, 4.0],
            [5.0, 5.0],
            [6.0, 6.0],
        ],
        columns=[Headers.MEASURED_DEPTH, Headers.TRUE_VERTICAL_DEPTH],
    )
    df_true = pd.DataFrame(
        [
            [0.0, 1.0, 0.50, 0.50],
            [1.0, 1.5, 1.25, 1.25],
            [1.5, 2.0, 1.75, 1.75],
            [2.0, 4.5, 3.25, 3.25],
            [4.5, 5.0, 4.75, 4.75],
            [5.0, 6.0, 5.50, 5.50],
        ],
        columns=[
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.TUBING_MEASURED_DEPTH,
            Headers.TRUE_VERTICAL_DEPTH,
        ],
    )

    df_test = completion.create_tubing_segments(df_reservoir, df_completion, df_mdtvd, Method.WELSEGS)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_complete_the_well():
    """Test the complete_the_well function."""
    df_completion = pd.DataFrame(
        [
            [0, 20, 1, 1.2, 2.1, 1.1, "AICD", 1, 1],
            [20, 30, 2, 1, 5, 2.0, "ICD", 2, 0],
            [30, 40, 3, 2, 3, 3.0, "VALVE", 3, 2],
            [40, 50, 3.5, 3, 4, 4.0, "DAR", 4, 3],
        ],
        columns=[
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.VALVES_PER_JOINT,
            Headers.INNER_DIAMETER,
            Headers.OUTER_DIAMETER,
            Headers.ROUGHNESS,
            Headers.DEVICE_TYPE,
            Headers.DEVICE_NUMBER,
            Headers.ANNULUS_ZONE,
        ],
    )

    df_tubing = pd.DataFrame(
        [
            [0, 26, 13, 19.5, "OriginalSegment"],
            [26, 35, 30.5, 32.75, "AdditionalSegment"],
            [35, 50, 42.5, 46.25, "OriginalSegment"],
        ],
        columns=[
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.TUBING_MEASURED_DEPTH,
            Headers.TRUE_VERTICAL_DEPTH,
            Headers.SEGMENT_DESC,
        ],
    )
    df_true = pd.DataFrame(
        [
            [13, 19.5, 26, "OriginalSegment", 3.2, 1, "AICD", 1.2, 1.723368794, 1.1, 1, -0.3125],
            [42.5, 46.25, 15, "OriginalSegment", 5, 4, "DAR", 3, 2.645751311, 4, 3, -0.2],
        ],
        columns=[
            Headers.TUBING_MEASURED_DEPTH,
            Headers.TRUE_VERTICAL_DEPTH,
            Headers.LENGTH,
            Headers.SEGMENT_DESC,
            Headers.NUMBER_OF_DEVICES,
            Headers.DEVICE_NUMBER,
            Headers.DEVICE_TYPE,
            Headers.INNER_DIAMETER,
            Headers.OUTER_DIAMETER,
            Headers.ROUGHNESS,
            Headers.ANNULUS_ZONE,
            Headers.SCALE_FACTOR,
        ],
    )

    joint_length = 10.0
    df_test = completion.complete_the_well(df_tubing, df_completion, joint_length)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_lumping_segment_1():
    """Test lumping_segment lumps the additional segment only with original segment containing an annulus zone."""
    df_well = pd.DataFrame(
        [
            [1.0, 0, Headers.ORIGINAL_SEGMENT],
            [2.0, 0, Headers.ORIGINAL_SEGMENT],
            [3.0, 1, Headers.ADDITIONAL_SEGMENT],
            [4.0, 1, Headers.ORIGINAL_SEGMENT],
        ],
        columns=[Headers.NUMBER_OF_DEVICES, Headers.ANNULUS_ZONE, Headers.SEGMENT_DESC],
    )
    df_true = pd.DataFrame(
        [
            [1.0, 0, Headers.ORIGINAL_SEGMENT],
            [2.0, 0, Headers.ORIGINAL_SEGMENT],
            [7.0, 1, Headers.ORIGINAL_SEGMENT],
        ],
        columns=[Headers.NUMBER_OF_DEVICES, Headers.ANNULUS_ZONE, Headers.SEGMENT_DESC],
    )

    df_test = completion.lumping_segments(df_well)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_lumping_segment_2():
    """Test lumping_segment lumps the additional segment only with original segment containing an annulus zone."""
    df_well = pd.DataFrame(
        [
            [1.0, 0, Headers.ORIGINAL_SEGMENT],
            [2.0, 1, Headers.ORIGINAL_SEGMENT],
            [3.0, 1, Headers.ADDITIONAL_SEGMENT],
            [4.0, 1, Headers.ORIGINAL_SEGMENT],
        ],
        columns=[Headers.NUMBER_OF_DEVICES, Headers.ANNULUS_ZONE, Headers.SEGMENT_DESC],
    )
    df_true = pd.DataFrame(
        [
            [1.0, 0, Headers.ORIGINAL_SEGMENT],
            [5.0, 1, Headers.ORIGINAL_SEGMENT],
            [4.0, 1, Headers.ORIGINAL_SEGMENT],
        ],
        columns=[Headers.NUMBER_OF_DEVICES, Headers.ANNULUS_ZONE, Headers.SEGMENT_DESC],
    )

    df_test = completion.lumping_segments(df_well)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_skin():
    """Test handle_compdat with a mix of values in COMPDAT, SKIN column."""
    compdat = [
        #                                                       SKIN
        ["A1", "3", "6", "1", "1", Headers.OPEN, "1*", "1", "2", "2", "0.0", "1*", "X", "1"],
        ["A1", "2", "6", "1", "1", Headers.OPEN, "1*", "8", "2", "1", "1*", "1*", "X", "1"],
        ["A1", "2", "6", "2", "2", Headers.OPEN, "1*", "2", "2", "4", "5.5", "1*", "X", "1"],
        ["A1", "2", "6", "3", "3", Headers.OPEN, "1*", "1", "2", "2", "1*", "1*", "X", "1"],
        ["A1", "1", "6", "3", "3", Headers.OPEN, "1*", "9", "2", "1", "2", "1*", "X", "1"],
    ]

    df_true = pd.DataFrame(
        [
            #                                               SKIN
            ["A1", 3, 6, 1, 1, Headers.OPEN, "1*", 1.0, 2.0, 2.0, 0.0, "1*", "X", 1.0],
            ["A1", 2, 6, 1, 1, Headers.OPEN, "1*", 8.0, 2.0, 1.0, 0.0, "1*", "X", 1.0],
            ["A1", 2, 6, 2, 2, Headers.OPEN, "1*", 2.0, 2.0, 4.0, 5.5, "1*", "X", 1.0],
            ["A1", 2, 6, 3, 3, Headers.OPEN, "1*", 1.0, 2.0, 2.0, 0.0, "1*", "X", 1.0],
            ["A1", 1, 6, 3, 3, Headers.OPEN, "1*", 9.0, 2.0, 1.0, 2.0, "1*", "X", 1.0],
        ],
        columns=[
            Headers.WELL,
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
        ],
    )
    active_wells = np.array(["A1"])
    schedule_data = completor.read_schedule.handle_compdat({}, active_wells, compdat)
    df_out = schedule_data["A1"][Keywords.COMPDAT]
    pd.testing.assert_frame_equal(df_out, df_true)


def test_set_welsegs_negative_length_segments(caplog):
    """Test that negative segments inside a branch give a warning."""
    active_wells = np.array(["A1"])
    completor.read_schedule.set_welsegs(
        {},
        active_wells,
        [
            ["A1", 2000.86739, 2186.68410, "1*", "ABS", "HF-", "NaN", "NaN"],
            [2, 2, 1, 1, 2202.75139, 2005.28911, 0.15200, 0.0000100],
            [3, 3, 1, 2, 2200.73413, 2007.00000, 0.15200, 0.0000100],
            [4, 4, 1, 3, 2219.76749, 2008.87380, 0.15200, 0.0000100],
        ],
    )
    assert len(caplog.text) > 0
    assert "WARNING" in caplog.text
