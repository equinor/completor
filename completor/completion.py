"""Completion related methods. Completion is the area where there is production."""

from __future__ import annotations

from typing import Literal, overload

import numpy as np
import numpy.typing as npt
import pandas as pd

from completor.constants import Content, Headers, Method
from completor.exceptions import CompletorError
from completor.logger import logger
from completor.utils import log_and_raise_exception, shift_array


def well_trajectory(df_well_segments_header: pd.DataFrame, df_well_segments_content: pd.DataFrame) -> pd.DataFrame:
    """Create trajectory relation between measured depth and true vertical depth.

    Well segments must be defined with absolute values (ABS) and not incremental (INC).

    Args:
        df_well_segments_header: First record of well segments.
        df_well_segments_content: Second record of well segments.

    Return:
        Measured depth versus true vertical depth.

    """
    measured_depth = df_well_segments_content[Headers.TUBING_MEASURED_DEPTH].to_numpy()
    measured_depth = np.insert(measured_depth, 0, df_well_segments_header[Headers.MEASURED_DEPTH].iloc[0])
    true_vertical_depth = df_well_segments_content[Headers.TRUE_VERTICAL_DEPTH].to_numpy()
    true_vertical_depth = np.insert(
        true_vertical_depth, 0, df_well_segments_header[Headers.TRUE_VERTICAL_DEPTH].iloc[0]
    )
    df_measured_true_vertical_depth = pd.DataFrame(
        {Headers.MEASURED_DEPTH: measured_depth, Headers.TRUE_VERTICAL_DEPTH: true_vertical_depth}
    )
    # sort based on md
    df_measured_true_vertical_depth = df_measured_true_vertical_depth.sort_values(
        by=[Headers.MEASURED_DEPTH, Headers.TRUE_VERTICAL_DEPTH]
    )
    # reset index after sorting
    return df_measured_true_vertical_depth.reset_index(drop=True)


def define_annulus_zone(df_completion: pd.DataFrame) -> pd.DataFrame:
    """Define annulus zones based on completion data.

    Zones are divided to better track individual separated areas of completion.
    The divisions are based on depths, packer location, and the annulus content.


    Args:
        df_completion: Raw completion data, must contain start/end measured depth, and annulus content.

    Returns:
        Updated completion data with additional column `ANNULUS_ZONE`.

    Raise:
        ValueError: If the dimensions are incorrect.
    """
    start_measured_depth = df_completion[Headers.START_MEASURED_DEPTH].iloc[0]
    end_measured_depth = df_completion[Headers.END_MEASURED_DEPTH].iloc[-1]
    gravel_pack_location = df_completion[df_completion[Headers.ANNULUS] == Content.GRAVEL_PACKED][
        [Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH]
    ].to_numpy()
    packer_location = df_completion[df_completion[Headers.ANNULUS] == Content.PACKER][
        [Headers.START_MEASURED_DEPTH, Headers.END_MEASURED_DEPTH]
    ].to_numpy()
    # update df_completion by removing PA rows
    df_completion = df_completion[df_completion[Headers.ANNULUS] != Content.PACKER].copy()
    # reset index after filter
    df_completion.reset_index(drop=True, inplace=True)
    annulus_content = df_completion[Headers.ANNULUS].to_numpy()
    df_completion[Headers.ANNULUS_ZONE] = 0
    if Content.OPEN_ANNULUS in annulus_content:
        # only if there is an open annulus
        boundary = np.concatenate((packer_location.flatten(), gravel_pack_location.flatten()))
        boundary = np.sort(np.append(np.insert(boundary, 0, start_measured_depth), end_measured_depth))
        boundary = np.unique(boundary)
        start_bound = boundary[:-1]
        end_bound = boundary[1:]
        # get annulus zone
        # initiate with 0
        annulus_zone = np.full(len(start_bound), 0)
        for idx, start_measured_depth in enumerate(start_bound):
            end_measured_depth = end_bound[idx]
            is_gravel_pack_location = np.any(
                (gravel_pack_location[:, 0] == start_measured_depth)
                & (gravel_pack_location[:, 1] == end_measured_depth)
            )
            if not is_gravel_pack_location:
                annulus_zone[idx] = max(annulus_zone) + 1
            # else it is 0
        df_annulus = pd.DataFrame(
            {
                Headers.START_MEASURED_DEPTH: start_bound,
                Headers.END_MEASURED_DEPTH: end_bound,
                Headers.ANNULUS_ZONE: annulus_zone,
            }
        )

        annulus_zone = np.full(df_completion.shape[0], 0)
        for idx in range(df_completion.shape[0]):
            start_measured_depth = df_completion[Headers.START_MEASURED_DEPTH].iloc[idx]
            end_measured_depth = df_completion[Headers.END_MEASURED_DEPTH].iloc[idx]
            idx0, idx1 = completion_index(df_annulus, start_measured_depth, end_measured_depth)
            if idx0 != idx1 or idx0 == -1:
                raise ValueError("Check Define Annulus Zone")
            annulus_zone[idx] = df_annulus[Headers.ANNULUS_ZONE].iloc[idx0]
        df_completion[Headers.ANNULUS_ZONE] = annulus_zone
    df_completion[Headers.ANNULUS_ZONE] = df_completion[Headers.ANNULUS_ZONE].astype(np.int64)
    return df_completion


