"""Completion."""

from __future__ import annotations

from typing import Literal, TypeAlias, overload

import numpy as np
import numpy.typing as npt
import pandas as pd

from completor.constants import Completion, Method
from completor.logger import logger
from completor.read_schedule import fix_compsegs, fix_welsegs
from completor.utils import abort, as_data_frame, log_and_raise_exception

# Use more precise type information, if possible
MethodType: TypeAlias = Literal["cells", "user", "fix", "welsegs"] | Method
DeviceType: TypeAlias = Literal["AICD", "ICD", "DAR", "VALVE", "AICV", "ICV"]


class Information:
    """Holds information from ``get_completion``."""

    def __init__(
        self,
        number_of_devices: float | list[float] | None = None,
        device_type: DeviceType | list[DeviceType] | None = None,
        device_number: int | list[int] | None = None,
        inner_diameter: float | list[float] | None = None,
        outer_diameter: float | list[float] | None = None,
        roughness: float | list[float] | None = None,
        annulus_zone: int | list[int] | None = None,
    ):
        """Initialize Information class."""
        self.number_of_devices = number_of_devices
        self.device_type = device_type
        self.device_number = device_number
        self.inner_diameter = inner_diameter
        self.outer_diameter = outer_diameter
        self.roughness = roughness
        self.annulus_zone = annulus_zone

    def __iadd__(self, other: Information):
        """Implement value-wise addition between two Information instances."""
        attributes = [
            attribute for attribute in dir(self) if not attribute.startswith("__") and not attribute.endswith("__")
        ]
        for attribute in attributes:
            value = getattr(self, attribute)
            if not isinstance(value, list):
                if value is None:
                    value = []
                else:
                    value = [value]
                setattr(self, attribute, value)

            value = getattr(other, attribute)
            attr: list = getattr(self, attribute)
            if attr is None:
                attr = []
            if isinstance(value, list):
                attr.extend(value)
            else:
                attr.append(value)
        return self


def well_trajectory(df_well_segments_header: pd.DataFrame, df_well_segments_content: pd.DataFrame) -> pd.DataFrame:
    """Create trajectory relation between measured depth and true vertical depth.

    Well segments must be defined with absolute values (ABS) and not incremental (INC).

    Args:
        df_well_segments_header: First record of well segments.
        df_well_segments_content: Second record of well segments.

    Return:
        Measured depth versus true vertical depth.

    """
    measured_depth = df_well_segments_content["TUBINGMD"].to_numpy()
    measured_depth = np.insert(measured_depth, 0, df_well_segments_header["SEGMENTMD"].iloc[0])
    true_vertical_depth = df_well_segments_content["TUBINGTVD"].to_numpy()
    true_vertical_depth = np.insert(true_vertical_depth, 0, df_well_segments_header["SEGMENTTVD"].iloc[0])
    df_measured_true_vertical_depth = as_data_frame({"MD": measured_depth, "TVD": true_vertical_depth})
    # sort based on md
    df_measured_true_vertical_depth = df_measured_true_vertical_depth.sort_values(by=["MD", "TVD"])
    # reset index after sorting
    return df_measured_true_vertical_depth.reset_index(drop=True)


def define_annulus_zone(df_completion: pd.DataFrame) -> pd.DataFrame:
    """Define the annulus zone from the COMPLETION.

    Args:
        df_completion: Must contain the columns `STARTMD`, `ENDMD`, and `ANNULUS`.

    Returns:
        Updated COMPLETION with additional column ``ANNULUS_ZONE``

    Raise:
        ValueError: If the dimension is not correct

    The DataFrame format of df_completion is shown in
    :ref:`create_wells.CreateWells.select_well <df_completion>`.
    """
    # define annular zone
    start_measured_depth = df_completion[Completion.START_MD].iloc[0]
    end_measured_depth = df_completion[Completion.END_MD].iloc[-1]
    gravel_pack_location = df_completion[df_completion[Completion.ANNULUS] == "GP"][["STARTMD", "ENDMD"]].to_numpy()
    packer_location = df_completion[df_completion[Completion.ANNULUS] == "PA"][["STARTMD", "ENDMD"]].to_numpy()
    # update df_completion by removing PA rows
    df_completion = df_completion[df_completion[Completion.ANNULUS] != "PA"].copy()
    # reset index after filter
    df_completion.reset_index(drop=True, inplace=True)
    annulus_content = df_completion[Completion.ANNULUS].to_numpy()
    df_completion[Completion.ANNULUS_ZONE] = 0
    if "OA" in annulus_content:
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
        df_annulus = as_data_frame(
            {Completion.START_MD: start_bound, Completion.END_MD: end_bound, Completion.ANNULUS_ZONE: annulus_zone}
        )

        annulus_zone = np.full(df_completion.shape[0], 0)
        for idx in range(df_completion.shape[0]):
            start_measured_depth = df_completion["STARTMD"].iloc[idx]
            end_measured_depth = df_completion["ENDMD"].iloc[idx]
            idx0, idx1 = completion_index(df_annulus, start_measured_depth, end_measured_depth)
            if idx0 != idx1 or idx0 == -1:
                raise ValueError("Check Define Annulus Zone")
            annulus_zone[idx] = df_annulus["ANNULUS_ZONE"].iloc[idx0]
        df_completion["ANNULUS_ZONE"] = annulus_zone
    df_completion["ANNULUS_ZONE"] = df_completion["ANNULUS_ZONE"].astype(np.int64)
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
    method: MethodType = ...,
    segment_length: float | str = ...,
    minimum_segment_length: float = 0.0,
) -> pd.DataFrame: ...


