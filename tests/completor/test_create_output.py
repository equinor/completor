"""Test functions for output creation."""

import pandas as pd

from completor import create_output, read_casefile
from completor.constants import Headers, Keywords
from completor.wells import Lateral, Well


def test_connect_lateral_logs_warning(caplog):
    """Test the warning occurs in connect_lateral when given segments with negative length.

    Segments with negative lengths can occur when trying to connect a lateral_number to its main bore/mother branch.
    They are caused by an error in the input, so the user must be warned about this.
    """
    df_tubing_lat_1 = pd.DataFrame(
        [
            [2, 2, 1, 1, 2219.76749],
            [3, 3, 1, 2, 2200.73413],
            [4, 4, 1, 3, 2202.75139],
        ],
        columns=[
            Headers.START_SEGMENT_NUMBER,
            Headers.END_SEGMENT_NUMBER,
            Headers.BRANCH,
            Headers.OUT,
            Headers.MEASURED_DEPTH,
        ],
    )
    df_tubing_lat_2 = pd.DataFrame(
        [
            [16, 16, 5, 15, 2179.9725],
            [17, 17, 5, 16, 2195.5],
        ],
        columns=[
            Headers.START_SEGMENT_NUMBER,
            Headers.END_SEGMENT_NUMBER,
            Headers.BRANCH,
            Headers.OUT,
            Headers.MEASURED_DEPTH,
        ],
    )
    df_top = pd.DataFrame(
        [[1, 2188.76261]],
        columns=[Headers.TUBING_BRANCH, Headers.TUBING_MEASURED_DEPTH],
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
--     Number  MEASURED_DEPTH   MEASURED_DEPTH  Tubing   Casing            Content Joint   Type  Number
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

    wells = Well("A1", case, {})
    lateral = Lateral(1, "A1", case, {})
    lateral.prepared_tubing = df_tubing_lat_1
    lateral2 = Lateral(2, "A1", case, {})
    lateral2.prepared_tubing = df_tubing_lat_2
    wells.active_laterals = [lateral, lateral2]

    create_output._connect_lateral("A1", lateral2, df_top, wells)

    assert len(caplog.text) > 0
    assert "WARNING" in caplog.text
