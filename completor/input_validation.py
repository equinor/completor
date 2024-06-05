"""Functions to validate user input for Completor."""

from __future__ import annotations

import numpy as np
import pandas as pd

from completor.constants import Headers
from completor.utils import abort


def set_default_packer_section(df_comp: pd.DataFrame) -> pd.DataFrame:
    """Set the default value for the packer section.

    This procedure sets the default values of the completion_table in read_casefile class if the annulus is packer (PA).

    Args:
        df_comp: Completion data.

    Returns:
        Updated completion data for packers.
    """
    # Set default values for packer sections
    df_comp[Headers.INNER_DIAMETER] = np.where(df_comp[Headers.ANNULUS] == "PA", 0.0, df_comp[Headers.INNER_DIAMETER])
    df_comp[Headers.OUTER_DIAMETER] = np.where(df_comp[Headers.ANNULUS] == "PA", 0.0, df_comp[Headers.OUTER_DIAMETER])
    df_comp[Headers.ROUGHNESS] = np.where(df_comp[Headers.ANNULUS] == "PA", 0.0, df_comp[Headers.ROUGHNESS])
    df_comp[Headers.VALVES_PER_JOINT] = np.where(
        df_comp[Headers.ANNULUS] == "PA", 0.0, df_comp[Headers.VALVES_PER_JOINT]
    )
    df_comp[Headers.DEVICE_TYPE] = np.where(df_comp[Headers.ANNULUS] == "PA", "PERF", df_comp[Headers.DEVICE_TYPE])
    df_comp[Headers.DEVICE_NUMBER] = np.where(df_comp[Headers.ANNULUS] == "PA", 0, df_comp[Headers.DEVICE_NUMBER])
    return df_comp


def set_default_perf_section(df_comp: pd.DataFrame) -> pd.DataFrame:
    """Set the default value for the perforated (PERF) section.

    Args:
        df_comp: Completion data.

    Returns:
        Updated completion data for perforated sections.
    """
    df_comp[Headers.VALVES_PER_JOINT] = np.where(
        df_comp[Headers.DEVICE_TYPE] == "PERF", 0.0, df_comp[Headers.VALVES_PER_JOINT]
    )
    df_comp[Headers.DEVICE_NUMBER] = np.where(df_comp[Headers.DEVICE_TYPE] == "PERF", 0, df_comp[Headers.DEVICE_NUMBER])
    return df_comp


def check_default_non_packer(df_comp: pd.DataFrame) -> pd.DataFrame:
    """Check default values for non-packers.

    This procedure checks if the user enters default values 1* for non-packer annulus content,
    e.g. Open annulus (OA) and gravel packed (GP).
    If this is the case, the program will report errors.

    Args:
        df_comp: Completion data.

    Returns:
        Updated completion with replaced roughness.

    Raises:
        SystemExit: If default value '1*' in non-packer columns

    """
    df_comp = df_comp.copy(True)
    # set default value of roughness
    df_comp[Headers.ROUGHNESS] = (
        df_comp[Headers.ROUGHNESS].replace("1*", "1e-5").astype(np.float64)
    )  # Ensures float after replacing!
    df_nonpa = df_comp[df_comp[Headers.ANNULUS] != "PA"]
    df_columns = df_nonpa.columns.to_numpy()
    for column in df_columns:
        if "1*" in df_nonpa[column]:
            raise abort(f"No default value 1* is allowed in {column} entry.")
    return df_comp


def set_format_completion(df_comp: pd.DataFrame) -> pd.DataFrame:
    """Set the column data format.

    Args:
        df_comp: Completion data.

    Returns:
        Updated completion data with enforced data types.
    """
    return df_comp.astype(
        {
            Headers.WELL: str,
            Headers.BRANCH: np.int64,
            Headers.START_MD: np.float64,
            Headers.END_MEASURED_DEPTH: np.float64,
            Headers.INNER_DIAMETER: np.float64,
            Headers.OUTER_DIAMETER: np.float64,
            Headers.ROUGHNESS: np.float64,
            Headers.ANNULUS: str,
            Headers.VALVES_PER_JOINT: np.float64,
            Headers.DEVICE_TYPE: str,
            Headers.DEVICE_NUMBER: np.int64,
        }
    )


def assess_completion(df_comp: pd.DataFrame) -> None:
    """Assess the user completion inputs.

    Args:
        df_comp: Completion data.
    """
    list_wells = df_comp[Headers.WELL].unique()
    for well_name in list_wells:
        df_well = df_comp[df_comp[Headers.WELL] == well_name]
        list_branches = df_well[Headers.BRANCH].unique()
        for branch in list_branches:
            df_comp = df_well[df_well[Headers.BRANCH] == branch]
            nrow = df_comp.shape[0]
            for idx in range(0, nrow):
                _check_for_errors(df_comp, well_name, idx)


