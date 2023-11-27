"""Test functions for the Completor completion module."""

from __future__ import annotations

from io import StringIO

import pandas as pd
import pytest

from completor import completion  # type: ignore


def test_completion_index():
    """Test completion_index gives correct indexes for start and end measured depth."""
    df_tubing_segments = pd.DataFrame([[1000, 2000], [2000, 3000], [3000, 4000]], columns=["STARTMD", "ENDMD"])
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
        columns=["TUB_MD"],
    )
    df_tubing_segments = pd.DataFrame(
        [
            [0.5, 1.5],
            [4.5, 5.5],
            [7.5, 8.5],
        ],
        columns=["STARTMD", "ENDMD"],
    )
    df_compsegs = pd.DataFrame(
        [[0.0, 3.00], [3.0, 10.0], [10.0, 20.0]],
        columns=["STARTMD", "ENDMD"],
    )
    df_merge = pd.DataFrame(
        [
            [0.0, 3.0, 1.5, 1.0],
            [3.0, 10.0, 6.5, 5.0],
            [10.0, 20.0, 15.0, 8.0],
        ],
        columns=["STARTMD", "ENDMD", "MD", "TUB_MD"],
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
        columns=["TUB_MD"],
    )
    df_tubing_segments = pd.DataFrame(
        [
            [0.5, 1.5],
            [14.5, 15.5],
            [17.5, 18.5],
        ],
        columns=["STARTMD", "ENDMD"],
    )
    df_compsegs = pd.DataFrame(
        [
            [0.0, 3.00],
            [3.0, 10.0],
            [10.0, 20.0],
        ],
        columns=["STARTMD", "ENDMD"],
    )

    df_merge = pd.DataFrame(
        [
            [0.0, 3.0, 1.5, 1.0],
            [3.0, 10.0, 6.5, 1.0],
            [10.0, 20.0, 15.0, 15.0],
        ],
        columns=["STARTMD", "ENDMD", "MD", "TUB_MD"],
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
        columns=["TUB_MD"],
    )
    df_tubing_segments = pd.DataFrame(
        [
            [0.0, 5.0],
            [2.6, 7.5],
            [7.5, 20.0],
        ],
        columns=["STARTMD", "ENDMD"],
    )
    df_compsegs = pd.DataFrame(
        [
            [0.0, 3.00],
            [3.0, 10.0],
            [10.0, 20.0],
        ],
        columns=["STARTMD", "ENDMD"],
    )
    df_merge = pd.DataFrame(
        [
            [0.0, 3.0, 1.5, 2.5],
            [3.0, 10.0, 6.5, 5.0],
            [10.0, 20.0, 15.0, 10.0],
        ],
        columns=["STARTMD", "ENDMD", "MD", "TUB_MD"],
    )

    df_test = completion.connect_cells_to_segments(df_segment, df_compsegs, df_tubing_segments, method="user")
    pd.testing.assert_frame_equal(df_test, df_merge)


def test_insert_missing_segments_no_gap():
    """
    Test insert_missing_segments does not insert dummy segments when
    there are no inactive cells.
    """
    df_tubing_segments = pd.DataFrame(
        [
            [1000, 2000],
            [2000, 3000],
            [3000, 4000],
        ],
        columns=["STARTMD", "ENDMD"],
    )
    df_true = pd.DataFrame(
        [
            [1000, 2000, "OriginalSegment"],
            [2000, 3000, "OriginalSegment"],
            [3000, 4000, "OriginalSegment"],
        ],
        columns=["STARTMD", "ENDMD", "SEGMENT_DESC"],
    )

    df_test = completion.insert_missing_segments(df_tubing_segments, "A1")
    pd.testing.assert_frame_equal(df_test, df_true)


