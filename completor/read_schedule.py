from __future__ import annotations

import numpy as np
import pandas as pd

from completor.constants import Completion, WellSegment
from completor.logger import logger
from completor.utils import sort_by_midpoint


def fix_welsegs(df_header: pd.DataFrame, df_content: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Convert a WELSEGS DataFrame specified in INC to ABS.

    Args:
        df_header: First record table of WELSEGS
        df_content: Second record table of WELSEGS

    Returns:
        tuple: (Updated header DataFrame, Updated content DataFrame)

    The formats of df_header and df_content are shown as df_welsegs_header and
    df_welsegs_content respectively in the function
    :ref:`create_wells.CreateWells.select_well <select_well>`.
    """
    df_header = df_header.copy()
    df_content = df_content.copy()

    if df_header["INFOTYPE"].iloc[0] == "ABS":
        return df_header, df_content

    ref_tvd = df_header["SEGMENTTVD"].iloc[0]
    ref_md = df_header["SEGMENTMD"].iloc[0]
    inlet_segment = df_content[WellSegment.TUBING_SEGMENT].to_numpy()
    outlet_segment = df_content[WellSegment.TUBING_OUTLET].to_numpy()
    md_inc = df_content[WellSegment.TUBING_MD].to_numpy()
    tvd_inc = df_content[WellSegment.TUBING_TVD].to_numpy()
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
    df_header["INFOTYPE"] = ["ABS"]
    df_content[WellSegment.TUBING_MD] = md_new
    df_content[WellSegment.TUBING_TVD] = tvd_new
    return df_header, df_content


def fix_compsegs(df_compsegs: pd.DataFrame, well_name: str) -> pd.DataFrame:
    """
    Fix the problem of having multiple connections in one cell.

    The issue occurs when one cell is penetrated more than once by a well, and happens
    when there are big cells and the well path is complex.
    The issue can be observed from a COMPSEGS definition that has overlapping start and
    end measured depth.

    Args:
        df_compsegs: DataFrame
        well_name: Well name

    Returns:
        Sorted DataFrame

    The DataFrame df is obtained from`` msws[well_name]['compsegs']``
    and has the following format:

        .. _compsegs_format:
        .. list-table:: df
           :widths: 10 10
           :header-rows: 1

           * - COLUMNS
             - TYPE
           * - I
             - int
           * - J
             - int
           * - K
             - int
           * - BRANCH
             - int
           * - STARTMD
             - float
           * - ENDMD
             - float
           * - COMPSEGS_DIRECTION
             - str
           * - ENDGRID
             - object
           * - PERFDEPTH
             - float
           * - THERM
             - object
           * - SEGMENT
             - int
    """
    df_compsegs = df_compsegs.copy(deep=True)
    start_md = df_compsegs[Completion.START_MD].to_numpy()
    end_md = df_compsegs[Completion.END_MD].to_numpy()
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
                logger.info(
