from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd

from completor.completion import WellSchedule
from completor.logger import logger
from completor.read_casefile import ReadCasefile
from completor.utils import abort, as_data_frame


def trim_pandas(df_temp: pd.DataFrame) -> pd.DataFrame:
    """
    Trim a pandas dataframe containing default values.

    Args:
        df_temp: DataFrame

    Returns:
        Updated DataFrame
    """
    header = df_temp.columns.to_numpy()
    start_trim = -1
    found_start = False
    for idx in range(df_temp.shape[1]):
        col_value = df_temp.iloc[:, idx].to_numpy().flatten().astype(str)
        find_star = all("*" in elem for elem in col_value)
        if find_star:
            if not found_start:
                start_trim = idx
                found_start = True
        else:
            start_trim = idx + 1
            found_start = False
    new_header = header[:start_trim]
    return df_temp[new_header]


def add_columns_first_last(df_temp: pd.DataFrame, add_first: bool = True, add_last: bool = True) -> pd.DataFrame:
    """
    Add the first and last column of DataFrame.

    Args:
        df_temp: E.g. WELSPECS, COMPSEGS, COMPDAT, WELSEGS, etc.
        add_first: Add the first column
        add_last: Add the last column

    Returns:
        Updated DataFrame
    """
    # first trim pandas
    df_temp = trim_pandas(df_temp)
    # add first and last column
    nline = df_temp.shape[0]
    if add_first:
        df_temp.insert(loc=0, column="--", value=np.full(nline, fill_value=" "))
    if add_last:
        df_temp[""] = ["/"] * nline
    return df_temp


def dataframe_tostring(
    df_temp: pd.DataFrame,
    format_column: bool = False,
    trim_df: bool = True,
    header: bool = True,
    formatters: Mapping[str | int, Callable[..., Any]] | None = None,
) -> str:
    """
    Convert DataFrame to string.

    Args:
        df_temp: COMPDAT, COMPSEGS, etc.
        format_column: If columns are formatted
        trim_df: To trim or not to trim. Default: True
        formatters: Dictionary of the column format. Default: None
        header: Keep header (True) or not (False)

    Returns:
        Text string of the DataFrame
    """
    if df_temp.empty:
        return ""
    # check if the dataframe has first = "--" and last column ""
    columns = df_temp.columns.to_numpy()
    if columns[-1] != "":
        if trim_df:
            df_temp = trim_pandas(df_temp)
        df_temp = add_columns_first_last(df_temp, add_first=False, add_last=True)
        columns = df_temp.columns.to_numpy()
    if columns[0] != "--":
        # then add first column
        df_temp = add_columns_first_last(df_temp, add_first=True, add_last=False)
    # Add single quotes around well names in output file
    if "WELL" in df_temp.columns:
        df_temp["WELL"] = "'" + df_temp["WELL"].astype(str) + "'"
    output_string = df_temp.to_string(index=False, justify="justify", header=header)
    if format_column:
        if formatters is None:
            formatters = {
                "ALPHA": "{:.10g}".format,
                "SF": "{:.10g}".format,
                "ROUGHNESS": "{:.10g}".format,
                "CF": "{:.10g}".format,
                "KH": "{:.10g}".format,
                "MD": "{:.3f}".format,
                "TVD": "{:.3f}".format,
                "STARTMD": "{:.3f}".format,
                "ENDMD": "{:.3f}".format,
                "CV_DAR": "{:.10g}".format,
                "CV": "{:.10g}".format,
                "AC": "{:.3e}".format,
                "AC_OIL": "{:.3e}".format,
                "AC_GAS": "{:.3e}".format,
                "AC_WATER": "{:.3e}".format,
                "AC_MAX": "{:.3e}".format,
                "DEFAULTS": "{:.10s}".format,
                "WHF_LCF_DAR": "{:.10g}".format,
                "WHF_HCF_DAR": "{:.10g}".format,
                "GHF_LCF_DAR": "{:.10g}".format,
                "GHF_HCF_DAR": "{:.10g}".format,
                "ALPHA_MAIN": "{:.10g}".format,
                "ALPHA_PILOT": "{:.10g}".format,
            }
        try:
            output_string = df_temp.to_string(index=False, justify="justify", formatters=formatters, header=header)
        except ValueError:
            pass
    if output_string is None:
        return ""
    return output_string