def create_tubing_segments(
    df_reservoir: pd.DataFrame,
    # Technically, df_completion is only required for SegmentCreationMethod.USER
    df_completion: pd.DataFrame,
    df_measured_depth_true_vertical_depth: pd.DataFrame,
    method: MethodType = Method.CELLS,
    segment_length: float | str = 0.0,
    minimum_segment_length: float = 0.0,
) -> pd.DataFrame:
    """Create segments in the tubing layer.

    Args:
        df_reservoir: Must contain `STARTMD` and `ENDMD`.
        df_completion: Must contain `ANNULUS`, ``STARTMD`, `ENDMD`, `ANNULUS_ZONE`,
            and no packer content in the completion.
        df_measured_depth_true_vertical_depth: Must contain `MD` and `TVD`.
        method: Method for segmentation. Defaults to cells.
        segment_length: Only if fix is selected in the method.
        minimum_segment_length: User input minimum segment length.

    Segmentation methods:
        cells - Create one segment per cell.
        user - Create segment based on the completion definition.
        fix - Create segment based on a fixed interval.
        well_segments - Create segment based on `WELSEGS` keyword.

    Returns:
        A dataframe with columns `STARTMD`, `ENDMD`, `TUB_MD`, `TUB_TVD`.

    Raises:
        ValueError: If the method is unknown.

    """
    start_measured_depth: npt.NDArray[np.float64]
    end_measured_depth: npt.NDArray[np.float64]
    if method == Method.CELLS:
        # Create the tubing layer one cell one segment while honoring df_reservoir["SEGMENT"]
        start_measured_depth = df_reservoir["STARTMD"].to_numpy()
        end_measured_depth = df_reservoir["ENDMD"].to_numpy()
        if "SEGMENT" in df_reservoir.columns:
            if not df_reservoir["SEGMENT"].isin(["1*"]).any():
                create_start_measured_depths = []
                create_end_measured_depths = []
                create_start_measured_depths.append(df_reservoir["STARTMD"].iloc[0])
                current_segment = df_reservoir["SEGMENT"].iloc[0]
                for i in range(1, len(df_reservoir["SEGMENT"])):
                    if df_reservoir["SEGMENT"].iloc[i] != current_segment:
                        create_end_measured_depths.append(df_reservoir["ENDMD"].iloc[i - 1])
                        create_start_measured_depths.append(df_reservoir["STARTMD"].iloc[i])
                        current_segment = df_reservoir["SEGMENT"].iloc[i]
                create_end_measured_depths.append(df_reservoir["ENDMD"].iloc[-1])
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
        start_measured_depth = df_temp["STARTMD"].to_numpy()
        end_measured_depth = df_temp["ENDMD"].to_numpy()
        # Fix the start and end.
        start_measured_depth[0] = max(df_reservoir["STARTMD"].iloc[0], float(start_measured_depth[0]))
        end_measured_depth[-1] = min(df_reservoir["ENDMD"].iloc[-1], float(end_measured_depth[-1]))
        if start_measured_depth[0] >= end_measured_depth[0]:
            start_measured_depth = np.delete(start_measured_depth, 0)
            end_measured_depth = np.delete(end_measured_depth, 0)
        if start_measured_depth[-1] >= end_measured_depth[-1]:
            start_measured_depth = np.delete(start_measured_depth, -1)
            end_measured_depth = np.delete(end_measured_depth, -1)
    elif method == Method.FIX:
        # Create tubing layer with fix interval according to the user input in the case file keyword SEGMENTLENGTH.
        min_measured_depth = df_reservoir["STARTMD"].min()
        max_measured_depth = df_reservoir["ENDMD"].max()
        if not isinstance(segment_length, (float, int)):
            raise ValueError(f"Segment length must be a number, when using method fix (was {segment_length}).")
        start_measured_depth = np.arange(min_measured_depth, max_measured_depth, segment_length)
        end_measured_depth = start_measured_depth + segment_length
        # Update the end point of the last segment.
        end_measured_depth[-1] = min(float(end_measured_depth[-1]), max_measured_depth)
    elif method == Method.WELSEGS:
        # Create the tubing layer from segment measured depths in the WELSEGS keyword that are missing from COMPSEGS.
        # WELSEGS segment depths are collected in the df_measured_depth_true_vertical_depth dataframe, which is available here.
        # Completor interprets WELSEGS depths as segment midpoint depths.
        # Obtain the well_segments segment midpoint depth.
        well_segments = df_measured_depth_true_vertical_depth["MD"].to_numpy()
        end_welsegs_depth = 0.5 * (well_segments[:-1] + well_segments[1:])
        # The start of the very first segment in any branch is the actual startMD of the first segment.
        start_welsegs_depth = np.insert(end_welsegs_depth[:-1], 0, well_segments[0], axis=None)
        start_compsegs_depth: npt.NDArray[np.float64] = df_reservoir["STARTMD"].to_numpy()
        end_compsegs_depth = df_reservoir["ENDMD"].to_numpy()
        # If there are gaps in compsegs and there are well_segments segments that fit in the gaps,
        # insert well_segments segments into the compsegs gaps.
        gaps_compsegs = start_compsegs_depth[1:] - end_compsegs_depth[:-1]
        # Indices of gaps in compsegs.
        indices_gaps = np.nonzero(gaps_compsegs)
        # Start of the gaps.
        start_gaps_depth = end_compsegs_depth[indices_gaps[0]]
        # End of the gaps.
        end_gaps_depth = start_compsegs_depth[indices_gaps[0] + 1]
        # Check the gaps between COMPSEGS and fill it out with WELSEGS.
        start = np.abs(start_welsegs_depth[:, np.newaxis] - start_gaps_depth).argmin(axis=0)
        end = np.abs(end_welsegs_depth[:, np.newaxis] - end_gaps_depth).argmin(axis=0)
        welsegs_to_add = np.setxor1d(start_welsegs_depth[start], end_welsegs_depth[end])
        start_welsegs_outside = start_welsegs_depth[np.argwhere(start_welsegs_depth < start_compsegs_depth[0])]
        end_welsegs_outside = end_welsegs_depth[np.argwhere(end_welsegs_depth > end_compsegs_depth[-1])]
        welsegs_to_add = np.append(welsegs_to_add, start_welsegs_outside)
        welsegs_to_add = np.append(welsegs_to_add, end_welsegs_outside)
        # Find well_segments start and end in gaps.
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
    # estimate TVD
    true_vertical_depth = np.interp(
        measured_depth_,
        df_measured_depth_true_vertical_depth["MD"].to_numpy(),
        df_measured_depth_true_vertical_depth["TVD"].to_numpy(),
    )
    # create data frame
    return as_data_frame(
        {
            "STARTMD": start_measured_depth,
            "ENDMD": end_measured_depth,
            "TUB_MD": measured_depth_,
            "TUB_TVD": true_vertical_depth,
        }
    )


