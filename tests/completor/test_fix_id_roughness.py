"""Tests the function prepare_output.py::fix_id_roughness."""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from completor.prepare_outputs import fix_tubing_inner_diam_roughness


def test_fix_inner_diam_roughness_default_parameters():
    """Tests fix_inner_diam_roughness with default parameters."""
    well_name = "A1"
    overburden = pd.DataFrame(
        [["A1", 1, 2000.0, 0.15, 0.00065]],
        columns=["WELL", "TUBINGBRANCH", "MD", "DIAM", "ROUGHNESS"],
    )
    completion_table = pd.DataFrame(
        [["A1", 1, 0.0, 5000.0, 0.2, 0.00035]],
        columns=["WELL", "BRANCH", "STARTMD", "ENDMD", "INNER_ID", "ROUGHNESS"],
    )
    true_overburden = pd.DataFrame(
        [["A1", 1, 2000.0, 0.2, 0.00035]],
        columns=["WELL", "TUBINGBRANCH", "MD", "DIAM", "ROUGHNESS"],
    )
    test_overburden = fix_tubing_inner_diam_roughness(well_name, overburden, completion_table)
    assert_frame_equal(test_overburden, true_overburden)


def test_overburden_md_at_boundary():
    """
    Test fix_id_roughness with overburden depth at boundary.

    The boundary is specified as between two depths in the case COMPLETION keyword.

    Always select ID and roughness from completion table where starting depth is equal
    to or greater than overburden md and the ending depth is less than or equal to
    the overburden md.
    """
    well_name = "A1"
    overburden = pd.DataFrame(
        [["A1", 1, 2000.0, 0.15, 0.00065]],
        columns=["WELL", "TUBINGBRANCH", "MD", "DIAM", "ROUGHNESS"],
    )
    completion_table = pd.DataFrame(
        [
            ["A1", 1, 0.0, 2000.0, 0.2, 0.00035],
            ["A1", 1, 2000.0, 5000.0, 0.1, 0.00015],
        ],
        columns=["WELL", "BRANCH", "STARTMD", "ENDMD", "INNER_ID", "ROUGHNESS"],
    )
    true_overburden = pd.DataFrame(
        [["A1", 1, 2000.0, 0.2, 0.00035]],
        columns=["WELL", "TUBINGBRANCH", "MD", "DIAM", "ROUGHNESS"],
    )
    test_overburden = fix_tubing_inner_diam_roughness(well_name, overburden, completion_table)
    assert_frame_equal(test_overburden, true_overburden)


def test_overburden_md_above_completion_table():
    """
    Test case with an incomplete completion table.

    The overburden segment md is above the first start and end md in the table.
    """
    well_name = "A1"
    overburden = pd.DataFrame(
        [["A1", 1, 2000.0, 0.15, 0.00065]],
        columns=["WELL", "TUBINGBRANCH", "MD", "DIAM", "ROUGHNESS"],
    )
    completion_table = pd.DataFrame(
        [
            ["A1", 1, 3000.0, 5000.0, 0.2, 0.00035],
            ["A1", 1, 5000.0, 6000.0, 0.1, 0.00025],
        ],
        columns=["WELL", "BRANCH", "STARTMD", "ENDMD", "INNER_ID", "ROUGHNESS"],
    )
    with pytest.raises(ValueError, match="Cannot find A1 completion in overburden at 2000.0 mMD"):
        fix_tubing_inner_diam_roughness(well_name, overburden, completion_table)


def test_overburden_md_outside_completion_table():
    """
    Test case with an incomplete completion table.

    The overburden segment md is below the last start and end md in the table.
    """
    well_name = "A1"
    overburden = pd.DataFrame(
        [["A1", 1, 5000.0, 0.15, 0.00065]],
        columns=["WELL", "TUBINGBRANCH", "MD", "DIAM", "ROUGHNESS"],
    )
    completion_table = pd.DataFrame(
        [
            ["A1", 1, 0.0, 2000.0, 0.2, 0.00035],
            ["A1", 1, 2000.0, 4000.0, 0.1, 0.00055],
        ],
        columns=["WELL", "BRANCH", "STARTMD", "ENDMD", "INNER_ID", "ROUGHNESS"],
    )
    with pytest.raises(ValueError, match="Cannot find A1 completion in overburden at 5000.0 mMD"):
        fix_tubing_inner_diam_roughness(well_name, overburden, completion_table)