@overload
def create_tubing_segments(
    df_reservoir: pd.DataFrame,
    df_completion: pd.DataFrame,
    df_measured_depth_true_vertical_depth: pd.DataFrame,
    method: Literal[Method.FIX] = ...,
    segment_length: float = ...,
    minimum_segment_length: float = 0.0,
) -> pd.DataFrame: ...


@overload
def create_tubing_segments(
    df_reservoir: pd.DataFrame,
    df_completion: pd.DataFrame,
    df_measured_depth_true_vertical_depth: pd.DataFrame,
    method: Method = ...,
    segment_length: float | str = ...,
    minimum_segment_length: float = 0.0,
) -> pd.DataFrame: ...


def create_tubing_segments(
    df_reservoir: pd.DataFrame,
    # Technically, df_completion is only required for SegmentCreationMethod.USER
    df_completion: pd.DataFrame,
    df_measured_depth_true_vertical_depth: pd.DataFrame,
    method: Method = Method.CELLS,
    segment_length: float | str = 0.0,
    minimum_segment_length: float = 0.0,
) -> pd.DataFrame:
    """Create segments in the tubing layer.

    Args:
        df_reservoir: Must contain start and end measured depth.
        df_completion: Must contain annulus, start and end measured depth, and annulus zone.
            The packers must be removed in the completion.
        df_measured_depth_true_vertical_depth: Measured and true vertical depths.
        method: Method for segmentation. Defaults to cells.
        segment_length: Only if fix is selected in the method.
        minimum_segment_length: User input minimum segment length.

    Segmentation methods:
        cells: Create one segment per cell.
        user: Create segment based on the completion definition.
        fix: Create segment based on a fixed interval.
        well_data: Create segment based on well segments keyword.

    Returns:
        DataFrame with start and end measured depth, tubing measured depth, and tubing true vertical depth.

    Raises:
        ValueError: If the method is unknown.
    """
    start_measured_depth: npt.NDArray[np.float64]
    end_measured_depth: npt.NDArray[np.float64]
    if method == Method.CELLS:
        # Create the tubing layer one cell one segment while honoring df_reservoir[Headers.SEGMENT]
        start_measured_depth = df_reservoir[Headers.START_MEASURED_DEPTH].to_numpy()
        end_measured_depth = df_reservoir[Headers.END_MEASURED_DEPTH].to_numpy()
        if Headers.SEGMENT in df_reservoir.columns:
            if not df_reservoir[Headers.SEGMENT].isin(["1*"]).any():
                create_start_measured_depths = []
                create_end_measured_depths = []
                try:
                    create_start_measured_depths.append(df_reservoir[Headers.START_MEASURED_DEPTH].iloc[0])
                except IndexError:
                    raise CompletorError("Number of WELSEGS and COMPSEGS is inconsistent.")
                current_segment = df_reservoir[Headers.SEGMENT].iloc[0]
                for i in range(1, len(df_reservoir[Headers.SEGMENT])):
                    if df_reservoir[Headers.SEGMENT].iloc[i] != current_segment:
                        create_end_measured_depths.append(df_reservoir[Headers.END_MEASURED_DEPTH].iloc[i - 1])
                        create_start_measured_depths.append(df_reservoir[Headers.START_MEASURED_DEPTH].iloc[i])
                        current_segment = df_reservoir[Headers.SEGMENT].iloc[i]
                create_end_measured_depths.append(df_reservoir[Headers.END_MEASURED_DEPTH].iloc[-1])
                start_measured_depth = np.array(create_start_measured_depths)
                end_measured_depth = np.array(create_end_measured_depths)

        minimum_segment_length = float(minimum_segment_length)
        if minimum_segment_length > 0.0:
            new_start_measured_depth = []
            new_end_measured_depth = []
            diff_measured_depth = end_measured_depth - start_measured_depth
            current_diff_measured_depth = 0.0
            i_start = 0
            i_end = 0
            for i in range(0, len(diff_measured_depth) - 1):
                current_diff_measured_depth += diff_measured_depth[i]
                if current_diff_measured_depth >= minimum_segment_length:
                    new_start_measured_depth.append(start_measured_depth[i_start])
                    new_end_measured_depth.append(end_measured_depth[i_end])
                    current_diff_measured_depth = 0.0
                    i_start = i + 1
                i_end = i + 1
            if current_diff_measured_depth < minimum_segment_length:
                new_start_measured_depth.append(start_measured_depth[i_start])
                new_end_measured_depth.append(end_measured_depth[i_end])
            start_measured_depth = np.array(new_start_measured_depth)
            end_measured_depth = np.array(new_end_measured_depth)
    elif method == Method.USER:
        # Create tubing layer based on the definition of COMPLETION keyword in the case file.
        # Read all segments except PA (which has no segment length).
        df_temp = df_completion.copy(deep=True)
        start_measured_depth = df_temp[Headers.START_MEASURED_DEPTH].to_numpy()
        end_measured_depth = df_temp[Headers.END_MEASURED_DEPTH].to_numpy()
        # Fix the start and end.
        start_measured_depth[0] = max(
            df_reservoir[Headers.START_MEASURED_DEPTH].iloc[0], float(start_measured_depth[0])
        )
        end_measured_depth[-1] = min(df_reservoir[Headers.END_MEASURED_DEPTH].iloc[-1], float(end_measured_depth[-1]))
        if start_measured_depth[0] >= end_measured_depth[0]:
            start_measured_depth = np.delete(start_measured_depth, 0)
            end_measured_depth = np.delete(end_measured_depth, 0)
        if start_measured_depth[-1] >= end_measured_depth[-1]:
            start_measured_depth = np.delete(start_measured_depth, -1)
            end_measured_depth = np.delete(end_measured_depth, -1)
    elif method == Method.FIX:
        # Create tubing layer with fix interval according to the user input in the case file keyword SEGMENTLENGTH.
        min_measured_depth = df_reservoir[Headers.START_MEASURED_DEPTH].min()
        max_measured_depth = df_reservoir[Headers.END_MEASURED_DEPTH].max()
        if not isinstance(segment_length, (float, int)):
            raise ValueError(f"Segment length must be a number, when using method fix (was {segment_length}).")
        start_measured_depth = np.arange(min_measured_depth, max_measured_depth, segment_length)
        end_measured_depth = start_measured_depth + segment_length
        # Update the end point of the last segment.
        end_measured_depth[-1] = min(float(end_measured_depth[-1]), max_measured_depth)
    elif method == Method.WELSEGS:
        # Create the tubing layer from measured depths in the WELL_SEGMENTS keyword that are missing from COMPLETION_SEGMENTS.
        # WELL_SEGMENTS depths are collected in the `df_measured_depth_true_vertical_depth`, available here.
        # Completor interprets WELL_SEGMENTS depths as segment midpoint depths.
        # Obtain the multisegmented well segments midpoint depth.
        well_segments = df_measured_depth_true_vertical_depth[Headers.MEASURED_DEPTH].to_numpy()
        end_welsegs_depth = 0.5 * (well_segments[:-1] + well_segments[1:])
        # The start of the very first segment in any branch is the actual startMD of the first segment.
        start_welsegs_depth = np.insert(end_welsegs_depth[:-1], 0, well_segments[0], axis=None)
        start_compsegs_depth: npt.NDArray[np.float64] = df_reservoir[Headers.START_MEASURED_DEPTH].to_numpy()
        end_compsegs_depth = df_reservoir[Headers.END_MEASURED_DEPTH].to_numpy()
        # If there are gaps in compsegs and there are schedule segments that fit in the gaps,
        # insert segments into the compsegs gaps.
        gaps_compsegs = start_compsegs_depth[1:] - end_compsegs_depth[:-1]
        # Indices of gaps in compsegs.
        indices_gaps = np.nonzero(gaps_compsegs)
        # Start of the gaps.
        start_gaps_depth = end_compsegs_depth[indices_gaps[0]]
        # End of the gaps.
        end_gaps_depth = start_compsegs_depth[indices_gaps[0] + 1]
        # Check the gaps between COMPLETION_SEGMENTS and fill it out with WELL_SEGMENTS.
        start = np.abs(start_welsegs_depth[:, np.newaxis] - start_gaps_depth).argmin(axis=0)
        end = np.abs(end_welsegs_depth[:, np.newaxis] - end_gaps_depth).argmin(axis=0)
        welsegs_to_add = np.setxor1d(start_welsegs_depth[start], end_welsegs_depth[end])
        start_welsegs_outside = start_welsegs_depth[np.argwhere(start_welsegs_depth < start_compsegs_depth[0])]
        end_welsegs_outside = end_welsegs_depth[np.argwhere(end_welsegs_depth > end_compsegs_depth[-1])]
        welsegs_to_add = np.append(welsegs_to_add, start_welsegs_outside)
        welsegs_to_add = np.append(welsegs_to_add, end_welsegs_outside)
        # Find schedule segments start and end in gaps.
        start_compsegs_depth = np.append(start_compsegs_depth, welsegs_to_add)
        end_compsegs_depth = np.append(end_compsegs_depth, welsegs_to_add)
        start_measured_depth = np.sort(start_compsegs_depth)
        end_measured_depth = np.sort(end_compsegs_depth)
        # Check for missing segment.
        shift_start_measured_depth = np.append(start_measured_depth[1:], end_measured_depth[-1])
        missing_index = np.argwhere(shift_start_measured_depth > end_measured_depth).flatten()
        missing_index += 1
        new_missing_start_measured_depth = end_measured_depth[missing_index - 1]
        new_missing_end_measured_depth = start_measured_depth[missing_index]
        start_measured_depth = np.sort(np.append(start_measured_depth, new_missing_start_measured_depth))
        end_measured_depth = np.sort(np.append(end_measured_depth, new_missing_end_measured_depth))
        # drop duplicate
        duplicate_indexes = np.argwhere(start_measured_depth == end_measured_depth)
        start_measured_depth = np.delete(start_measured_depth, duplicate_indexes)
        end_measured_depth = np.delete(end_measured_depth, duplicate_indexes)
    else:
        raise ValueError(f"Unknown method '{method}'.")

    # md for tubing segments
    measured_depth_ = 0.5 * (start_measured_depth + end_measured_depth)
    # estimate TRUE_VERTICAL_DEPTH
    true_vertical_depth = np.interp(
        measured_depth_,
        df_measured_depth_true_vertical_depth[Headers.MEASURED_DEPTH].to_numpy(),
        df_measured_depth_true_vertical_depth[Headers.TRUE_VERTICAL_DEPTH].to_numpy(),
    )
    # create data frame
    return pd.DataFrame(
        {
            Headers.START_MEASURED_DEPTH: start_measured_depth,
            Headers.END_MEASURED_DEPTH: end_measured_depth,
            Headers.TUBING_MEASURED_DEPTH: measured_depth_,
            Headers.TRUE_VERTICAL_DEPTH: true_vertical_depth,
        }
    )