def insert_missing_segments(df_tubing_segments: pd.DataFrame, well_name: str | None) -> pd.DataFrame:
    """Create segments for inactive cells.

    Sometimes inactive cells have no segments.
    It is required to create segments for these cells to get the scaling factor correct.
    Inactive cells are indicated
    if there are segments starting at measured depth deeper than the end measured depth of the previous cell.

    Args:
        df_tubing_segments: Must contain column `STARTMD` and `ENDMD`.
        well_name: Name of well.

    Returns:
        Updated dataframe if missing cells are found.

    Raises:
        SystemExit: If the Schedule file is missing data for one or more branches in the case file.

    """
    if df_tubing_segments.empty:
        raise abort(
            "Schedule file is missing data for one or more branches defined in the "
            f"case file. Please check the data for Well {well_name}."
        )
    # sort the data frame based on STARTMD
    df_tubing_segments.sort_values(by=["STARTMD"], inplace=True)
    # add column to indicate original segment
    df_tubing_segments["SEGMENT_DESC"] = ["OriginalSegment"] * df_tubing_segments.shape[0]
    end_measured_depth = df_tubing_segments["ENDMD"].to_numpy()
    # get start_measured_depth and start from segment 2 and add the last item to be the last end_measured_depth
    start_measured_depth = np.append(df_tubing_segments["STARTMD"].to_numpy()[1:], end_measured_depth[-1])
    # find rows where start_measured_depth > end_measured_depth
    missing_index = np.argwhere(start_measured_depth > end_measured_depth).flatten()
    # proceed only if there are missing index
    if missing_index.size == 0:
        return df_tubing_segments
    # shift one row down because we move it up one row
    missing_index += 1
    df_copy = df_tubing_segments.iloc[missing_index, :].copy(deep=True)
    # new start measured depth is the previous segment end measured depth
    df_copy["STARTMD"] = df_tubing_segments["ENDMD"].to_numpy()[missing_index - 1]
    df_copy["ENDMD"] = df_tubing_segments["STARTMD"].to_numpy()[missing_index]
    df_copy["SEGMENT_DESC"] = ["AdditionalSegment"] * df_copy.shape[0]
    # combine the two data frame
    df_tubing_segments = pd.concat([df_tubing_segments, df_copy])
    df_tubing_segments.sort_values(by=["STARTMD"], inplace=True)
    df_tubing_segments.reset_index(drop=True, inplace=True)
    return df_tubing_segments