def test_insert_missing_segments_one_gap():
    """Test insert_missing_segments inserts one dummy segments due to inactive cells."""
    df_tubing_segments = pd.DataFrame(
        [
            [1000, 2000],
            [2500, 3000],
            [3000, 4000],
        ],
        columns=["STARTMD", "ENDMD"],
    )
    df_true = pd.DataFrame(
        [
            [1000, 2000, "OriginalSegment"],
            [2000, 2500, "AdditionalSegment"],
            [2500, 3000, "OriginalSegment"],
            [3000, 4000, "OriginalSegment"],
        ],
        columns=["STARTMD", "ENDMD", "SEGMENT_DESC"],
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
        columns=["STARTMD", "ENDMD"],
    )
    df_true = pd.DataFrame(
        [
            [1000, 2000, "OriginalSegment"],
            [2000, 2500, "AdditionalSegment"],
            [2500, 3000, "OriginalSegment"],
            [3000, 3005, "AdditionalSegment"],
            [3005, 4000, "OriginalSegment"],
        ],
        columns=["STARTMD", "ENDMD", "SEGMENT_DESC"],
    )

    df_test = completion.insert_missing_segments(df_tubing_segments, "A1")
    pd.testing.assert_frame_equal(df_test, df_true)


def test_insert_missing_segments_raise_error():
    """Test that an error is raised when there is no data in df_tubing_segments."""
    df_tubing_segments = pd.DataFrame([], columns=["STARTMD", "ENDMD"])

    with pytest.raises(SystemExit):
        completion.insert_missing_segments(df_tubing_segments, "A1")


def test_well_trajectory():
    """
    Test well_trajectory creates correct relation (sorted by MD) between
    well segments' (welsegs) header and content.
    """
    df_welsegs_header = pd.DataFrame(
        [
            [2.0, 1.0],
        ],
        columns=["SEGMENTMD", "SEGMENTTVD"],
    )
    df_welsegs_content = pd.DataFrame(
        [
            [5.0, 1.0],
            [4.0, 3.0],
        ],
        columns=["TUBINGMD", "TUBINGTVD"],
    )
    df_true = pd.DataFrame(
        [
            [2.0, 1.0],
            [4.0, 3.0],
            [5.0, 1.0],
        ],
        columns=["MD", "TVD"],
    )

    df_test = completion.well_trajectory(df_welsegs_header, df_welsegs_content)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_define_annulus_zone_keep_gravel_pack_1():
    """
    Test define_annulus_zone gives open annulus segment
    when interrupted by packer segments and gravel packs.

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
        columns=["STARTMD", "ENDMD", "ANNULUS"],
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
        columns=["STARTMD", "ENDMD", "ANNULUS", "ANNULUS_ZONE"],
    )

    df_test = completion.define_annulus_zone(df_completion)
    pd.testing.assert_frame_equal(df_completion_before, df_completion)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_define_annulus_zone_keep_gravel_pack_2():
    """
    Test define_annulus_zone gives open annulus segment
    when interrupted by packer segments and gravel packs.

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
        columns=["STARTMD", "ENDMD", "ANNULUS"],
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
        columns=["STARTMD", "ENDMD", "ANNULUS", "ANNULUS_ZONE"],
    )

    df_test = completion.define_annulus_zone(df_completion)
    pd.testing.assert_frame_equal(df_completion_before, df_completion)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_define_annulus_zone_packer_segments():
    """
    Test define_annulus_zone gives three open annulus segment
    when interrupted by packer segments.

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
        columns=["STARTMD", "ENDMD", "ANNULUS"],
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
        columns=["STARTMD", "ENDMD", "ANNULUS", "ANNULUS_ZONE"],
    )

    df_test = completion.define_annulus_zone(df_completion)
    pd.testing.assert_frame_equal(df_completion_before, df_completion)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_define_annulus_zone_continious_annulus_1():
    """
    Test define_annulus_zone gives one continious open annulus segment
    when all segment are open annulus.
    """
    df_completion = pd.DataFrame(
        [
            [1.0, 2.0, "OA"],
            [2.0, 3.0, "OA"],
            [3.0, 4.0, "OA"],
            [4.0, 5.0, "OA"],
            [5.0, 6.0, "OA"],
        ],
        columns=["STARTMD", "ENDMD", "ANNULUS"],
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
        columns=["STARTMD", "ENDMD", "ANNULUS", "ANNULUS_ZONE"],
    )

    df_test = completion.define_annulus_zone(df_completion)
    pd.testing.assert_frame_equal(df_completion_before, df_completion)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_define_annulus_zone_continious_annulus_2():
    """
    Test define_annulus_zone gives one continious open annulus segment
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
        columns=["STARTMD", "ENDMD", "ANNULUS"],
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
        columns=["STARTMD", "ENDMD", "ANNULUS", "ANNULUS_ZONE"],
    )

    df_test = completion.define_annulus_zone(df_completion)
    pd.testing.assert_frame_equal(df_completion_before, df_completion)
    pd.testing.assert_frame_equal(df_test, df_true)