def insert_missing_segments(df_tubing_segments: pd.DataFrame, well_name: str | None) -> pd.DataFrame:
    """Create segments for inactive cells.

    Sometimes inactive cells have no segments.
    It is required to create segments for these cells to get the scaling factor correct.
    Inactive cells are indicated by segments starting at measured depth deeper than the end of the previous cell.

    Args:
        df_tubing_segments: Must contain start and end measured depth.
        well_name: Name of well.

    Returns:
        DataFrame with the gaps filled.

    Raises:
        CompletorError: If the Schedule file is missing data for one or more branches in the case file.
    """
    if df_tubing_segments.empty:
        raise CompletorError(
            "Schedule file is missing data for one or more branches defined in the case file. "
            f"Please check the data for well {well_name}."
        )
    df_tubing_segments.sort_values(by=[Headers.START_MEASURED_DEPTH], inplace=True)
    # Add column to indicate original segment.
    df_tubing_segments[Headers.SEGMENT_DESC] = Headers.ORIGINAL_SEGMENT
    end_measured_depth = df_tubing_segments[Headers.END_MEASURED_DEPTH].to_numpy()
    # Get start_measured_depth and start from segment 2 and add the last item to be the last end_measured_depth.
    start_measured_depth = np.append(
        df_tubing_segments[Headers.START_MEASURED_DEPTH].to_numpy()[1:], end_measured_depth[-1]
    )
    # Find rows where start_measured_depth > end_measured_depth.
    missing_index = np.argwhere(start_measured_depth > end_measured_depth).flatten()
    # Proceed only if there are missing indexes.
    if missing_index.size == 0:
        return df_tubing_segments
    # Shift one row down because we move it up one row.
    missing_index += 1
    df_copy = df_tubing_segments.iloc[missing_index, :].copy(deep=True)
    # New start measured depth is the previous segment end measured depth.
    df_copy[Headers.START_MEASURED_DEPTH] = df_tubing_segments[Headers.END_MEASURED_DEPTH].to_numpy()[missing_index - 1]
    df_copy[Headers.END_MEASURED_DEPTH] = df_tubing_segments[Headers.START_MEASURED_DEPTH].to_numpy()[missing_index]
    df_copy[Headers.SEGMENT_DESC] = [Headers.ADDITIONAL_SEGMENT] * df_copy.shape[0]
    # Combine the dataframes.
    df_tubing_segments = pd.concat([df_tubing_segments, df_copy])
    df_tubing_segments = df_tubing_segments.sort_values(by=[Headers.START_MEASURED_DEPTH])
    return df_tubing_segments.reset_index(drop=True)