def completion_index(df_completion: pd.DataFrame, start: float, end: float) -> tuple[int, int]:
    """Find the indices in the completion DataFrame of start measured depth and end measured depth.

    Args:
        df_completion: Must contain `STARTMD` and `ENDMD`.
        start: Start measured depth.
        end: End measured depth.

    Returns:
        Indices of the start and end depths.

    """
    start_measured_depth = df_completion[Completion.START_MD].to_numpy()
    end_measured_depth = df_completion[Completion.END_MD].to_numpy()
    _start = np.argwhere((start_measured_depth <= start) & (end_measured_depth > start)).flatten()
    _end = np.argwhere((start_measured_depth < end) & (end_measured_depth >= end)).flatten()
    if _start.size == 0 or _end.size == 0:
        # completion index not found then give negative value for both
        return -1, -1
    return int(_start[0]), int(_end[0])


def get_completion(start: float, end: float, df_completion: pd.DataFrame, joint_length: float) -> Information:
    """Get information from the completion.

    Args:
        start: Start measured depth of the segment.
        end: End measured depth of the segment.
        df_completion: COMPLETION table that must contain columns: `STARTMD`, `ENDMD`, `NVALVEPERJOINT`, `INNER_ID`,
        `OUTER_ID`, `ROUGHNESS`, `DEVICETYPE`, `DEVICENUMBER`, and `ANNULUS_ZONE`.
        joint_length: Length of a joint.

    Returns:
        Instance of Information.

    Raises:
        ValueError:
            If the completion is not defined from start to end.
            If outer diameter is smaller than inner diameter.
            If the completion data contains illegal / invalid rows.
            If information class is None.

    """
    information = None
    device_type = None
    device_number = None
    inner_diameter = None
    outer_diameter = None
    roughness = None
    annulus_zone = None

    start_completion = df_completion[Completion.START_MD].to_numpy()
    end_completion = df_completion[Completion.END_MD].to_numpy()
    idx0, idx1 = completion_index(df_completion, start, end)

    if idx0 == -1 or idx1 == -1:
        well_name = df_completion["WELL"].iloc[0]
        log_and_raise_exception(f"No completion is defined on well {well_name} from {start} to {end}.")

    # previous length start with 0
    prev_length = 0.0
    num_device = 0.0

    for completion_idx in range(idx0, idx1 + 1):
        completion_length = min(end_completion[completion_idx], end) - max(start_completion[completion_idx], start)
        if completion_length <= 0:
            _ = "equals" if completion_length == 0 else "less than"
            logger.warning(
                f"Start depth {_} stop depth, in row {completion_idx}, "
                f"for well {df_completion[Completion.WELL][completion_idx]}"
            )
        # calculate cumulative parameter
        num_device += (completion_length / joint_length) * df_completion[Completion.NUM_VALVES_PER_JOINT].iloc[
            completion_idx
        ]

        if completion_length > prev_length:
            # get well geometry
            inner_diameter = df_completion[Completion.INNER_ID].iloc[completion_idx]
            outer_diameter = df_completion[Completion.OUTER_ID].iloc[completion_idx]
            roughness = df_completion[Completion.ROUGHNESS].iloc[completion_idx]
            if outer_diameter > inner_diameter:
                outer_diameter = (outer_diameter**2 - inner_diameter**2) ** 0.5
            else:
                raise ValueError("Check screen/tubing and well/casing ID in case file.")

            # get device information
            device_type = df_completion[Completion.DEVICE_TYPE].iloc[completion_idx]
            device_number = df_completion[Completion.DEVICE_NUMBER].iloc[completion_idx]
            # other information
            annulus_zone = df_completion[Completion.ANNULUS_ZONE].iloc[completion_idx]
            # set prev_length to this segment
            prev_length = completion_length

        if all(
            x is not None for x in [device_type, device_number, inner_diameter, outer_diameter, roughness, annulus_zone]
        ):
            information = Information(
                num_device, device_type, device_number, inner_diameter, outer_diameter, roughness, annulus_zone
            )
        else:
            # I.e. if completion_length > prev_length never happens
            raise ValueError(
                f"The completion data for well '{df_completion[Completion.WELL][completion_idx]}' "
                "contains illegal / invalid row(s). "
                "Please check their start mD / end mD columns, and ensure that they start before they end."
            )
    if information is None:
        raise ValueError(
            f"idx0 == idx1 + 1 (idx0={idx0}). "
            "For the time being, the reason is unknown. "
            "Please reach out to the Equinor Inflow Control Team if you encounter this."
        )
    return information


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
    start = df_tubing_segments[Completion.START_MD].to_numpy()
    end = df_tubing_segments[Completion.END_MD].to_numpy()
    information = Information()
    # loop through the cells
    for i in range(df_tubing_segments.shape[0]):
        information += get_completion(start[i], end[i], df_completion, joint_length)

    df_well = as_data_frame(
        {
            "TUB_MD": df_tubing_segments["TUB_MD"].to_numpy(),
            "TUB_TVD": df_tubing_segments["TUB_TVD"].to_numpy(),
            "LENGTH": end - start,
            "SEGMENT_DESC": df_tubing_segments["SEGMENT_DESC"].to_numpy(),
            "NDEVICES": information.number_of_devices,
            "DEVICENUMBER": information.device_number,
            "DEVICETYPE": information.device_type,
            "INNER_DIAMETER": information.inner_diameter,
            "OUTER_DIAMETER": information.outer_diameter,
            "ROUGHNESS": information.roughness,
            "ANNULUS_ZONE": information.annulus_zone,
        }
    )

    # lumping segments
    df_well = lumping_segments(df_well)

    # create scaling factor
    df_well["SCALINGFACTOR"] = np.where(df_well["NDEVICES"] > 0.0, -1.0 / df_well["NDEVICES"], 0.0)
    return df_well


