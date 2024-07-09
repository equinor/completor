from __future__ import annotations

import numpy as np
import pandas as pd

from completor.constants import Headers
from completor.logger import logger
from completor.utils import sort_by_midpoint


def fix_welsegs(df_header: pd.DataFrame, df_content: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convert a WELSEGS DataFrame specified in incremental (INC) to absolute (ABS) values.

    Args:
        df_header: First record table of WELSEGS.
        df_content: Second record table of WELSEGS.

    Returns:
        Updated header DataFrame, Updated content DataFrame.
    """
    df_header = df_header.copy()
    df_content = df_content.copy()

    if df_header[Headers.INFO_TYPE].iloc[0] == "ABS":
        return df_header, df_content

    ref_tvd = df_header[Headers.SEGMENT_TRUE_VERTICAL_DEPTH].iloc[0]
    ref_md = df_header[Headers.SEGMENT_MEASURED_DEPTH].iloc[0]
    inlet_segment = df_content[Headers.TUBING_SEGMENT].to_numpy()
    outlet_segment = df_content[Headers.TUBING_OUTLET].to_numpy()
    md_inc = df_content[Headers.TUBING_MEASURED_DEPTH].to_numpy()
    tvd_inc = df_content[Headers.TUBING_TRUE_VERTICAL_DEPTH].to_numpy()
    md_new = np.zeros(inlet_segment.shape[0])
    tvd_new = np.zeros(inlet_segment.shape[0])

    for idx, idx_segment in enumerate(outlet_segment):
        if idx_segment == 1:
            md_new[idx] = ref_md + md_inc[idx]
            tvd_new[idx] = ref_tvd + tvd_inc[idx]
        else:
            out_idx = np.where(inlet_segment == idx_segment)[0][0]
            md_new[idx] = md_new[out_idx] + md_inc[idx]
            tvd_new[idx] = tvd_new[out_idx] + tvd_inc[idx]

    # update data frame
    df_header[Headers.INFO_TYPE] = ["ABS"]
    df_content[Headers.TUBING_MEASURED_DEPTH] = md_new
    df_content[Headers.TUBING_TRUE_VERTICAL_DEPTH] = tvd_new
    return df_header, df_content


def fix_compsegs(df_compsegs: pd.DataFrame, well_name: str) -> pd.DataFrame:
    """Fix the problem of having multiple connections in one cell.

    The issue occurs when one cell is penetrated more than once by a well, and happens
    when there are big cells and the well path is complex.
    The issue can be observed from a COMPSEGS definition that has overlapping start and end measured depth.

    Args:
        df_compsegs: DataFrame.
        well_name: Well name.

    Returns:
        Sorted DataFrame.
    """
    df_compsegs = df_compsegs.copy(deep=True)
    start_md = df_compsegs[Headers.START_MEASURED_DEPTH].to_numpy()
    end_md = df_compsegs[Headers.END_MEASURED_DEPTH].to_numpy()
    data_length = len(start_md)
    start_md_new = np.zeros(data_length)
    end_md_new = np.zeros(data_length)

    if len(start_md) > 0:
        start_md_new[0] = start_md[0]
        end_md_new[0] = end_md[0]

    # Check the cells connection
    for idx in range(1, len(start_md)):
        if (start_md[idx] - end_md_new[idx - 1]) < -0.1:
            if end_md[idx] > end_md_new[idx - 1]:
                # fix the start of current cells
                start_md_new[idx] = end_md_new[idx - 1]
                end_md_new[idx] = end_md[idx]

            # fix the end of the previous cells
            elif start_md[idx] > start_md_new[idx - 1]:
                end_md_new[idx - 1] = start_md[idx]
                start_md_new[idx - 1] = start_md_new[idx - 1]
                start_md_new[idx] = start_md[idx]
                end_md_new[idx] = end_md[idx]
            else:
                logger.info("Overlapping in COMPSEGS for %s. Sorts the depths accordingly", well_name)
                comb_depth = np.append(start_md, end_md)
                comb_depth = np.sort(comb_depth)
                start_md_new = np.copy(comb_depth[::2])
                end_md_new = np.copy(comb_depth[1::2])
                break
        else:
            start_md_new[idx] = start_md[idx]
            end_md_new[idx] = end_md[idx]
    # In some instances with complex overlapping segments, the algorithm above
    # creates segments where start == end. To overcome this, the following is added.
    for idx in range(1, len(start_md_new) - 1):
        if start_md_new[idx] == end_md_new[idx]:
            if start_md_new[idx + 1] >= end_md_new[idx]:
                end_md_new[idx] = start_md_new[idx + 1]
            if start_md_new[idx] >= end_md_new[idx - 1]:
                start_md_new[idx] = end_md_new[idx - 1]
            else:
                logger.error("Cannot construct COMPSEGS segments based on current input")
    return sort_by_midpoint(df_compsegs, start_md_new, end_md_new)


def fix_compsegs_by_priority(
    df_completion: pd.DataFrame, df_compsegs: pd.DataFrame, df_custom_compsegs: pd.DataFrame
) -> pd.DataFrame:
    """Fixes a dataframe of composition segments, prioritizing the custom compsegs.

    Args:
        df_completion: ..
        df_compsegs: Containing composition segments data.
        df_custom_compsegs: Containing custom composition segments data with priority.

    Returns:
        Fixed composition segments dataframe.
    """
    # slicing two dataframe for user and cells segment length
    start_md_comp = df_completion[
        (df_completion[Headers.DEVICE_TYPE] == "ICV") & (df_completion[Headers.VALVES_PER_JOINT] > 0)
    ][Headers.START_MEASURED_DEPTH].reset_index(drop=True)
    df_custom_compsegs = df_custom_compsegs[df_custom_compsegs[Headers.START_MEASURED_DEPTH].isin(start_md_comp)]
    df_compsegs["priority"] = 1
    df_custom_compsegs = df_custom_compsegs.copy(deep=True)
    df_custom_compsegs["priority"] = 2
    start_end = df_custom_compsegs[[Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH]]
    # Remove the rows that are between the STARTMD and ENDMD
    # values of the custom composition segments.
    for start, end in start_end.values:
        between_lower_upper = (df_compsegs[Headers.START_MEASURED_DEPTH] >= start) & (
            df_compsegs[Headers.END_MEASURED_DEPTH] <= end
        )
        df_compsegs = df_compsegs[~between_lower_upper]

    # Concatenate the fixed df_compsegs dataframe and the df_custom_compsegs
    # dataframe and sort it by the STARTMD column.
    df = (
        pd.concat([df_compsegs, df_custom_compsegs])
        .sort_values(by=[Headers.START_MEASURED_DEPTH])
        .reset_index(drop=True)
    )
    # Filter the dataframe to get only rows where the "priority" column has a value of 2
    for idx in df[df["priority"] == 2].index:
        # Set previous row's ENDMD to correct value.
        df.loc[idx - 1, Headers.END_MEASURED_DEPTH] = df.loc[idx, Headers.START_MEASURED_DEPTH]
        # Set next row's STARTMD to correct value.
        df.loc[idx + 1, Headers.START_MEASURED_DEPTH] = df.loc[idx, Headers.END_MEASURED_DEPTH]
    df = fix_compsegs(df, "Fix compseg after prioriry")
    df = df.dropna()

    return df.drop("priority", axis=1)
