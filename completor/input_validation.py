"""Functions to validate user input for Completor."""

from __future__ import annotations

import numpy as np
import pandas as pd

from completor.utils import abort


def set_default_packer_section(df_comp: pd.DataFrame) -> pd.DataFrame:
    """
    Set default value for the packer section.

    This procedure sets the default values of the
    completion_table in read_casefile class if the annulus is PA (packer)

    Args:
        df_comp: COMPLETION table

    Returns:
        Updated COMPLETION

    The format of the COMPLETION table DataFrame is shown in
    ``read_casefile.ReadCasefile.read_completion``.
    """
    # Set default values for packer sections
    df_comp["INNER_DIAMETER"] = np.where(df_comp["ANNULUS"] == "PA", 0.0, df_comp["INNER_DIAMETER"])
    df_comp["OUTER_DIAMETER"] = np.where(df_comp["ANNULUS"] == "PA", 0.0, df_comp["OUTER_DIAMETER"])
    df_comp["ROUGHNESS"] = np.where(df_comp["ANNULUS"] == "PA", 0.0, df_comp["ROUGHNESS"])
    df_comp["NVALVEPERJOINT"] = np.where(df_comp["ANNULUS"] == "PA", 0.0, df_comp["NVALVEPERJOINT"])
    df_comp["DEVICETYPE"] = np.where(df_comp["ANNULUS"] == "PA", "PERF", df_comp["DEVICETYPE"])
    df_comp["DEVICENUMBER"] = np.where(df_comp["ANNULUS"] == "PA", 0, df_comp["DEVICENUMBER"])
    return df_comp


def set_default_perf_section(df_comp: pd.DataFrame) -> pd.DataFrame:
    """
    Set the default value for the PERF section.

    Args:
        df_comp : COMPLETION table

    Returns:
        Updated COMPLETION

    The format of the COMPLETION table DataFrame is shown in
    ``read_casefile.ReadCasefile.read_completion``.
    """
    # set default value of the PERF section
    df_comp["NVALVEPERJOINT"] = np.where(df_comp["DEVICETYPE"] == "PERF", 0.0, df_comp["NVALVEPERJOINT"])
    df_comp["DEVICENUMBER"] = np.where(df_comp["DEVICETYPE"] == "PERF", 0, df_comp["DEVICENUMBER"])
    return df_comp


def check_default_non_packer(df_comp: pd.DataFrame) -> pd.DataFrame:
    """
    Check default values for non-packers.

    This procedure checks if the user enters default values 1*
    for non-packer annulus content, e.g. OA, GP.
    If this is the case, the program will report errors.

    Args:
        df_comp: COMPLETION table

    Returns:
        Updated COMPLETION

    Raises:
        SystemExit: If default value '1*' in non-packer columns

    The format of the COMPLETION table DataFrame is shown in
    ``read_casefile.ReadCasefile.read_completion``.
    """
    df_comp = df_comp.copy(True)
    # set default value of roughness
    df_comp["ROUGHNESS"] = (
        df_comp["ROUGHNESS"].replace("1*", "1e-5").astype(np.float64)
    )  # Ensures float after replacing!
    df_nonpa = df_comp[df_comp["ANNULUS"] != "PA"]
    df_columns = df_nonpa.columns.to_numpy()
    for column in df_columns:
        if "1*" in df_nonpa[column]:
            raise abort(f"No default value 1* is allowed in {column} entry.")
    return df_comp


def set_format_completion(df_comp: pd.DataFrame) -> pd.DataFrame:
    """
    Set the column data format.

    Args:
        df_comp: COMPLETION table

    Returns:
        Updated COMPLETION table

    The format of the COMPLETION table DataFrame is shown in
    ``read_casefile.ReadCasefile.read_completion``.
    """
    return df_comp.astype(
        {
            "WELL": str,
            "BRANCH": np.int64,
            "STARTMD": np.float64,
            "ENDMD": np.float64,
            "INNER_DIAMETER": np.float64,
            "OUTER_DIAMETER": np.float64,
            "ROUGHNESS": np.float64,
            "ANNULUS": str,
            "NVALVEPERJOINT": np.float64,
            "DEVICETYPE": str,
            "DEVICENUMBER": np.int64,
        }
    )


def assess_completion(df_comp: pd.DataFrame):
    """
    Assess the user completion inputs.

    Args:
        df_comp: COMPLETION table

    The format of the COMPLETION table DataFrame is shown in
    ``read_casefile.ReadCasefile.read_completion``.
    """
    list_wells = df_comp["WELL"].unique()
    for well_name in list_wells:
        df_well = df_comp[df_comp["WELL"] == well_name]
        list_branches = df_well["BRANCH"].unique()
        for branch in list_branches:
            df_comp = df_well[df_well["BRANCH"] == branch]
            nrow = df_comp.shape[0]
            for idx in range(0, nrow):
                _check_for_errors(df_comp, well_name, idx)