def completion_index(df_completion: pd.DataFrame, start: float, end: float) -> tuple[int, int]:
    """Find the indices in the completion DataFrame of start and end measured depth.

    Args:
        df_completion: Must contain start and end measured depth.
        start: Start measured depth.
        end: End measured depth.

    Returns:
        Indices - Tuple of int.
    """
    start_md = df_completion[Headers.START_MEASURED_DEPTH].to_numpy()
    end_md = df_completion[Headers.END_MEASURED_DEPTH].to_numpy()
    _start = np.argwhere((start_md <= start) & (end_md > start)).flatten()
    _end = np.argwhere((start_md < end) & (end_md >= end)).flatten()
    if _start.size == 0 or _end.size == 0:
        # completion index not found then give negative value for both
        return -1, -1
    return int(_start[0]), int(_end[0])


def get_completion(
    start: float, end: float, df_completion: pd.DataFrame, joint_length: float
) -> tuple[float, float, float, float, float, float, float]:
    """Get information from the completion.

    Args:
        start: Start measured depth of the segment.
        end: End measured depth of the segment.
        df_completion: COMPLETION table that must contain columns: `STARTMD`, `ENDMD`, `NVALVEPERJOINT`,
            `INNER_DIAMETER`, `OUTER_DIAMETER`, `ROUGHNESS`, `DEVICETYPE`, `DEVICENUMBER`, and `ANNULUS_ZONE`.
        joint_length: Length of a joint.

    Returns:
        The number of devices, device type, device number, inner diameter, outer diameter, roughness, annulus zone.

    Raises:
        ValueError:
            If the completion is not defined from start to end.
            If outer diameter is smaller than inner diameter.
            If the completion data contains illegal / invalid rows.
            If information class is None.
    """

    start_completion = df_completion[Headers.START_MEASURED_DEPTH].to_numpy()
    end_completion = df_completion[Headers.END_MEASURED_DEPTH].to_numpy()
    idx0, idx1 = completion_index(df_completion, start, end)

    if idx0 == -1 or idx1 == -1:
        well_name = df_completion[Headers.WELL].iloc[0]
        log_and_raise_exception(f"No completion is defined on well {well_name} from {start} to {end}.")

    indices = np.arange(idx0, idx1 + 1)
    lengths = np.minimum(end_completion[indices], end) - np.maximum(start_completion[indices], start)
    if (lengths <= 0).any():
        # _ = "equals" if length == 0 else "less than"
        # _ = np.where(lengths == 0, "equals", 0)
        # _2 = np.where(lengths < 0, "less than", 0)
        # logger.warning(
        #     f"Start depth less than or equals to stop depth,
        #     for {df_completion[Headers.START_MEASURED_DEPTH][indices][warning_mask]}"
        # )
        logger.warning("Depths are incongruent.")
    number_of_devices = np.sum((lengths / joint_length) * df_completion[Headers.VALVES_PER_JOINT].to_numpy()[indices])

    mask = lengths > shift_array(lengths, 1, fill_value=0)
    inner_diameter = df_completion[Headers.INNER_DIAMETER].to_numpy()[indices][mask]
    outer_diameter = df_completion[Headers.OUTER_DIAMETER].to_numpy()[indices][mask]
    roughness = df_completion[Headers.ROUGHNESS].to_numpy()[indices][mask]
    if (inner_diameter > outer_diameter).any():
        raise ValueError("Check screen/tubing and well/casing ID in case file.")
    outer_diameter = (outer_diameter**2 - inner_diameter**2) ** 0.5
    device_type = df_completion[Headers.DEVICE_TYPE].to_numpy()[indices][mask]
    device_number = df_completion[Headers.DEVICE_NUMBER].to_numpy()[indices][mask]
    annulus_zone = df_completion[Headers.ANNULUS_ZONE].to_numpy()[indices][mask]

    return (
        number_of_devices,
        device_type[-1],
        device_number[-1],
        inner_diameter[-1],
        outer_diameter[-1],
        roughness[-1],
        annulus_zone[-1],
    )