def lumping_segments(df_well: pd.DataFrame) -> pd.DataFrame:
    """Lump additional segments to the original segments.

    This only applies if the additional segments have an annulus zone.

    Args:
        df_well: Must contain `ANNULUS_ZONE`, `NDEVICES`, and `SEGMENT_DESC`

    Returns:
        Updated well information.

    """
    number_of_devices = df_well["NDEVICES"].to_numpy()
    annulus_zone = df_well["ANNULUS_ZONE"].to_numpy()
    segments_descending = df_well["SEGMENT_DESC"].to_numpy()
    number_of_rows = df_well.shape[0]
    for i in range(number_of_rows):
        if segments_descending[i] != "AdditionalSegment":
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
    df_well["NDEVICES"] = number_of_devices
    # from now on it is only original segment
    df_well = df_well[df_well["SEGMENT_DESC"] == "OriginalSegment"].copy()
    # reset index after filter
    return df_well.reset_index(drop=True, inplace=False)


def get_device(df_well: pd.DataFrame, df_device: pd.DataFrame, device_type: DeviceType) -> pd.DataFrame:
    """Get device characteristics.

    Args:
        df_well: Must contain columns `DEVICETYPE`, `DEVICENUMBER`, and `SCALINGFACTOR`.
        df_device: Device table.
        device_type: Device type, in `AICD`, `ICD`, `DAR`, `VALVE`,`AICV`, `ICV`.

    Returns:
        Updated well information with device characteristics.

    Raises:
        ValueError: If `DEVICETYPE` keyword is missing in input files.

    """
    columns = ["DEVICETYPE", "DEVICENUMBER"]
    try:
        df_well = pd.merge(df_well, df_device, how="left", on=columns)
    except KeyError as err:
        if "'DEVICETYPE'" in str(err):
            raise ValueError(f"Missing keyword 'DEVICETYPE {device_type}' in input files.") from err
        raise err
    if device_type == "VALVE":
        # rescale the Cv
        # because no scaling factor in WSEGVALV
        df_well["CV"] = -df_well["CV"] / df_well["SCALINGFACTOR"]
    elif device_type == "DAR":
        # rescale the Cv
        # because no scaling factor in WSEGVALV
        df_well["CV_DAR"] = -df_well["CV_DAR"] / df_well["SCALINGFACTOR"]
    return df_well


def correct_annulus_zone(df_well: pd.DataFrame) -> pd.DataFrame:
    """
    Correct the annulus zone.

    If there are no connections to the tubing in the annulus zone then there is no
    annulus zone.

    Args:
        df_well: Must contain ANNULUS_ZONE, NDEVICES, and DEVICETYPE

    Returns:
        Updated DataFrame with corrected annulus zone

    The DataFrame df_well has the format shown in the following function:
    :ref:`create_wells.CreateWells.complete_the_well <df_well>`.
    """
    zones = df_well["ANNULUS_ZONE"].unique()
    for zone in zones:
        if zone == 0:
            continue
        df_zone = df_well[df_well["ANNULUS_ZONE"] == zone]
        df_zone_device = df_zone[(df_zone["NDEVICES"].to_numpy() > 0) | (df_zone["DEVICETYPE"].to_numpy() == "PERF")]
        if df_zone_device.shape[0] == 0:
            df_well["ANNULUS_ZONE"].replace(zone, 0, inplace=True)
    return df_well


def connect_cells_to_segments(
    df_well: pd.DataFrame, df_reservoir: pd.DataFrame, df_tubing_segments: pd.DataFrame, method: MethodType
) -> pd.DataFrame:
    """
    Connect cells to segments.

    Args:
        df_well: Segment table. Must contain column ``TUB_MD``
        df_reservoir: COMPSEGS table. Must contain columns ``STARTMD`` and ``ENDMD``
        df_tubing_segments: Tubing segment dataframe. Must contain columns ``STARTMD`` and ``ENDMD``.
        method: Segmentation method indicator. Must contain 'user', 'fix', 'welsegs', or 'cells'.


    Returns:
        Merged DataFrame.

    | The DataFrame formats in this function are shown in
    | df_well (:ref:`create_wells.CreateWells.complete_the_well <df_well>`)
    | df_reservoir (:ref:`create_wells.CreateWells.select_well <df_reservoir>`)
    """
    # Calculate mid cell MD
    df_reservoir["MD"] = (df_reservoir["STARTMD"] + df_reservoir["ENDMD"]) * 0.5
    if method == Method.USER:
        df_res = df_reservoir.copy(deep=True)
        df_wel = df_well.copy(deep=True)
        # Ensure that tubing segment boundaries as described in the case file
        # are honored.
        # Associate reservoir cells with tubing segment midpoints using markers
        marker = 1
        df_res["MARKER"] = pd.Series([0 for _ in range(len(df_reservoir.index))])
        df_wel["MARKER"] = pd.Series([x + 1 for x in range(len(df_well.index))])
        for idx in df_wel["TUB_MD"].index:
            start_md = df_tubing_segments["STARTMD"].iloc[idx]
            end_md = df_tubing_segments["ENDMD"].iloc[idx]
            df_res.loc[df_res["MD"].between(start_md, end_md), "MARKER"] = marker
            marker += 1
        # Merge
        tmp = df_res.merge(df_wel, on=["MARKER"])
        return tmp.drop(["MARKER"], axis=1, inplace=False)

    return pd.merge_asof(left=df_reservoir, right=df_well, left_on=["MD"], right_on=["TUB_MD"], direction="nearest")