def _check_for_errors(df_comp: pd.DataFrame, well_name: str, idx: int):
    """
    Check for errors in completion.

    Args:
        df_comp: Completion data frame
        well_name: Well name
        idx: Index

    Raises:
        SystemExit:
            If packer segments is missing length
            If non-packer segments is missing length
            If the completion description is incomplete for some range of depth
            If the completion description is overlapping for some range of depth
    """
    if df_comp["ANNULUS"].iloc[idx] == "PA" and (df_comp["STARTMD"].iloc[idx] != df_comp["ENDMD"].iloc[idx]):
        raise abort("Packer segments must not have length")

    if (
        df_comp["ANNULUS"].iloc[idx] != "PA"
        and df_comp["DEVICETYPE"].iloc[idx] != "ICV"
        and df_comp["STARTMD"].iloc[idx] == df_comp["ENDMD"].iloc[idx]
    ):
        raise abort("Non packer segments must have length")

    if idx > 0:
        if df_comp["STARTMD"].iloc[idx] > df_comp["ENDMD"].iloc[idx - 1]:
            raise abort(
                f"Incomplete completion description in well {well_name} from depth {df_comp['ENDMD'].iloc[idx - 1]} "
                f"to depth {df_comp['STARTMD'].iloc[idx]}"
            )

        if df_comp["STARTMD"].iloc[idx] < df_comp["ENDMD"].iloc[idx - 1]:
            raise abort(
                f"Overlapping completion description in well {well_name} from depth {df_comp['ENDMD'].iloc[idx - 1]} "
                f"to depth {(df_comp['STARTMD'].iloc[idx])}"
            )
    if df_comp["DEVICETYPE"].iloc[idx] not in ["PERF", "AICD", "ICD", "VALVE", "DAR", "AICV", "ICV"]:
        raise abort(
            f"{df_comp['DEVICETYPE'].iloc[idx]} not a valid device type. "
            "Valid types are PERF, AICD, ICD, VALVE, DAR, AICV, and ICV."
        )
    if df_comp["ANNULUS"].iloc[idx] not in ["GP", "OA", "PA"]:
        raise abort(f"{df_comp['ANNULUS'].iloc[idx]} not a valid annulus type. Valid types are GP, OA, and PA")


def set_format_wsegvalv(df_temp: pd.DataFrame) -> pd.DataFrame:
    """
    Format the WSEGVALV table.

    Args:
        df_temp: WSEGVALV table

    Returns:
        updated WSEGVALV

    The format of the WSEGVALV table DataFrame is shown in
    ``read_casefile.ReadCasefile.read_wsegvalv``.
    """
    # set data type
    df_temp["DEVICENUMBER"] = df_temp["DEVICENUMBER"].astype(np.int64)
    df_temp[["CV", "AC", "AC_MAX"]] = df_temp[["CV", "AC", "AC_MAX"]].astype(np.float64)
    # allows column L to have default value 1* thus it is not set to float
    # Create ID device column
    df_temp.insert(0, "DEVICETYPE", np.full(df_temp.shape[0], fill_value="VALVE"))
    return df_temp


def set_format_wsegsicd(df_temp: pd.DataFrame) -> pd.DataFrame:
    """
    Format the WSEGSICD table.

    Args:
        df_temp: WSEGSICD table

    Returns:
        Updated WSEGSICD

    The format of the WSEGSICD table DataFrame is shown in
    ``read_casefile.ReadCasefile.read_wsegsicd``.
    """
    # if WCUT is defaulted then set to 0.5
    # the same default value as in simulator
    df_temp["WCUT"] = df_temp["WCUT"].replace("1*", "0.5").astype(np.float64)  # Ensures float after replacing!
    # set data type
    df_temp["DEVICENUMBER"] = df_temp["DEVICENUMBER"].astype(np.int64)
    # left out devicenumber because it has been formatted as integer
    columns = df_temp.columns.to_numpy()[1:]
    df_temp[columns] = df_temp[columns].astype(np.float64)
    # Create ID device column
    df_temp.insert(0, "DEVICETYPE", np.full(df_temp.shape[0], "ICD"))
    return df_temp


def set_format_wsegaicd(df_temp: pd.DataFrame) -> pd.DataFrame:
    """
    Format the WSEGAICD table.

    Args:
        df_temp: WSEGAICD table

    Returns:
        Updated WSEGAICD

    The format of the WSEGAICD table DataFrame is shown in
    ``read_casefile.ReadCasefile.read_wsegaicd``.
    """
    # Fix table format
    df_temp["DEVICENUMBER"] = df_temp["DEVICENUMBER"].astype(np.int64)
    # left out devicenumber because it has been formatted as integer
    columns = df_temp.columns.to_numpy()[1:]
    df_temp[columns] = df_temp[columns].astype(np.float64)
    # Create ID device column
    df_temp.insert(0, "DEVICETYPE", np.full(df_temp.shape[0], "AICD"))
    return df_temp