def complete_the_well(
    df_tubing_segments: pd.DataFrame, df_completion: pd.DataFrame, joint_length: float
) -> pd.DataFrame:
    """Complete the well with the user completion.

    Args:
        df_tubing_segments: Output from function create_tubing_segments.
        df_completion: Output from define_annulus_zone.
        joint_length: Length of a joint.

    Returns:
        Well information.
    """
    number_of_devices = []
    device_type = []
    device_number = []
    inner_diameter = []
    outer_diameter = []
    roughness = []
    annulus_zone = []

    start = df_tubing_segments[Headers.START_MEASURED_DEPTH].to_numpy()
    end = df_tubing_segments[Headers.END_MEASURED_DEPTH].to_numpy()

    # loop through the cells
    for i in range(df_tubing_segments.shape[0]):
        indices = [np.array(completion_index(df_completion, s, e)) for s, e in zip(start, end)]

        if any(idx0 == -1 or idx1 == -1 for idx0, idx1 in indices):
            well_name = df_completion[Headers.WELL].iloc[0]
            log_and_raise_exception(f"No completion is defined on well {well_name} from {start} to {end}.")

        completion_data = get_completion(start[i], end[i], df_completion, joint_length)
        number_of_devices.append(completion_data[0])
        device_type.append(completion_data[1])
        device_number.append(completion_data[2])
        inner_diameter.append(completion_data[3])
        outer_diameter.append(completion_data[4])
        roughness.append(completion_data[5])
        annulus_zone.append(completion_data[6])

    df_well = pd.DataFrame(
        {
            Headers.TUBING_MEASURED_DEPTH: df_tubing_segments[Headers.TUBING_MEASURED_DEPTH].to_numpy(),
            Headers.TRUE_VERTICAL_DEPTH: df_tubing_segments[Headers.TRUE_VERTICAL_DEPTH].to_numpy(),
            Headers.LENGTH: end - start,
            Headers.SEGMENT_DESC: df_tubing_segments[Headers.SEGMENT_DESC].to_numpy(),
            Headers.NUMBER_OF_DEVICES: number_of_devices,
            Headers.DEVICE_NUMBER: device_number,
            Headers.DEVICE_TYPE: device_type,
            Headers.INNER_DIAMETER: inner_diameter,
            Headers.OUTER_DIAMETER: outer_diameter,
            Headers.ROUGHNESS: roughness,
            Headers.ANNULUS_ZONE: annulus_zone,
        }
    )

    # lumping segments
    df_well = lumping_segments(df_well)

    # create scaling factor
    df_well[Headers.SCALE_FACTOR] = np.where(
        df_well[Headers.NUMBER_OF_DEVICES] > 0.0, -1.0 / df_well[Headers.NUMBER_OF_DEVICES], 0.0
    )
    return df_well