def _check_for_errors(df_comp: pd.DataFrame, well_name: str, idx: int) -> None:
    """Check for errors in completion.

    Args:
        df_comp: Completion data frame.
        well_name: Well name.
        idx: Index.

    Raises:
        SystemExit:
            If packer segments are missing length.
            If non-packer segments are missing length.
            If the completion description is incomplete for some range of depth.
            If the completion description is overlapping for some range of depth.
    """
    if df_comp[Headers.ANNULUS].iloc[idx] == "PA" and (
        df_comp[Headers.START_MD].iloc[idx] != df_comp[Headers.END_MEASURED_DEPTH].iloc[idx]
    ):
        raise abort("Packer segments must not have length")

    if (
        df_comp[Headers.ANNULUS].iloc[idx] != "PA"
        and df_comp[Headers.DEVICE_TYPE].iloc[idx] != "ICV"
        and df_comp[Headers.START_MD].iloc[idx] == df_comp[Headers.END_MEASURED_DEPTH].iloc[idx]
    ):
        raise abort("Non packer segments must have length")

    if idx > 0:
        if df_comp[Headers.START_MD].iloc[idx] > df_comp[Headers.END_MEASURED_DEPTH].iloc[idx - 1]:
            raise abort(
                f"Incomplete completion description in well {well_name} from depth "
                f"{df_comp[Headers.END_MEASURED_DEPTH].iloc[idx - 1]} "
                f"to depth {df_comp[Headers.START_MEASURED_DEPTH].iloc[idx]}"
            )

        if df_comp[Headers.START_MD].iloc[idx] < df_comp[Headers.END_MEASURED_DEPTH].iloc[idx - 1]:
            raise abort(
                f"Overlapping completion description in well {well_name} from depth "
                f"{df_comp[Headers.END_MEASURED_DEPTH].iloc[idx - 1]} "
                f"to depth {(df_comp[Headers.START_MEASURED_DEPTH].iloc[idx])}"
            )
    if df_comp[Headers.DEVICE_TYPE].iloc[idx] not in ["PERF", "AICD", "ICD", "VALVE", "DAR", "AICV", "ICV"]:
        raise abort(
            f"{df_comp[Headers.DEVICE_TYPE].iloc[idx]} not a valid device type. "
            "Valid types are PERF, AICD, ICD, VALVE, DAR, AICV, and ICV."
        )
    if df_comp[Headers.ANNULUS].iloc[idx] not in ["GP", "OA", "PA"]:
        raise abort(f"{df_comp[Headers.ANNULUS].iloc[idx]} not a valid annulus type. Valid types are GP, OA, and PA")


def set_format_wsegvalv(df_temp: pd.DataFrame) -> pd.DataFrame:
    """Format the well segments valve (WSEGVALV) table.

    Args:
        df_temp: Well segments valve data.

    Returns:
        Updated data with enforced data types and device type filled with default values.
    """
    df_temp[Headers.DEVICE_NUMBER] = df_temp[Headers.DEVICE_NUMBER].astype(np.int64)
    df_temp[[Headers.CV, Headers.AC, Headers.AC_MAX]] = df_temp[[Headers.CV, Headers.AC, Headers.AC_MAX]].astype(
        np.float64
    )
    # allows column L to have default value 1* thus it is not set to float
    # Create ID device column
    df_temp.insert(0, Headers.DEVICE_TYPE, np.full(df_temp.shape[0], fill_value="VALVE"))
    return df_temp


def set_format_wsegsicd(df_temp: pd.DataFrame) -> pd.DataFrame:
    """Format the well segments inflow control device (WSEGSICD) table.

    Args:
        df_temp: Well segments inflow control device data.

    Returns:
        Updated data.
    """
    # if WCUT is defaulted then set to 0.5, the same default value as in simulator
    df_temp[Headers.WCUT] = df_temp[Headers.WCUT].replace("1*", 0.5).astype(np.float64)
    # set data type
    df_temp[Headers.DEVICE_NUMBER] = df_temp[Headers.DEVICE_NUMBER].astype(np.int64)
    # left out device number because it has been formatted as integer
    columns = df_temp.columns.to_numpy()[1:]
    df_temp[columns] = df_temp[columns].astype(np.float64)
    # Create ID device column
    df_temp.insert(0, Headers.DEVICE_TYPE, np.full(df_temp.shape[0], "ICD"))
    return df_temp