def get_outlet_segment(
    target_md: npt.NDArray[np.float64] | list[float],
    reference_md: npt.NDArray[np.float64] | list[float],
    reference_segment_number: npt.NDArray[np.float64] | list[int],
) -> npt.NDArray[np.float64]:
    """
    Find the outlet segment in the other layers.

    For example: Find the corresponding tubing segment of the device segment,
    or the corresponding device segment of the annulus segment.

    Args:
        target_md: Target measured depth
        reference_md: Reference measured depth
        reference_segment_number: Reference segment number

    Returns:
        The outlet segments
    """
    df_target_md = pd.DataFrame(target_md, columns=["MD"])
    df_reference = pd.DataFrame(np.column_stack((reference_md, reference_segment_number)), columns=["MD", "SEG"])
    df_reference["SEG"] = df_reference["SEG"].astype(np.int64)
    df_reference.sort_values(by=["MD"], inplace=True)
    return (
        pd.merge_asof(left=df_target_md, right=df_reference, on=["MD"], direction="nearest")["SEG"].to_numpy().flatten()
    )


def get_number_of_characters(df: pd.DataFrame) -> int:
    """
    Calculate the number of characters.

    Args:
        df: DataFrame

    Returns:
        Number of characters
    """
    df_temp = df.iloc[:1, :].copy()
    df_temp = dataframe_tostring(df_temp, True)
    df_temp = df_temp.split("\n")
    return len(df_temp[0])


def get_header(well_name: str, keyword: str, lat: int, layer: str, nchar: int = 100) -> str:
    """
    Print the header.

    Args:
        well_name: Well name
        keyword: Table keyword e.g. WELSEGS, COMPSEGS, COMPDAT, etc.
        lat: Lateral number
        layer: Layer description e.g. tubing, device and annulus
        nchar: Number of characters for the line boundary. Default 100

    Returns:
        String header
    """
    if keyword == "WELSEGS":
        header = f"{'-' * nchar}\n-- Well : {well_name} : Lateral : {lat} : {layer} layer\n"
    else:
        header = f"{'-' * nchar}\n-- Well : {well_name} : Lateral : {lat}\n"
    return header + "-" * nchar + "\n"