def lumping_segments(df_well: pd.DataFrame) -> pd.DataFrame:
    """Lump additional segments to the original segments.

    This only applies if the additional segments have an annulus zone.

    Args:
        df_well: Must contain data on annulus zone, number of devices and the segments descending.

    Returns:
        Updated well information.
    """
    number_of_devices = df_well[Headers.NUMBER_OF_DEVICES].to_numpy()
    annulus_zone = df_well[Headers.ANNULUS_ZONE].to_numpy()
    segments_descending = df_well[Headers.SEGMENT_DESC].to_numpy()
    number_of_rows = df_well.shape[0]
    for i in range(number_of_rows):
        if segments_descending[i] != Headers.ADDITIONAL_SEGMENT:
            continue

        # only additional segments
        if annulus_zone[i] > 0:
            # meaning only annular zones
            # compare it to the segment before and after
            been_lumped = False
            if i - 1 >= 0 and not been_lumped and annulus_zone[i] == annulus_zone[i - 1]:
                # compare it to the segment before
                number_of_devices[i - 1] = number_of_devices[i - 1] + number_of_devices[i]
                been_lumped = True
            if i + 1 < number_of_rows and not been_lumped and annulus_zone[i] == annulus_zone[i + 1]:
                # compare it to the segment after
                number_of_devices[i + 1] = number_of_devices[i + 1] + number_of_devices[i]
        # update the number of devices to 0 for this segment
        # because it is lumped to others
        # and it is 0 if it has no annulus zone
        number_of_devices[i] = 0.0
    df_well[Headers.NUMBER_OF_DEVICES] = number_of_devices
    # from now on it is only original segment
    df_well = df_well[df_well[Headers.SEGMENT_DESC] == Headers.ORIGINAL_SEGMENT].copy()
    # reset index after filter
    return df_well.reset_index(drop=True, inplace=False)


