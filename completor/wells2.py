"""Classes to keep track of Well objects."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from numpy import typing as npt

from completor.constants import Headers, Keywords
from completor.logger import logger
from completor.read_schedule import fix_compsegs, fix_welsegs


class WellSchedule:
    """A collection of all the active multi-segment wells.

    Attributes:
        msws: Multisegmented well segments.
        active_wells: The active wells for completor to work on.

    Args:
        active_wells: Active multi-segment wells defined in a case file.
    """

    def __init__(self, active_wells: npt.NDArray[np.unicode_]):
        """Initialize WellSchedule."""
        self.msws: dict[str, dict[str, Any]] = {}
        self.active_wells = active_wells


def set_welspecs(
    multisegmented_well_segments: dict[str, dict[str, Any]], records: list[list[str]]
) -> dict[str, dict[str, Any]]:
    """Convert the well specifications (WELSPECS) record to a Pandas DataFrame.

    * Sets DataFrame column titles.
    * Formats column values.
    * Pads missing columns at the end of the DataFrame with default values (1*).

    Args:
        multisegmented_well_segments: Data containing multisegmented well schedules.
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
        if well_name not in multisegmented_well_segments:
            multisegmented_well_segments[well_name] = {}
        multisegmented_well_segments[well_name][Keywords.WELSPECS] = df[df[Headers.WELL] == well_name]
        logger.debug("set_welspecs for %s", well_name)
    return multisegmented_well_segments


def handle_compdat(
    multisegmented_well_segments: dict[str, dict[str, Any]], active_wells: set[str], records: list[list[str]]
) -> dict[str, dict[str, Any]]:
    """Convert completion data (COMPDAT) record to a DataFrame.

    * Sets DataFrame column titles.
    * Pads missing values with default values (1*).
    * Sets column data types.

    Args:
        multisegmented_well_segments: Data containing multisegmented well schedules.
        active_wells: Active wells, without duplicates.
        records: Record set of COMPDAT data.

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
        if well_name not in multisegmented_well_segments:
            multisegmented_well_segments[well_name] = {}
        multisegmented_well_segments[well_name][Keywords.COMPDAT] = df[df[Headers.WELL] == well_name]
        logger.debug("handle_compdat for %s", well_name)
    return multisegmented_well_segments


def set_welsegs(
    multisegmented_well_segments: dict[str, dict[str, Any]], active_wells: npt.NDArray[np.str_], recs: list[list[str]]
) -> dict[str, dict[str, Any]]:
    """Update the well segments (WELSEGS) for a given well if it is an active well.

    * Pads missing record columns in header and contents with default values.
    * Convert header and column records to DataFrames.
    * Sets proper DataFrame column types and titles.
    * Converts segment depth specified in incremental (INC) to absolute (ABS) values using fix_welsegs.

    Args:
        multisegmented_well_segments: Data containing multisegmented well schedules.
        active_wells: Active wells.
        recs: Record set of header and contents data.

    Returns:
        Name of well if it was updated, or None if it is not in the active_wells list.

    Raises:
        ValueError: If a well is not an active well.
    """
    well_name = recs[0][0]  # each WELSEGS-chunk is for one well only
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
    df_records[columns_data[4:7]] = df_records[columns_data[4:7]].astype(np.float64)
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
                "The branch %s in well %s contains negative length segments. "
                "Check the input schedulefile WELSEGS keyword for inconsistencies "
                "in measured depth (MEASURED_DEPTH) of Tubing layer.",
                branch_num,
                well_name,
            )

    if well_name not in multisegmented_well_segments:
        multisegmented_well_segments[well_name] = {}
    multisegmented_well_segments[well_name][Keywords.WELSEGS] = df_header, df_records
    return multisegmented_well_segments


def set_compsegs(
    multisegmented_well_segments: dict[str, dict[str, Any]], active_wells: npt.NDArray[np.str_], recs: list[list[str]]
) -> dict[str, dict[str, Any]]:
    """Update COMPSEGS for a well if it is an active well.

    * Pads missing record columns in header and contents with default 1*.
    * Convert header and column records to DataFrames.
    * Sets proper DataFrame column types and titles.

    Args:
        multisegmented_well_segments: Data containing multisegmented well schedules.
        active_wells: Active wells.
        recs: Record set of header and contents data.

    Returns:
        The updated well segments.

    Raises:
        ValueError: If a well is not an active well.
    """
    well_name = recs[0][0]  # each COMPSEGS-chunk is for one well only
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
    if well_name not in multisegmented_well_segments:
        multisegmented_well_segments[well_name] = {}
    multisegmented_well_segments[well_name][Keywords.COMPSEGS] = df
    logger.debug("set_compsegs for %s", well_name)
    return multisegmented_well_segments


def get_completion_data(multisegmented_well_segments: dict[str, dict[str, Any]], well_name: str) -> pd.DataFrame:
    """Get-function for COMPDAT.

    Args:
        multisegmented_well_segments: Segment information.
        well_name: Well name.

    Returns:
        Completion data.

    Raises:
        ValueError: If completion data keyword is missing in input schedule file.
    """
    try:
        return multisegmented_well_segments[well_name][Keywords.COMPDAT]
    except KeyError as err:
        if f"'{Keywords.COMPDAT}'" in str(err):
            raise ValueError("Input schedule file missing COMPDAT keyword.") from err
        raise err


def get_completion_segments(
    multisegmented_well_segments: dict[str, dict[str, Any]], well_name: str, branch: int | None = None
) -> pd.DataFrame:
    """Get-function for COMPSEGS.

    Args:
       multisegmented_well_segments: Data containing multisegmented well segments.
       well_name: Well name.
       branch: Branch number.

    Returns:
        Completion segment data.
    """
    df = multisegmented_well_segments[well_name][Keywords.COMPSEGS].copy()
    if branch is not None:
        df = df[df[Headers.BRANCH] == branch]
    df.reset_index(drop=True, inplace=True)  # reset index after filtering
    return fix_compsegs(df, well_name)


def get_well_segments(
    multisegmented_well_segments: dict[str, dict[str, Any]], well_name: str, branch: int | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Get-function for well segments.

    Args:
        multisegmented_well_segments: The multisegmented wells.
        well_name: Well name.
        branch: Branch number.

    Returns:
        Well segments headers and content.

    Raises:
        ValueError: If WELSEGS keyword missing in input schedule file.
    """
    try:
        columns, content = multisegmented_well_segments[well_name][Keywords.WELSEGS]
    except KeyError as err:
        if f"'{Keywords.WELSEGS}'" in str(err):
            raise ValueError("Input schedule file missing WELSEGS keyword.") from err
        raise err
    if branch is not None:
        content = content[content[Headers.TUBING_BRANCH] == branch]
    content.reset_index(drop=True, inplace=True)
    return columns, content


def get_well_number(well_name: str, active_wells: npt.NDArray[np.str_]) -> int:
    """Well number in the active_wells list.

    Args:
        well_name: Well name.
        active_wells: The active wells.

    Returns:
        Well number.
    """
    return int(np.where(active_wells == well_name)[0][0])