def test_define_annulus_zone_no_open_annulus():
    """
    Test define_annulus_zone gives no open annulus segments
    when all segments are gravel packs.
    """
    df_completion = pd.DataFrame(
        [
            [1.0, 2.0, "GP"],
            [2.0, 3.0, "GP"],
            [3.0, 4.0, "GP"],
            [4.0, 5.0, "GP"],
            [5.0, 6.0, "GP"],
        ],
        columns=["STARTMD", "ENDMD", "ANNULUS"],
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
        columns=["STARTMD", "ENDMD", "ANNULUS", "ANNULUS_ZONE"],
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
        columns=["STARTMD", "ENDMD"],
    )
    df_reservoir = df_completion.copy()
    df_mdtvd = pd.DataFrame(
        [
            [0, 0],
            [10, 10],
        ],
        columns=["MD", "TVD"],
    )
    df_true = pd.DataFrame(
        [
            [1.0, 2.0, 1.5, 1.5],
            [2.0, 3.0, 2.5, 2.5],
            [3.0, 4.0, 3.5, 3.5],
            [4.0, 5.0, 4.5, 4.5],
            [5.0, 6.0, 5.5, 5.5],
        ],
        columns=["STARTMD", "ENDMD", "TUB_MD", "TUB_TVD"],
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
        columns=["STARTMD", "ENDMD"],
    )
    df_reservoir = pd.DataFrame(
        [
            [1.0, 2.0, 1],
            [2.0, 3.0, 1],
            [3.0, 4.0, 2],
            [4.0, 5.0, 2],
            [5.0, 6.0, 2],
        ],
        columns=["STARTMD", "ENDMD", "SEGMENT"],
    )
    df_mdtvd = pd.DataFrame(
        [
            [0, 0],
            [10, 10],
        ],
        columns=["MD", "TVD"],
    )
    df_true = pd.DataFrame(
        [
            [1.0, 3.0, 2.0, 2.0],
            [3.0, 6.0, 4.5, 4.5],
        ],
        columns=["STARTMD", "ENDMD", "TUB_MD", "TUB_TVD"],
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
        columns=["STARTMD", "ENDMD"],
    )
    df_reservoir = df_completion.copy()
    df_mdtvd = pd.DataFrame(
        [
            [0, 0],
            [30, 30],
        ],
        columns=["MD", "TVD"],
    )
    df_true = pd.DataFrame(
        [
            [0.0, 12.0, 6.0, 6.0],
            [12.0, 29.0, 20.5, 20.5],
            [29.0, 30.0, 29.5, 29.5],
        ],
        columns=["STARTMD", "ENDMD", "TUB_MD", "TUB_TVD"],
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
        columns=["STARTMD", "ENDMD"],
    )
    df_reservoir = df_completion.copy()
    df_mdtvd = pd.DataFrame(
        [
            [0, 0],
            [30, 30],
        ],
        columns=["MD", "TVD"],
    )
    df_true = pd.DataFrame(
        [
            [0.0, 12.0, 6.0, 6.0],
            [12.0, 13.0, 12.5, 12.5],
            [13.0, 20.0, 16.5, 16.5],
            [20.0, 29.0, 24.5, 24.5],
            [29.0, 30.0, 29.5, 29.5],
        ],
        columns=["STARTMD", "ENDMD", "TUB_MD", "TUB_TVD"],
    )

    df_test = completion.create_tubing_segments(
        df_reservoir,
        df_completion,
        df_mdtvd,
        method="CELLS",
        minimum_segment_length=minimum_segment_length,
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
        columns=["STARTMD", "ENDMD"],
    )
    df_reservoir = df_completion.copy()
    df_mdtvd = pd.DataFrame(
        [
            [0, 0],
            [30, 30],
        ],
        columns=["MD", "TVD"],
    )
    df_true = pd.DataFrame(
        [
            [0.0, 12.0, 6.0, 6.0],
            [12.0, 13.0, 12.5, 12.5],
            [13.0, 20.0, 16.5, 16.5],
            [20.0, 29.0, 24.5, 24.5],
            [29.0, 30.0, 29.5, 29.5],
        ],
        columns=["STARTMD", "ENDMD", "TUB_MD", "TUB_TVD"],
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
        columns=["STARTMD", "ENDMD"],
    )
    df_reservoir = df_completion.copy()
    df_mdtvd = pd.DataFrame(
        [
            [0, 0],
            [10, 10],
        ],
        columns=["MD", "TVD"],
    )
    df_true = pd.DataFrame(
        [
            [1.0, 2.0, 1.5, 1.5],
            [5.0, 6.0, 5.5, 5.5],
            [6.5, 7.0, 6.75, 6.75],
            [8.1, 8.7, 8.399999999999999, 8.399999999999999],
            [9.0, 9.5, 9.25, 9.25],
        ],
        columns=["STARTMD", "ENDMD", "TUB_MD", "TUB_TVD"],
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
        columns=["STARTMD", "ENDMD"],
    )
    df_reservoir = df_completion.copy()
    df_mdtvd = pd.DataFrame(
        [
            [0, 0],
            [10, 10],
        ],
        columns=["MD", "TVD"],
    )
    df_true = pd.DataFrame(
        [
            [1.0, 2.5, 1.75, 1.75],
            [2.5, 4.0, 3.25, 3.25],
            [4.0, 5.5, 4.75, 4.75],
            [5.5, 6.0, 5.75, 5.75],
        ],
        columns=["STARTMD", "ENDMD", "TUB_MD", "TUB_TVD"],
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
        columns=["STARTMD", "ENDMD"],
    )
    df_reservoir = df_completion.copy()
    df_mdtvd = pd.DataFrame(
        [
            [0, 0],
            [10, 10],
        ],
        columns=["MD", "TVD"],
    )
    df_true = pd.DataFrame(
        [
            [1.0, 2.0, 1.5, 1.5],
            [2.0, 3.0, 2.5, 2.5],
            [3.0, 4.0, 3.5, 3.5],
            [4.0, 5.0, 4.5, 4.5],
            [5.0, 6.0, 5.5, 5.5],
        ],
        columns=["STARTMD", "ENDMD", "TUB_MD", "TUB_TVD"],
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
        columns=["STARTMD", "ENDMD"],
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
        columns=["MD", "TVD"],
    )
    df_true = pd.DataFrame(
        [
            [0.0, 1.0, 0.50, 0.50],
            [1.0, 1.5, 1.25, 1.25],
            [1.5, 2.0, 1.75, 1.75],
            [2.0, 4.5, 3.25, 3.25],
            [4.5, 5.0, 4.75, 4.75],
            [5.0, 6.0, 5.50, 5.50],