def get_device(df_well: pd.DataFrame, df_device: pd.DataFrame, device_type: str) -> pd.DataFrame:
    """Get device characteristics.

    Args:
        df_well: Must contain device type, device number, and the scaling factor.
        df_device: Device table.
        device_type: Device type. `AICD`, `ICD`, `DAR`, `VALVE`, `AICV`, `ICV`.

    Returns:
        Updated well information with device characteristics.

    Raises:
        ValueError: If missing device type in input files.
    """
    columns = [Headers.DEVICE_TYPE, Headers.DEVICE_NUMBER]
    try:
        df_well = pd.merge(df_well, df_device, how="left", on=columns)
    except KeyError as err:
        if f"'{Headers.DEVICE_TYPE}'" in str(err):
            raise ValueError(f"Missing keyword 'DEVICETYPE {device_type}' in input files.") from err
        raise err
    if device_type == Content.VALVE:
        # rescale the Cv
        # because no scaling factor in WELL_SEGMENTS_VALVE
        df_well[Headers.FLOW_COEFFICIENT] = -df_well[Headers.FLOW_COEFFICIENT] / df_well[Headers.SCALE_FACTOR]
    elif device_type == Content.DENSITY_ACTIVATED_RECOVERY:
        # rescale the Cv
        # because no scaling factor in WELL_SEGMENTS_VALVE
        df_well[Headers.FLOW_COEFFICIENT] = -df_well[Headers.FLOW_COEFFICIENT] / df_well[Headers.SCALE_FACTOR]
    return df_well


