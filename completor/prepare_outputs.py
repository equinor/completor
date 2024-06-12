from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd

from completor.completion import WellSchedule
from completor.constants import Headers, Keywords
from completor.exceptions import CompletorError
from completor.logger import logger
from completor.read_casefile import ReadCasefile
from completor.utils import as_data_frame


def trim_pandas(df_temp: pd.DataFrame) -> pd.DataFrame:
    """Trim a pandas dataframe containing default values.

    Args:
        df_temp: DataFrame.

    Returns:
        Updated DataFrame.
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
    """Add the first and last column of DataFrame.

    Args:
        df_temp: E.g. WELSPECS, COMPSEGS, COMPDAT, WELSEGS, etc.
        add_first: Add the first column.
        add_last: Add the last column.

    Returns:
        Updated DataFrame.
    """
    df_temp = trim_pandas(df_temp)
    # add first and last column
    nline = df_temp.shape[0]
    if add_first:
        df_temp.insert(loc=0, column="--", value=np.full(nline, fill_value=" "))
    if add_last:
        df_temp[Headers.EMPTY] = ["/"] * nline
    return df_temp


def dataframe_tostring(
    df_temp: pd.DataFrame,
    format_column: bool = False,
    trim_df: bool = True,
    header: bool = True,
    formatters: Mapping[str | int, Callable[..., Any]] | None = None,
) -> str:
    """Convert DataFrame to string.

    Args:
        df_temp: COMPDAT, COMPSEGS, etc.
        format_column: If columns are to be formatted.
        trim_df: To trim or not to trim. Default: True.
        formatters: Dictionary of the column format. Default: None.
        header: Keep header (True) or not (False).

    Returns:
        Text string of the DataFrame.
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
    if Headers.WELL in df_temp.columns:
        df_temp[Headers.WELL] = "'" + df_temp[Headers.WELL].astype(str) + "'"
    output_string = df_temp.to_string(index=False, justify="justify", header=header)
    if format_column:
        if formatters is None:
            formatters = {
                Headers.ALPHA: "{:.10g}".format,
                Headers.SF: "{:.10g}".format,
                Headers.ROUGHNESS: "{:.10g}".format,
                Headers.CF: "{:.10g}".format,
                Headers.KH: "{:.10g}".format,
                Headers.MD: "{:.3f}".format,
                Headers.TVD: "{:.3f}".format,
                Headers.START_MD: "{:.3f}".format,
                Headers.END_MEASURED_DEPTH: "{:.3f}".format,
                Headers.CV_DAR: "{:.10g}".format,
                Headers.CV: "{:.10g}".format,
                Headers.AC: "{:.3e}".format,
                Headers.AC_OIL: "{:.3e}".format,
                Headers.AC_GAS: "{:.3e}".format,
                Headers.AC_WATER: "{:.3e}".format,
                Headers.AC_MAX: "{:.3e}".format,
                Headers.DEFAULTS: "{:.10s}".format,
                Headers.WHF_LCF_DAR: "{:.10g}".format,
                Headers.WHF_HCF_DAR: "{:.10g}".format,
                Headers.GHF_LCF_DAR: "{:.10g}".format,
                Headers.GHF_HCF_DAR: "{:.10g}".format,
                Headers.ALPHA_MAIN: "{:.10g}".format,
                Headers.ALPHA_PILOT: "{:.10g}".format,
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
    """Find the outlet segment in the other layers.

    For example: Find the corresponding tubing segment of the device segment,
    or the corresponding device segment of the annulus segment.

    Args:
        target_md: Target measured depth.
        reference_md: Reference measured depth.
        reference_segment_number: Reference segment number.

    Returns:
        The outlet segments.
    """
    df_target_md = pd.DataFrame(target_md, columns=[Headers.MD])
    df_reference = pd.DataFrame(
        np.column_stack((reference_md, reference_segment_number)), columns=[Headers.MD, Headers.SEG]
    )
    df_reference[Headers.SEG] = df_reference[Headers.SEG].astype(np.int64)
    df_reference.sort_values(by=[Headers.MD], inplace=True)
    return (
        pd.merge_asof(left=df_target_md, right=df_reference, on=[Headers.MD], direction="nearest")[Headers.SEG]
        .to_numpy()
        .flatten()
    )


def get_number_of_characters(df: pd.DataFrame) -> int:
    """Calculate the number of characters.

    Args:
        df: Data.

    Returns:
        Number of characters.
    """
    df_temp = df.iloc[:1, :].copy()
    df_temp = dataframe_tostring(df_temp, True)
    df_temp = df_temp.split("\n")
    return len(df_temp[0])


def get_header(well_name: str, keyword: str, lat: int, layer: str, nchar: int = 100) -> str:
    """Print the header.

    Args:
        well_name: Well name.
        keyword: Table keyword e.g. WELSEGS, COMPSEGS, COMPDAT, etc.
        lat: Lateral number.
        layer: Layer description e.g. tubing, device and annulus.
        nchar: Number of characters for the line boundary. Default 100.

    Returns:
        String header.
    """
    if keyword == Keywords.WELSEGS:
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
    """Prepare tubing layer data frame.

    Args:
        schedule: Schedule object.
        well_name: Well name.
        lateral: Lateral number.
        df_well: Must contain column LATERAL, TUB_MD, TUB_TVD, INNER_DIAMETER, ROUGHNESS.
        start_segment: Start number of the first tubing segment.
        branch_no: Branch number for this tubing layer.
        completion_table: DataFrame with completion data.

    Returns:
        DataFrame for tubing layer.
    """
    rnm = {
        Headers.TUBINGMD: Headers.MD,
        Headers.TUBINGTVD: Headers.TVD,
        Headers.TUBINGID: Headers.DIAM,
        Headers.TUBINGROUGHNESS: Headers.ROUGHNESS,
    }
    cols = list(rnm.values())
    df_well = df_well[df_well[Headers.WELL] == well_name]
    df_well = df_well[df_well[Headers.LATERAL] == lateral]
    df_tubing_in_reservoir = as_data_frame(
        MD=df_well[Headers.TUB_MD],
        TVD=df_well[Headers.TUB_TVD],
        DIAM=df_well[Headers.INNER_DIAMETER],
        ROUGHNESS=df_well[Headers.ROUGHNESS],
    )
    # handle overburden
    well_segments = schedule.get_well_segments(well_name, lateral)[1]
    md_input_welsegs = well_segments[Headers.TUBINGMD]
    md_welsegs_in_reservoir = df_tubing_in_reservoir[Headers.MD]
    overburden = well_segments[(md_welsegs_in_reservoir[0] - md_input_welsegs) > 1.0]
    if not overburden.empty:
        overburden = overburden.rename(index=str, columns=rnm)
        overburden_fixed = fix_tubing_inner_diam_roughness(well_name, overburden, completion_table)
        df_tubing_with_overburden = pd.concat([overburden_fixed[cols], df_tubing_in_reservoir])
    else:
        df_tubing_with_overburden = df_tubing_in_reservoir
    df_tubing_with_overburden[Headers.SEG] = start_segment + np.arange(df_tubing_with_overburden.shape[0])
    df_tubing_with_overburden[Headers.SEG2] = df_tubing_with_overburden[Headers.SEG]
    df_tubing_with_overburden[Headers.BRANCH] = branch_no
    df_tubing_with_overburden.reset_index(drop=True, inplace=True)
    # set out-segment to be successive.
    # The first item will be updated in connect_lateral
    df_tubing_with_overburden[Headers.OUT] = df_tubing_with_overburden[Headers.SEG] - 1
    # make sure order is correct
    df_tubing_with_overburden = df_tubing_with_overburden.reindex(
        columns=[Headers.SEG, Headers.SEG2, Headers.BRANCH, Headers.OUT] + cols
    )
    df_tubing_with_overburden[Headers.EMPTY] = "/"  # for printing
    # locate where it attached to (the top segment)
    wsa = schedule.get_well_segments(well_name)[1]  # all laterals
    top = wsa[wsa.TUBINGSEGMENT == well_segments.iloc[0].TUBINGOUTLET]  # could be empty

    return df_tubing_with_overburden, top


def fix_tubing_inner_diam_roughness(
    well_name: str, overburden: pd.DataFrame, completion_table: pd.DataFrame
) -> pd.DataFrame:
    """Ensure roughness and inner diameter of the overburden segments are from the case and not the schedule file.

    Overburden segments are WELSEGS segments located above the top COMPSEGS segment.

    Args:
        well_name: Well name.
        overburden: Input schedule WELSEGS segments in the overburden.
        completion_table: Completion table from the case file, ReadCasefile object.

    Returns:
        Corrected overburden DataFrame with inner diameter and roughness taken from the ReadCasefile object.

    Raises:
        ValueError: If the well completion in not found in overburden at overburden_md.
    """
    overburden_out = overburden.copy(deep=True)
    completion_table_well = completion_table.loc[completion_table[Headers.WELL] == well_name]
    completion_table_well = completion_table_well.loc[
        completion_table_well[Headers.BRANCH] == overburden_out[Headers.TUBINGBRANCH].iloc[0]
    ]
    overburden_found_in_completion = False
    overburden_md = None

    for idx_overburden in range(overburden_out.shape[0]):
        overburden_md = overburden_out[Headers.MD].iloc[idx_overburden]
        overburden_found_in_completion = False
        for idx_completion_table_well in range(completion_table_well.shape[0]):
            completion_table_start = completion_table_well[Headers.START_MD].iloc[idx_completion_table_well]
            completion_table_end = completion_table_well[Headers.END_MEASURED_DEPTH].iloc[idx_completion_table_well]
            if (completion_table_end >= overburden_md >= completion_table_start) and not overburden_found_in_completion:
                overburden_out.iloc[idx_overburden, overburden_out.columns.get_loc(Headers.DIAM)] = (
                    completion_table_well[Headers.INNER_DIAMETER].iloc[idx_completion_table_well]
                )
                overburden_out.iloc[idx_overburden, overburden_out.columns.get_loc(Headers.ROUGHNESS)] = (
                    completion_table_well[Headers.ROUGHNESS].iloc[idx_completion_table_well]
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
    """Connect lateral to main wellbore/branch.

    The main branch can either have a tubing- or device-layer connected.
    By default, the lateral will be connected to tubing-layer, but if connect_to_tubing is False,
    it will be connected to device-layer.
    Abort if it cannot find device layer at junction depth.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        data: Dict with integer key 'lateral' containing:.
            df_tubing: DataFrame tubing layer.
            df_device: DataFrame device layer.
            df_annulus: DataFrame annulus layer.
            df_wseglink: DataFrame WSEGLINK.
            top: DataFrame of first connection.
        case: ReadCasefile object.

    Raises:
        SystemExit: If there is no device layer at junction of lateral.
    """
    df_tubing, _, _, _, top = data[lateral]
    if not top.empty:
        lateral0 = top.TUBINGBRANCH.to_numpy()[0]
        md_junct = top.TUBINGMD.to_numpy()[0]
        if md_junct > df_tubing[Headers.MD][0]:
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
            raise CompletorError(f"Cannot find a device layer at junction of lateral {lateral} in {well_name}") from err
        outsegm = df_segm0.at[idx, Headers.SEG]
    else:
        outsegm = 1  # default
    df_tubing.at[0, Headers.OUT] = outsegm


def prepare_device_layer(
    well_name: str, lateral: int, df_well: pd.DataFrame, df_tubing: pd.DataFrame, device_length: float = 0.1
) -> pd.DataFrame:
    """Prepare device layer dataframe.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        df_well: Must contain LATERAL, TUB_MD, TUB_TVD, INNER_DIAMETER, ROUGHNESS, DEVICETYPE and NDEVICES.
        df_tubing: Data frame from function prepare_tubing_layer for this well and this lateral.
        device_length: Segment length. Default to 0.1.

    Returns:
        DataFrame for device layer.
    """
    start_segment = max(df_tubing[Headers.SEG].to_numpy()) + 1
    start_branch = max(df_tubing[Headers.BRANCH].to_numpy()) + 1
    df_well = df_well[df_well[Headers.WELL] == well_name]
    df_well = df_well[df_well[Headers.LATERAL] == lateral]
    # device segments are only created if:
    # 1. the device type is PERF
    # 2. if it is not PERF then it must have number of device > 0
    df_well = df_well[(df_well[Headers.DEVICE_TYPE] == "PERF") | (df_well[Headers.NDEVICES] > 0)]
    if df_well.empty:
        # return blank dataframe
        return pd.DataFrame()
    # now create dataframe for device layer
    df_device = pd.DataFrame()
    df_device[Headers.SEG] = start_segment + np.arange(df_well.shape[0])
    df_device[Headers.SEG2] = df_device[Headers.SEG].to_numpy()
    df_device[Headers.BRANCH] = start_branch + np.arange(df_well.shape[0])
    df_device[Headers.OUT] = get_outlet_segment(
        df_well[Headers.TUB_MD].to_numpy(), df_tubing[Headers.MD].to_numpy(), df_tubing[Headers.SEG].to_numpy()
    )
    df_device[Headers.MD] = df_well[Headers.TUB_MD].to_numpy() + device_length
    df_device[Headers.TVD] = df_well[Headers.TUB_TVD].to_numpy()
    df_device[Headers.DIAM] = df_well[Headers.INNER_DIAMETER].to_numpy()
    df_device[Headers.ROUGHNESS] = df_well[Headers.ROUGHNESS].to_numpy()
    device_comment = np.where(
        df_well[Headers.DEVICE_TYPE] == "PERF",
        "/ -- Open Perforation",
        np.where(
            df_well[Headers.DEVICE_TYPE] == "AICD",
            "/ -- AICD types",
            np.where(
                df_well[Headers.DEVICE_TYPE] == "ICD",
                "/ -- ICD types",
                np.where(
                    df_well[Headers.DEVICE_TYPE] == "VALVE",
                    "/ -- Valve types",
                    np.where(
                        df_well[Headers.DEVICE_TYPE] == "DAR",
                        "/ -- DAR types",
                        np.where(
                            df_well[Headers.DEVICE_TYPE] == "AICV",
                            "/ -- AICV types",
                            np.where(df_well[Headers.DEVICE_TYPE] == "ICV", "/ -- ICV types", ""),
                        ),
                    ),
                ),
            ),
        ),
    )
    df_device[Headers.EMPTY] = device_comment
    return df_device


def prepare_annulus_layer(
    well_name: str, lateral: int, df_well: pd.DataFrame, df_device: pd.DataFrame, annulus_length: float = 0.1
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Prepare annulus layer and wseglink dataframe.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        df_well: Must contain LATERAL, ANNULUS_ZONE, TUB_MD, TUB_TVD, OUTER_DIAMETER,
            ROUGHNESS, DEVICETYPE and NDEVICES.
        df_device: DataFrame from function prepare_device_layer for this well and this lateral.
        annulus_length: Annulus segment length increment. Default to 0.1.

    Returns:
        Annulus DataFrame, wseglink DataFrame.
    """
    # filter for this lateral
    df_well = df_well[df_well[Headers.WELL] == well_name]
    df_well = df_well[df_well[Headers.LATERAL] == lateral]
    # filter segments which have annular zones
    df_well = df_well[df_well[Headers.ANNULUS_ZONE] > 0]
    # loop through all annular zones
    # initiate annulus and wseglink dataframe
    df_annulus = pd.DataFrame()
    df_wseglink = pd.DataFrame()
    for izone, zone in enumerate(df_well[Headers.ANNULUS_ZONE].unique()):
        # filter only that annular zone
        df_branch = df_well[df_well[Headers.ANNULUS_ZONE] == zone]
        df_active = df_branch[
            (df_branch[Headers.NDEVICES].to_numpy() > 0) | (df_branch[Headers.DEVICE_TYPE].to_numpy() == "PERF")
        ]
        # setting the start segment number and start branch number
        if izone == 0:
            start_segment = max(df_device[Headers.SEG]) + 1
            start_branch = max(df_device[Headers.BRANCH]) + 1
        else:
            start_segment = max(df_annulus[Headers.SEG]) + 1
            start_branch = max(df_annulus[Headers.BRANCH]) + 1
        # now find the most downstream connection of the annulus zone
        idx_connection = np.argwhere(
            (df_branch[Headers.NDEVICES].to_numpy() > 0) | (df_branch[Headers.DEVICE_TYPE].to_numpy() == "PERF")
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
                raise CompletorError(
                    "Most likely error is that Completor cannot have open annulus above top reservoir with"
                    " zero valves pr joint. Please contact user support if this is not the case."
                )
            # downstream part
            df_annulus_downstream = pd.DataFrame()
            df_annulus_downstream[Headers.SEG] = start_segment + np.arange(df_branch_downstream.shape[0])
            df_annulus_downstream[Headers.SEG2] = df_annulus_downstream[Headers.SEG]
            df_annulus_downstream[Headers.BRANCH] = start_branch
            df_annulus_downstream[Headers.OUT] = df_annulus_downstream[Headers.SEG] + 1
            df_annulus_downstream[Headers.MD] = df_branch_downstream[Headers.TUB_MD].to_numpy() + annulus_length
            df_annulus_downstream[Headers.TVD] = df_branch_downstream[Headers.TUB_TVD].to_numpy()
            df_annulus_downstream[Headers.DIAM] = df_branch_downstream[Headers.OUTER_DIAMETER].to_numpy()
            df_annulus_downstream[Headers.ROUGHNESS] = df_branch_downstream[Headers.ROUGHNESS].to_numpy()

            # no WSEGLINK in the downstream part because
            # no annulus segment have connection to
            # the device segment. in case you wonder why :)

            # upstream part
            # update the start segment and start branch
            start_segment = max(df_annulus_downstream[Headers.SEG]) + 1
            start_branch = max(df_annulus_downstream[Headers.BRANCH]) + 1
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
        df_wseglink = df_wseglink[[Headers.WELL, Headers.ANNULUS, Headers.DEVICE]]
        df_wseglink[Headers.ANNULUS] = df_wseglink[Headers.ANNULUS].astype(np.int64)
        df_wseglink[Headers.DEVICE] = df_wseglink[Headers.DEVICE].astype(np.int64)
        df_wseglink[Headers.EMPTY] = "/"

    if df_annulus.shape[0] > 0:
        df_annulus[Headers.EMPTY] = "/"
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
    """Calculate upstream for annulus and wseglink.

    Args:
        df_branch: The well for current annulus zone.
        df_active: Active segments (NDEVICES > 0 or DEVICETYPE is PERF).
        df_device: Device layer.
        start_branch: Start branch number.
        annulus_length: Annulus segment length increment. Default to 0.1.
        start_segment: Start segment number of annulus.
        well_name: Well name.

    Returns:
        Annulus upstream and wseglink upstream.
    """
    df_annulus_upstream = pd.DataFrame()
    df_annulus_upstream[Headers.SEG] = start_segment + np.arange(df_branch.shape[0])
    df_annulus_upstream[Headers.SEG2] = df_annulus_upstream[Headers.SEG]
    df_annulus_upstream[Headers.BRANCH] = start_branch
    out_segment = df_annulus_upstream[Headers.SEG].to_numpy() - 1
    # determining the outlet segment of the annulus segment
    # if the annulus segment is not the most downstream which has connection
    # then the outlet is its adjacent annulus segment
    device_segment = get_outlet_segment(
        df_branch[Headers.TUB_MD].to_numpy(), df_device[Headers.MD].to_numpy(), df_device[Headers.SEG].to_numpy()
    )
    # but for the most downstream annulus segment
    # its outlet is the device segment
    out_segment[0] = device_segment[0]
    # determining segment position
    md_ = df_branch[Headers.TUB_MD].to_numpy() + annulus_length
    md_[0] = md_[0] + annulus_length
    df_annulus_upstream[Headers.OUT] = out_segment
    df_annulus_upstream[Headers.MD] = md_
    df_annulus_upstream[Headers.TVD] = df_branch[Headers.TUB_TVD].to_numpy()
    df_annulus_upstream[Headers.DIAM] = df_branch[Headers.OUTER_DIAMETER].to_numpy()
    df_annulus_upstream[Headers.ROUGHNESS] = df_branch[Headers.ROUGHNESS].to_numpy()
    device_segment = get_outlet_segment(
        df_active[Headers.TUB_MD].to_numpy(), df_device[Headers.MD].to_numpy(), df_device[Headers.SEG].to_numpy()
    )
    annulus_segment = get_outlet_segment(
        df_active[Headers.TUB_MD].to_numpy(),
        df_annulus_upstream[Headers.MD].to_numpy(),
        df_annulus_upstream[Headers.SEG].to_numpy(),
    )
    outlet_segment = get_outlet_segment(
        df_active[Headers.TUB_MD].to_numpy(),
        df_annulus_upstream[Headers.MD].to_numpy(),
        df_annulus_upstream[Headers.OUT].to_numpy(),
    )
    df_wseglink_upstream = as_data_frame(
        WELL=[well_name] * device_segment.shape[0],
        ANNULUS=annulus_segment,
        DEVICE=device_segment,
        OUTLET=outlet_segment,
    )
    # basically WSEGLINK is only for those segments
    # whose its outlet segment is not a device segment
    df_wseglink_upstream = df_wseglink_upstream[df_wseglink_upstream[Headers.DEVICE] != df_wseglink_upstream["OUTLET"]]
    return df_annulus_upstream, df_wseglink_upstream


def connect_compseg_icv(
    df_reservoir: pd.DataFrame, df_device: pd.DataFrame, df_annulus: pd.DataFrame, df_completion_table: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Connect COMPSEGS with the correct depth due to ICV segmenting combination.

    Args:
        df_reservoir: The df_reservoir from class object CreateWells.
        df_device: DataFrame from function prepare_device_layer for this well and lateral.
        df_annulus: DataFrame from function prepare_annulus_layer for this well and lateral.
        df_completion_table: DataFrame.

    Returns:
        df_compseg_device, df_compseg_annulus.
    """
    df_temp = df_completion_table[
        (df_completion_table[Headers.VALVES_PER_JOINT] > 0.0) | (df_completion_table[Headers.DEVICE_TYPE] == "PERF")
    ]
    df_completion_table_clean = df_temp[(df_temp[Headers.ANNULUS] != "PA") & (df_temp[Headers.DEVICE_TYPE] == "ICV")]
    df_res = df_reservoir.copy(deep=True)

    df_res[Headers.MD_MARKER] = df_res[Headers.MD]
    starts = df_completion_table_clean[Headers.START_MD].apply(lambda x: max(x, df_res[Headers.START_MD].iloc[0]))
    ends = df_completion_table_clean[Headers.END_MEASURED_DEPTH].apply(
        lambda x: min(x, df_res[Headers.END_MEASURED_DEPTH].iloc[-1])
    )
    for start, end in zip(starts, ends):
        condition = f"@df_res.MD >= {start} and @df_res.MD <= {end} and @df_res.DEVICETYPE == 'ICV'"
        func = float(start + end) / 2
        column_to_modify = Headers.MD_MARKER
        column_index = df_res.query(condition).index
        df_res.loc[column_index, column_to_modify] = func

    df_compseg_device = pd.merge_asof(
        left=df_res, right=df_device, left_on=Headers.MD_MARKER, right_on=Headers.MD, direction="nearest"
    )
    df_compseg_annulus = pd.DataFrame()
    if (df_completion_table[Headers.ANNULUS] == "OA").any():
        df_compseg_annulus = pd.merge_asof(
            left=df_res, right=df_annulus, left_on=Headers.MD_MARKER, right_on=Headers.MD, direction="nearest"
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
    """Prepare output for COMPSEGS.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        df_reservoir: The df_reservoir from class object CreateWells.
        df_device: DataFrame from function prepare_device_layer for this well and this lateral.
        df_annulus: DataFrame from function prepare_annulus_layer for this well and this lateral.
        df_completion_table: DataFrame.
        segment_length: Segment length.

    Returns:
        COMPSEGS DataFrame.

    Raises:
        SystemExit: If dataframes are unable to merge correctly.
    """
    df_reservoir = df_reservoir[df_reservoir[Headers.WELL] == well_name]
    df_reservoir = df_reservoir[df_reservoir[Headers.LATERAL] == lateral]
    # compsegs is only for those who are either:
    # 1. open perforation in the device segment
    # 2. has number of device > 0
    # 3. it is connected in the annular zone
    df_reservoir = df_reservoir[
        (df_reservoir[Headers.ANNULUS_ZONE] > 0)
        | (df_reservoir[Headers.NDEVICES] > 0)
        | (df_reservoir[Headers.DEVICE_TYPE] == "PERF")
    ]
    # sort device dataframe by MD to be used for pd.merge_asof
    if df_reservoir.shape[0] == 0:
        return pd.DataFrame()
    df_device = df_device.sort_values(by=[Headers.MD])
    if isinstance(segment_length, str):
        if segment_length.upper() == "USER":
            segment_length = -1.0
    icv_segmenting = (
        df_reservoir[Headers.DEVICE_TYPE].nunique() > 1
        and (df_reservoir[Headers.DEVICE_TYPE] == "ICV").any()
        and not df_reservoir[Headers.NDEVICES].empty
    )
    if df_annulus.empty:
        # There are no annular zones then all cells in this lateral and this well is connected to the device segment.
        if isinstance(segment_length, float):
            if segment_length >= 0:
                df_compseg_device = pd.merge_asof(
                    left=df_reservoir, right=df_device, on=[Headers.MD], direction="nearest"
                )
            else:
                # Ensure that tubing segment boundaries as described in the case
                # file are honored.
                # Associate reservoir cells with tubing segment midpoints using
                # markers
                df_compseg_device, df_compseg_annulus = connect_compseg_usersegment(
                    df_reservoir, df_device, df_annulus, df_completion_table
                )
        else:
            df_compseg_device = pd.merge_asof(left=df_reservoir, right=df_device, on=[Headers.MD], direction="nearest")
        if icv_segmenting:
            df_compseg_device, _ = connect_compseg_icv(df_reservoir, df_device, df_annulus, df_completion_table)
        compseg = pd.DataFrame()
        compseg[Headers.I] = df_compseg_device[Headers.I].to_numpy()
        compseg[Headers.J] = df_compseg_device[Headers.J].to_numpy()
        compseg[Headers.K] = df_compseg_device[Headers.K].to_numpy()
        # take the BRANCH column from df_device
        compseg[Headers.BRANCH] = df_compseg_device[Headers.BRANCH].to_numpy()
        compseg[Headers.START_MD] = df_compseg_device[Headers.START_MD].to_numpy()
        compseg[Headers.END_MEASURED_DEPTH] = df_compseg_device[Headers.END_MEASURED_DEPTH].to_numpy()
        compseg[Headers.DIR] = df_compseg_device[Headers.COMPSEGS_DIRECTION].to_numpy()
        compseg[Headers.DEF] = "3*"
        compseg[Headers.SEG] = df_compseg_device[Headers.SEG].to_numpy()
    else:
        # sort the df_annulus and df_device
        df_annulus = df_annulus.sort_values(by=[Headers.MD])
        if isinstance(segment_length, float):
            # SEGMENTLENGTH = FIXED
            if segment_length >= 0:
                df_compseg_annulus = pd.merge_asof(
                    left=df_reservoir, right=df_annulus, on=[Headers.MD], direction="nearest"
                )
                df_compseg_device = pd.merge_asof(
                    left=df_reservoir, right=df_device, on=[Headers.MD], direction="nearest"
                )
            else:
                # Ensure that tubing segment boundaries as described in the case
                # file are honored.
                # Associate reservoir cells with tubing segment midpoints using
                # markers
                df_compseg_device, df_compseg_annulus = connect_compseg_usersegment(
                    df_reservoir, df_device, df_annulus, df_completion_table
                )
                # Restore original sorting of DataFrames
                df_compseg_annulus.sort_values(by=[Headers.START_MD], inplace=True)
                df_compseg_device.sort_values(by=[Headers.START_MD], inplace=True)
                df_compseg_device.drop([Headers.MARKER], axis=1, inplace=True)
                df_compseg_annulus.drop([Headers.MARKER], axis=1, inplace=True)
        else:
            df_compseg_annulus = pd.merge_asof(
                left=df_reservoir, right=df_annulus, on=[Headers.MD], direction="nearest"
            )
            df_compseg_device = pd.merge_asof(left=df_reservoir, right=df_device, on=[Headers.MD], direction="nearest")
        if icv_segmenting:
            df_compseg_device, df_compseg_annulus = connect_compseg_icv(
                df_reservoir, df_device, df_annulus, df_completion_table
            )

        def _choose(parameter: str) -> np.ndarray:
            return choose_layer(df_reservoir, df_compseg_annulus, df_compseg_device, parameter)

        compseg = as_data_frame(
            I=_choose(Headers.I),
            J=_choose(Headers.J),
            K=_choose(Headers.K),
            BRANCH=_choose(Headers.BRANCH),
            STARTMD=_choose(Headers.START_MD),
            ENDMD=_choose(Headers.END_MEASURED_DEPTH),
            DIR=_choose(Headers.COMPSEGS_DIRECTION),
            DEF="3*",
            SEG=_choose(Headers.SEG),
        )
    compseg[Headers.EMPTY] = "/"
    return compseg


def connect_compseg_usersegment(
    df_reservoir: pd.DataFrame, df_device: pd.DataFrame, df_annulus: pd.DataFrame, df_completion_table: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Connect COMPSEGS with user segmentation.

    This method will connect df_reservoir with df_device and df_annulus in accordance with its
    depth in the df_completion_table due to user segmentation method.

    Args:
        df_reservoir: The df_reservoir from class object CreateWells.
        df_device: DataFrame from function prepare_device_layer for this well and lateral.
        df_annulus: DataFrame from function prepare_annulus_layer for this well and lateral.
        df_completion_table: DataFrame.

    Returns:
        df_compseg_device, df_compseg_annulus.
    """
    # check on top of df_res if the completion table is feasible
    df_temp = df_completion_table[
        (df_completion_table[Headers.VALVES_PER_JOINT] > 0.0) | (df_completion_table[Headers.DEVICE_TYPE] == "PERF")
    ]
    df_completion_table_clean = df_temp[(df_temp[Headers.ANNULUS] != "PA")]
    if not df_annulus.empty:
        df_completion_table_clean = df_completion_table[df_completion_table[Headers.ANNULUS] == "OA"]
    df_completion_table_clean = df_completion_table_clean[
        (df_completion_table_clean[Headers.END_MEASURED_DEPTH] > df_reservoir[Headers.START_MD].iloc[0])
    ]
    df_annulus.reset_index(drop=True, inplace=True)
    df_res = df_reservoir.assign(MARKER=[0 for _ in range(df_reservoir.shape[0])])
    df_dev = df_device.assign(MARKER=[x + 1 for x in range(df_device.shape[0])])
    df_ann = df_annulus.assign(MARKER=[x + 1 for x in range(df_annulus.shape[0])])
    starts = df_completion_table_clean[Headers.START_MD].apply(lambda x: max(x, df_res[Headers.START_MD].iloc[0]))
    ends = df_completion_table_clean[Headers.END_MEASURED_DEPTH].apply(
        lambda x: min(x, df_res[Headers.END_MEASURED_DEPTH].iloc[-1])
    )
    func = 1
    for start, end in zip(starts, ends):
        condition = f"@df_res.MD >= {start} and @df_res.MD <= {end}"
        column_to_modify = Headers.MARKER
        column_index = df_res.query(condition).index
        df_res.loc[column_index, column_to_modify] = func
        func += 1
    df_res.reset_index(drop=True, inplace=True)
    df_compseg_annulus = pd.DataFrame()
    if not df_annulus.empty:
        try:
            df_compseg_annulus = pd.merge_asof(
                left=df_res.sort_values(Headers.MARKER), right=df_ann, on=[Headers.MARKER], direction="nearest"
            )
        except ValueError as err:
            raise CompletorError(
                "Unexpected error when merging data frames. Please contact the "
                "dev-team with the stack trace above and the files that caused this error."
            ) from err
    try:
        df_compseg_device = pd.merge_asof(
            left=df_res.sort_values(Headers.MARKER), right=df_dev, on=[Headers.MARKER], direction="nearest"
        )
    except ValueError as err:
        raise CompletorError(
            "Unexpected error when merging data frames. Please contact the "
            "dev-team with the stack trace above and the files that caused this error."
        ) from err

    return df_compseg_device, df_compseg_annulus


def choose_layer(
    df_reservoir: pd.DataFrame, df_compseg_annulus: pd.DataFrame, df_compseg_device: pd.DataFrame, parameter: str
) -> np.ndarray:
    """Choose relevant parameters from either df_compseg_annulus or df_compseg_device.

    Args:
        df_reservoir:
        df_compseg_annulus:
        df_compseg_device:
        parameter:

    Returns:
        Relevant parameters.
    """
    branch_num = df_reservoir[Headers.ANNULUS_ZONE].to_numpy()
    ndevice = df_reservoir[Headers.NDEVICES].to_numpy()
    dev_type = df_reservoir[Headers.DEVICE_TYPE].to_numpy()
    return np.where(
        branch_num > 0,
        df_compseg_annulus[parameter].to_numpy(),
        np.where((ndevice > 0) | (dev_type == "PERF"), df_compseg_device[parameter].to_numpy(), -1),
    )


def fix_well_id(df_reservoir: pd.DataFrame, df_completion: pd.DataFrame) -> pd.DataFrame:
    """Ensure that well/casing inner diameter in the COMPDAT section is in agreement with
    the case/config file and not the input schedule file.

    Args:
        df_reservoir: Reservoir dataframe.
        df_completion_table: ReadCasefile object for current well/lateral.

    Returns:
        Corrected DataFrame for current well/lateral with inner diameter taken from the ReadCasefile object.
    """
    df_reservoir = df_reservoir.copy(deep=True)
    completion_diameters = []
    for md_reservoir in df_reservoir[Headers.MD]:
        for start_completion, outer_inner_diameter_completion, end_completion in zip(
            df_completion[Headers.START_MD],
            df_completion[Headers.OUTER_DIAMETER],
            df_completion[Headers.END_MEASURED_DEPTH],
        ):
            if start_completion <= md_reservoir <= end_completion:
                completion_diameters.append(outer_inner_diameter_completion)
                break
    df_reservoir[Headers.DIAM] = completion_diameters
    return df_reservoir


def prepare_compdat(
    well_name: str, lateral: int, df_reservoir: pd.DataFrame, df_completion_table: pd.DataFrame
) -> pd.DataFrame:
    """Prepare COMPDAT data frame.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        df_reservoir: df_reservoir from class CreateWells.
        df_completion_table: From class ReadCasefile.

    Returns:
        COMPDAT.
    """
    df_reservoir = df_reservoir[df_reservoir[Headers.WELL] == well_name]
    df_reservoir = df_reservoir[df_reservoir[Headers.LATERAL] == lateral]
    df_reservoir = df_reservoir[
        (df_reservoir[Headers.ANNULUS_ZONE] > 0)
        | ((df_reservoir[Headers.NDEVICES] > 0) | (df_reservoir[Headers.DEVICE_TYPE] == "PERF"))
    ]
    if df_reservoir.shape[0] == 0:
        return pd.DataFrame()
    compdat = pd.DataFrame()
    compdat[Headers.WELL] = [well_name] * df_reservoir.shape[0]
    compdat[Headers.I] = df_reservoir[Headers.I].to_numpy()
    compdat[Headers.J] = df_reservoir[Headers.J].to_numpy()
    compdat[Headers.K] = df_reservoir[Headers.K].to_numpy()
    compdat[Headers.K2] = df_reservoir[Headers.K2].to_numpy()
    compdat[Headers.FLAG] = df_reservoir[Headers.STATUS].to_numpy()
    compdat[Headers.SAT] = df_reservoir[Headers.SATNUM].to_numpy()
    compdat[Headers.CF] = df_reservoir[Headers.CF].to_numpy()
    compdat[Headers.DIAM] = fix_well_id(df_reservoir, df_completion_table)[Headers.DIAM].to_numpy()
    compdat[Headers.KH] = df_reservoir[Headers.KH].to_numpy()
    compdat[Headers.SKIN] = df_reservoir[Headers.SKIN].to_numpy()
    compdat[Headers.DFACT] = df_reservoir[Headers.DFACT].to_numpy()
    compdat[Headers.DIR] = df_reservoir[Headers.COMPDAT_DIRECTION].to_numpy()
    compdat[Headers.RO] = df_reservoir[Headers.RO].to_numpy()
    # remove default columns
    compdat = trim_pandas(compdat)
    compdat[Headers.EMPTY] = "/"
    return compdat


def prepare_wsegaicd(well_name: str, lateral: int, df_well: pd.DataFrame, df_device: pd.DataFrame) -> pd.DataFrame:
    """Prepare WSEGAICD data frame.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        df_well: df_well from class CreateWells.
        df_device: From function prepare_device_layer for this well and this lateral.

    Returns:
        WSEGAICD.
    """
    df_well = df_well[df_well[Headers.WELL] == well_name]
    df_well = df_well[df_well[Headers.LATERAL] == lateral]
    df_well = df_well[(df_well[Headers.DEVICE_TYPE] == "PERF") | (df_well[Headers.NDEVICES] > 0)]
    if df_well.shape[0] == 0:
        return pd.DataFrame()
    df_merge = pd.merge_asof(
        left=df_device, right=df_well, left_on=[Headers.MD], right_on=[Headers.TUB_MD], direction="nearest"
    )
    df_merge = df_merge[df_merge[Headers.DEVICE_TYPE] == "AICD"]
    wsegaicd = pd.DataFrame()
    if df_merge.shape[0] > 0:
        wsegaicd[Headers.WELL] = [well_name] * df_merge.shape[0]
        wsegaicd[Headers.SEG] = df_merge[Headers.SEG].to_numpy()
        wsegaicd[Headers.SEG2] = df_merge[Headers.SEG].to_numpy()
        wsegaicd[Headers.ALPHA] = df_merge[Headers.ALPHA].to_numpy()
        wsegaicd[Headers.SF] = df_merge[Headers.SCALINGFACTOR].to_numpy()
        wsegaicd[Headers.RHO] = df_merge[Headers.RHOCAL_AICD].to_numpy()
        wsegaicd[Headers.VIS] = df_merge[Headers.VISCAL_AICD].to_numpy()
        wsegaicd[Headers.DEF] = ["5*"] * df_merge.shape[0]
        wsegaicd[Headers.X] = df_merge[Headers.X].to_numpy()
        wsegaicd[Headers.Y] = df_merge[Headers.Y].to_numpy()
        wsegaicd[Headers.FLAG] = [Headers.OPEN] * df_merge.shape[0]
        wsegaicd[Headers.A] = df_merge[Headers.A].to_numpy()
        wsegaicd[Headers.B] = df_merge[Headers.B].to_numpy()
        wsegaicd[Headers.C] = df_merge[Headers.C].to_numpy()
        wsegaicd[Headers.D] = df_merge[Headers.D].to_numpy()
        wsegaicd[Headers.E] = df_merge[Headers.E].to_numpy()
        wsegaicd[Headers.F] = df_merge[Headers.F].to_numpy()
        wsegaicd[Headers.EMPTY] = "/"
    return wsegaicd


def prepare_wsegsicd(well_name: str, lateral: int, df_well: pd.DataFrame, df_device: pd.DataFrame) -> pd.DataFrame:
    """Prepare WSEGSICD data frame.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        df_well: df_well from class CreateWells.
        df_device: From function prepare_device_layer for this well and this lateral.

    Returns:
        WSEGSICD.
    """
    df_well = df_well[df_well[Headers.LATERAL] == lateral]
    df_well = df_well[(df_well[Headers.DEVICE_TYPE] == "PERF") | (df_well[Headers.NDEVICES] > 0)]
    if df_well.shape[0] == 0:
        return pd.DataFrame()
    df_merge = pd.merge_asof(
        left=df_device, right=df_well, left_on=[Headers.MD], right_on=[Headers.TUB_MD], direction="nearest"
    )
    df_merge = df_merge[df_merge[Headers.DEVICE_TYPE] == "ICD"]
    wsegsicd = pd.DataFrame()
    if df_merge.shape[0] > 0:
        wsegsicd[Headers.WELL] = [well_name] * df_merge.shape[0]
        wsegsicd[Headers.SEG] = df_merge[Headers.SEG].to_numpy()
        wsegsicd[Headers.SEG2] = df_merge[Headers.SEG].to_numpy()
        wsegsicd[Headers.ALPHA] = df_merge[Headers.STRENGTH].to_numpy()
        wsegsicd[Headers.SF] = df_merge[Headers.SCALINGFACTOR].to_numpy()
        wsegsicd[Headers.RHO] = df_merge[Headers.RHOCAL_ICD].to_numpy()
        wsegsicd[Headers.VIS] = df_merge[Headers.VISCAL_ICD].to_numpy()
        wsegsicd[Headers.WCT] = df_merge[Headers.WCUT].to_numpy()
        wsegsicd[Headers.EMPTY] = "/"
    return wsegsicd


def prepare_wsegvalv(well_name: str, lateral: int, df_well: pd.DataFrame, df_device: pd.DataFrame) -> pd.DataFrame:
    """Prepare WSEGVALV data frame.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        df_well: df_well from class CreateWells.
        df_device: From function prepare_device_layer for this well and this lateral.

    Returns:
        WSEGVALV.
    """
    df_well = df_well[df_well[Headers.LATERAL] == lateral]
    df_well = df_well[(df_well[Headers.DEVICE_TYPE] == "PERF") | (df_well[Headers.NDEVICES] > 0)]
    if df_well.shape[0] == 0:
        return pd.DataFrame()
    df_merge = pd.merge_asof(
        left=df_device, right=df_well, left_on=[Headers.MD], right_on=[Headers.TUB_MD], direction="nearest"
    )
    df_merge = df_merge[df_merge[Headers.DEVICE_TYPE] == "VALVE"].reset_index(drop=True)
    wsegvalv = pd.DataFrame()
    if df_merge.shape[0] > 0:
        wsegvalv[Headers.WELL] = [well_name] * df_merge.shape[0]
        wsegvalv[Headers.SEG] = df_merge[Headers.SEG].to_numpy()
        # the Cv is already corrected by the scaling factor
        wsegvalv[Headers.CV] = df_merge[Headers.CV].to_numpy()
        wsegvalv[Headers.AC] = df_merge[Headers.AC].to_numpy()
        wsegvalv[Headers.L] = "5*"
        wsegvalv[Headers.AC_MAX] = df_merge[Headers.AC_MAX].to_numpy()
        wsegvalv[Headers.AC_MAX] = wsegvalv[Headers.AC_MAX].fillna(df_merge[Headers.AC])
        wsegvalv[Headers.EMPTY] = "/"
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
    """Prepare WSEGICV DataFrame with WSEGVALV format. Include ICVs in device and tubing layer.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        df_well: df_well from class CreateWells.
        df_device: From function prepare_device_layer for this well and this lateral.
        df_tubing: From function prepare_tubing_layer for this well and this lateral.
        df_icv_tubing: df_icv_tubing completion from class ReadCaseFile.
        df_icv: df_icv for WSEGICV keyword from class ReadCaseFile.

    Returns:
        Dataframe for ICV.
    """
    df_well = df_well[
        (df_well[Headers.LATERAL] == lateral)
        & ((df_well[Headers.DEVICE_TYPE] == "PERF") | (df_well[Headers.NDEVICES] > 0))
    ]
    if df_well.empty:
        return df_well
    df_merge = pd.merge_asof(
        left=df_device, right=df_well, left_on=Headers.MD, right_on=Headers.TUB_MD, direction="nearest"
    )
    wsegicv = pd.DataFrame()
    df_merge = df_merge[df_merge[Headers.DEVICE_TYPE] == "ICV"]
    if not df_merge.empty:
        wsegicv = df_merge.copy()
        wsegicv = wsegicv[[Headers.SEG, Headers.CV, Headers.AC, Headers.AC_MAX]]
        wsegicv[Headers.WELL] = [well_name] * df_merge.shape[0]
        wsegicv[Headers.DEFAULTS] = "5*"
        wsegicv[Headers.AC_MAX] = wsegicv[Headers.AC_MAX].fillna(df_merge[Headers.AC])
        wsegicv = wsegicv.reindex(
            columns=[Headers.WELL, Headers.SEG, Headers.CV, Headers.AC, Headers.DEFAULTS, Headers.AC_MAX]
        )
        wsegicv[Headers.EMPTY] = "/"
        # create tubing icv table
    if not df_icv_tubing.empty:
        mask = (df_icv_tubing[Headers.WELL] == well_name) & (df_icv_tubing[Headers.BRANCH] == lateral)
        df_icv_tubing = df_icv_tubing.loc[mask]
        df_merge_tubing = pd.merge_asof(left=df_icv_tubing, right=df_icv, on=Headers.DEVICE_NUMBER, direction="nearest")
        df_merge_tubing = pd.merge_asof(
            left=df_merge_tubing, right=df_tubing, left_on=Headers.START_MD, right_on=Headers.MD, direction="nearest"
        )
        df_temp = df_merge_tubing.copy()
        df_temp = df_temp[[Headers.SEG, Headers.CV, Headers.AC, Headers.AC_MAX]]
        df_temp[Headers.WELL] = [well_name] * df_merge_tubing.shape[0]
        df_temp[Headers.DEFAULTS] = "5*"
        df_temp[Headers.AC_MAX] = df_temp[Headers.AC_MAX].fillna(math.pi * 0.5 * df_tubing[Headers.DIAM] ** 2)
        df_temp = df_temp.reindex(
            columns=[Headers.WELL, Headers.SEG, Headers.CV, Headers.AC, Headers.DEFAULTS, Headers.AC_MAX]
        )
        df_temp[Headers.EMPTY] = "/"
        wsegicv = pd.concat([wsegicv, df_temp], axis=0).reset_index(drop=True)
    return wsegicv


def prepare_wsegdar(well_name: str, lateral: int, df_well: pd.DataFrame, df_device: pd.DataFrame) -> pd.DataFrame:
    """Prepare data frame for DAR.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        df_well: df_well from class CreateWells.
        df_device: From function prepare_device_layer for this well and this lateral.

    Returns:
        DataFrame for DAR.
    """
    df_well = df_well[df_well[Headers.LATERAL] == lateral]
    df_well = df_well[(df_well[Headers.DEVICE_TYPE] == "PERF") | (df_well[Headers.NDEVICES] > 0)]
    if df_well.shape[0] == 0:
        return pd.DataFrame()
    df_merge = pd.merge_asof(
        left=df_device, right=df_well, left_on=[Headers.MD], right_on=[Headers.TUB_MD], direction="nearest"
    )
    df_merge = df_merge[df_merge[Headers.DEVICE_TYPE] == "DAR"]
    wsegdar = pd.DataFrame()
    if df_merge.shape[0] > 0:
        wsegdar[Headers.WELL] = [well_name] * df_merge.shape[0]
        wsegdar[Headers.SEG] = df_merge[Headers.SEG].to_numpy()
        # the Cv is already corrected by the scaling factor
        wsegdar[Headers.CV_DAR] = df_merge[Headers.CV_DAR].to_numpy()
        wsegdar[Headers.AC_OIL] = df_merge[Headers.AC_OIL].to_numpy()
        wsegdar[Headers.AC_GAS] = df_merge[Headers.AC_GAS].to_numpy()
        wsegdar[Headers.AC_WATER] = df_merge[Headers.AC_WATER].to_numpy()
        wsegdar[Headers.WHF_LCF_DAR] = df_merge[Headers.WHF_LCF_DAR].to_numpy()
        wsegdar[Headers.WHF_HCF_DAR] = df_merge[Headers.WHF_HCF_DAR].to_numpy()
        wsegdar[Headers.GHF_LCF_DAR] = df_merge[Headers.GHF_LCF_DAR].to_numpy()
        wsegdar[Headers.GHF_HCF_DAR] = df_merge[Headers.GHF_HCF_DAR].to_numpy()
        wsegdar[Headers.DEFAULTS] = "5*"
        wsegdar[Headers.AC_MAX] = wsegdar[Headers.AC_OIL].to_numpy()
        wsegdar[Headers.EMPTY] = "/"
    return wsegdar


def prepare_wsegaicv(well_name: str, lateral: int, df_well: pd.DataFrame, df_device: pd.DataFrame) -> pd.DataFrame:
    """Prepare data frame for AICV.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        df_well: df_well from class CreateWells.
        df_device: From function prepare_device_layer for this well and this lateral.

    Returns:
        DataFrame for AICV.
    """
    df_well = df_well[df_well[Headers.LATERAL] == lateral]
    df_well = df_well[(df_well[Headers.DEVICE_TYPE] == "PERF") | (df_well[Headers.NDEVICES] > 0)]
    if df_well.shape[0] == 0:
        return pd.DataFrame()
    df_merge = pd.merge_asof(
        left=df_device, right=df_well, left_on=[Headers.MD], right_on=[Headers.TUB_MD], direction="nearest"
    )
    df_merge = df_merge[df_merge[Headers.DEVICE_TYPE] == "AICV"]
    wsegaicv = pd.DataFrame()
    if df_merge.shape[0] > 0:
        wsegaicv[Headers.WELL] = [well_name] * df_merge.shape[0]
        wsegaicv[Headers.SEG] = df_merge[Headers.SEG].to_numpy()
        wsegaicv[Headers.SEG2] = df_merge[Headers.SEG].to_numpy()
        wsegaicv[Headers.ALPHA_MAIN] = df_merge[Headers.ALPHA_MAIN].to_numpy()
        wsegaicv[Headers.SF] = df_merge[Headers.SCALINGFACTOR].to_numpy()
        wsegaicv[Headers.RHO] = df_merge[Headers.RHOCAL_AICV].to_numpy()
        wsegaicv[Headers.VIS] = df_merge[Headers.VISCAL_AICV].to_numpy()
        wsegaicv[Headers.DEF] = ["5*"] * df_merge.shape[0]
        wsegaicv[Headers.X_MAIN] = df_merge[Headers.X_MAIN].to_numpy()
        wsegaicv[Headers.Y_MAIN] = df_merge[Headers.Y_MAIN].to_numpy()
        wsegaicv[Headers.FLAG] = [Headers.OPEN] * df_merge.shape[0]
        wsegaicv[Headers.A_MAIN] = df_merge[Headers.A_MAIN].to_numpy()
        wsegaicv[Headers.B_MAIN] = df_merge[Headers.B_MAIN].to_numpy()
        wsegaicv[Headers.C_MAIN] = df_merge[Headers.C_MAIN].to_numpy()
        wsegaicv[Headers.D_MAIN] = df_merge[Headers.D_MAIN].to_numpy()
        wsegaicv[Headers.E_MAIN] = df_merge[Headers.E_MAIN].to_numpy()
        wsegaicv[Headers.F_MAIN] = df_merge[Headers.F_MAIN].to_numpy()
        wsegaicv[Headers.ALPHA_PILOT] = df_merge[Headers.ALPHA_PILOT].to_numpy()
        wsegaicv[Headers.X_PILOT] = df_merge[Headers.X_PILOT].to_numpy()
        wsegaicv[Headers.Y_PILOT] = df_merge[Headers.Y_PILOT].to_numpy()
        wsegaicv[Headers.A_PILOT] = df_merge[Headers.A_PILOT].to_numpy()
        wsegaicv[Headers.B_PILOT] = df_merge[Headers.B_PILOT].to_numpy()
        wsegaicv[Headers.C_PILOT] = df_merge[Headers.C_PILOT].to_numpy()
        wsegaicv[Headers.D_PILOT] = df_merge[Headers.D_PILOT].to_numpy()
        wsegaicv[Headers.E_PILOT] = df_merge[Headers.E_PILOT].to_numpy()
        wsegaicv[Headers.F_PILOT] = df_merge[Headers.F_PILOT].to_numpy()
        wsegaicv[Headers.WCT_AICV] = df_merge[Headers.WCT_AICV].to_numpy()
        wsegaicv[Headers.GHF_AICV] = df_merge[Headers.GHF_AICV].to_numpy()
        wsegaicv[Headers.EMPTY] = "/"
    return wsegaicv


def print_wsegdar(df_wsegdar: pd.DataFrame, well_number: int) -> str:
    """Print DAR devices.

    Args:
        df_wsegdar: Output from function prepare_wsegdar.
        well_number: Well number.

    Returns:
        Formatted actions to be included in the output file.

    Raises:
        SystemExit: If there are to many wells and/or segments with DAR.
    """
    header = [
        [Headers.WELL, Headers.SEG, Headers.CV_DAR, Headers.AC_GAS, Headers.DEFAULTS, Headers.AC_MAX],
        [Headers.WELL, Headers.SEG, Headers.CV_DAR, Headers.AC_WATER, Headers.DEFAULTS, Headers.AC_MAX],
        [Headers.WELL, Headers.SEG, Headers.CV_DAR, Headers.AC_OIL, Headers.DEFAULTS, Headers.AC_MAX],
        [Headers.WELL, Headers.SEG, Headers.CV_DAR, Headers.AC_OIL, Headers.DEFAULTS, Headers.AC_MAX],
    ]
    sign_water = ["<=", ">", "", "<"]
    sign_gas = [">", "<=", "<", ""]
    suvtrig = ["0", "0", "1", "2"]
    action = "UDQ\n"
    for idx in range(df_wsegdar.shape[0]):
        segment_number = df_wsegdar[Headers.SEG].iloc[idx]
        well_name = df_wsegdar[Headers.WELL].iloc[idx]
        action += f"  ASSIGN SUVTRIG {well_name} {segment_number} 0 /\n"
    action += "/\n\n"
    iaction = 3
    action += Keywords.WSEGVALV + "\n"
    header_string = "--"
    for itm in header[iaction]:
        header_string += "  " + itm
    action += header_string.rstrip() + "\n"
    for idx in range(df_wsegdar.shape[0]):
        segment_number = df_wsegdar[Headers.SEG].iloc[idx]
        print_df = df_wsegdar[df_wsegdar[Headers.SEG] == segment_number]
        print_df = print_df[header[iaction]]
        print_df = dataframe_tostring(print_df, True, False, False) + "\n"
        action += print_df
    action += "/\n\n"
    for idx in range(df_wsegdar.shape[0]):
        segment_number = df_wsegdar[Headers.SEG].iloc[idx]
        well_name = df_wsegdar[Headers.WELL].iloc[idx]
        water_holdup_fraction_low_cutoff = df_wsegdar[Headers.WHF_LCF_DAR].iloc[idx]
        water_holdup_fraction_high_cutoff = df_wsegdar[Headers.WHF_HCF_DAR].iloc[idx]
        gas_holdup_fraction_low_cutoff = df_wsegdar[Headers.GHF_LCF_DAR].iloc[idx]
        gas_holdup_fraction_high_cutoff = df_wsegdar[Headers.GHF_HCF_DAR].iloc[idx]
        for iaction in range(2):
            act_number = iaction + 1
            act_name = f"D{well_number:03d}{segment_number:03d}{act_number:1d}"
            if len(act_name) > 8:
                raise CompletorError("Too many wells and/or too many segments with DAR")
            action += (
                f"ACTIONX\n{act_name} 1000000 /\n"
                f"SWHF '{well_name}' {segment_number} "
                f"{sign_water[iaction]} {water_holdup_fraction_high_cutoff} AND /\n"
                f"SGHF '{well_name}' {segment_number} "
                f"{sign_gas[iaction]} {gas_holdup_fraction_high_cutoff} AND /\n"
                f"SUVTRIG '{well_name}' {segment_number} "
                f"= {suvtrig[iaction]} /\n/\n\n"
            )
            print_df = df_wsegdar[df_wsegdar[Headers.SEG] == segment_number]
            print_df = print_df[header[iaction]]  # type: ignore
            header_string = Keywords.WSEGVALV + "\n--"
            for item in header[iaction]:
                header_string += "  " + item
            header_string = header_string.rstrip() + "\n"
            print_df = header_string + dataframe_tostring(print_df, True, False, False)  # type: ignore
            print_df += "\n/\n"
            if iaction == 0:
                print_df += f"\nUDQ\n  ASSIGN SUVTRIG '{well_name}' {segment_number} 1 /\n/\n"
            elif iaction == 1:
                print_df += f"\nUDQ\n  ASSIGN SUVTRIG '{well_name}' {segment_number} 2 /\n/\n"
            action += print_df + "\nENDACTIO\n\n"

        iaction = 2
        act_number = iaction + 1
        act_name = f"D{well_number:03d}{segment_number:03d}{act_number:1d}"
        if len(act_name) > 8:
            raise CompletorError("Too many wells and/or too many segments with DAR")
        action += (
            f"ACTIONX\n{act_name} 1000000 /\n"
            f"SGHF '{well_name}' {segment_number} "
            f"{sign_gas[iaction]} {gas_holdup_fraction_low_cutoff} AND /\n"
            f"SUVTRIG '{well_name}' {segment_number} "
            f"= {suvtrig[iaction]} /\n/\n\n"
        )
        print_df = df_wsegdar[df_wsegdar[Headers.SEG] == segment_number]
        print_df = print_df[header[iaction]]  # type: ignore
        header_string = Keywords.WSEGVALV + "\n--"
        for item in header[iaction]:
            header_string += "  " + item
        header_string = header_string.rstrip() + "\n"
        print_df = header_string + dataframe_tostring(print_df, True, False, False)  # type: ignore
        print_df += "\n/\n"
        print_df += f"\nUDQ\n  ASSIGN SUVTRIG {well_name} {segment_number} 0 /\n/\n"
        action += print_df + "\nENDACTIO\n\n"

        iaction = 3
        act_number = iaction + 1
        act_name = f"D{well_number:03d}{segment_number:03d}{act_number:1d}"
        if len(act_name) > 8:
            raise CompletorError("Too many wells and/or too many segments with DAR")
        action += (
            f"ACTIONX\n{act_name} 1000000 /\n"
            f"SWHF '{well_name}' {segment_number} "
            f"{sign_water[iaction]} {water_holdup_fraction_low_cutoff} AND /\n"
            f"SUVTRIG '{well_name}' {segment_number} "
            f"= {suvtrig[iaction]} /\n/\n\n"
        )
        print_df = df_wsegdar[df_wsegdar[Headers.SEG] == segment_number]
        print_df = print_df[header[iaction]]  # type: ignore
        header_string = Keywords.WSEGVALV + "\n--"
        for item in header[iaction]:
            header_string += "  " + item
        header_string = header_string.rstrip() + "\n"
        print_df = header_string + dataframe_tostring(print_df, True, False, False)  # type: ignore
        print_df += "\n/\n"
        print_df += f"UDQ\n  ASSIGN SUVTRIG {well_name} {segment_number} 0 /\n/\n"
        action += print_df + "\nENDACTIO\n\n"
    return action


def print_wsegaicv(df_wsegaicv: pd.DataFrame, well_number: int) -> str:
    """Print for AICV devices.

    Args:
        df_wsegaicv: Output from function prepare_wsegaicv.
        well_number: Well number.

    Returns:
        Formatted actions to be included in the output file.

    Raises:
        SystemExit: If there are too many wells and/or segments with AICV.
    """
    header = [
        [
            Headers.WELL,
            Headers.SEG,
            Headers.SEG2,
            Headers.ALPHA_MAIN,
            Headers.SF,
            Headers.RHO,
            Headers.VIS,
            Headers.DEF,
            Headers.X_MAIN,
            Headers.Y_MAIN,
            Headers.FLAG,
            Headers.A_MAIN,
            Headers.B_MAIN,
            Headers.C_MAIN,
            Headers.D_MAIN,
            Headers.E_MAIN,
            Headers.F_MAIN,
            Headers.EMPTY,
        ],
        [
            Headers.WELL,
            Headers.SEG,
            Headers.SEG2,
            Headers.ALPHA_PILOT,
            Headers.SF,
            Headers.RHO,
            Headers.VIS,
            Headers.DEF,
            Headers.X_PILOT,
            Headers.Y_PILOT,
            Headers.FLAG,
            Headers.A_PILOT,
            Headers.B_PILOT,
            Headers.C_PILOT,
            Headers.D_PILOT,
            Headers.E_PILOT,
            Headers.F_PILOT,
            Headers.EMPTY,
        ],
    ]
    new_column = [
        Headers.WELL,
        Headers.SEG,
        Headers.SEG2,
        Headers.ALPHA,
        Headers.SF,
        Headers.RHO,
        Headers.VIS,
        Headers.DEF,
        Headers.X,
        Headers.Y,
        Headers.FLAG,
        Headers.A,
        Headers.B,
        Headers.C,
        Headers.D,
        Headers.E,
        Headers.F,
        Headers.EMPTY,
    ]
    sign_water = ["<", ">="]
    sign_gas = ["<", ">="]
    operator = ["AND", "OR"]
    action = ""
    for idx in range(df_wsegaicv.shape[0]):
        segment_number = df_wsegaicv[Headers.SEG].iloc[idx]
        well_name = df_wsegaicv[Headers.WELL].iloc[idx]
        wct = df_wsegaicv[Headers.WCT_AICV].iloc[idx]
        ghf = df_wsegaicv[Headers.GHF_AICV].iloc[idx]
        # LOWWCT_LOWGHF
        for iaction in range(2):
            act_number = iaction + 1
            act_name = f"V{well_number:03d}{segment_number:03d}{act_number:1d}"
            if len(act_name) > 8:
                raise CompletorError("Too many wells and/or too many segments with AICV")
            action += (
                f"ACTIONX\n{act_name} 1000000 /\n"
                f"SUWCT '{well_name}' {segment_number} {sign_water[iaction]} "
                f"{wct} {operator[iaction]} /\n"
                f"SGHF '{well_name}' {segment_number} {sign_gas[iaction]} {ghf} /\n/\n"
            )

            print_df = df_wsegaicv[df_wsegaicv[Headers.SEG] == segment_number]
            print_df = print_df[header[iaction]]
            print_df.columns = new_column
            print_df = Keywords.WSEGAICD + "\n" + dataframe_tostring(print_df, True)
            action += f"{print_df}\n/\nENDACTIO\n\n"
    return action
