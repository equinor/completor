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
    df_well = df_well[df_well["WELL"] == well_name]
    df_well = df_well[df_well["LATERAL"] == lateral]
    df_tubing_in_reservoir = as_data_frame(
        MD=df_well["TUB_MD"], TVD=df_well["TUB_TVD"], DIAM=df_well["INNER_DIAMETER"], ROUGHNESS=df_well["ROUGHNESS"]
    )
    # handle overburden
    well_segments = schedule.get_well_segments(well_name, lateral)[1]
    md_input_welsegs = well_segments["TUBINGMD"]
    md_welsegs_in_reservoir = df_tubing_in_reservoir["MD"]
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
    wsa = schedule.get_well_segments(well_name)[1]  # all laterals
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
                    "INNER_DIAMETER"
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
        lateral0 = top.TUBINGBRANCH.to_numpy()[0]
        md_junct = top.TUBINGMD.to_numpy()[0]
        if md_junct > df_tubing["MD"][0]:
            logger.warning(
                "Found a junction above the start of the tubing layer, well %s, "
                "branch %s. Check the depth of segments pointing at the main stem "
                "in schedule-file",
                well_name,
                lateral,
            )
        if case.connect_to_tubing(well_name, lateral):
            df_segm0 = data[lateral0][0]  # df_tubing
        else:
            df_segm0 = data[lateral0][1]  # df_device
        try:
            if case.connect_to_tubing(well_name, lateral):
                # Since md_junct (top.TUBINGMD) has segment tops and
                # segm0.MD has grid block midpoints, a junction at the top of the
                # well may not be found. Therefore, we try the following:
                if (~(df_segm0.MD <= md_junct)).all():
                    md_junct = df_segm0.MD.iloc[0]
                    idx = np.where(df_segm0.MD <= md_junct)[0][-1]
                else:
                    idx = np.where(df_segm0.MD <= md_junct)[0][-1]
            else:
                # Add 0.1 to md_junct since md_junct refers to the tubing layer
                # junction md and the device layer md is shifted 0.1 m to the
                # tubing layer.
                idx = np.where(df_segm0.MD <= md_junct + 0.1)[0][-1]
        except IndexError as err:
            raise abort("Cannot find a device layer at " f"junction of lateral {lateral} in {well_name}") from err
        outsegm = df_segm0.at[idx, "SEG"]
    else:
        outsegm = 1  # default
    df_tubing.at[0, "OUT"] = outsegm


def prepare_device_layer(
    well_name: str, lateral: int, df_well: pd.DataFrame, df_tubing: pd.DataFrame, device_length: float = 0.1
) -> pd.DataFrame:
    """
    Prepare device layer dataframe.

    Args:
        well_name: Well name
        lateral: Lateral number
        df_well: Must contain LATERAL, TUB_MD, TUB_TVD,
                 INNER_DIAMETER, ROUGHNESS, DEVICETYPE and NDEVICES
        df_tubing: Data frame from function prepare_tubing_layer
                   for this well and this lateral
        device_length: Segment length (default: 0.1)

    Returns:
        DataFrame for device layer
    """
    start_segment = max(df_tubing["SEG"].to_numpy()) + 1
    start_branch = max(df_tubing["BRANCH"].to_numpy()) + 1
    df_well = df_well[df_well["WELL"] == well_name]
    df_well = df_well[df_well["LATERAL"] == lateral]
    # device segments are only created if:
    # 1. the device type is PERF
    # 2. if it is not PERF then it must have number of device > 0
    df_well = df_well[(df_well["DEVICETYPE"] == "PERF") | (df_well["NDEVICES"] > 0)]
    if df_well.empty:
        # return blank dataframe
        return pd.DataFrame()
    # now create dataframe for device layer
    df_device = pd.DataFrame()
    df_device["SEG"] = start_segment + np.arange(df_well.shape[0])
    df_device["SEG2"] = df_device["SEG"].to_numpy()
    df_device["BRANCH"] = start_branch + np.arange(df_well.shape[0])
    df_device["OUT"] = get_outlet_segment(
        df_well["TUB_MD"].to_numpy(), df_tubing["MD"].to_numpy(), df_tubing["SEG"].to_numpy()
    )
    df_device["MD"] = df_well["TUB_MD"].to_numpy() + device_length
    df_device["TVD"] = df_well["TUB_TVD"].to_numpy()
    df_device["DIAM"] = df_well["INNER_DIAMETER"].to_numpy()
    df_device["ROUGHNESS"] = df_well["ROUGHNESS"].to_numpy()
    device_comment = np.where(
        df_well["DEVICETYPE"] == "PERF",
        "/ -- Open Perforation",
        np.where(
            df_well["DEVICETYPE"] == "AICD",
            "/ -- AICD types",
            np.where(
                df_well["DEVICETYPE"] == "ICD",
                "/ -- ICD types",
                np.where(
                    df_well["DEVICETYPE"] == "VALVE",
                    "/ -- Valve types",
                    np.where(
                        df_well["DEVICETYPE"] == "DAR",
                        "/ -- DAR types",
                        np.where(
                            df_well["DEVICETYPE"] == "AICV",
                            "/ -- AICV types",
                            np.where(df_well["DEVICETYPE"] == "ICV", "/ -- ICV types", ""),
                        ),
                    ),
                ),
            ),
        ),
    )
    df_device[""] = device_comment
    return df_device


def prepare_annulus_layer(
    well_name: str, lateral: int, df_well: pd.DataFrame, df_device: pd.DataFrame, annulus_length: float = 0.1
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Prepare annulus layer and wseglink dataframe.

    Args:
        well_name: Well name
        lateral: Lateral number
        df_well: Must contain LATERAL, ANNULUS_ZONE,
            TUB_MD, TUB_TVD, OUTER_DIAMETER, ROUGHNESS, DEVICETYPE and NDEVICES
        df_device: DataFrame from function prepare_device_layer
            for this well and this lateral
        annulus_length: Annulus segment length increment (default: 0.1)

    Returns:
        Annulus DataFrame, wseglink DataFrame
    """
    # filter for this lateral
    df_well = df_well[df_well["WELL"] == well_name]
    df_well = df_well[df_well["LATERAL"] == lateral]
    # filter segments which have annular zones
    df_well = df_well[df_well["ANNULUS_ZONE"] > 0]
    # loop through all annular zones
    # initiate annulus and wseglink dataframe
    df_annulus = pd.DataFrame()
    df_wseglink = pd.DataFrame()
    for izone, zone in enumerate(df_well["ANNULUS_ZONE"].unique()):
        # filter only that annular zone
        df_branch = df_well[df_well["ANNULUS_ZONE"] == zone]
        df_active = df_branch[(df_branch["NDEVICES"].to_numpy() > 0) | (df_branch["DEVICETYPE"].to_numpy() == "PERF")]
        # setting the start segment number and start branch number
        if izone == 0:
            start_segment = max(df_device["SEG"]) + 1
            start_branch = max(df_device["BRANCH"]) + 1
        else:
            start_segment = max(df_annulus["SEG"]) + 1
            start_branch = max(df_annulus["BRANCH"]) + 1
        # now find the most downstream connection of the annulus zone
        idx_connection = np.argwhere(
            (df_branch["NDEVICES"].to_numpy() > 0) | (df_branch["DEVICETYPE"].to_numpy() == "PERF")
        )
        if idx_connection[0] == 0:
            # If the first connection then everything is easy
            df_annulus_upstream, df_wseglink_upstream = calculate_upstream(
                df_branch, df_active, df_device, start_branch, annulus_length, start_segment, well_name
            )
        else:
            # meaning the main connection is not the most downstream segment
            # therefore we have to split the annulus segment into two
            # the splitting point is the most downstream segment
            # which have device segment open or PERF
            try:
                df_branch_downstream = df_branch.iloc[0 : idx_connection[0], :]
                df_branch_upstream = df_branch.iloc[idx_connection[0] :,]
            except TypeError:
                raise abort(
                    "Most likely error is that Completor cannot have "
                    "open annulus above top reservoir with"
                    " zero valves pr joint. Please contact user support"
                    " if this is not the case."
                )
            # downstream part
            df_annulus_downstream = pd.DataFrame()
            df_annulus_downstream["SEG"] = start_segment + np.arange(df_branch_downstream.shape[0])
            df_annulus_downstream["SEG2"] = df_annulus_downstream["SEG"]
            df_annulus_downstream["BRANCH"] = start_branch
            df_annulus_downstream["OUT"] = df_annulus_downstream["SEG"] + 1
            df_annulus_downstream["MD"] = df_branch_downstream["TUB_MD"].to_numpy() + annulus_length
            df_annulus_downstream["TVD"] = df_branch_downstream["TUB_TVD"].to_numpy()
            df_annulus_downstream["DIAM"] = df_branch_downstream["OUTER_DIAMETER"].to_numpy()
            df_annulus_downstream["ROUGHNESS"] = df_branch_downstream["ROUGHNESS"].to_numpy()

            # no WSEGLINK in the downstream part because
            # no annulus segment have connection to
            # the device segment. in case you wonder why :)

            # upstream part
            # update the start segment and start branch
            start_segment = max(df_annulus_downstream["SEG"]) + 1
            start_branch = max(df_annulus_downstream["BRANCH"]) + 1
            # create dataframe for upstream part
            df_annulus_upstream, df_wseglink_upstream = calculate_upstream(
                df_branch_upstream, df_active, df_device, start_branch, annulus_length, start_segment, well_name
            )
            # combine the two dataframe upstream and downstream
            df_annulus_upstream = pd.concat([df_annulus_downstream, df_annulus_upstream])

        # combine annulus and wseglink dataframe
        if izone == 0:
            df_annulus = df_annulus_upstream.copy(deep=True)
            df_wseglink = df_wseglink_upstream.copy(deep=True)
        else:
            df_annulus = pd.concat([df_annulus, df_annulus_upstream])
            df_wseglink = pd.concat([df_wseglink, df_wseglink_upstream])

    if df_wseglink.shape[0] > 0:
        df_wseglink = df_wseglink[["WELL", "ANNULUS", "DEVICE"]]
        df_wseglink["ANNULUS"] = df_wseglink["ANNULUS"].astype(np.int64)
        df_wseglink["DEVICE"] = df_wseglink["DEVICE"].astype(np.int64)
        df_wseglink[""] = "/"

    if df_annulus.shape[0] > 0:
        df_annulus[""] = "/"
    return df_annulus, df_wseglink


def calculate_upstream(
    df_branch: pd.DataFrame,
    df_active: pd.DataFrame,
    df_device: pd.DataFrame,
    start_branch: int,
    annulus_length: float,
    start_segment: int,
    well_name: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calculate upstream for annulus and wseglink.

    Args:
        df_branch: The well for current annulus zone
        df_active: Active segments (NDEVICES > 0 or DEVICETYPE is PERF)
        df_device: Device layer
        start_branch: Start branch number
        annulus_length: Annulus segment length increment (default 0.1)
        start_segment: Start segment number of annulus
        well_name: Well name

    Returns:
        Annulus upstream and wseglink upstream
    """

    df_annulus_upstream = pd.DataFrame()
    df_annulus_upstream["SEG"] = start_segment + np.arange(df_branch.shape[0])
    df_annulus_upstream["SEG2"] = df_annulus_upstream["SEG"]
    df_annulus_upstream["BRANCH"] = start_branch
    out_segment = df_annulus_upstream["SEG"].to_numpy() - 1
    # determining the outlet segment of the annulus segment
    # if the annulus segment is not the most downstream which has connection
    # then the outlet is its adjacent annulus segment
    device_segment = get_outlet_segment(
        df_branch["TUB_MD"].to_numpy(), df_device["MD"].to_numpy(), df_device["SEG"].to_numpy()
    )
    # but for the most downstream annulus segment
    # its outlet is the device segment
    out_segment[0] = device_segment[0]
    # determining segment position
    md_ = df_branch["TUB_MD"].to_numpy() + annulus_length
    md_[0] = md_[0] + annulus_length
    df_annulus_upstream["OUT"] = out_segment
    df_annulus_upstream["MD"] = md_
    df_annulus_upstream["TVD"] = df_branch["TUB_TVD"].to_numpy()
    df_annulus_upstream["DIAM"] = df_branch["OUTER_DIAMETER"].to_numpy()
    df_annulus_upstream["ROUGHNESS"] = df_branch["ROUGHNESS"].to_numpy()
    device_segment = get_outlet_segment(
        df_active["TUB_MD"].to_numpy(), df_device["MD"].to_numpy(), df_device["SEG"].to_numpy()
    )
    annulus_segment = get_outlet_segment(
        df_active["TUB_MD"].to_numpy(), df_annulus_upstream["MD"].to_numpy(), df_annulus_upstream["SEG"].to_numpy()
    )
    outlet_segment = get_outlet_segment(
        df_active["TUB_MD"].to_numpy(), df_annulus_upstream["MD"].to_numpy(), df_annulus_upstream["OUT"].to_numpy()
    )
    df_wseglink_upstream = as_data_frame(
        WELL=[well_name] * device_segment.shape[0],
        ANNULUS=annulus_segment,
        DEVICE=device_segment,
        OUTLET=outlet_segment,
    )
    # basically WSEGLINK is only for those segments
    # whose its outlet segment is not a device segment
    df_wseglink_upstream = df_wseglink_upstream[df_wseglink_upstream["DEVICE"] != df_wseglink_upstream["OUTLET"]]
    return df_annulus_upstream, df_wseglink_upstream


def connect_compseg_icv(
    df_reservoir: pd.DataFrame, df_device: pd.DataFrame, df_annulus: pd.DataFrame, df_completion_table: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Connect COMPSEGS with the correct depth due to ICV segmenting combination.

    Args:
        df_reservoir: The df_reservoir from class object CreateWells
        df_device: DataFrame from function prepare_device_layer
                    for this well and lateral
        df_annulus: DataFrame from function prepare_annulus_layer
                    for this well and lateral
        df_completion_table: DataFrame

    Returns:
        df_compseg_device, df_compseg_annulus
    """

    df_temp = df_completion_table[
        (df_completion_table["NVALVEPERJOINT"] > 0.0) | (df_completion_table["DEVICETYPE"] == "PERF")
    ]
    df_completion_table_clean = df_temp[(df_temp["ANNULUS"] != "PA") & (df_temp["DEVICETYPE"] == "ICV")]
    df_res = df_reservoir.copy(deep=True)

    df_res["MD_MARKER"] = df_res["MD"]
    starts = df_completion_table_clean["STARTMD"].apply(lambda x: max(x, df_res["STARTMD"].iloc[0]))
    ends = df_completion_table_clean["ENDMD"].apply(lambda x: min(x, df_res["ENDMD"].iloc[-1]))
    for start, end in zip(starts, ends):
        condition = f"@df_res.MD >= {start} and @df_res.MD <= {end} and @df_res.DEVICETYPE == 'ICV'"
        func = float(start + end) / 2
        column_to_modify = "MD_MARKER"
        column_index = df_res.query(condition).index
        df_res.loc[column_index, column_to_modify] = func

    df_compseg_device = pd.merge_asof(
        left=df_res, right=df_device, left_on="MD_MARKER", right_on="MD", direction="nearest"
    )
    df_compseg_annulus = pd.DataFrame()
    if (df_completion_table["ANNULUS"] == "OA").any():
        df_compseg_annulus = pd.merge_asof(
            left=df_res, right=df_annulus, left_on="MD_MARKER", right_on="MD", direction="nearest"
        )
    return df_compseg_device, df_compseg_annulus


def prepare_compsegs(
    well_name: str,
    lateral: int,
    df_reservoir: pd.DataFrame,
    df_device: pd.DataFrame,
    df_annulus: pd.DataFrame,
    df_completion_table: pd.DataFrame,
    segment_length: float | str,
) -> pd.DataFrame:
    """
    Prepare output for COMPSEGS.

    Args:
        well_name: Well name
        lateral: Lateral number
        df_reservoir: The df_reservoir from class object CreateWells
        df_device: DataFrame from function prepare_device_layer
                   for this well and this lateral
        df_annulus: DataFrame from function prepare_annulus_layer
                    for this well and this lateral
        df_completion_table: DataFrame
        segment_length: Segment length

    Returns:
        COMPSEGS DataFrame

    Raises:
        SystemExit: If dataframes are unable to merge correctly.
    """
    # filter for this lateral

    df_reservoir = df_reservoir[df_reservoir["WELL"] == well_name]
    df_reservoir = df_reservoir[df_reservoir["LATERAL"] == lateral]
    # compsegs is only for those who are either:
    # 1. open perforation in the device segment
    # 2. has number of device > 0
    # 3. it is connected in the annular zone
    df_reservoir = df_reservoir[
        (df_reservoir["ANNULUS_ZONE"] > 0) | (df_reservoir["NDEVICES"] > 0) | (df_reservoir["DEVICETYPE"] == "PERF")
    ]
    # sort device dataframe by MD to be used for pd.merge_asof
    if df_reservoir.shape[0] == 0:
        return pd.DataFrame()
    df_device = df_device.sort_values(by=["MD"])
    if isinstance(segment_length, str):
        if segment_length.upper() == "USER":
            segment_length = -1.0
    icv_segmenting = (
        df_reservoir["DEVICETYPE"].nunique() > 1
        and (df_reservoir["DEVICETYPE"] == "ICV").any()
        and not df_reservoir["NDEVICES"].empty
    )
    if df_annulus.empty:
        # meaning there are no annular zones then
        # all cells in this lateral and this well
        # are connected to the device segment
        if isinstance(segment_length, float):
            if segment_length >= 0:
                df_compseg_device = pd.merge_asof(left=df_reservoir, right=df_device, on=["MD"], direction="nearest")
            else:
                # Ensure that tubing segment boundaries as described in the case
                # file are honored.
                # Associate reservoir cells with tubing segment midpoints using
                # markers
                df_compseg_device, df_compseg_annulus = connect_compseg_usersegment(
                    df_reservoir, df_device, df_annulus, df_completion_table
                )
        else:
            df_compseg_device = pd.merge_asof(left=df_reservoir, right=df_device, on=["MD"], direction="nearest")
        if icv_segmenting:
            df_compseg_device, _ = connect_compseg_icv(df_reservoir, df_device, df_annulus, df_completion_table)
        compseg = pd.DataFrame()
        compseg["I"] = df_compseg_device["I"].to_numpy()
        compseg["J"] = df_compseg_device["J"].to_numpy()
        compseg["K"] = df_compseg_device["K"].to_numpy()
        # take the BRANCH column from df_device
        compseg["BRANCH"] = df_compseg_device["BRANCH"].to_numpy()
        compseg["STARTMD"] = df_compseg_device["STARTMD"].to_numpy()
        compseg["ENDMD"] = df_compseg_device["ENDMD"].to_numpy()
        compseg["DIR"] = df_compseg_device["COMPSEGS_DIRECTION"].to_numpy()
        compseg["DEF"] = "3*"
        compseg["SEG"] = df_compseg_device["SEG"].to_numpy()
    else:
        # sort the df_annulus and df_device
        df_annulus = df_annulus.sort_values(by=["MD"])
        if isinstance(segment_length, float):
            # SEGMENTLENGTH = FIXED
            if segment_length >= 0:
                df_compseg_annulus = pd.merge_asof(left=df_reservoir, right=df_annulus, on=["MD"], direction="nearest")
                df_compseg_device = pd.merge_asof(left=df_reservoir, right=df_device, on=["MD"], direction="nearest")
            else:
                # Ensure that tubing segment boundaries as described in the case
                # file are honored.
                # Associate reservoir cells with tubing segment midpoints using
                # markers
                df_compseg_device, df_compseg_annulus = connect_compseg_usersegment(
                    df_reservoir, df_device, df_annulus, df_completion_table
                )
                # Restore original sorting of DataFrames
                df_compseg_annulus.sort_values(by=["STARTMD"], inplace=True)
                df_compseg_device.sort_values(by=["STARTMD"], inplace=True)
                df_compseg_device.drop(["MARKER"], axis=1, inplace=True)
                df_compseg_annulus.drop(["MARKER"], axis=1, inplace=True)
        else:
            df_compseg_annulus = pd.merge_asof(left=df_reservoir, right=df_annulus, on=["MD"], direction="nearest")
            df_compseg_device = pd.merge_asof(left=df_reservoir, right=df_device, on=["MD"], direction="nearest")
        if icv_segmenting:
            df_compseg_device, df_compseg_annulus = connect_compseg_icv(
                df_reservoir, df_device, df_annulus, df_completion_table
            )

        def _choose(parameter: str) -> np.ndarray:
            return choose_layer(df_reservoir, df_compseg_annulus, df_compseg_device, parameter)

        compseg = as_data_frame(
            I=_choose("I"),
            J=_choose("J"),
            K=_choose("K"),
            BRANCH=_choose("BRANCH"),
            STARTMD=_choose("STARTMD"),
            ENDMD=_choose("ENDMD"),
            DIR=_choose("COMPSEGS_DIRECTION"),
            DEF="3*",
            SEG=_choose("SEG"),
        )
    compseg[""] = "/"
    return compseg


def connect_compseg_usersegment(
    df_reservoir: pd.DataFrame, df_device: pd.DataFrame, df_annulus: pd.DataFrame, df_completion_table: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Connect COMPSEGS with user segmentation. This method will connect
    df_reservoir with df_device and df_annulus in accordance of its
    depth in the df_completion_table due to user segmentation method.

    Args:
        df_reservoir: The df_reservoir from class object CreateWells
        df_device: DataFrame from function prepare_device_layer
                    for this well and lateral
        df_annulus: DataFrame from function prepare_annulus_layer
                    for this well and lateral
        df_completion_table: DataFrame

    Returns:
        df_compseg_device, df_compseg_annulus
    """
    # check on top of df_res if the completion table is feasible
    df_temp = df_completion_table[
        (df_completion_table["NVALVEPERJOINT"] > 0.0) | (df_completion_table["DEVICETYPE"] == "PERF")
    ]
    df_completion_table_clean = df_temp[(df_temp["ANNULUS"] != "PA")]
    if not df_annulus.empty:
        df_completion_table_clean = df_completion_table[df_completion_table["ANNULUS"] == "OA"]
    df_completion_table_clean = df_completion_table_clean[
        (df_completion_table_clean["ENDMD"] > df_reservoir["STARTMD"].iloc[0])
    ]
    df_annulus.reset_index(drop=True, inplace=True)
    df_res = df_reservoir.assign(MARKER=[0 for _ in range(df_reservoir.shape[0])])
    df_dev = df_device.assign(MARKER=[x + 1 for x in range(df_device.shape[0])])
    df_ann = df_annulus.assign(MARKER=[x + 1 for x in range(df_annulus.shape[0])])
    starts = df_completion_table_clean["STARTMD"].apply(lambda x: max(x, df_res["STARTMD"].iloc[0]))
    ends = df_completion_table_clean["ENDMD"].apply(lambda x: min(x, df_res["ENDMD"].iloc[-1]))
    func = 1
    for start, end in zip(starts, ends):
        condition = f"@df_res.MD >= {start} and @df_res.MD <= {end}"
        column_to_modify = "MARKER"
        column_index = df_res.query(condition).index
        df_res.loc[column_index, column_to_modify] = func
        func += 1
    df_res.reset_index(drop=True, inplace=True)
    df_compseg_annulus = pd.DataFrame()
    if not df_annulus.empty:
        try:
            df_compseg_annulus = pd.merge_asof(
                left=df_res.sort_values("MARKER"), right=df_ann, on=["MARKER"], direction="nearest"
            )
        except ValueError as err:
            raise abort(
                "Unexpected error when merging data frames. Please contact the "
                "dev-team with the stack trace above and the files that caused "
                "this error"
            ) from err
    try:
        df_compseg_device = pd.merge_asof(
            left=df_res.sort_values("MARKER"), right=df_dev, on=["MARKER"], direction="nearest"
        )
    except ValueError as err:
        raise abort(
            "Unexpected error when merging data frames. Please contact the "
            "dev-team with the stack trace above and the files that caused "
            "this error"
        ) from err

    return df_compseg_device, df_compseg_annulus


def choose_layer(
    df_reservoir: pd.DataFrame, df_compseg_annulus: pd.DataFrame, df_compseg_device: pd.DataFrame, parameter: str
) -> np.ndarray:
    """
    Choose relevant parameters from either df_compseg_annulus or df_compseg_device.

    Args:
        df_reservoir:
        df_compseg_annulus:
        df_compseg_device:
        parameter:

    Returns:
        Relevant parameters
    """
    branch_num = df_reservoir["ANNULUS_ZONE"].to_numpy()
    ndevice = df_reservoir["NDEVICES"].to_numpy()
    dev_type = df_reservoir["DEVICETYPE"].to_numpy()
    return np.where(
        branch_num > 0,
        df_compseg_annulus[parameter].to_numpy(),
        np.where((ndevice > 0) | (dev_type == "PERF"), df_compseg_device[parameter].to_numpy(), -1),
    )


def fix_well_id(df_reservoir: pd.DataFrame, df_completion: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure that well/casing inner diameter in the COMPDAT section is in agreement with
    case/config file and not the input schedule file.

    Args:
        df_reservoir: Reservoir dataframe
        df_completion_table: ReadCasefile object for current well/lateral

    Returns:
        Corrected df_reservoir DataFrame for current well/lateral
        with inner diameter taken from the ReadCasefile object.
    """
    df_reservoir = df_reservoir.copy(deep=True)
    completion_diameters = []
    for md_reservoir in df_reservoir["MD"]:
        for start_completion, outer_inner_diameter_completion, end_completion in zip(
            df_completion["STARTMD"], df_completion["OUTER_DIAMETER"], df_completion["ENDMD"]
        ):
            if start_completion <= md_reservoir <= end_completion:
                completion_diameters.append(outer_inner_diameter_completion)
                break
    df_reservoir["DIAM"] = completion_diameters
    return df_reservoir


def prepare_compdat(
    well_name: str, lateral: int, df_reservoir: pd.DataFrame, df_completion_table: pd.DataFrame
) -> pd.DataFrame:
    """
    Prepare COMPDAT data frame.

    Args:
        well_name: Well name
        lateral: Lateral number
        df_reservoir: df_reservoir from class CreateWells
        df_completion_table: From class ReadCasefile

    Returns:
        COMPDAT
    """
    df_reservoir = df_reservoir[df_reservoir["WELL"] == well_name]
    df_reservoir = df_reservoir[df_reservoir["LATERAL"] == lateral]
    df_reservoir = df_reservoir[
        (df_reservoir["ANNULUS_ZONE"] > 0) | ((df_reservoir["NDEVICES"] > 0) | (df_reservoir["DEVICETYPE"] == "PERF"))
    ]
    if df_reservoir.shape[0] == 0:
        return pd.DataFrame()
    compdat = pd.DataFrame()
    compdat["WELL"] = [well_name] * df_reservoir.shape[0]
    compdat["I"] = df_reservoir["I"].to_numpy()
    compdat["J"] = df_reservoir["J"].to_numpy()
    compdat["K"] = df_reservoir["K"].to_numpy()
    compdat["K2"] = df_reservoir["K2"].to_numpy()
    compdat["FLAG"] = df_reservoir["STATUS"].to_numpy()
    compdat["SAT"] = df_reservoir["SATNUM"].to_numpy()
    compdat["CF"] = df_reservoir["CF"].to_numpy()
    compdat["DIAM"] = fix_well_id(df_reservoir, df_completion_table)["DIAM"].to_numpy()
    compdat["KH"] = df_reservoir["KH"].to_numpy()
    compdat["SKIN"] = df_reservoir["SKIN"].to_numpy()
    compdat["DFACT"] = df_reservoir["DFACT"].to_numpy()
    compdat["DIR"] = df_reservoir["COMPDAT_DIRECTION"].to_numpy()
    compdat["RO"] = df_reservoir["RO"].to_numpy()
    # remove default columns
    compdat = trim_pandas(compdat)
    compdat[""] = "/"
    return compdat


def prepare_wsegaicd(well_name: str, lateral: int, df_well: pd.DataFrame, df_device: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare WSEGAICD data frame.

    Args:
        well_name: Well name
        lateral: Lateral number
        df_well: df_well from class CreateWells
        df_device: From function prepare_device_layer for this well and this lateral

    Returns:
        WSEGAICD
    """
    df_well = df_well[df_well["WELL"] == well_name]
    df_well = df_well[df_well["LATERAL"] == lateral]
    df_well = df_well[(df_well["DEVICETYPE"] == "PERF") | (df_well["NDEVICES"] > 0)]
    if df_well.shape[0] == 0:
        return pd.DataFrame()
    df_merge = pd.merge_asof(left=df_device, right=df_well, left_on=["MD"], right_on=["TUB_MD"], direction="nearest")
    df_merge = df_merge[df_merge["DEVICETYPE"] == "AICD"]
    wsegaicd = pd.DataFrame()
    if df_merge.shape[0] > 0:
        wsegaicd["WELL"] = [well_name] * df_merge.shape[0]
        wsegaicd["SEG"] = df_merge["SEG"].to_numpy()
        wsegaicd["SEG2"] = df_merge["SEG"].to_numpy()
        wsegaicd["ALPHA"] = df_merge["ALPHA"].to_numpy()
        wsegaicd["SF"] = df_merge["SCALINGFACTOR"].to_numpy()
        wsegaicd["RHO"] = df_merge["RHOCAL_AICD"].to_numpy()
        wsegaicd["VIS"] = df_merge["VISCAL_AICD"].to_numpy()
        wsegaicd["DEF"] = ["5*"] * df_merge.shape[0]
        wsegaicd["X"] = df_merge["X"].to_numpy()
        wsegaicd["Y"] = df_merge["Y"].to_numpy()
        wsegaicd["FLAG"] = ["OPEN"] * df_merge.shape[0]
        wsegaicd["A"] = df_merge["A"].to_numpy()
        wsegaicd["B"] = df_merge["B"].to_numpy()
        wsegaicd["C"] = df_merge["C"].to_numpy()
        wsegaicd["D"] = df_merge["D"].to_numpy()
        wsegaicd["E"] = df_merge["E"].to_numpy()
        wsegaicd["F"] = df_merge["F"].to_numpy()
        wsegaicd[""] = "/"
    return wsegaicd


def prepare_wsegsicd(well_name: str, lateral: int, df_well: pd.DataFrame, df_device: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare WSEGSICD data frame.

    Args:
        well_name: Well name
        lateral: Lateral number
        df_well: df_well from class CreateWells
        df_device: From function prepare_device_layer for this well and this lateral

    Returns:
        WSEGSICD
    """
    df_well = df_well[df_well["LATERAL"] == lateral]
    df_well = df_well[(df_well["DEVICETYPE"] == "PERF") | (df_well["NDEVICES"] > 0)]
    if df_well.shape[0] == 0:
        return pd.DataFrame()
    df_merge = pd.merge_asof(left=df_device, right=df_well, left_on=["MD"], right_on=["TUB_MD"], direction="nearest")
    df_merge = df_merge[df_merge["DEVICETYPE"] == "ICD"]
    wsegsicd = pd.DataFrame()
    if df_merge.shape[0] > 0:
        wsegsicd["WELL"] = [well_name] * df_merge.shape[0]
        wsegsicd["SEG"] = df_merge["SEG"].to_numpy()
        wsegsicd["SEG2"] = df_merge["SEG"].to_numpy()
        wsegsicd["ALPHA"] = df_merge["STRENGTH"].to_numpy()
        wsegsicd["SF"] = df_merge["SCALINGFACTOR"].to_numpy()
        wsegsicd["RHO"] = df_merge["RHOCAL_ICD"].to_numpy()
        wsegsicd["VIS"] = df_merge["VISCAL_ICD"].to_numpy()
        wsegsicd["WCT"] = df_merge["WCUT"].to_numpy()
        wsegsicd[""] = "/"
    return wsegsicd


def prepare_wsegvalv(well_name: str, lateral: int, df_well: pd.DataFrame, df_device: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare WSEGVALV data frame.

    Args:
        well_name: Well name
        lateral: Lateral number
        df_well: df_well from class CreateWells
        df_device: From function prepare_device_layer for this well and this lateral

    Returns:
        WSEGVALV
    """
    df_well = df_well[df_well["LATERAL"] == lateral]
    df_well = df_well[(df_well["DEVICETYPE"] == "PERF") | (df_well["NDEVICES"] > 0)]
    if df_well.shape[0] == 0:
        return pd.DataFrame()
    df_merge = pd.merge_asof(left=df_device, right=df_well, left_on=["MD"], right_on=["TUB_MD"], direction="nearest")
    df_merge = df_merge[df_merge["DEVICETYPE"] == "VALVE"].reset_index(drop=True)
    wsegvalv = pd.DataFrame()
    if df_merge.shape[0] > 0:
        wsegvalv["WELL"] = [well_name] * df_merge.shape[0]
        wsegvalv["SEG"] = df_merge["SEG"].to_numpy()
        # the Cv is already corrected by the scaling factor
        wsegvalv["CV"] = df_merge["CV"].to_numpy()
        wsegvalv["AC"] = df_merge["AC"].to_numpy()
        wsegvalv["L"] = "5*"
        wsegvalv["AC_MAX"] = df_merge["AC_MAX"].to_numpy()
        wsegvalv["AC_MAX"] = wsegvalv["AC_MAX"].fillna(df_merge["AC"])
        wsegvalv[""] = "/"
    return wsegvalv


def prepare_wsegicv(
    well_name: str,
    lateral: int,
    df_well: pd.DataFrame,
    df_device: pd.DataFrame,
    df_tubing: pd.DataFrame,
    df_icv_tubing: pd.DataFrame,
    df_icv: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepare WSEGICV DataFrame with WSEGVALV format.
    Include ICVs in device and tubing layer.

    Args:
        well_name: Well name
        lateral: Lateral number
        df_well: df_well from class CreateWells
        df_device: From function prepare_device_layer for this well and this lateral
        df_tubing: From function prepare_tubing_layer for this well and this lateral
        df_icv_tubing: df_icv_tubing completion from class ReadCaseFile
        df_icv: df_icv for WSEGICV keyword from class ReadCaseFile

    Returns:
        Dataframe for ICV
    """
    df_well = df_well[(df_well["LATERAL"] == lateral) & ((df_well["DEVICETYPE"] == "PERF") | (df_well["NDEVICES"] > 0))]
    if df_well.empty:
        return df_well
    df_merge = pd.merge_asof(left=df_device, right=df_well, left_on="MD", right_on="TUB_MD", direction="nearest")
    wsegicv = pd.DataFrame()
    df_merge = df_merge[df_merge["DEVICETYPE"] == "ICV"]
    if not df_merge.empty:
        wsegicv = df_merge.copy()
        wsegicv = wsegicv[["SEG", "CV", "AC", "AC_MAX"]]
        wsegicv["WELL"] = [well_name] * df_merge.shape[0]
        wsegicv["DEFAULTS"] = "5*"
        wsegicv["AC_MAX"] = wsegicv["AC_MAX"].fillna(df_merge["AC"])
        wsegicv = wsegicv.reindex(columns=["WELL", "SEG", "CV", "AC", "DEFAULTS", "AC_MAX"])
        wsegicv[""] = "/"
        # create tubing icv table
    if not df_icv_tubing.empty:
        mask = (df_icv_tubing["WELL"] == well_name) & (df_icv_tubing["BRANCH"] == lateral)
        df_icv_tubing = df_icv_tubing.loc[mask]
        df_merge_tubing = pd.merge_asof(left=df_icv_tubing, right=df_icv, on="DEVICENUMBER", direction="nearest")
        df_merge_tubing = pd.merge_asof(
            left=df_merge_tubing, right=df_tubing, left_on="STARTMD", right_on="MD", direction="nearest"
        )
        df_temp = df_merge_tubing.copy()
        df_temp = df_temp[["SEG", "CV", "AC", "AC_MAX"]]
        df_temp["WELL"] = [well_name] * df_merge_tubing.shape[0]
        df_temp["DEFAULTS"] = "5*"
        df_temp["AC_MAX"] = df_temp["AC_MAX"].fillna(math.pi * 0.5 * df_tubing["DIAM"] ** 2)
        df_temp = df_temp.reindex(columns=["WELL", "SEG", "CV", "AC", "DEFAULTS", "AC_MAX"])
        df_temp[""] = "/"
        wsegicv = pd.concat([wsegicv, df_temp], axis=0).reset_index(drop=True)
    return wsegicv


def prepare_wsegdar(well_name: str, lateral: int, df_well: pd.DataFrame, df_device: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare data frame for DAR.

    Args:
        well_name: Well name
        lateral: Lateral number
        df_well: df_well from class CreateWells
        df_device: From function prepare_device_layer for this well and this lateral

    Returns:
        DataFrame for DAR
    """
    df_well = df_well[df_well["LATERAL"] == lateral]
    df_well = df_well[(df_well["DEVICETYPE"] == "PERF") | (df_well["NDEVICES"] > 0)]
    if df_well.shape[0] == 0:
        return pd.DataFrame()
    df_merge = pd.merge_asof(left=df_device, right=df_well, left_on=["MD"], right_on=["TUB_MD"], direction="nearest")
    df_merge = df_merge[df_merge["DEVICETYPE"] == "DAR"]
    wsegdar = pd.DataFrame()
    if df_merge.shape[0] > 0:
        wsegdar["WELL"] = [well_name] * df_merge.shape[0]
        wsegdar["SEG"] = df_merge["SEG"].to_numpy()
        # the Cv is already corrected by the scaling factor
        wsegdar["CV_DAR"] = df_merge["CV_DAR"].to_numpy()
        wsegdar["AC_OIL"] = df_merge["AC_OIL"].to_numpy()
        wsegdar["AC_GAS"] = df_merge["AC_GAS"].to_numpy()
        wsegdar["AC_WATER"] = df_merge["AC_WATER"].to_numpy()
        wsegdar["WHF_LCF_DAR"] = df_merge["WHF_LCF_DAR"].to_numpy()
        wsegdar["WHF_HCF_DAR"] = df_merge["WHF_HCF_DAR"].to_numpy()
        wsegdar["GHF_LCF_DAR"] = df_merge["GHF_LCF_DAR"].to_numpy()
        wsegdar["GHF_HCF_DAR"] = df_merge["GHF_HCF_DAR"].to_numpy()
        wsegdar["DEFAULTS"] = "5*"
        wsegdar["AC_MAX"] = wsegdar["AC_OIL"].to_numpy()
        wsegdar[""] = "/"
    return wsegdar


def prepare_wsegaicv(well_name: str, lateral: int, df_well: pd.DataFrame, df_device: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare data frame for AICV.

    Args:
        well_name: Well name
        lateral: Lateral number
        df_well: df_well from class CreateWells
        df_device: From function prepare_device_layer for this well and this lateral

    Returns:
        DataFrame for AICV
    """
    df_well = df_well[df_well["LATERAL"] == lateral]
    df_well = df_well[(df_well["DEVICETYPE"] == "PERF") | (df_well["NDEVICES"] > 0)]
    if df_well.shape[0] == 0:
        return pd.DataFrame()
    df_merge = pd.merge_asof(left=df_device, right=df_well, left_on=["MD"], right_on=["TUB_MD"], direction="nearest")
    df_merge = df_merge[df_merge["DEVICETYPE"] == "AICV"]
    wsegaicv = pd.DataFrame()
    if df_merge.shape[0] > 0:
        wsegaicv["WELL"] = [well_name] * df_merge.shape[0]
        wsegaicv["SEG"] = df_merge["SEG"].to_numpy()
        wsegaicv["SEG2"] = df_merge["SEG"].to_numpy()
        wsegaicv["ALPHA_MAIN"] = df_merge["ALPHA_MAIN"].to_numpy()
        wsegaicv["SF"] = df_merge["SCALINGFACTOR"].to_numpy()
        wsegaicv["RHO"] = df_merge["RHOCAL_AICV"].to_numpy()
        wsegaicv["VIS"] = df_merge["VISCAL_AICV"].to_numpy()
        wsegaicv["DEF"] = ["5*"] * df_merge.shape[0]
        wsegaicv["X_MAIN"] = df_merge["X_MAIN"].to_numpy()
        wsegaicv["Y_MAIN"] = df_merge["Y_MAIN"].to_numpy()
        wsegaicv["FLAG"] = ["OPEN"] * df_merge.shape[0]
        wsegaicv["A_MAIN"] = df_merge["A_MAIN"].to_numpy()
        wsegaicv["B_MAIN"] = df_merge["B_MAIN"].to_numpy()
        wsegaicv["C_MAIN"] = df_merge["C_MAIN"].to_numpy()
        wsegaicv["D_MAIN"] = df_merge["D_MAIN"].to_numpy()
        wsegaicv["E_MAIN"] = df_merge["E_MAIN"].to_numpy()
        wsegaicv["F_MAIN"] = df_merge["F_MAIN"].to_numpy()
        wsegaicv["ALPHA_PILOT"] = df_merge["ALPHA_PILOT"].to_numpy()
        wsegaicv["X_PILOT"] = df_merge["X_PILOT"].to_numpy()
        wsegaicv["Y_PILOT"] = df_merge["Y_PILOT"].to_numpy()
        wsegaicv["A_PILOT"] = df_merge["A_PILOT"].to_numpy()
        wsegaicv["B_PILOT"] = df_merge["B_PILOT"].to_numpy()
        wsegaicv["C_PILOT"] = df_merge["C_PILOT"].to_numpy()
        wsegaicv["D_PILOT"] = df_merge["D_PILOT"].to_numpy()
        wsegaicv["E_PILOT"] = df_merge["E_PILOT"].to_numpy()
        wsegaicv["F_PILOT"] = df_merge["F_PILOT"].to_numpy()
        wsegaicv["WCT_AICV"] = df_merge["WCT_AICV"].to_numpy()
        wsegaicv["GHF_AICV"] = df_merge["GHF_AICV"].to_numpy()
        wsegaicv[""] = "/"
    return wsegaicv


def print_wsegdar(df_wsegdar: pd.DataFrame, well_number: int) -> str:
    """
    Print DAR devices.

    Args:
        df_wsegdar: Output from function prepare_wsegdar
        well_number: Well number

    Returns:
        Formatted actions to be included in the output file

    Raises:
        SystemExit: If there are to many wells and/or segments with DAR
    """
    header = [
        ["WELL", "SEG", "CV_DAR", "AC_GAS", "DEFAULTS", "AC_MAX"],
        ["WELL", "SEG", "CV_DAR", "AC_WATER", "DEFAULTS", "AC_MAX"],
        ["WELL", "SEG", "CV_DAR", "AC_OIL", "DEFAULTS", "AC_MAX"],
        ["WELL", "SEG", "CV_DAR", "AC_OIL", "DEFAULTS", "AC_MAX"],
    ]
    sign_water = ["<=", ">", "", "<"]
    sign_gas = [">", "<=", "<", ""]
    suvtrig = ["0", "0", "1", "2"]
    action = "UDQ\n"
    for idx in range(df_wsegdar.shape[0]):
        segment_number = df_wsegdar["SEG"].iloc[idx]
        well_name = df_wsegdar["WELL"].iloc[idx]
        action += f"  ASSIGN SUVTRIG {well_name} {segment_number} 0 /\n"
    action += "/\n\n"
    iaction = 3
    action += "WSEGVALV\n"
    header_string = "--"
    for itm in header[iaction]:
        header_string += "  " + itm
    action += header_string.rstrip() + "\n"
    for idx in range(df_wsegdar.shape[0]):
        segment_number = df_wsegdar["SEG"].iloc[idx]
        well_name = df_wsegdar["WELL"].iloc[idx]
        print_df = df_wsegdar[df_wsegdar["SEG"] == segment_number]
        print_df = print_df[header[iaction]]
        print_df = dataframe_tostring(print_df, True, False, False) + "\n"
        action += print_df
    action += "/\n\n"
    for idx in range(df_wsegdar.shape[0]):
        segment_number = df_wsegdar["SEG"].iloc[idx]
        well_name = df_wsegdar["WELL"].iloc[idx]
        water_holdup_fraction_low_cutoff = df_wsegdar["WHF_LCF_DAR"].iloc[idx]
        water_holdup_fraction_high_cutoff = df_wsegdar["WHF_HCF_DAR"].iloc[idx]
        gas_holdup_fraction_low_cutoff = df_wsegdar["GHF_LCF_DAR"].iloc[idx]
        gas_holdup_fraction_high_cutoff = df_wsegdar["GHF_HCF_DAR"].iloc[idx]
        for iaction in range(2):
            act_number = iaction + 1
            act_name = f"D{well_number:03d}{segment_number:03d}{act_number:1d}"
            if len(act_name) > 8:
                raise abort("Too many wells and/or too many segments with DAR")
            action += (
                f"ACTIONX\n{act_name} 1000000 /\n"
                f"SWHF '{well_name}' {segment_number} "
                f"{sign_water[iaction]} {water_holdup_fraction_high_cutoff} AND /\n"
                f"SGHF '{well_name}' {segment_number} "
                f"{sign_gas[iaction]} {gas_holdup_fraction_high_cutoff} AND /\n"
                f"SUVTRIG '{well_name}' {segment_number} "
                f"= {suvtrig[iaction]} /\n/\n\n"
            )
            print_df = df_wsegdar[df_wsegdar["SEG"] == segment_number]
            print_df = print_df[header[iaction]]  # type: ignore
            header_string = "WSEGVALV\n--"
            for item in header[iaction]:
                header_string += "  " + item
            header_string = header_string.rstrip() + "\n"
            print_df = header_string + dataframe_tostring(print_df, True, False, False)  # type: ignore
            print_df += "\n/\n"
            if iaction == 0:
                print_df += "\nUDQ\n" f"  ASSIGN SUVTRIG '{well_name}' {segment_number} 1 /\n/\n"
            elif iaction == 1:
                print_df += "\nUDQ\n" f"  ASSIGN SUVTRIG '{well_name}' {segment_number} 2 /\n/\n"
            action += print_df + "\nENDACTIO\n\n"

        iaction = 2
        act_number = iaction + 1
        act_name = f"D{well_number:03d}{segment_number:03d}{act_number:1d}"
        if len(act_name) > 8:
            raise abort("Too many wells and/or too many segments with DAR")
        action += (
            f"ACTIONX\n{act_name} 1000000 /\n"
            f"SGHF '{well_name}' {segment_number} "
            f"{sign_gas[iaction]} {gas_holdup_fraction_low_cutoff} AND /\n"
            f"SUVTRIG '{well_name}' {segment_number} "
            f"= {suvtrig[iaction]} /\n/\n\n"
        )
        print_df = df_wsegdar[df_wsegdar["SEG"] == segment_number]
        print_df = print_df[header[iaction]]  # type: ignore
        header_string = "WSEGVALV\n--"
        for item in header[iaction]:
            header_string += "  " + item
        header_string = header_string.rstrip() + "\n"
        print_df = header_string + dataframe_tostring(print_df, True, False, False)  # type: ignore
        print_df += "\n/\n"
        print_df += "\nUDQ\n" f"  ASSIGN SUVTRIG {well_name} {segment_number} 0 /\n/\n"
        action += print_df + "\nENDACTIO\n\n"

        iaction = 3
        act_number = iaction + 1
        act_name = f"D{well_number:03d}{segment_number:03d}{act_number:1d}"
        if len(act_name) > 8:
            raise abort("Too many wells and/or too many segments with DAR")
        action += (
            f"ACTIONX\n{act_name} 1000000 /\n"
            f"SWHF '{well_name}' {segment_number} "
            f"{sign_water[iaction]} {water_holdup_fraction_low_cutoff} AND /\n"
            f"SUVTRIG '{well_name}' {segment_number} "
            f"= {suvtrig[iaction]} /\n/\n\n"
        )
        print_df = df_wsegdar[df_wsegdar["SEG"] == segment_number]
        print_df = print_df[header[iaction]]  # type: ignore
        header_string = "WSEGVALV\n--"
        for item in header[iaction]:
            header_string += "  " + item
        header_string = header_string.rstrip() + "\n"
        print_df = header_string + dataframe_tostring(print_df, True, False, False)  # type: ignore
        print_df += "\n/\n"
        print_df += f"UDQ\n  ASSIGN SUVTRIG {well_name} {segment_number} 0 /\n/\n"
        action += print_df + "\nENDACTIO\n\n"
    return action


def print_wsegaicv(df_wsegaicv: pd.DataFrame, well_number: int) -> str:
    """
    Print for AICV devices.

    Args:
        df_wsegaicv: Output from function prepare_wsegaicv
        well_number: Well number

    Returns:
        Formatted actions to be included in the output file

    Raises:
        SystemExit: If there are too many wells and/or segments with AICV
    """
    header = [
        [
            "WELL",
            "SEG",
            "SEG2",
            "ALPHA_MAIN",
            "SF",
            "RHO",
            "VIS",
            "DEF",
            "X_MAIN",
            "Y_MAIN",
            "FLAG",
            "A_MAIN",
            "B_MAIN",
            "C_MAIN",
            "D_MAIN",
            "E_MAIN",
            "F_MAIN",
            "",
        ],
        [
            "WELL",
            "SEG",
            "SEG2",
            "ALPHA_PILOT",
            "SF",
            "RHO",
            "VIS",
            "DEF",
            "X_PILOT",
            "Y_PILOT",
            "FLAG",
            "A_PILOT",
            "B_PILOT",
            "C_PILOT",
            "D_PILOT",
            "E_PILOT",
            "F_PILOT",
            "",
        ],
    ]
    new_column = [
        "WELL",
        "SEG",
        "SEG2",
        "ALPHA",
        "SF",
        "RHO",
        "VIS",
        "DEF",
        "X",
        "Y",
        "FLAG",
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "",
    ]
    sign_water = ["<", ">="]
    sign_gas = ["<", ">="]
    operator = ["AND", "OR"]
    action = ""
    for idx in range(df_wsegaicv.shape[0]):
        segment_number = df_wsegaicv["SEG"].iloc[idx]
        well_name = df_wsegaicv["WELL"].iloc[idx]
        wct = df_wsegaicv["WCT_AICV"].iloc[idx]
        ghf = df_wsegaicv["GHF_AICV"].iloc[idx]
        # LOWWCT_LOWGHF
        for iaction in range(2):
            act_number = iaction + 1
            act_name = f"V{well_number:03d}{segment_number:03d}{act_number:1d}"
            if len(act_name) > 8:
                raise abort("Too many wells and/or too many segments with AICV")
            action += (
                f"ACTIONX\n{act_name} 1000000 /\n"
                f"SUWCT '{well_name}' {segment_number} {sign_water[iaction]} "
                f"{wct} {operator[iaction]} /\n"
                f"SGHF '{well_name}' {segment_number} {sign_gas[iaction]} {ghf} /\n/\n"
            )

            print_df = df_wsegaicv[df_wsegaicv["SEG"] == segment_number]
            print_df = print_df[header[iaction]]
            print_df.columns = new_column
            print_df = "WSEGAICD\n" + dataframe_tostring(print_df, True)
            action += f"{print_df}\n/\nENDACTIO\n\n"
    return action