def correct_annulus_zone(df_well: pd.DataFrame) -> pd.DataFrame:
    """Correct the annulus zone.

    If there are no connections to the tubing in the annulus zone, then there is no annulus zone.

    Args:
        df_well: Must contain annulus zone, number of devices, and device type.

    Returns:
        Updated DataFrame with corrected annulus zone.
    """
    zones = df_well[Headers.ANNULUS_ZONE].unique()
    for zone in zones:
        if zone == 0:
            continue
        df_zone = df_well[df_well[Headers.ANNULUS_ZONE] == zone]
        df_zone_device = df_zone[
            (df_zone[Headers.NUMBER_OF_DEVICES].to_numpy() > 0)
            | (df_zone[Headers.DEVICE_TYPE].to_numpy() == Content.PERFORATED)
        ]
        if df_zone_device.shape[0] == 0:
            df_well[Headers.ANNULUS_ZONE].replace(zone, 0, inplace=True)
    return df_well


def connect_cells_to_segments(
    df_well: pd.DataFrame, df_reservoir: pd.DataFrame, df_tubing_segments: pd.DataFrame, method: Method
) -> pd.DataFrame:
    """Connect cells to segments.

    Args:
        df_well: Segment table. Must contain tubing measured depth.
        df_reservoir: COMPLETION_SEGMENTS table. Must contain start and end measured depth.
        df_tubing_segments: Tubing segment dataframe. Must contain start and end measured depth.
        method: Segmentation method indicator. Must be one of 'user', 'fix', 'welsegs', or 'cells'.

    Returns:
        Merged DataFrame.
    """
    # Calculate mid cell measured depth
    df_reservoir[Headers.MEASURED_DEPTH] = (
        df_reservoir[Headers.START_MEASURED_DEPTH] + df_reservoir[Headers.END_MEASURED_DEPTH]
    ) / 2
    if method == Method.USER:
        # Ensure that tubing segment boundaries as described in the case file are honored.
        # Associate reservoir cells with tubing segment midpoints using markers.
        df_reservoir[Headers.MARKER] = np.full(df_reservoir.shape[0], 0)
        df_well[Headers.MARKER] = np.arange(df_well.shape[0]) + 1

        start_measured_depths = df_tubing_segments[Headers.START_MEASURED_DEPTH]
        end_measured_depths = df_tubing_segments[Headers.END_MEASURED_DEPTH]

        marker = 1
        for start, end in zip(start_measured_depths, end_measured_depths):
            df_reservoir.loc[df_reservoir[Headers.MEASURED_DEPTH].between(start, end), Headers.MARKER] = marker
            marker += 1

        return df_reservoir.merge(df_well, on=Headers.MARKER).drop(Headers.MARKER, axis=1)

    return pd.merge_asof(
        left=df_reservoir,
        right=df_well,
        left_on=Headers.MEASURED_DEPTH,
        right_on=Headers.TUBING_MEASURED_DEPTH,
        direction="nearest",
    )