def set_format_wsegaicd(df_temp: pd.DataFrame) -> pd.DataFrame:
    """Format the well segments automatic inflow control device (WSEGAICD) table.

    Args:
        df_temp: Well segments automatic inflow control device data.

    Returns:
        Updated data.
    """
    # Fix table format
    df_temp[Headers.DEVICE_NUMBER] = df_temp[Headers.DEVICE_NUMBER].astype(np.int64)
    # left out device number because it has been formatted as integer
    columns = df_temp.columns.to_numpy()[1:]
    df_temp[columns] = df_temp[columns].astype(np.float64)
    # Create ID device column
    df_temp.insert(0, Headers.DEVICE_TYPE, np.full(df_temp.shape[0], "AICD"))
    return df_temp


def set_format_wsegdar(df_temp: pd.DataFrame) -> pd.DataFrame:
    """Format the well segments DAR (WSEGDAR) data.

    Args:
        df_temp: Well segments DAR device data.

    Returns:
        Updated data.
    """
    df_temp[Headers.DEVICE_NUMBER] = df_temp[Headers.DEVICE_NUMBER].astype(np.int64)
    # left out devicenumber because it has been formatted as integer
    columns = df_temp.columns.to_numpy()[1:]
    df_temp[columns] = df_temp[columns].astype(np.float64)
    # Create ID device column
    df_temp.insert(0, Headers.DEVICE_TYPE, np.full(df_temp.shape[0], "DAR"))
    return df_temp


def set_format_wsegaicv(df_temp: pd.DataFrame) -> pd.DataFrame:
    """Format the well segments automatic inflow control valve (WSEGAICV) table.

    Args:
        df_temp: Well segments automatic inflow control valve table.

    Returns:
        Updated data.
    """
    df_temp[Headers.DEVICE_NUMBER] = df_temp[Headers.DEVICE_NUMBER].astype(np.int64)
    # left out devicenumber because it has been formatted as integer
    columns = df_temp.columns.to_numpy()[1:]
    df_temp[columns] = df_temp[columns].astype(np.float64)
    # Create ID device column
    df_temp.insert(0, Headers.DEVICE_TYPE, np.full(df_temp.shape[0], "AICV"))
    return df_temp


def set_format_wsegicv(df_temp: pd.DataFrame) -> pd.DataFrame:
    """Format the well segments inflow control valve (WSEGICV) table.

    Args:
        df_temp: Well segments inflow control valve table.

    Returns:
        Updated data.
    """
    df_temp[Headers.DEVICE_NUMBER] = df_temp[Headers.DEVICE_NUMBER].astype(np.int64)
    df_temp[[Headers.CV, Headers.AC, Headers.AC_MAX]] = df_temp[[Headers.CV, Headers.AC, Headers.AC_MAX]].astype(
        np.float64
    )
    # allows column DEFAULTS to have default value 5*,  thus it is not set to float
    # Create ID device column
    df_temp.insert(0, Headers.DEVICE_TYPE, np.full(df_temp.shape[0], fill_value="ICV"))
    return df_temp


def validate_lateral_to_device(df_lat2dev: pd.DataFrame, df_comp: pd.DataFrame) -> None:
    """Assess the lateral-to-device inputs.

    Abort if a lateral is connected to a device layer in a well with open annuli.

    Args:
        df_lat2dev: Lateral to device contents.
        df_comp: Completion data.

    Raises:
        SystemExit:
            If the LATERAL_TO_DEVICE keyword is set for a multisegmented well with open annulus.
    """
    try:
        df_lat2dev[Headers.BRANCH].astype(np.int64)
    except ValueError:
        raise abort(
            f"Could not convert BRANCH {df_lat2dev[Headers.BRANCH].values} "
            "to integer. Make sure that BRANCH is an integer."
        )

    nrow = df_lat2dev.shape[0]
    for idx in range(0, nrow):
        l2d_well = df_lat2dev[Headers.WELL].iloc[idx]
        if (df_comp[df_comp[Headers.WELL] == l2d_well][Headers.ANNULUS] == "OA").any():
            raise abort(
                f"Please do not connect a lateral to the mother bore in well {l2d_well} that has open annuli. "
                "This may trigger an error in reservoir simulator."
            )


def validate_minimum_segment_length(minimum_segment_length: str | float) -> float:
    """Assess the minimum segment length.

    Abort if the minimum segment length is not a number >= 0.0.

    Args:
        minimum_segment_length: Possible user input.

    Raises:
        SystemExit:
            If the minimum_segment_length is not greater or equals to 0.0.

    Returns:
        Minimum segment length if no errors occurred.
    """
    try:
        minimum_segment_length = float(minimum_segment_length)
    except ValueError:
        raise abort(f"The MINIMUM_SEGMENT_LENGTH {minimum_segment_length} has to be a float.")
    if minimum_segment_length < 0.0:
        raise abort(f"The MINIMUM_SEGMENT_LENGTH {minimum_segment_length} cannot be less than 0.0.")
    return minimum_segment_length