def prepare_tubing_layer(
    schedule: WellSchedule,
    well_name: str,
    lateral: int,
    df_well: pd.DataFrame,
    start_segment: int,
    branch_no: int,
    completion_table: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare tubing layer data frame.

    Args:
        schedule: Schedule object
        well_name: Well name
        lateral: Lateral number
        df_well: Must contain column LATERAL, TUB_MD, TUB_TVD, INNER_DIAMETER, ROUGHNESS
        start_segment: Start number of the first tubing segment
        branch_no: Branch number for this tubing layer
        completion_table: DataFrame with completion data.

    Returns:
        DataFrame for tubing layer

    The DataFrame df_well has the format shown in
    ``create_wells.complete_the_well``.
    """
    # for convenience
    rnm = {"TUBINGMD": "MD", "TUBINGTVD": "TVD", "TUBINGID": "DIAM", "TUBINGROUGHNESS": "ROUGHNESS"}
    cols = list(rnm.values())
    #
    df_well = df_well[df_well["WELL"] == well_name]
    df_well = df_well[df_well["LATERAL"] == lateral]
    df_tubing_in_reservoir = as_data_frame(
        MD=df_well["TUB_MD"], TVD=df_well["TUB_TVD"], DIAM=df_well["INNER_DIAMETER"], ROUGHNESS=df_well["ROUGHNESS"]
    )
    # handle overburden
    well_segments = schedule.get_welsegs(well_name, lateral)[1]
    md_input_welsegs = well_segments["TUBINGMD"]
    md_welsegs_in_reservoir = df_tubing_in_reservoir["MD"]
    # TODO: check if ok. should it be ENDMD above (not available here)
    overburden = well_segments[(md_welsegs_in_reservoir[0] - md_input_welsegs) > 1.0]
    if not overburden.empty:
        overburden = overburden.rename(index=str, columns=rnm)
        overburden_fixed = fix_tubing_inner_diam_roughness(well_name, overburden, completion_table)
        df_tubing_with_overburden = pd.concat([overburden_fixed[cols], df_tubing_in_reservoir])
    else:
        df_tubing_with_overburden = df_tubing_in_reservoir
    df_tubing_with_overburden["SEG"] = start_segment + np.arange(df_tubing_with_overburden.shape[0])
    df_tubing_with_overburden["SEG2"] = df_tubing_with_overburden["SEG"]
    df_tubing_with_overburden["BRANCH"] = branch_no
    df_tubing_with_overburden.reset_index(drop=True, inplace=True)
    # set out-segment to be successive.
    # The first item will be updated in connect_lateral
    df_tubing_with_overburden["OUT"] = df_tubing_with_overburden["SEG"] - 1
    # make sure order is correct
    df_tubing_with_overburden = df_tubing_with_overburden.reindex(columns=["SEG", "SEG2", "BRANCH", "OUT"] + cols)
    df_tubing_with_overburden[""] = "/"  # for printing
    # locate where it attached to (the top segment)
    wsa = schedule.get_welsegs(well_name)[1]  # all laterals
    top = wsa[wsa.TUBINGSEGMENT == well_segments.iloc[0].TUBINGOUTLET]  # could be empty

    return df_tubing_with_overburden, top


def fix_tubing_inner_diam_roughness(
    well_name: str, overburden: pd.DataFrame, completion_table: pd.DataFrame
) -> pd.DataFrame:
    """
    Ensure roughness and inner diameter of the overburden segments are
    taken from the case file and not the input schedule file.

    Overburden segments are WELSEGS segments located above the top COMPSEGS segment.

    Args:
        well_name: Well name
        overburden: Input schedule WELSEGS segments in the overburden
        completion_table: Completion table from the case file, ReadCasefile object.

    Returns:
        Corrected overburden DataFrame with inner diameter and roughness taken
        from the ReadCasefile object.

    Raises:
        ValueError: If the well completion in not found in overburden at overburden_md
    """

    overburden_out = overburden.copy(deep=True)
    completion_table_well = completion_table.loc[completion_table["WELL"] == well_name]
    completion_table_well = completion_table_well.loc[
        completion_table_well["BRANCH"] == overburden_out["TUBINGBRANCH"].iloc[0]
    ]
    overburden_found_in_completion = False

    for idx_overburden in range(overburden_out.shape[0]):
        overburden_md = overburden_out["MD"].iloc[idx_overburden]
        overburden_found_in_completion = False
        for idx_completion_table_well in range(completion_table_well.shape[0]):
            completion_table_start = completion_table_well["STARTMD"].iloc[idx_completion_table_well]
            completion_table_end = completion_table_well["ENDMD"].iloc[idx_completion_table_well]
            if (completion_table_end >= overburden_md >= completion_table_start) and not overburden_found_in_completion:
                overburden_out.iloc[idx_overburden, overburden_out.columns.get_loc("DIAM")] = completion_table_well[
                    "INNER_ID"
                ].iloc[idx_completion_table_well]
                overburden_out.iloc[idx_overburden, overburden_out.columns.get_loc("ROUGHNESS")] = (
                    completion_table_well["ROUGHNESS"].iloc[idx_completion_table_well]
                )
                overburden_found_in_completion = True
                break
    if overburden_found_in_completion:
        return overburden_out

    try:
        raise ValueError(f"Cannot find {well_name} completion in overburden at {overburden_md} mMD")
    except NameError as err:
        raise ValueError(f"Cannot find {well_name} in completion overburden; it is empty") from err


def connect_lateral(
    well_name: str,
    lateral: int,
    data: dict[int, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]],
    case: ReadCasefile,
) -> None:
    """
    Connect lateral to main wellbore/branch.

    The main branch can either have a tubing- or device-layer connected.
    By default the lateral will be connected to tubing-layer, but if
    connect_to_tubing is False it will be connected to device-layer.
    Aborts if cannot find device layer at junction depth

    Args:
        well_name: Well name
        lateral: Lateral number
        data: Dict with integer key 'lateral' containing:
            df_tubing: DataFrame tubing layer
            df_device: DataFrame device layer
            df_annulus: DataFrame annulus layer
            df_wseglink: DataFrame WSEGLINK
            top: DataFrame of first connection
        case: ReadCasefile object

    Raises:
        SystemExit: If there is no device layer at junction of lateral
    """
    df_tubing, _, _, _, top = data[lateral]
    if not top.empty:
