from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from numpy import typing as npt

from completor.constants import Content, Headers, Keywords
from completor.logger import logger
from completor.utils import sort_by_midpoint


def fix_welsegs(df_header: pd.DataFrame, df_content: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Convert a WELL_SEGMENTS DataFrame specified in incremental (INC) to absolute (ABS) values.

    Args:
        df_header: First record table of WELL_SEGMENTS.
        df_content: Second record table of WELL_SEGMENTS.

    Returns:
        Updated header DataFrame, Updated content DataFrame.
    """
    df_header = df_header.copy()
    df_content = df_content.copy()

    if df_header[Headers.INFO_TYPE].iloc[0] == "ABS":
        return df_header, df_content

    ref_tvd = df_header[Headers.TRUE_VERTICAL_DEPTH].iloc[0]
    ref_md = df_header[Headers.MEASURED_DEPTH].iloc[0]
    inlet_segment = df_content[Headers.TUBING_SEGMENT].to_numpy()
    outlet_segment = df_content[Headers.TUBING_OUTLET].to_numpy()
    md_inc = df_content[Headers.TUBING_MEASURED_DEPTH].to_numpy()
    tvd_inc = df_content[Headers.TRUE_VERTICAL_DEPTH].to_numpy()
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
    df_content[Headers.TRUE_VERTICAL_DEPTH] = tvd_new
    return df_header, df_content


def fix_compsegs(df_compsegs: pd.DataFrame, well_name: str) -> pd.DataFrame:
    """Fix the problem of having multiple connections in one cell.

    The issue occurs when one cell is penetrated more than once by a well, and happens
    when there are big cells and the well path is complex.
    The issue can be observed from a COMPLETION_SEGMENTS definition that has overlapping start and end measured depth.

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
                logger.info(
                    "Overlapping in COMPLETION_SEGMENTS%s for %s. Sorts the depths accordingly",
                    Keywords.COMPLETION_SEGMENTS,
                    well_name,
                )
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
                logger.error(
                    "Cannot construct COMPLETION_SEGMENTS%s segments based on current input",
                    Keywords.COMPLETION_SEGMENTS,
                )
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
        (df_completion[Headers.DEVICE_TYPE] == Content.INFLOW_CONTROL_VALVE)
        & (df_completion[Headers.VALVES_PER_JOINT] > 0)
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


def set_welspecs(schedule_data: dict[str, dict[str, Any]], records: list[list[str]]) -> dict[str, dict[str, Any]]:
    """Convert the well specifications (WELSPECS) record to a Pandas DataFrame.

    * Sets DataFrame column titles.
    * Formats column values.
    * Pads missing columns at the end of the DataFrame with default values (1*).

    Args:
        schedule_data: Data containing multisegmented well schedules.
        records: Raw well specification.

    Returns:
        Multisegmented wells with updated welspecs records.
    """
    columns = [
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
    ]
    _records = records[0] + ["1*"] * (len(columns) - len(records[0]))  # pad with default values (1*)
    df = pd.DataFrame(np.array(_records).reshape((1, len(columns))), columns=columns)
    df[columns[2:4]] = df[columns[2:4]].astype(np.int64)
    df[columns[4]] = df[columns[4]].astype(np.float64, errors="ignore")
    # welspecs could be for multiple wells - split it
    for well_name in df[Headers.WELL].unique():
        if well_name not in schedule_data:
            schedule_data[well_name] = {}
        schedule_data[well_name][Keywords.WELL_SPECIFICATION] = df[df[Headers.WELL] == well_name]
        logger.debug("set_welspecs for %s", well_name)
    return schedule_data


def set_welsegs(
    schedule_data: dict[str, dict[str, Any]], active_wells: npt.NDArray[np.str_], recs: list[list[str]]
) -> dict[str, dict[str, Any]]:
    """Update the well segments (WELSEGS) for a given well if it is an active well.

    * Pads missing record columns in header and contents with default values.
    * Convert header and column records to DataFrames.
    * Sets proper DataFrame column types and titles.
    * Converts segment depth specified in incremental (INC) to absolute (ABS) values using fix_welsegs.

    Args:
        schedule_data: Data containing multisegmented well schedules.
        active_wells: Active wells.
        recs: Record set of header and contents data.

    Returns:
        Name of well if it was updated, or None if it is not in the active_wells list.

    Raises:
        ValueError: If a well is not an active well.
    """
    well_name = recs[0][0]  # each WELL_SEGMENTS-chunk is for one well only
    if well_name not in active_wells:
        raise ValueError("The well must be active!")

    # make df for header record
    columns_header = [
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
    ]
    # pad header with default values (1*)
    header = recs[0] + ["1*"] * (len(columns_header) - len(recs[0]))
    df_header = pd.DataFrame(np.array(header).reshape((1, len(columns_header))), columns=columns_header)
    df_header[columns_header[1:3]] = df_header[columns_header[1:3]].astype(np.float64)  # data types

    # make df for data records
    columns_data = [
        Headers.TUBING_SEGMENT,
        Headers.TUBING_SEGMENT_2,
        Headers.TUBING_BRANCH,
        Headers.TUBING_OUTLET,
        Headers.TUBING_MEASURED_DEPTH,
        Headers.TRUE_VERTICAL_DEPTH,
        Headers.TUBING_INNER_DIAMETER,
        Headers.TUBING_ROUGHNESS,
        Headers.FLOW_CROSS_SECTIONAL_AREA,
        Headers.SEGMENT_VOLUME,
        Headers.X_COORDINATE_LAST_SEGMENT,
        Headers.Y_COORDINATE_LAST_SEGMENT,
        Headers.THERMAL_CONDUCTIVITY_CROSS_SECTIONAL_AREA,
        Headers.VOLUMETRIC_HEAT_CAPACITY_PIPE_WALL,
        Headers.THERMAL_CONDUCTIVITY_PIPE_WALL,
    ]
    # pad with default values (1*)
    recs = [rec + ["1*"] * (len(columns_data) - len(rec)) for rec in recs[1:]]
    df_records = pd.DataFrame(recs, columns=columns_data)
    # data types
    df_records[columns_data[:4]] = df_records[columns_data[:4]].astype(np.int64)
    df_records[columns_data[4:8]] = df_records[columns_data[4:8]].astype(np.float64)
    # fix abs/inc issue with welsegs
    df_header, df_records = fix_welsegs(df_header, df_records)

    # Warn user if the tubing segments' measured depth for a branch
    # is not sorted in ascending order (monotonic)
    for branch_num in df_records[Headers.TUBING_BRANCH].unique():
        if (
            not df_records[Headers.TUBING_MEASURED_DEPTH]
            .loc[df_records[Headers.TUBING_BRANCH] == branch_num]
            .is_monotonic_increasing
        ):
            logger.warning(
                "The branch %s in well %s contains negative length segments. Check the input schedulefile %s "
                "keyword for inconsistencies in measured depth (MEASURED_DEPTH) of Tubing layer.",
                Keywords.WELL_SEGMENTS,
                branch_num,
                well_name,
            )

    if well_name not in schedule_data:
        schedule_data[well_name] = {}
    schedule_data[well_name][Keywords.WELL_SEGMENTS] = df_header, df_records
    return schedule_data


def set_compsegs(
    schedule_data: dict[str, dict[str, Any]], active_wells: npt.NDArray[np.str_], recs: list[list[str]]
) -> dict[str, dict[str, Any]]:
    """Update COMPLETION_SEGMENTS for a well if it is an active well.

    * Pads missing record columns in header and contents with default 1*.
    * Convert header and column records to DataFrames.
    * Sets proper DataFrame column types and titles.

    Args:
        schedule_data: Data containing multisegmented well schedules.
        active_wells: Active wells.
        recs: Record set of header and contents data.

    Returns:
        The updated well segments.

    Raises:
        ValueError: If a well is not an active well.
    """
    well_name = recs[0][0]  # each COMPLETION_SEGMENTS-chunk is for one well only
    if well_name not in active_wells:
        raise ValueError("The well must be active!")
    columns = [
        Headers.I,
        Headers.J,
        Headers.K,
        Headers.BRANCH,
        Headers.START_MEASURED_DEPTH,
        Headers.END_MEASURED_DEPTH,
        Headers.COMPSEGS_DIRECTION,
        Headers.ENDGRID,
        Headers.PERFORATION_DEPTH,
        Headers.THERMAL_CONTACT_LENGTH,
        Headers.SEGMENT,
    ]
    recs = np.array(recs[1:])
    recs = np.pad(recs, ((0, 0), (0, len(columns) - recs.shape[1])), "constant", constant_values="1*")
    df = pd.DataFrame(recs, columns=columns)
    df[columns[:4]] = df[columns[:4]].astype(np.int64)
    df[columns[4:6]] = df[columns[4:6]].astype(np.float64)
    if well_name not in schedule_data:
        schedule_data[well_name] = {}
    schedule_data[well_name][Keywords.COMPLETION_SEGMENTS] = df
    logger.debug("set_compsegs for %s", well_name)
    return schedule_data


def handle_compdat(
    schedule_data: dict[str, dict[str, Any]],
    active_wells: npt.NDArray[np.str_],
    records: list[list[str]],
) -> dict[str, dict[str, Any]]:
    """Convert completion data (COMPDAT) record to a DataFrame.

    * Sets DataFrame column titles.
    * Pads missing values with default values (1*).
    * Sets column data types.

    Args:
        schedule_data: Data containing multisegmented well schedules.
        active_wells: Active wells, without duplicates.
        records: Record set of COMPLETION_DATA data.

    Returns:
        Records for inactive wells.
    """
    columns = [
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
    ]
    df = pd.DataFrame(records, columns=columns[0 : len(records[0])])
    if Headers.RO in df.columns:
        df[Headers.RO] = df[Headers.RO].fillna("1*")
    for i in range(len(records[0]), len(columns)):
        df[columns[i]] = ["1*"] * len(records)
    df[columns[1:5]] = df[columns[1:5]].astype(np.int64)
    # Change default value '1*' to equivalent float
    df["SKIN"] = df["SKIN"].replace(["1*"], 0.0)
    df[[Headers.WELL_BORE_DIAMETER, Headers.SKIN]] = df[[Headers.WELL_BORE_DIAMETER, Headers.SKIN]].astype(np.float64)
    # check if CONNECTION_FACTOR, FORMATION_PERMEABILITY_THICKNESS, and RO are defaulted by the users
    df = df.astype(
        {
            Headers.CONNECTION_FACTOR: np.float64,
            Headers.FORMATION_PERMEABILITY_THICKNESS: np.float64,
            Headers.RO: np.float64,
        },
        errors="ignore",
    )
    # Compdat could be for multiple wells, split it.
    for well_name in active_wells:
        if well_name not in schedule_data:
            schedule_data[well_name] = {}
        schedule_data[well_name][Keywords.COMPLETION_DATA] = df[df[Headers.WELL] == well_name]
        logger.debug("handle_compdat for %s", well_name)
    return schedule_data


def get_completion_data(schedule_data: dict[str, Any]) -> pd.DataFrame:
    """Get-function for COMPLETION_DATA.

    Args:
        schedule_data: Segment information.

    Returns:
        Completion data.

    Raises:
        ValueError: If completion data keyword is missing in input schedule file.
    """
    data = schedule_data.get(Keywords.COMPDAT)
    if data is None:
        raise KeyError("Input schedule file missing COMPDAT keyword.")
    return data


def get_completion_segments(schedule_data: dict[str, Any], well_name: str, branch: int | None = None) -> pd.DataFrame:
    """Get-function for COMPLETION_SEGMENTS.

    Args:
       schedule_data: Data containing multisegmented well segments.
       well_name: Well name.
       branch: Branch number.

    Returns:
        Completion segment data.
    """
    df = schedule_data[Keywords.COMPLETION_SEGMENTS].copy()
    if branch is not None:
        df = df[df[Headers.BRANCH] == branch]
    df.reset_index(drop=True, inplace=True)  # reset index after filtering
    return fix_compsegs(df, well_name)


def get_well_segments(
    well_data: dict[str, pd.DataFrame], branch: int | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Get-function for well segments.

    Args:
        well_data: The multisegmented wells.
        branch: Branch number.

    Returns:
        Well segments headers and content.

    Raises:
        ValueError: If WELL_SEGMENTS keyword missing in input schedule file.
    """
    data = well_data.get(Keywords.WELSEGS)
    if data is None:
        raise ValueError("Input schedule file missing WELSEGS keyword.")
    columns, content = data

    if branch is not None:
        content = content[content[Headers.TUBING_BRANCH] == branch]
    content = content.reset_index(drop=True)
    return columns, content
