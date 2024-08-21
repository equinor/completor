from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd

from completor.constants import Content, Headers, Keywords
from completor.exceptions import CompletorError
from completor.wells import Lateral, Well


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
        df_temp: E.g. WELL_SPECIFICATION, COMPLETION_SEGMENTS, COMPLETION_DATA, WELL_SEGMENTS, etc.
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
        df_temp: COMPLETION_DATA, COMPLETION_SEGMENTS, etc.
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
                Headers.STRENGTH: "{:.10g}".format,
                Headers.SCALE_FACTOR: "{:.10g}".format,
                Headers.ROUGHNESS: "{:.10g}".format,
                Headers.CONNECTION_FACTOR: "{:.10g}".format,
                Headers.FORMATION_PERMEABILITY_THICKNESS: "{:.10g}".format,
                Headers.MEASURED_DEPTH: "{:.3f}".format,
                Headers.TRUE_VERTICAL_DEPTH: "{:.3f}".format,
                Headers.START_MEASURED_DEPTH: "{:.3f}".format,
                Headers.END_MEASURED_DEPTH: "{:.3f}".format,
                Headers.FLOW_COEFFICIENT: "{:.10g}".format,
                Headers.FLOW_CROSS_SECTIONAL_AREA: "{:.3e}".format,
                Headers.OIL_FLOW_CROSS_SECTIONAL_AREA: "{:.3e}".format,
                Headers.GAS_FLOW_CROSS_SECTIONAL_AREA: "{:.3e}".format,
                Headers.WATER_FLOW_CROSS_SECTIONAL_AREA: "{:.3e}".format,
                Headers.MAX_FLOW_CROSS_SECTIONAL_AREA: "{:.3e}".format,
                Headers.DEFAULTS: "{:.10s}".format,
                Headers.WATER_HOLDUP_FRACTION_LOW_CUTOFF: "{:.10g}".format,
                Headers.WATER_HOLDUP_FRACTION_HIGH_CUTOFF: "{:.10g}".format,
                Headers.GAS_HOLDUP_FRACTION_LOW_CUTOFF: "{:.10g}".format,
                Headers.GAS_HOLDUP_FRACTION_HIGH_CUTOFF: "{:.10g}".format,
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
    df_target_md = pd.DataFrame(target_md, columns=[Headers.MEASURED_DEPTH])
    df_reference = pd.DataFrame(
        np.column_stack((reference_md, reference_segment_number)),
        columns=[Headers.MEASURED_DEPTH, Headers.START_SEGMENT_NUMBER],
    )
    df_reference[Headers.START_SEGMENT_NUMBER] = df_reference[Headers.START_SEGMENT_NUMBER].astype(np.int64)
    df_reference.sort_values(by=[Headers.MEASURED_DEPTH], inplace=True)
    return (
        pd.merge_asof(left=df_target_md, right=df_reference, on=[Headers.MEASURED_DEPTH], direction="nearest")[
            Headers.START_SEGMENT_NUMBER
        ]
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
        keyword: Table keyword e.g. WELL_SEGMENTS, COMPLETION_SEGMENTS, COMPLETION_DATA, etc.
        lat: Lateral number.
        layer: Layer description e.g. tubing, device and annulus.
        nchar: Number of characters for the line boundary. Default 100.

    Returns:
        String header.
    """
    if keyword == Keywords.WELL_SEGMENTS:
        header = f"{'-' * nchar}\n-- Well : {well_name} : Lateral : {lat} : {layer} layer\n"
    else:
        header = f"{'-' * nchar}\n-- Well : {well_name} : Lateral : {lat}\n"
    return header + "-" * nchar + "\n"


def prepare_tubing_layer(
    well_name: str, lateral: Lateral, start_segment: int, branch_no: int, completion_table: pd.DataFrame, well: Well
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Prepare tubing layer data frame.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        start_segment: Start number of the first tubing segment.
        branch_no: Branch number for this tubing layer.
        completion_table: DataFrame with completion data.
        well: Well object.

    Returns:
        DataFrame for tubing layer.
    """
    alias_rename = {
        Headers.TUBING_MEASURED_DEPTH: Headers.MEASURED_DEPTH,
        Headers.TRUE_VERTICAL_DEPTH: Headers.TRUE_VERTICAL_DEPTH,
        Headers.TUBING_INNER_DIAMETER: Headers.WELL_BORE_DIAMETER,
        Headers.TUBING_ROUGHNESS: Headers.ROUGHNESS,
    }
    cols = list(alias_rename.values())
    df_tubing_in_reservoir = pd.DataFrame(
        {
            Headers.MEASURED_DEPTH: lateral.df_well[Headers.TUBING_MEASURED_DEPTH],
            Headers.TRUE_VERTICAL_DEPTH: lateral.df_well[Headers.TRUE_VERTICAL_DEPTH],
            Headers.WELL_BORE_DIAMETER: lateral.df_well[Headers.INNER_DIAMETER],
            Headers.ROUGHNESS: lateral.df_well[Headers.ROUGHNESS],
        }
    )

    # Handle overburden.
    md_input_welsegs = lateral.df_welsegs_content[Headers.TUBING_MEASURED_DEPTH]
    md_welsegs_in_reservoir = df_tubing_in_reservoir[Headers.MEASURED_DEPTH]
    overburden = lateral.df_welsegs_content[(md_welsegs_in_reservoir[0] - md_input_welsegs) > 1.0]
    if overburden.empty:
        df_tubing_with_overburden = df_tubing_in_reservoir
    else:
        overburden = overburden.rename(index=str, columns=alias_rename)
        overburden_fixed = fix_tubing_inner_diam_roughness(well_name, overburden, completion_table)
        df_tubing_with_overburden = pd.concat([overburden_fixed[cols], df_tubing_in_reservoir])

    df_tubing_with_overburden[Headers.START_SEGMENT_NUMBER] = start_segment + np.arange(
        df_tubing_with_overburden.shape[0]
    )
    df_tubing_with_overburden[Headers.END_SEGMENT_NUMBER] = df_tubing_with_overburden[Headers.START_SEGMENT_NUMBER]
    df_tubing_with_overburden[Headers.BRANCH] = branch_no
    df_tubing_with_overburden.reset_index(drop=True, inplace=True)
    # Set the out-segments to be successive, the first item will be updated in connect_lateral.
    df_tubing_with_overburden[Headers.OUT] = df_tubing_with_overburden[Headers.START_SEGMENT_NUMBER] - 1
    # Make sure the order is correct.
    df_tubing_with_overburden = df_tubing_with_overburden.reindex(
        columns=[Headers.START_SEGMENT_NUMBER, Headers.END_SEGMENT_NUMBER, Headers.BRANCH, Headers.OUT] + cols
    )
    df_tubing_with_overburden[Headers.EMPTY] = "/"  # For printing.
    # Locate where it's attached to (the top segment). Can be empty!
    top = well.df_welsegs_content_all_laterals[
        well.df_welsegs_content_all_laterals[Headers.TUBING_SEGMENT]
        == lateral.df_welsegs_content.iloc[0][Headers.TUBING_OUTLET]
    ]

    return df_tubing_with_overburden, top


def fix_tubing_inner_diam_roughness(
    well_name: str, overburden: pd.DataFrame, completion_table: pd.DataFrame
) -> pd.DataFrame:
    """Ensure roughness and inner diameter of the overburden segments are from the case and not the schedule file.

    Overburden segments are WELL_SEGMENTS segments located above the top COMPLETION_SEGMENTS segment.

    Args:
        well_name: Well name.
        overburden: Input schedule WELL_SEGMENTS segments in the overburden.
        completion_table: Completion table from the case file, ReadCasefile object.

    Returns:
        Corrected overburden DataFrame with inner diameter and roughness taken from the ReadCasefile object.

    Raises:
        ValueError: If the well completion is not found in overburden at overburden_md.
    """
    overburden_out = overburden.copy(deep=True)
    completion_table_well = completion_table.loc[completion_table[Headers.WELL] == well_name]
    completion_table_well = completion_table_well.loc[
        completion_table_well[Headers.BRANCH] == overburden_out[Headers.TUBING_BRANCH].iloc[0]
    ]
    overburden_found_in_completion = False
    overburden_md = None

    for idx_overburden in range(overburden_out.shape[0]):
        overburden_md = overburden_out[Headers.MEASURED_DEPTH].iloc[idx_overburden]
        overburden_found_in_completion = False
        for idx_completion_table_well in range(completion_table_well.shape[0]):
            completion_table_start = completion_table_well[Headers.START_MEASURED_DEPTH].iloc[idx_completion_table_well]
            completion_table_end = completion_table_well[Headers.END_MEASURED_DEPTH].iloc[idx_completion_table_well]
            if (completion_table_end >= overburden_md >= completion_table_start) and not overburden_found_in_completion:
                overburden_out.iloc[idx_overburden, overburden_out.columns.get_loc(Headers.WELL_BORE_DIAMETER)] = (
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


def prepare_device_layer(df_well: pd.DataFrame, df_tubing: pd.DataFrame, device_length: float = 0.1) -> pd.DataFrame:
    """Prepare device layer dataframe.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        df_well: Must contain LATERAL, TUBING_MEASURED_DEPTH, TRUE_VERTICAL_DEPTH,
            INNER_DIAMETER, ROUGHNESS, DEVICE_TYPE and NDEVICES.
        df_tubing: Data frame from function prepare_tubing_layer for this well and this lateral.
        device_length: Segment length. Default to 0.1.

    Returns:
        DataFrame for device layer.
    """
    start_segment = max(df_tubing[Headers.START_SEGMENT_NUMBER].to_numpy()) + 1
    start_branch = max(df_tubing[Headers.BRANCH].to_numpy()) + 1

    # device segments are only created if:
    # 1. the device type is PERF
    # 2. if it is not PERF then it must have number of device > 0
    df_well = df_well[(df_well[Headers.DEVICE_TYPE] == Content.PERFORATED) | (df_well[Headers.NUMBER_OF_DEVICES] > 0)]
    if df_well.empty:
        # return blank dataframe
        return pd.DataFrame()
    # now create dataframe for device layer
    df_device = pd.DataFrame()
    df_device[Headers.START_SEGMENT_NUMBER] = start_segment + np.arange(df_well.shape[0])
    df_device[Headers.END_SEGMENT_NUMBER] = df_device[Headers.START_SEGMENT_NUMBER].to_numpy()
    df_device[Headers.BRANCH] = start_branch + np.arange(df_well.shape[0])
    df_device[Headers.OUT] = get_outlet_segment(
        df_well[Headers.TUBING_MEASURED_DEPTH].to_numpy(),
        df_tubing[Headers.MEASURED_DEPTH].to_numpy(),
        df_tubing[Headers.START_SEGMENT_NUMBER].to_numpy(),
    )
    df_device[Headers.MEASURED_DEPTH] = df_well[Headers.TUBING_MEASURED_DEPTH].to_numpy() + device_length
    df_device[Headers.TRUE_VERTICAL_DEPTH] = df_well[Headers.TRUE_VERTICAL_DEPTH].to_numpy()
    df_device[Headers.WELL_BORE_DIAMETER] = df_well[Headers.INNER_DIAMETER].to_numpy()
    df_device[Headers.ROUGHNESS] = df_well[Headers.ROUGHNESS].to_numpy()
    device_comment = np.where(
        df_well[Headers.DEVICE_TYPE] == Content.PERFORATED,
        "/ -- Open Perforation",
        np.where(
            df_well[Headers.DEVICE_TYPE] == Content.AUTONOMOUS_INFLOW_CONTROL_DEVICE,
            "/ -- AICD types",
            np.where(
                df_well[Headers.DEVICE_TYPE] == Content.INFLOW_CONTROL_DEVICE,
                "/ -- ICD types",
                np.where(
                    df_well[Headers.DEVICE_TYPE] == Content.VALVE,
                    "/ -- Valve types",
                    np.where(
                        df_well[Headers.DEVICE_TYPE] == Content.DENSITY_ACTIVATED_RECOVERY,
                        "/ -- DAR types",
                        np.where(
                            df_well[Headers.DEVICE_TYPE] == Content.AUTONOMOUS_INFLOW_CONTROL_VALVE,
                            "/ -- AICV types",
                            np.where(
                                df_well[Headers.DEVICE_TYPE] == Content.INFLOW_CONTROL_VALVE, "/ -- ICV types", ""
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    df_device[Headers.EMPTY] = device_comment
    return df_device


def prepare_annulus_layer(
    well_name: str, df_well: pd.DataFrame, df_device: pd.DataFrame, annulus_length: float = 0.1
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Prepare annulus layer and wseglink dataframe.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        df_well: Must contain LATERAL, ANNULUS_ZONE, TUBING_MEASURED_DEPTH, TRUE_VERTICAL_DEPTH, OUTER_DIAMETER,
            ROUGHNESS, DEVICETYPE and NDEVICES.
        df_device: DataFrame from function prepare_device_layer for this well and this lateral.
        annulus_length: Annulus segment length increment. Default to 0.1.

    Returns:
        Annulus DataFrame, wseglink DataFrame.

    Raises:
          CompletorError: If splitting annulus fails.

    """
    # filter for this lateral
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
            (df_branch[Headers.NUMBER_OF_DEVICES].to_numpy() > 0)
            | (df_branch[Headers.DEVICE_TYPE].to_numpy() == Content.PERFORATED)
        ]
        # setting the start segment number and start branch number
        if izone == 0:
            start_segment = max(df_device[Headers.START_SEGMENT_NUMBER]) + 1
            start_branch = max(df_device[Headers.BRANCH]) + 1
        else:
            start_segment = max(df_annulus[Headers.START_SEGMENT_NUMBER]) + 1
            start_branch = max(df_annulus[Headers.BRANCH]) + 1
        # now find the most downstream connection of the annulus zone
        idx_connection = np.argwhere(
            (df_branch[Headers.NUMBER_OF_DEVICES].to_numpy() > 0)
            | (df_branch[Headers.DEVICE_TYPE].to_numpy() == Content.PERFORATED)
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
            df_annulus_downstream[Headers.START_SEGMENT_NUMBER] = start_segment + np.arange(
                df_branch_downstream.shape[0]
            )
            df_annulus_downstream[Headers.END_SEGMENT_NUMBER] = df_annulus_downstream[Headers.START_SEGMENT_NUMBER]
            df_annulus_downstream[Headers.BRANCH] = start_branch
            df_annulus_downstream[Headers.OUT] = df_annulus_downstream[Headers.START_SEGMENT_NUMBER] + 1
            df_annulus_downstream[Headers.MEASURED_DEPTH] = (
                df_branch_downstream[Headers.TUBING_MEASURED_DEPTH].to_numpy() + annulus_length
            )
            df_annulus_downstream[Headers.TRUE_VERTICAL_DEPTH] = df_branch_downstream[
                Headers.TRUE_VERTICAL_DEPTH
            ].to_numpy()
            df_annulus_downstream[Headers.WELL_BORE_DIAMETER] = df_branch_downstream[Headers.OUTER_DIAMETER].to_numpy()
            df_annulus_downstream[Headers.ROUGHNESS] = df_branch_downstream[Headers.ROUGHNESS].to_numpy()

            # no WELL_SEGMENTS_LINK in the downstream part because
            # no annulus segment have connection to
            # the device segment. in case you wonder why :)

            # upstream part
            # update the start segment and start branch
            start_segment = max(df_annulus_downstream[Headers.START_SEGMENT_NUMBER]) + 1
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
    df_annulus_upstream[Headers.START_SEGMENT_NUMBER] = start_segment + np.arange(df_branch.shape[0])
    df_annulus_upstream[Headers.END_SEGMENT_NUMBER] = df_annulus_upstream[Headers.START_SEGMENT_NUMBER]
    df_annulus_upstream[Headers.BRANCH] = start_branch
    out_segment = df_annulus_upstream[Headers.START_SEGMENT_NUMBER].to_numpy() - 1
    # determining the outlet segment of the annulus segment
    # if the annulus segment is not the most downstream which has connection
    # then the outlet is its adjacent annulus segment
    device_segment = get_outlet_segment(
        df_branch[Headers.TUBING_MEASURED_DEPTH].to_numpy(),
        df_device[Headers.MEASURED_DEPTH].to_numpy(),
        df_device[Headers.START_SEGMENT_NUMBER].to_numpy(),
    )
    # but for the most downstream annulus segment
    # its outlet is the device segment
    out_segment[0] = device_segment[0]
    # determining segment position
    md_ = df_branch[Headers.TUBING_MEASURED_DEPTH].to_numpy() + annulus_length
    md_[0] = md_[0] + annulus_length
    df_annulus_upstream[Headers.OUT] = out_segment
    df_annulus_upstream[Headers.MEASURED_DEPTH] = md_
    df_annulus_upstream[Headers.TRUE_VERTICAL_DEPTH] = df_branch[Headers.TRUE_VERTICAL_DEPTH].to_numpy()
    df_annulus_upstream[Headers.WELL_BORE_DIAMETER] = df_branch[Headers.OUTER_DIAMETER].to_numpy()
    df_annulus_upstream[Headers.ROUGHNESS] = df_branch[Headers.ROUGHNESS].to_numpy()
    device_segment = get_outlet_segment(
        df_active[Headers.TUBING_MEASURED_DEPTH].to_numpy(),
        df_device[Headers.MEASURED_DEPTH].to_numpy(),
        df_device[Headers.START_SEGMENT_NUMBER].to_numpy(),
    )
    annulus_segment = get_outlet_segment(
        df_active[Headers.TUBING_MEASURED_DEPTH].to_numpy(),
        df_annulus_upstream[Headers.MEASURED_DEPTH].to_numpy(),
        df_annulus_upstream[Headers.START_SEGMENT_NUMBER].to_numpy(),
    )
    outlet_segment = get_outlet_segment(
        df_active[Headers.TUBING_MEASURED_DEPTH].to_numpy(),
        df_annulus_upstream[Headers.MEASURED_DEPTH].to_numpy(),
        df_annulus_upstream[Headers.OUT].to_numpy(),
    )
    df_wseglink_upstream = pd.DataFrame(
        {
            Headers.WELL: [well_name] * device_segment.shape[0],
            Headers.ANNULUS: annulus_segment,
            Headers.DEVICE: device_segment,
            Headers.OUT: outlet_segment,
        }
    )
    # WELL_SEGMENTS_LINK is only for those segments whose outlet segment is not a device segment.
    df_wseglink_upstream = df_wseglink_upstream[
        df_wseglink_upstream[Headers.DEVICE] != df_wseglink_upstream[Headers.OUT]
    ]
    return df_annulus_upstream, df_wseglink_upstream


def connect_compseg_icv(
    df_reservoir: pd.DataFrame, df_device: pd.DataFrame, df_annulus: pd.DataFrame, df_completion: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Connect COMPLETION_SEGMENTS with the correct depth due to ICV segmenting combination.

    Args:
        df_reservoir: Reservoir data.
        df_device: Device data for this well and lateral.
        df_annulus: Annulus data for this well and lateral.
        df_completion: Completion data.

    Returns:
        Completion segments for devices and completion segments for annulus.
    """
    _MARKER_MEASURED_DEPTH = "TEMPORARY_MARKER_MEASURED_DEPTH"
    df_temp = df_completion[
        (df_completion[Headers.VALVES_PER_JOINT] > 0.0) | (df_completion[Headers.DEVICE_TYPE] == Content.PERFORATED)
    ]
    df_completion_table_clean = df_temp[
        (df_temp[Headers.ANNULUS] != Content.PACKER) & (df_temp[Headers.DEVICE_TYPE] == Content.INFLOW_CONTROL_VALVE)
    ]
    df_res = df_reservoir.copy(deep=True)

    df_res[_MARKER_MEASURED_DEPTH] = df_res[Headers.MEASURED_DEPTH]
    starts = df_completion_table_clean[Headers.START_MEASURED_DEPTH].apply(
        lambda x: max(x, df_res[Headers.START_MEASURED_DEPTH].iloc[0])
    )
    ends = df_completion_table_clean[Headers.END_MEASURED_DEPTH].apply(
        lambda x: min(x, df_res[Headers.END_MEASURED_DEPTH].iloc[-1])
    )
    for start, end in zip(starts, ends):
        condition = (
            f"@df_res.{Headers.MEASURED_DEPTH} >= {start} and @df_res.{Headers.MEASURED_DEPTH} <= {end} "
            f"and @df_res.{Headers.DEVICE_TYPE} == 'ICV'"
        )
        func = float(start + end) / 2
        column_index = df_res.query(condition).index
        df_res.loc[column_index, _MARKER_MEASURED_DEPTH] = func

    df_compseg_device = pd.merge_asof(
        left=df_res,
        right=df_device,
        left_on=_MARKER_MEASURED_DEPTH,
        right_on=Headers.MEASURED_DEPTH,
        direction="nearest",
    )
    df_compseg_annulus = pd.DataFrame()
    if (df_completion[Headers.ANNULUS] == Content.OPEN_ANNULUS).any():
        df_compseg_annulus = pd.merge_asof(
            left=df_res,
            right=df_annulus,
            left_on=_MARKER_MEASURED_DEPTH,
            right_on=Headers.MEASURED_DEPTH,
            direction="nearest",
        ).drop(_MARKER_MEASURED_DEPTH, axis=1)
    return df_compseg_device.drop(_MARKER_MEASURED_DEPTH, axis=1), df_compseg_annulus


def prepare_completion_segments(
    well_name: str,
    lateral: int,
    df_reservoir: pd.DataFrame,
    df_device: pd.DataFrame,
    df_annulus: pd.DataFrame,
    df_completion_table: pd.DataFrame,
    segment_length: float | str,
) -> pd.DataFrame:
    """Prepare output for COMPLETION_SEGMENTS.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        df_reservoir: The reservoir data.
        df_device:  Device data for this well and lateral.
        df_annulus: Annulus data for this well and lateral.
        df_completion_table: DataFrame.
        segment_length: Segment length.

    Returns:
        COMPLETION_SEGMENTS DataFrame.
    """
    df_reservoir = df_reservoir[df_reservoir[Headers.WELL] == well_name]
    df_reservoir = df_reservoir[df_reservoir[Headers.LATERAL] == lateral]
    # compsegs is only for those who are either:
    # 1. open perforation in the device segment
    # 2. has number of device > 0
    # 3. it is connected in the annular zone
    df_reservoir = df_reservoir[
        (df_reservoir[Headers.ANNULUS_ZONE] > 0)
        | (df_reservoir[Headers.NUMBER_OF_DEVICES] > 0)
        | (df_reservoir[Headers.DEVICE_TYPE] == Content.PERFORATED)
    ]
    # sort device dataframe by MEASURED_DEPTH to be used for pd.merge_asof
    if df_reservoir.shape[0] == 0:
        return pd.DataFrame()
    df_device = df_device.sort_values(by=[Headers.MEASURED_DEPTH])
    if isinstance(segment_length, str):
        if segment_length.upper() == "USER":
            segment_length = -1.0
    icv_segmenting = (
        df_reservoir[Headers.DEVICE_TYPE].nunique() > 1
        and (df_reservoir[Headers.DEVICE_TYPE] == Content.INFLOW_CONTROL_VALVE).any()
        and not df_reservoir[Headers.NUMBER_OF_DEVICES].empty
    )
    if df_annulus.empty:
        # There are no annular zones then all cells in this lateral and this well is connected to the device segment.
        if isinstance(segment_length, float):
            if segment_length >= 0:
                df_compseg_device = pd.merge_asof(
                    left=df_reservoir, right=df_device, on=[Headers.MEASURED_DEPTH], direction="nearest"
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
            df_compseg_device = pd.merge_asof(
                left=df_reservoir, right=df_device, on=[Headers.MEASURED_DEPTH], direction="nearest"
            )
        if icv_segmenting:
            df_compseg_device, _ = connect_compseg_icv(df_reservoir, df_device, df_annulus, df_completion_table)
        compseg = pd.DataFrame()
        compseg[Headers.I] = df_compseg_device[Headers.I].to_numpy()
        compseg[Headers.J] = df_compseg_device[Headers.J].to_numpy()
        compseg[Headers.K] = df_compseg_device[Headers.K].to_numpy()
        # take the BRANCH column from df_device
        compseg[Headers.BRANCH] = df_compseg_device[Headers.BRANCH].to_numpy()
        compseg[Headers.START_MEASURED_DEPTH] = df_compseg_device[Headers.START_MEASURED_DEPTH].to_numpy()
        compseg[Headers.END_MEASURED_DEPTH] = df_compseg_device[Headers.END_MEASURED_DEPTH].to_numpy()
        compseg[Headers.COMPSEGS_DIRECTION] = df_compseg_device[Headers.COMPSEGS_DIRECTION].to_numpy()
        compseg[Headers.DEF] = "3*"
        compseg[Headers.START_SEGMENT_NUMBER] = df_compseg_device[Headers.START_SEGMENT_NUMBER].to_numpy()
    else:
        # sort the df_annulus and df_device
        df_annulus = df_annulus.sort_values(by=[Headers.MEASURED_DEPTH])
        if isinstance(segment_length, float):
            # SEGMENTLENGTH = FIXED
            if segment_length >= 0:
                df_compseg_annulus = pd.merge_asof(
                    left=df_reservoir, right=df_annulus, on=[Headers.MEASURED_DEPTH], direction="nearest"
                )
                df_compseg_device = pd.merge_asof(
                    left=df_reservoir, right=df_device, on=[Headers.MEASURED_DEPTH], direction="nearest"
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
                df_compseg_annulus.sort_values(by=[Headers.START_MEASURED_DEPTH], inplace=True)
                df_compseg_device.sort_values(by=[Headers.START_MEASURED_DEPTH], inplace=True)
                df_compseg_device.drop([Headers.MARKER], axis=1, inplace=True)
                df_compseg_annulus.drop([Headers.MARKER], axis=1, inplace=True)
        else:
            df_compseg_annulus = pd.merge_asof(
                left=df_reservoir, right=df_annulus, on=[Headers.MEASURED_DEPTH], direction="nearest"
            )
            df_compseg_device = pd.merge_asof(
                left=df_reservoir, right=df_device, on=[Headers.MEASURED_DEPTH], direction="nearest"
            )
        if icv_segmenting:
            df_compseg_device, df_compseg_annulus = connect_compseg_icv(
                df_reservoir, df_device, df_annulus, df_completion_table
            )

        compseg = pd.DataFrame(
            {
                Headers.I: choose_layer(df_reservoir, df_compseg_annulus, df_compseg_device, Headers.I),
                Headers.J: choose_layer(df_reservoir, df_compseg_annulus, df_compseg_device, Headers.J),
                Headers.K: choose_layer(df_reservoir, df_compseg_annulus, df_compseg_device, Headers.K),
                Headers.BRANCH: choose_layer(df_reservoir, df_compseg_annulus, df_compseg_device, Headers.BRANCH),
                Headers.START_MEASURED_DEPTH: choose_layer(
                    df_reservoir, df_compseg_annulus, df_compseg_device, Headers.START_MEASURED_DEPTH
                ),
                Headers.END_MEASURED_DEPTH: choose_layer(
                    df_reservoir, df_compseg_annulus, df_compseg_device, Headers.END_MEASURED_DEPTH
                ),
                Headers.COMPSEGS_DIRECTION: choose_layer(
                    df_reservoir, df_compseg_annulus, df_compseg_device, Headers.COMPSEGS_DIRECTION
                ),
                Headers.DEF: "3*",
                Headers.START_SEGMENT_NUMBER: choose_layer(
                    df_reservoir, df_compseg_annulus, df_compseg_device, Headers.START_SEGMENT_NUMBER
                ),
            }
        )
    compseg[Headers.EMPTY] = "/"
    return compseg


def connect_compseg_usersegment(
    df_reservoir: pd.DataFrame, df_device: pd.DataFrame, df_annulus: pd.DataFrame, df_completion_table: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Connect COMPLETION_SEGMENTS with user segmentation.

    This method will connect df_reservoir with df_device and df_annulus in accordance with its
    depth in the df_completion due to user segmentation method.

    Args:
        df_reservoir: The reservoir data.
        df_device: Device data for this well and lateral.
        df_annulus: Annulus data for this well and lateral.
        df_completion_table: Completion data.

    Returns:
        Completion segments for devices and completion segments for annulus.
    """
    # check on top of df_res if the completion table is feasible
    df_temp = df_completion_table[
        (df_completion_table[Headers.VALVES_PER_JOINT] > 0.0)
        | (df_completion_table[Headers.DEVICE_TYPE] == Content.PERFORATED)
    ]
    df_completion_table_clean = df_temp[(df_temp[Headers.ANNULUS] != Content.PACKER)]
    if not df_annulus.empty:
        df_completion_table_clean = df_completion_table[df_completion_table[Headers.ANNULUS] == Content.OPEN_ANNULUS]
    df_completion_table_clean = df_completion_table_clean[
        (df_completion_table_clean[Headers.END_MEASURED_DEPTH] > df_reservoir[Headers.START_MEASURED_DEPTH].iloc[0])
    ]
    df_annulus.reset_index(drop=True, inplace=True)
    df_res = df_reservoir.assign(MARKER=[0 for _ in range(df_reservoir.shape[0])])
    df_dev = df_device.assign(MARKER=[x + 1 for x in range(df_device.shape[0])])
    df_ann = df_annulus.assign(MARKER=[x + 1 for x in range(df_annulus.shape[0])])
    starts = df_completion_table_clean[Headers.START_MEASURED_DEPTH].apply(
        lambda x: max(x, df_res[Headers.START_MEASURED_DEPTH].iloc[0])
    )
    ends = df_completion_table_clean[Headers.END_MEASURED_DEPTH].apply(
        lambda x: min(x, df_res[Headers.END_MEASURED_DEPTH].iloc[-1])
    )
    func = 1
    for start, end in zip(starts, ends):
        condition = f"@df_res.{Headers.MEASURED_DEPTH} >= {start} and @df_res.{Headers.MEASURED_DEPTH} <= {end}"
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
) -> npt.NDArray[np.float64 | np.int64]:
    """Choose relevant parameters from either completion segments annulus or completion segments device.

    Args:
        df_reservoir:
        df_compseg_annulus:
        df_compseg_device:
        parameter:

    Returns:
        Relevant parameters.
    """
    branch_num = df_reservoir[Headers.ANNULUS_ZONE].to_numpy()
    ndevice = df_reservoir[Headers.NUMBER_OF_DEVICES].to_numpy()
    dev_type = df_reservoir[Headers.DEVICE_TYPE].to_numpy()
    return np.where(
        branch_num > 0,
        df_compseg_annulus[parameter].to_numpy(),
        np.where((ndevice > 0) | (dev_type == Content.PERFORATED), df_compseg_device[parameter].to_numpy(), -1),
    )


def fix_well_id(df_reservoir: pd.DataFrame, df_completion: pd.DataFrame) -> pd.DataFrame:
    """Ensure that well/casing inner diameter in the COMPLETION_DATA section is in agreement with
    the case/config file and not the input schedule file.

    Args:
        df_reservoir: Reservoir data.
        df_completion: Completion data for current well/lateral.

    Returns:
        Corrected DataFrame for current well/lateral with inner diameter taken from the casefile object.
    """
    df_reservoir = df_reservoir.copy(deep=True)
    completion_diameters = []
    for md_reservoir in df_reservoir[Headers.MEASURED_DEPTH]:
        for start_completion, outer_inner_diameter_completion, end_completion in zip(
            df_completion[Headers.START_MEASURED_DEPTH],
            df_completion[Headers.OUTER_DIAMETER],
            df_completion[Headers.END_MEASURED_DEPTH],
        ):
            if start_completion <= md_reservoir <= end_completion:
                completion_diameters.append(outer_inner_diameter_completion)
                break
    df_reservoir[Headers.WELL_BORE_DIAMETER] = completion_diameters
    return df_reservoir


def prepare_completion_data(
    well_name: str, lateral: int, df_reservoir: pd.DataFrame, df_completion: pd.DataFrame
) -> pd.DataFrame:
    """Prepare COMPLETION_DATA data frame.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        df_reservoir: Reservoir data.
        df_completion: Completion data.

    Returns:
        COMPLETION_DATA.
    """
    df_reservoir = df_reservoir[df_reservoir[Headers.WELL] == well_name]
    df_reservoir = df_reservoir[df_reservoir[Headers.LATERAL] == lateral]
    df_reservoir = df_reservoir[
        (df_reservoir[Headers.ANNULUS_ZONE] > 0)
        | ((df_reservoir[Headers.NUMBER_OF_DEVICES] > 0) | (df_reservoir[Headers.DEVICE_TYPE] == Content.PERFORATED))
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
    compdat[Headers.SATURATION_FUNCTION_REGION_NUMBERS] = df_reservoir[
        Headers.SATURATION_FUNCTION_REGION_NUMBERS
    ].to_numpy()
    compdat[Headers.CONNECTION_FACTOR] = df_reservoir[Headers.CONNECTION_FACTOR].to_numpy()
    compdat[Headers.WELL_BORE_DIAMETER] = fix_well_id(df_reservoir, df_completion)[
        Headers.WELL_BORE_DIAMETER
    ].to_numpy()
    compdat[Headers.FORMATION_PERMEABILITY_THICKNESS] = df_reservoir[
        Headers.FORMATION_PERMEABILITY_THICKNESS
    ].to_numpy()
    compdat[Headers.SKIN] = df_reservoir[Headers.SKIN].to_numpy()
    compdat[Headers.D_FACTOR] = df_reservoir[Headers.D_FACTOR].to_numpy()
    compdat[Headers.COMPDAT_DIRECTION] = df_reservoir[Headers.COMPDAT_DIRECTION].to_numpy()
    compdat[Headers.RO] = df_reservoir[Headers.RO].to_numpy()
    # remove default columns
    compdat = trim_pandas(compdat)
    compdat[Headers.EMPTY] = "/"
    return compdat


def prepare_autonomous_inflow_control_device(
    well_name: str, df_well: pd.DataFrame, df_device: pd.DataFrame
) -> pd.DataFrame:
    """Prepare AUTONOMOUS_INFLOW_CONTROL_DEVICE data frame.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        df_well: Well data.
        df_device: From function prepare_device_layer for this well and this lateral.

    Returns:
        AUTONOMOUS_INFLOW_CONTROL_DEVICE.
    """
    df_well = df_well[(df_well[Headers.DEVICE_TYPE] == Content.PERFORATED) | (df_well[Headers.NUMBER_OF_DEVICES] > 0)]
    if df_well.shape[0] == 0:
        return pd.DataFrame()
    df_merge = pd.merge_asof(
        left=df_device,
        right=df_well,
        left_on=[Headers.MEASURED_DEPTH],
        right_on=[Headers.TUBING_MEASURED_DEPTH],
        direction="nearest",
    )
    df_merge = df_merge[df_merge[Headers.DEVICE_TYPE] == Content.AUTONOMOUS_INFLOW_CONTROL_DEVICE]
    wsegaicd = pd.DataFrame()
    if df_merge.shape[0] > 0:
        wsegaicd[Headers.WELL] = [well_name] * df_merge.shape[0]
        wsegaicd[Headers.START_SEGMENT_NUMBER] = df_merge[Headers.START_SEGMENT_NUMBER].to_numpy()
        wsegaicd[Headers.END_SEGMENT_NUMBER] = df_merge[Headers.START_SEGMENT_NUMBER].to_numpy()
        wsegaicd[Headers.STRENGTH] = df_merge[Headers.STRENGTH].to_numpy()
        wsegaicd[Headers.SCALE_FACTOR] = df_merge[Headers.SCALE_FACTOR].to_numpy()
        wsegaicd[Headers.CALIBRATION_FLUID_DENSITY] = df_merge[Headers.AICD_CALIBRATION_FLUID_DENSITY].to_numpy()
        wsegaicd[Headers.CALIBRATION_FLUID_VISCOSITY] = df_merge[Headers.AICD_FLUID_VISCOSITY].to_numpy()
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


def prepare_inflow_control_device(well_name: str, df_well: pd.DataFrame, df_device: pd.DataFrame) -> pd.DataFrame:
    """Prepare WSEGSICD data frame.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        df_well: Well data.
        df_device: Device data for this well and lateral.

    Returns:
        WSEGSICD.
    """
    df_well = df_well[(df_well[Headers.DEVICE_TYPE] == Content.PERFORATED) | (df_well[Headers.NUMBER_OF_DEVICES] > 0)]
    if df_well.shape[0] == 0:
        return pd.DataFrame()
    df_merge = pd.merge_asof(
        left=df_device,
        right=df_well,
        left_on=[Headers.MEASURED_DEPTH],
        right_on=[Headers.TUBING_MEASURED_DEPTH],
        direction="nearest",
    )
    df_merge = df_merge[df_merge[Headers.DEVICE_TYPE] == Content.INFLOW_CONTROL_DEVICE]
    wsegsicd = pd.DataFrame()
    if df_merge.shape[0] > 0:
        wsegsicd[Headers.WELL] = [well_name] * df_merge.shape[0]
        wsegsicd[Headers.START_SEGMENT_NUMBER] = df_merge[Headers.START_SEGMENT_NUMBER].to_numpy()
        wsegsicd[Headers.END_SEGMENT_NUMBER] = df_merge[Headers.START_SEGMENT_NUMBER].to_numpy()
        wsegsicd[Headers.STRENGTH] = df_merge[Headers.STRENGTH].to_numpy()
        wsegsicd[Headers.SCALE_FACTOR] = df_merge[Headers.SCALE_FACTOR].to_numpy()
        wsegsicd[Headers.CALIBRATION_FLUID_DENSITY] = df_merge[Headers.CALIBRATION_FLUID_DENSITY].to_numpy()
        wsegsicd[Headers.CALIBRATION_FLUID_VISCOSITY] = df_merge[Headers.CALIBRATION_FLUID_VISCOSITY].to_numpy()
        wsegsicd[Headers.WATER_CUT] = df_merge[Headers.WATER_CUT].to_numpy()
        wsegsicd[Headers.EMPTY] = "/"
    return wsegsicd


def prepare_valve(well_name: str, df_well: pd.DataFrame, df_device: pd.DataFrame) -> pd.DataFrame:
    """Prepare WELL_SEGMENTS_VALVE data frame.

    Args:
        well_name: Well name.
        df_well: Well data.
        df_device: From function prepare_device_layer for this well and this lateral.

    Returns:
        WELL_SEGMENTS_VALVE.
    """
    df_well = df_well[(df_well[Headers.DEVICE_TYPE] == Content.PERFORATED) | (df_well[Headers.NUMBER_OF_DEVICES] > 0)]
    if df_well.shape[0] == 0:
        return pd.DataFrame()
    df_merge = pd.merge_asof(
        left=df_device,
        right=df_well,
        left_on=[Headers.MEASURED_DEPTH],
        right_on=[Headers.TUBING_MEASURED_DEPTH],
        direction="nearest",
    )
    df_merge = df_merge[df_merge[Headers.DEVICE_TYPE] == Content.VALVE].reset_index(drop=True)
    wsegvalv = pd.DataFrame()
    if df_merge.shape[0] > 0:
        wsegvalv[Headers.WELL] = [well_name] * df_merge.shape[0]
        wsegvalv[Headers.START_SEGMENT_NUMBER] = df_merge[Headers.START_SEGMENT_NUMBER].to_numpy()
        # the Cv is already corrected by the scaling factor
        wsegvalv[Headers.FLOW_COEFFICIENT] = df_merge[Headers.FLOW_COEFFICIENT].to_numpy()
        wsegvalv[Headers.FLOW_CROSS_SECTIONAL_AREA] = df_merge[Headers.FLOW_CROSS_SECTIONAL_AREA].to_numpy()
        wsegvalv[Headers.ADDITIONAL_PIPE_LENGTH_FRICTION_PRESSURE_DROP] = "5*"
        wsegvalv[Headers.MAX_FLOW_CROSS_SECTIONAL_AREA] = df_merge[Headers.MAX_FLOW_CROSS_SECTIONAL_AREA].fillna(
            df_merge[Headers.FLOW_CROSS_SECTIONAL_AREA]
        )
        wsegvalv[Headers.EMPTY] = "/"
    return wsegvalv


def prepare_inflow_control_valve(
    well_name: str,
    lateral: int,
    df_well: pd.DataFrame,
    df_device: pd.DataFrame,
    df_tubing: pd.DataFrame,
    df_icv_tubing: pd.DataFrame,
    df_icv: pd.DataFrame,
) -> pd.DataFrame:
    """Prepare INFLOW_CONTROL_VALVE DataFrame with WELL_SEGMENTS_VALVE format. Include ICVs in device and tubing layer.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        df_well: Well data.
        df_device: From function prepare_device_layer for this well and this lateral.
        df_tubing: From function prepare_tubing_layer for this well and this lateral.
        df_icv_tubing: df_icv_tubing completion from class ReadCaseFile.
        df_icv: df_icv for INFLOW_CONTROL_VALVE keyword from class ReadCaseFile.

    Returns:
        Dataframe for ICV.
    """
    df_well = df_well[
        (df_well[Headers.LATERAL] == lateral)
        & ((df_well[Headers.DEVICE_TYPE] == Content.PERFORATED) | (df_well[Headers.NUMBER_OF_DEVICES] > 0))
    ]
    if df_well.empty:
        return df_well
    df_merge = pd.merge_asof(
        left=df_device,
        right=df_well,
        left_on=Headers.MEASURED_DEPTH,
        right_on=Headers.TUBING_MEASURED_DEPTH,
        direction="nearest",
    )
    wsegicv = pd.DataFrame()
    df_merge = df_merge[df_merge[Headers.DEVICE_TYPE] == Content.INFLOW_CONTROL_VALVE]
    if not df_merge.empty:
        wsegicv = df_merge.copy()
        wsegicv = wsegicv[
            [
                Headers.START_SEGMENT_NUMBER,
                Headers.FLOW_COEFFICIENT,
                Headers.FLOW_CROSS_SECTIONAL_AREA,
                Headers.MAX_FLOW_CROSS_SECTIONAL_AREA,
            ]
        ]
        wsegicv[Headers.WELL] = [well_name] * df_merge.shape[0]
        wsegicv[Headers.DEFAULTS] = "5*"
        wsegicv[Headers.MAX_FLOW_CROSS_SECTIONAL_AREA] = wsegicv[Headers.MAX_FLOW_CROSS_SECTIONAL_AREA].fillna(
            df_merge[Headers.FLOW_CROSS_SECTIONAL_AREA]
        )
        wsegicv = wsegicv.reindex(
            columns=[
                Headers.WELL,
                Headers.START_SEGMENT_NUMBER,
                Headers.FLOW_COEFFICIENT,
                Headers.FLOW_CROSS_SECTIONAL_AREA,
                Headers.DEFAULTS,
                Headers.MAX_FLOW_CROSS_SECTIONAL_AREA,
            ]
        )
        wsegicv[Headers.EMPTY] = "/"
        # create tubing icv table
    if not df_icv_tubing.empty:
        mask = (df_icv_tubing[Headers.WELL] == well_name) & (df_icv_tubing[Headers.BRANCH] == lateral)
        df_icv_tubing = df_icv_tubing.loc[mask]
        df_merge_tubing = pd.merge_asof(left=df_icv_tubing, right=df_icv, on=Headers.DEVICE_NUMBER, direction="nearest")
        df_merge_tubing = pd.merge_asof(
            left=df_merge_tubing,
            right=df_tubing,
            left_on=Headers.START_MEASURED_DEPTH,
            right_on=Headers.MEASURED_DEPTH,
            direction="nearest",
        )
        df_temp = df_merge_tubing.copy()
        df_temp = df_temp[
            [
                Headers.START_SEGMENT_NUMBER,
                Headers.FLOW_COEFFICIENT,
                Headers.FLOW_CROSS_SECTIONAL_AREA,
                Headers.MAX_FLOW_CROSS_SECTIONAL_AREA,
            ]
        ]
        df_temp[Headers.WELL] = [well_name] * df_merge_tubing.shape[0]
        df_temp[Headers.DEFAULTS] = "5*"
        df_temp[Headers.MAX_FLOW_CROSS_SECTIONAL_AREA] = df_temp[Headers.MAX_FLOW_CROSS_SECTIONAL_AREA].fillna(
            math.pi * 0.5 * df_tubing[Headers.WELL_BORE_DIAMETER] ** 2
        )
        df_temp = df_temp.reindex(
            columns=[
                Headers.WELL,
                Headers.START_SEGMENT_NUMBER,
                Headers.FLOW_COEFFICIENT,
                Headers.FLOW_CROSS_SECTIONAL_AREA,
                Headers.DEFAULTS,
                Headers.MAX_FLOW_CROSS_SECTIONAL_AREA,
            ]
        )
        df_temp[Headers.EMPTY] = "/"
        wsegicv = pd.concat([wsegicv, df_temp], axis=0).reset_index(drop=True)
    return wsegicv


def prepare_density_activated_recovery(well_name: str, df_well: pd.DataFrame, df_device: pd.DataFrame) -> pd.DataFrame:
    """Prepare data frame for DAR.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        df_well: Well data.
        df_device: Device data for this well and lateral.

    Returns:
        DataFrame for DAR.
    """
    df_well = df_well[(df_well[Headers.DEVICE_TYPE] == Content.PERFORATED) | (df_well[Headers.NUMBER_OF_DEVICES] > 0)]
    if df_well.shape[0] == 0:
        return pd.DataFrame()
    df_merge = pd.merge_asof(
        left=df_device,
        right=df_well,
        left_on=[Headers.MEASURED_DEPTH],
        right_on=[Headers.TUBING_MEASURED_DEPTH],
        direction="nearest",
    )
    df_merge = df_merge[df_merge[Headers.DEVICE_TYPE] == Content.DENSITY_ACTIVATED_RECOVERY]
    wsegdar = pd.DataFrame()
    if df_merge.shape[0] > 0:
        wsegdar[Headers.WELL] = [well_name] * df_merge.shape[0]
        wsegdar[Headers.START_SEGMENT_NUMBER] = df_merge[Headers.START_SEGMENT_NUMBER].to_numpy()
        # the Cv is already corrected by the scaling factor
        wsegdar[Headers.FLOW_COEFFICIENT] = df_merge[Headers.FLOW_COEFFICIENT].to_numpy()
        wsegdar[Headers.OIL_FLOW_CROSS_SECTIONAL_AREA] = df_merge[Headers.OIL_FLOW_CROSS_SECTIONAL_AREA].to_numpy()
        wsegdar[Headers.GAS_FLOW_CROSS_SECTIONAL_AREA] = df_merge[Headers.GAS_FLOW_CROSS_SECTIONAL_AREA].to_numpy()
        wsegdar[Headers.WATER_FLOW_CROSS_SECTIONAL_AREA] = df_merge[Headers.WATER_FLOW_CROSS_SECTIONAL_AREA].to_numpy()
        wsegdar[Headers.WATER_HOLDUP_FRACTION_LOW_CUTOFF] = df_merge[
            Headers.WATER_HOLDUP_FRACTION_LOW_CUTOFF
        ].to_numpy()
        wsegdar[Headers.WATER_HOLDUP_FRACTION_HIGH_CUTOFF] = df_merge[
            Headers.WATER_HOLDUP_FRACTION_HIGH_CUTOFF
        ].to_numpy()
        wsegdar[Headers.GAS_HOLDUP_FRACTION_LOW_CUTOFF] = df_merge[Headers.GAS_HOLDUP_FRACTION_LOW_CUTOFF].to_numpy()
        wsegdar[Headers.GAS_HOLDUP_FRACTION_HIGH_CUTOFF] = df_merge[Headers.GAS_HOLDUP_FRACTION_HIGH_CUTOFF].to_numpy()
        wsegdar[Headers.DEFAULTS] = "5*"
        wsegdar[Headers.MAX_FLOW_CROSS_SECTIONAL_AREA] = wsegdar[Headers.OIL_FLOW_CROSS_SECTIONAL_AREA].to_numpy()
        wsegdar[Headers.EMPTY] = "/"
    return wsegdar


def prepare_autonomous_inflow_control_valve(
    well_name: str, df_well: pd.DataFrame, df_device: pd.DataFrame
) -> pd.DataFrame:
    """Prepare data frame for AICV.

    Args:
        well_name: Well name.
        lateral: Lateral number.
        df_well: Well data.
        df_device: Device data for this well and lateral.

    Returns:
        DataFrame for AICV.
    """
    df_well = df_well[(df_well[Headers.DEVICE_TYPE] == Content.PERFORATED) | (df_well[Headers.NUMBER_OF_DEVICES] > 0)]
    if df_well.shape[0] == 0:
        return pd.DataFrame()
    df_merge = pd.merge_asof(
        left=df_device,
        right=df_well,
        left_on=[Headers.MEASURED_DEPTH],
        right_on=[Headers.TUBING_MEASURED_DEPTH],
        direction="nearest",
    )
    df_merge = df_merge[df_merge[Headers.DEVICE_TYPE] == Content.AUTONOMOUS_INFLOW_CONTROL_VALVE]
    wsegaicv = pd.DataFrame()
    if df_merge.shape[0] > 0:
        wsegaicv[Headers.WELL] = [well_name] * df_merge.shape[0]
        wsegaicv[Headers.START_SEGMENT_NUMBER] = df_merge[Headers.START_SEGMENT_NUMBER].to_numpy()
        wsegaicv[Headers.END_SEGMENT_NUMBER] = df_merge[Headers.START_SEGMENT_NUMBER].to_numpy()
        wsegaicv[Headers.ALPHA_MAIN] = df_merge[Headers.ALPHA_MAIN].to_numpy()
        wsegaicv[Headers.SCALE_FACTOR] = df_merge[Headers.SCALE_FACTOR].to_numpy()
        wsegaicv[Headers.CALIBRATION_FLUID_DENSITY] = df_merge[Headers.AICV_CALIBRATION_FLUID_DENSITY].to_numpy()
        wsegaicv[Headers.CALIBRATION_FLUID_VISCOSITY] = df_merge[Headers.AICV_FLUID_VISCOSITY].to_numpy()
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
        wsegaicv[Headers.AICV_WATER_CUT] = df_merge[Headers.AICV_WATER_CUT].to_numpy()
        wsegaicv[Headers.AICV_GAS_HOLDUP_FRACTION] = df_merge[Headers.AICV_GAS_HOLDUP_FRACTION].to_numpy()
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
        CompletorError: If there are to many wells and/or segments with DAR.
    """
    header = [
        [
            Headers.WELL,
            Headers.START_SEGMENT_NUMBER,
            Headers.FLOW_COEFFICIENT,
            Headers.GAS_FLOW_CROSS_SECTIONAL_AREA,
            Headers.DEFAULTS,
            Headers.MAX_FLOW_CROSS_SECTIONAL_AREA,
        ],
        [
            Headers.WELL,
            Headers.START_SEGMENT_NUMBER,
            Headers.FLOW_COEFFICIENT,
            Headers.WATER_FLOW_CROSS_SECTIONAL_AREA,
            Headers.DEFAULTS,
            Headers.MAX_FLOW_CROSS_SECTIONAL_AREA,
        ],
        [
            Headers.WELL,
            Headers.START_SEGMENT_NUMBER,
            Headers.FLOW_COEFFICIENT,
            Headers.OIL_FLOW_CROSS_SECTIONAL_AREA,
            Headers.DEFAULTS,
            Headers.MAX_FLOW_CROSS_SECTIONAL_AREA,
        ],
        [
            Headers.WELL,
            Headers.START_SEGMENT_NUMBER,
            Headers.FLOW_COEFFICIENT,
            Headers.OIL_FLOW_CROSS_SECTIONAL_AREA,
            Headers.DEFAULTS,
            Headers.MAX_FLOW_CROSS_SECTIONAL_AREA,
        ],
    ]
    sign_water = ["<=", ">", "", "<"]
    sign_gas = [">", "<=", "<", ""]
    suvtrig = ["0", "0", "1", "2"]
    action = "UDQ\n"
    for idx in range(df_wsegdar.shape[0]):
        segment_number = df_wsegdar[Headers.START_SEGMENT_NUMBER].iloc[idx]
        well_name = df_wsegdar[Headers.WELL].iloc[idx]
        action += f"  ASSIGN SUVTRIG {well_name} {segment_number} 0 /\n"
    action += "/\n\n"
    iaction = 3
    action += Keywords.WELL_SEGMENTS_VALVE + "\n"
    header_string = "--"
    for itm in header[iaction]:
        header_string += "  " + itm
    action += header_string.rstrip() + "\n"
    for idx in range(df_wsegdar.shape[0]):
        segment_number = df_wsegdar[Headers.START_SEGMENT_NUMBER].iloc[idx]
        print_df = df_wsegdar[df_wsegdar[Headers.START_SEGMENT_NUMBER] == segment_number]
        print_df = print_df[header[iaction]]
        print_df = dataframe_tostring(print_df, True, False, False) + "\n"
        action += print_df
    action += "/\n\n"
    for idx in range(df_wsegdar.shape[0]):
        segment_number = df_wsegdar[Headers.START_SEGMENT_NUMBER].iloc[idx]
        well_name = df_wsegdar[Headers.WELL].iloc[idx]
        water_holdup_fraction_low_cutoff = df_wsegdar[Headers.WATER_HOLDUP_FRACTION_LOW_CUTOFF].iloc[idx]
        water_holdup_fraction_high_cutoff = df_wsegdar[Headers.WATER_HOLDUP_FRACTION_HIGH_CUTOFF].iloc[idx]
        gas_holdup_fraction_low_cutoff = df_wsegdar[Headers.GAS_HOLDUP_FRACTION_LOW_CUTOFF].iloc[idx]
        gas_holdup_fraction_high_cutoff = df_wsegdar[Headers.GAS_HOLDUP_FRACTION_HIGH_CUTOFF].iloc[idx]
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
            print_df = df_wsegdar[df_wsegdar[Headers.START_SEGMENT_NUMBER] == segment_number]
            print_df = print_df[header[iaction]]  # type: ignore
            header_string = Keywords.WELL_SEGMENTS_VALVE + "\n--"
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
        print_df = df_wsegdar[df_wsegdar[Headers.START_SEGMENT_NUMBER] == segment_number]
        print_df = print_df[header[iaction]]  # type: ignore
        header_string = Keywords.WELL_SEGMENTS_VALVE + "\n--"
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
        print_df = df_wsegdar[df_wsegdar[Headers.START_SEGMENT_NUMBER] == segment_number]
        print_df = print_df[header[iaction]]  # type: ignore
        header_string = Keywords.WELL_SEGMENTS_VALVE + "\n--"
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
        CompletorError: If there are too many wells and/or segments with AICV.
    """
    header = [
        [
            Headers.WELL,
            Headers.START_SEGMENT_NUMBER,
            Headers.END_SEGMENT_NUMBER,
            Headers.ALPHA_MAIN,
            Headers.SCALE_FACTOR,
            Headers.CALIBRATION_FLUID_DENSITY,
            Headers.CALIBRATION_FLUID_VISCOSITY,
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
            Headers.START_SEGMENT_NUMBER,
            Headers.END_SEGMENT_NUMBER,
            Headers.ALPHA_PILOT,
            Headers.SCALE_FACTOR,
            Headers.CALIBRATION_FLUID_DENSITY,
            Headers.CALIBRATION_FLUID_VISCOSITY,
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
        Headers.START_SEGMENT_NUMBER,
        Headers.END_SEGMENT_NUMBER,
        Headers.STRENGTH,
        Headers.SCALE_FACTOR,
        Headers.CALIBRATION_FLUID_DENSITY,
        Headers.CALIBRATION_FLUID_VISCOSITY,
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
        segment_number = df_wsegaicv[Headers.START_SEGMENT_NUMBER].iloc[idx]
        well_name = df_wsegaicv[Headers.WELL].iloc[idx]
        wct = df_wsegaicv[Headers.AICV_WATER_CUT].iloc[idx]
        ghf = df_wsegaicv[Headers.AICV_GAS_HOLDUP_FRACTION].iloc[idx]
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

            print_df = df_wsegaicv[df_wsegaicv[Headers.START_SEGMENT_NUMBER] == segment_number]
            print_df = print_df[header[iaction]]
            print_df.columns = new_column
            print_df = Keywords.AUTONOMOUS_INFLOW_CONTROL_DEVICE + "\n" + dataframe_tostring(print_df, True)
            action += f"{print_df}\n/\nENDACTIO\n\n"
    return action