def set_format_wsegdar(df_temp: pd.DataFrame) -> pd.DataFrame:
    """
    Format the WSEGDAR table.

    Args:
        df_temp: WSEGDAR table

    Returns:
        Updated WSEGDAR

    The format of the WSEGDAR table DataFrame is shown in
    ``read_casefile.ReadCasefile.read_wsegdar``.
    """
    # Set data type
    df_temp["DEVICENUMBER"] = df_temp["DEVICENUMBER"].astype(np.int64)
    # left out devicenumber because it has been formatted as integer
    columns = df_temp.columns.to_numpy()[1:]
    df_temp[columns] = df_temp[columns].astype(np.float64)
    # Create ID device column
    df_temp.insert(0, "DEVICETYPE", np.full(df_temp.shape[0], "DAR"))
    return df_temp


def set_format_wsegaicv(df_temp: pd.DataFrame) -> pd.DataFrame:
    """
    Format the WSEGAICV table.

    Args:
        df_temp: WSEGAICV table

    Returns:
        Updated WSEGAICV

    The format of the WSEGAICV table DataFrame is shown in
    ``read_casefile.ReadCasefile.read_wsegaicv``.
    """
    # Fix table format
    df_temp["DEVICENUMBER"] = df_temp["DEVICENUMBER"].astype(np.int64)
    # left out devicenumber because it has been formatted as integer
    columns = df_temp.columns.to_numpy()[1:]
    df_temp[columns] = df_temp[columns].astype(np.float64)
    # Create ID device column
    df_temp.insert(0, "DEVICETYPE", np.full(df_temp.shape[0], "AICV"))
    return df_temp


def set_format_wsegicv(df_temp: pd.DataFrame) -> pd.DataFrame:
    """
    Format the WSEGICV table.

    Args:
        df_temp: WSEGICV table

    Returns:
        Updated WSEGICV

    The format of the WSEGICV table DataFrame is shown in
    ``read_casefile.ReadCasefile.read_wsegicv``.
    """
    # set data type
    df_temp["DEVICENUMBER"] = df_temp["DEVICENUMBER"].astype(np.int64)
    df_temp[["CV", "AC", "AC_MAX"]] = df_temp[["CV", "AC", "AC_MAX"]].astype(np.float64)
    # allows column DEFAULTS to have default value 5*
    # thus it is not set to float
    # Create ID device column
    df_temp.insert(0, "DEVICETYPE", np.full(df_temp.shape[0], fill_value="ICV"))
    return df_temp


def validate_lateral2device(df_lat2dev: pd.DataFrame, df_comp: pd.DataFrame):
    """
    Assess the lateral 2 device inputs.

    Abort if a lateral is
    connected to a device layer in a well with open annuli.

    Args:
        df_lat2dev: Lateral to device contents
        df_comp: COMPLETION table

    Raises:
        SystemExit:
            If the LATERAL_TO_DEVICE keyword is set for a multisegment
            well with open annulus.

    The format of the COMPLETION table DataFrame is shown in
    ``read_casefile.ReadCasefile.read_completion``.
    """
    try:
        df_lat2dev["BRANCH"].astype(np.int64)
    except ValueError:
        raise abort(
            f"Could not convert BRANCH {df_lat2dev['BRANCH'].values} to integer. Make sure that BRANCH is an integer."
        )

    nrow = df_lat2dev.shape[0]
    for idx in range(0, nrow):
        l2d_well = df_lat2dev["WELL"].iloc[idx]
        if (df_comp[df_comp["WELL"] == l2d_well]["ANNULUS"] == "OA").any():
            raise abort(
                f"Please do not connect a lateral to the mother bore in well {l2d_well} that has open annuli. "
                "This may trigger an error in reservoir simulator."
            )


def validate_minimum_segment_length(minimum_segment_length: str | float) -> float:
    """
    Assess the minimum_segment_length input.

    Abort if the minimum segment length is not a number >= 0.0.

    Args:
        minimum_segment_length: Possible user input

    Raises:
        SystemExit:
            If the minimum_segment_length is not a number >= 0.0.

    Returns:
        Minimum segment length if no errors occured.

    """
    try:
        minimum_segment_length = float(minimum_segment_length)
    except ValueError:
        raise abort(f"The MINIMUM_SEGMENT_LENGTH {minimum_segment_length} has to be a float.")
    if minimum_segment_length < 0.0:
        raise abort(f"The MINIMUM_SEGMENT_LENGTH {minimum_segment_length} cannot be less than 0.0.")
    return minimum_segment_length