class WellSchedule:
    """
    A collection of all the active multi-segment wells.

    Attributes:
        msws: Multisegmentet well segments.
        active_wells: The active wells for completor to work on.

    Args:
        active_wells: Active multi-segment wells defined in a case file

    """

    def __init__(self, active_wells: npt.NDArray[np.unicode_] | list[str]):
        """Initialize WellSchedule."""
        self.msws: dict[str, dict] = {}
        self.active_wells = np.array(active_wells)

    def set_welspecs(self, records: list[list[str]]) -> None:
        """
        Convert a WELSPECS record set to a Pandas DataFrame.

        * Sets DataFrame column titles
        * Formats column values
        * Pads missing columns at end of the DataFrame with default values (1*)

        Args:
            recs: A WELSPECS record set

        Returns:
            Record of inactive wells (in ``self.msws``)

        The function creates the class property DataFrame
        ``msws[well_name]['welspecs']`` with the following format:

        .. _welspecs_format:
        .. list-table:: ``msws[well_name]['welspecs']``
           :widths: 10 10
           :header-rows: 1

           * - COLUMNS
             - TYPE
           * - WELL
             - str
           * - GROUP
             - str
           * - I
             - int
           * - J
             - int
           * - BHP_DEPTH
             - float
           * - PHASE
             - str
           * - DR
             - object
           * - FLAG
             - object
           * - SHUT
             - object
           * - CROSS
             - object
           * - PRESSURETABLE
             - object
           * - DENSCAL
             - object
           * - REGION
             - object
           * - ITEM14
             - object
           * - ITEM15
             - object
           * - ITEM16
             - object
           * - ITEM17
             - object

        """
        # make df
        columns = [
            "WELL",
            "GROUP",
            "I",
            "J",
            "BHP_DEPTH",
            "PHASE",
            "DR",
            "FLAG",
            "SHUT",
            "CROSS",
            "PRESSURETABLE",
            "DENSCAL",
            "REGION",
            "ITEM14",
            "ITEM15",
            "ITEM16",
            "ITEM17",
        ]
        ncols = len(columns)
        _records = records[0] + ["1*"] * (ncols - len(records[0]))  # pad with default values (1*)
        df = pd.DataFrame(np.array(_records).reshape((1, ncols)), columns=columns)
        #  datatypes
        df[columns[2:4]] = df[columns[2:4]].astype(np.int64)
        try:
            df[columns[4]] = df[columns[4]].astype(np.float64)
        except ValueError:
            pass
        # welspecs could be for multiple wells - split it
        for well_name in df["WELL"].unique():
            if well_name not in self.msws:
                self.msws[well_name] = {}
            self.msws[well_name]["welspecs"] = df[df["WELL"] == well_name]
            logger.debug("set_welspecs for %s", well_name)

    def handle_compdat(self, recs: list[list[str]]) -> list[list[str]]:
        """
        Convert a COMPDAT record set to a Pandas DataFrame.

        * Sets DataFrame column titles
        * Pads missing values with default values (1*)
        * Sets column data types

        Args:
            recs: Record set of COMPDAT data

        Returns:
            list: Records for inactive wells

        The function creates the class property DataFrame
        msws[well_name]['compdat'] with the following format:

        .. _compdat_format:
        .. list-table:: msws[well_name]['compdat']
           :widths: 10 10
           :header-rows: 1

           * - COLUMNS
             - TYPE
           * - WELL
             - str
           * - I
             - int
           * - J
             - int
           * - K
             - int
           * - K2
             - int
           * - STATUS
             - object
           * - SATNUM
             - object
           * - CF
             - float
           * - DIAM
             - float
           * - KH
             - float
           * - SKIN
             - float
           * - DFACT
             - object
           * - COMPDAT_DIRECTION
             - object
           * - RO
             - float

        """
        well_names = set()  # the active well-names found in this chunk
        remains = []  # the other wells
        for rec in recs:
            well_name = rec[0]
            if well_name in list(self.active_wells):
                well_names.add(well_name)
            else:
                remains.append(rec)
        # make df
        columns = [
            "WELL",
            "I",
            "J",
            "K",
            "K2",
            "STATUS",
            "SATNUM",
            "CF",
            "DIAM",
            "KH",
            "SKIN",
            "DFACT",
            "COMPDAT_DIRECTION",
            "RO",
        ]
        df = pd.DataFrame(recs, columns=columns[0 : len(recs[0])])
        if "RO" in df.columns:
            df["RO"] = df["RO"].fillna("1*")
        for idx in range(len(recs[0]), len(columns)):
            df[columns[idx]] = ["1*"] * len(recs)
        # data types
        df[columns[1:5]] = df[columns[1:5]].astype(np.int64)
        # Change default value '1*' to equivalent float
        df["SKIN"] = df["SKIN"].replace(["1*"], 0.0)
        df[["DIAM", "SKIN"]] = df[["DIAM", "SKIN"]].astype(np.float64)
        # check if CF, KH, and RO are defaulted by the users
        try:
            df[["CF"]] = df[["CF"]].astype(np.float64)
        except ValueError:
            pass
        try:
            df[["KH"]] = df[["KH"]].astype(np.float64)
        except ValueError:
            pass
        try:
            df[["RO"]] = df[["RO"]].astype(np.float64)
        except ValueError:
            pass
        # compdat could be for multiple wells - split it
        for well_name in well_names:
            if well_name not in self.msws:
                self.msws[well_name] = {}
            self.msws[well_name]["compdat"] = df[df["WELL"] == well_name]
            logger.debug("handle_compdat for %s", well_name)
        return remains

    def set_welsegs(self, recs: list[list[str]]) -> str | None:
        """Update WELSEGS for a given well if it is an active well.

        * Pads missing record columns in header and contents with default values
        * Converts header and column records to Pandas DataFrames
        * Sets proper DataFrame column types and titles
        * Converts segment depth specified by INC to ABS using fix_welsegs

        Args:
            recs: Record set of header and contents data

        Returns:
            Name of well if it was updated, or None if it is\
            not in the active_wells list.

        The function creates two DataFrames stored in the tuple variable\
        msws[well_name]['welsegs']. The first tuple element is the welsegs header\
        and the second is the record DataFrame with following formats:

        .. _welsegs_header_format:
        .. list-table:: msws[well_name]['welsegs'][0] - Header
           :widths: 10 10
           :header-rows: 1

           * - COLUMNS
             - TYPE
           * - WELL
             - str
           * - SEGMENTTVD
             - float
           * - SEGMENTMD
             - float
           * - WBVOLUME
             - float
           * - INFOTYPE
             - object
           * - PDROPCOMP
             - object
           * - MPMODEL
             - object
           * - ITEM8
             - object
           * - ITEM9
             - object
           * - ITEM10
             - object
           * - ITEM11
             - object
           * - ITEM12
             - object

        .. _welsegs_content_format:
        .. list-table:: msws[well_name]['welsegs'][1] - Record
           :widths: 10 10
           :header-rows: 1

           * - COLUMNS
             - TYPE
           * - TUBINGSEGMENT
             - int
           * - TUBINGSEGMENT2
             - int
           * - TUBINGBRANCH
             - int
           * - TUBINGOUTLET
             - int
           * - TUBINGMD
             - float
           * - TUBINGTVD
             - float
           * - TUBINGID
             - float
           * - TUBINGROUGHNESS
             - float
           * - CROSS
             - float
           * - VSEG
             - float
           * - ITEM11
             - object
           * - ITEM12
             - object
           * - ITEM13
             - object
           * - ITEM14
             - object
           * - ITEM15
             - object

        """
        well_name = recs[0][0]  # each WELSEGS-chunk is for one well only
        if well_name not in self.active_wells:
            return None

        # make df for header record
        columns = [
            "WELL",
            "SEGMENTTVD",
            "SEGMENTMD",
            "WBVOLUME",
            "INFOTYPE",
            "PDROPCOMP",
            "MPMODEL",
            "ITEM8",
            "ITEM9",
            "ITEM10",
            "ITEM11",
            "ITEM12",
        ]
        ncols = len(columns)
        # pad header with default values (1*)
        header = recs[0] + ["1*"] * (ncols - len(recs[0]))
        dfh = pd.DataFrame(np.array(header).reshape((1, ncols)), columns=columns)
        dfh[columns[1:3]] = dfh[columns[1:3]].astype(np.float64)  # data types

        # make df for data records
        columns = [
            "TUBINGSEGMENT",
            "TUBINGSEGMENT2",
            "TUBINGBRANCH",
            "TUBINGOUTLET",
            "TUBINGMD",
            "TUBINGTVD",
            "TUBINGID",
            "TUBINGROUGHNESS",
            "CROSS",
            "VSEG",
            "ITEM11",
            "ITEM12",
            "ITEM13",
            "ITEM14",
            "ITEM15",
        ]
        ncols = len(columns)
        # pad with default values (1*)
        recs = [rec + ["1*"] * (ncols - len(rec)) for rec in recs[1:]]
        dfr = pd.DataFrame(recs, columns=columns)
        # data types
        dfr[columns[:4]] = dfr[columns[:4]].astype(np.int64)
        dfr[columns[4:7]] = dfr[columns[4:7]].astype(np.float64)
        # fix abs/inc issue with welsegs
        dfh, dfr = fix_welsegs(dfh, dfr)

        # Warn user if the tubing segments' measured depth for a branch
        # is not sorted in ascending order (monotonic)
        for branch_num in dfr["TUBINGBRANCH"].unique():
            if not dfr["TUBINGMD"].loc[dfr["TUBINGBRANCH"] == branch_num].is_monotonic_increasing:
                logger.warning(
                    "The branch %s in well %s contains negative length segments. "
                    "Check the input schedulefile WELSEGS keyword for inconsistencies "
                    "in measured depth (MD) of Tubing layer.",
                    branch_num,
                    well_name,
                )

        if well_name not in self.msws:
            self.msws[well_name] = {}
        self.msws[well_name]["welsegs"] = dfh, dfr
        return well_name

    def set_compsegs(self, recs: list[list[str]]) -> str | None:
        """
        Update COMPSEGS for a well if it is an active well.

        * Pads missing record columns in header and contents with default 1*
        * Converts header and column records to Pandas DataFrames
        * Sets proper DataFrame column types and titles

        Args:
            recs: Record set of header and contents data

        Returns:
            Name of well if it was updated, or None if it is not in active_wells

        The function creates the class property DataFrame
        ``msws[well_name]['compsegs']`` with the following format:

        .. list-table:: ``msws[well_name]['compsegs']``
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
             - object
           * - ENDGRID
             - object
           * - PERFDEPTH
             - object
           * - THERM
             - object
           * - SEGMENT
             - int

        """
        well_name = recs[0][0]  # each COMPSEGS-chunk is for one well only
        if well_name not in self.active_wells:
            return None
        columns = [
            "I",
            "J",
            "K",
            "BRANCH",
            "STARTMD",
            "ENDMD",
            "COMPSEGS_DIRECTION",
            "ENDGRID",
            "PERFDEPTH",
            "THERM",
            "SEGMENT",
        ]
        ncols = len(columns)
        recs = [rec + ["1*"] * (ncols - len(rec)) for rec in recs[1:]]  # pad with default values (1*)
        df = pd.DataFrame(recs, columns=columns)
        #  datatypes
        df[columns[:4]] = df[columns[:4]].astype(np.int64)
        df[columns[4:6]] = df[columns[4:6]].astype(np.float64)
        if well_name not in self.msws:
            self.msws[well_name] = {}
        self.msws[well_name]["compsegs"] = df
        logger.debug("set_compsegs for %s", well_name)
        return well_name

    def get_welspecs(self, well_name: str) -> pd.DataFrame:
        """
        Get-function for WELSPECS.

        Args:
            well_name: Well name

        Returns:
            :ref:`WELSPECS DataFrame <welspecs_format>`

        """
        return self.msws[well_name]["welspecs"]

    def get_compdat(self, well_name: str) -> pd.DataFrame:
        """
        Get-function for COMPDAT.

        Args:
            well_name: Well name

        Returns:
            :ref:`COMPDAT DataFrame <compdat_format>`

        Raises:
            ValueError: If COMPDAT keyword is missing in input schedule file

        """
        try:
            return self.msws[well_name]["compdat"]
        except KeyError as err:
            if "'compdat'" in str(err):
                raise ValueError("Input schedule file missing COMPDAT keyword.") from err
            raise err

    def get_compsegs(self, well_name: str, branch: int | None = None) -> pd.DataFrame:
        """
        Get-function for COMPSEGS.

        Args:
           well_name: Well name
           branch: Branch number

        Returns:
            :ref:`COMPSEGS DataFrame <compsegs_format>`

        """
        df = self.msws[well_name]["compsegs"].copy()
        if branch is not None:
            df = df[df["BRANCH"] == branch]
        df.reset_index(drop=True, inplace=True)  # reset index after filtering
        # (why??)
        return fix_compsegs(df, well_name)

    def get_welsegs(self, well_name: str, branch: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Get-function for WELSEGS.

        Args:
            well_name: Well name
            branch: Branch number

        Returns:
            | :ref:`WELSEGS header <welsegs_header_format>`
            | :ref:`WELSEGS records <welsegs_content_format>`

        Raises:
            ValueError: If WELSEGS keyword missing in input schedule file

        """
        try:
            dfh, dfr = self.msws[well_name]["welsegs"]
        except KeyError as err:
            if "'welsegs'" in str(err):
                raise ValueError("Input schedule file missing WELSEGS keyword.") from err
            raise err
        if branch is not None:
            dfr = dfr[dfr["TUBINGBRANCH"] == branch]
        dfr.reset_index(drop=True, inplace=True)  # reset index after filtering (why??)
        return dfh, dfr

    def get_well_number(self, well_name: str) -> int:
        """
        Well number in the active_wells list.

        Args:
            well_name: Well name

        Returns:
            Well number

        """
        return (self.active_wells == well_name).nonzero()[0][0]
