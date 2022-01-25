"""Completion."""

from __future__ import annotations

from typing import Union, overload

import numpy as np
import numpy.typing as npt
import pandas as pd

from completor.constants import Completion, SegmentCreationMethod
from completor.logger import logger
from completor.read_schedule import fix_compsegs, fix_welsegs
from completor.utils import abort, as_data_frame, log_and_raise_exception

try:
    from typing import Literal, TypeAlias  # type: ignore
except ImportError:
    pass

# Use more precise type information, if possible
MethodType: TypeAlias = Union['Literal["cells", "user", "fix", "welsegs"]', SegmentCreationMethod]
DeviceType: TypeAlias = 'Literal["AICD", "ICD", "DAR", "VALVE", "AICV", "ICV"]'


class Information:
    """Holds information from ``get_completion``."""

    def __init__(
        self,
        num_device: float | list[float] | None = None,
        device_type: DeviceType | list[DeviceType] | None = None,
        device_number: int | list[int] | None = None,
        inner_diameter: float | list[float] | None = None,
        outer_diameter: float | list[float] | None = None,
        roughness: float | list[float] | None = None,
        annulus_zone: int | list[int] | None = None,
    ):
        """Initialize Information class."""
        self.num_device = num_device
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


def well_trajectory(df_welsegs_header: pd.DataFrame, df_welsegs_content: pd.DataFrame) -> pd.DataFrame:
    """
    Create trajectory relation between MD and TVD.

    WELSEGS must be defined as ABS and not INC.

    Args:
        df_welsegs_header: First record of WELSEGS
        df_welsegs_content: Second record WELSEGS

    Return:
        MD versus TVD

    The DataFrame format of df_mdtvd is shown in the class function
    ``create_wells.CreateWells.well_trajectory``. The formats of ``df_welsegs_header``
    and ``df_welsegs_content`` are shown in the function
    :ref:`create_wells.CreateWells.select_well <select_well>`.
    """
    md_ = df_welsegs_content["TUBINGMD"].to_numpy()
    md_ = np.insert(md_, 0, df_welsegs_header["SEGMENTMD"].iloc[0])
    tvd = df_welsegs_content["TUBINGTVD"].to_numpy()
    tvd = np.insert(tvd, 0, df_welsegs_header["SEGMENTTVD"].iloc[0])
    df_mdtvd = as_data_frame({"MD": md_, "TVD": tvd})
    # sort based on md
    df_mdtvd.sort_values(by=["MD", "TVD"], inplace=True)
    # reset index after sorting
    df_mdtvd.reset_index(drop=True, inplace=True)
    return df_mdtvd


def define_annulus_zone(df_completion: pd.DataFrame) -> pd.DataFrame:
    """Define the annulus zone from the COMPLETION.

    Args:
        df_completion: Must contain the columns ``STARTMD``, ``ENDMD``, and ``ANNULUS``

    Returns:
        Updated COMPLETION with additional column ``ANNULUS_ZONE``

    Raise:
        ValueError: If the dimension is not correct

    The DataFrame format of df_completion is shown in
    :ref:`create_wells.CreateWells.select_well <df_completion>`.
    """
    # define annular zone
    start_md = df_completion[Completion.START_MD].iloc[0]
    end_md = df_completion[Completion.END_MD].iloc[-1]
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
        boundary = np.sort(np.append(np.insert(boundary, 0, start_md), end_md))
        boundary = np.unique(boundary)
        start_bound = boundary[:-1]
        end_bound = boundary[1:]
        # get annulus zone
        # initiate with 0
        annulus_zone = np.full(len(start_bound), 0)
        for idx, start_md in enumerate(start_bound):
            end_md = end_bound[idx]
            is_gravel_pack_location = np.any(
                (gravel_pack_location[:, 0] == start_md) & (gravel_pack_location[:, 1] == end_md)
            )
            if not is_gravel_pack_location:
                annulus_zone[idx] = max(annulus_zone) + 1
            # else it is 0
        df_annulus = as_data_frame(
            {Completion.START_MD: start_bound, Completion.END_MD: end_bound, Completion.ANNULUS_ZONE: annulus_zone}
        )

        annulus_zone = np.full(df_completion.shape[0], 0)
        for idx in range(df_completion.shape[0]):
            start_md = df_completion["STARTMD"].iloc[idx]
            end_md = df_completion["ENDMD"].iloc[idx]
            idx0, idx1 = completion_index(df_annulus, start_md, end_md)
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
    df_mdtvd: pd.DataFrame,
    method: Literal[SegmentCreationMethod.FIX] = ...,
    segment_length: float = ...,
    minimum_segment_length: float = 0.0,
) -> pd.DataFrame: ...


@overload
def create_tubing_segments(
    df_reservoir: pd.DataFrame,
    df_completion: pd.DataFrame,
    df_mdtvd: pd.DataFrame,
    method: MethodType = ...,
    segment_length: float | str = ...,
    minimum_segment_length: float = 0.0,
) -> pd.DataFrame: ...


def create_tubing_segments(
    df_reservoir: pd.DataFrame,
    # Technically, df_completion is only required for SegmentCreationMethod.USER
    df_completion: pd.DataFrame,
    df_mdtvd: pd.DataFrame,
    method: MethodType = SegmentCreationMethod.CELLS,
    segment_length: float | str = 0.0,
    minimum_segment_length: float = 0.0,
) -> pd.DataFrame:
    """
    Procedure to create segments in the tubing layer.

    Args:
        df_reservoir: Must contain ``STARTMD`` and ``ENDMD``
        df_completion: Must contain ``ANNULUS``, ``STARTMD``, ``ENDMD``,
                    ``ANNULUS_ZONE`` and no packer content in the completion
        df_mdtvd: Must contain ``MD`` and ``TVD``
        method: Method for segmentation. Default: cells
        segment_length: Only if fix is selected in the method.
        minimum_segment_length: User input minimum segment length.

    Segmentation methods

    | cells: Create one segment per cell
    | user: Create segment based on the completion definition
    | fix: Create segment based on fix interval
    | welsegs: Create segment based on ``WELSEGS`` keyword

    Returns:
        A dataframe with columns ``STARTMD``, ``ENDMD``, ``TUB_MD``, ``TUB_TVD``

    | The formats of DataFrames are shown in
    | df_reservoir (:ref:`create_wells.CreateWells.select_well <df_reservoir>`)
    | df_completion (:ref:`create_wells.CreateWells.select_well <df_completion>`)
    | df_mdtvd (:ref:`create_wells.CreateWells.well_trajectory <df_mdtvd>`)
    | df_tubing_segments
        (:ref:`create_wells.CreateWells.create_tubing_segments <df_tubing_segments>`)

    Raises:
        ValueError: If the method is unknown

    """
    start_measure_depth: npt.NDArray[np.float64]
    end_measure_depth: npt.NDArray[np.float64]
    if method == SegmentCreationMethod.CELLS:
        # in this method we create the tubing layer
        # one cell one segment while honoring df_reservoir["SEGMENT"]
        start_measure_depth = df_reservoir["STARTMD"].to_numpy()
        end_measure_depth = df_reservoir["ENDMD"].to_numpy()
        if "SEGMENT" in df_reservoir.columns:
            if not df_reservoir["SEGMENT"].isin(["1*"]).any():
                create_start_md = []
                create_end_md = []
                create_start_md.append(df_reservoir["STARTMD"].iloc[0])
                current_segment = df_reservoir["SEGMENT"].iloc[0]
                for idx in range(1, len(df_reservoir["SEGMENT"])):
                    if df_reservoir["SEGMENT"].iloc[idx] != current_segment:
                        create_end_md.append(df_reservoir["ENDMD"].iloc[idx - 1])
                        create_start_md.append(df_reservoir["STARTMD"].iloc[idx])
                        current_segment = df_reservoir["SEGMENT"].iloc[idx]
                create_end_md.append(df_reservoir["ENDMD"].iloc[-1])
                start_measure_depth = np.array(create_start_md)
                end_measure_depth = np.array(create_end_md)
        # if users want a minumum segment length, we do the following
        minimum_segment_length = float(minimum_segment_length)
        if minimum_segment_length > 0.0:
            new_start_md = []
            new_end_md = []
            diff_md = end_measure_depth - start_measure_depth  # get the segment lengths
            current_diff_md = 0.0
            start_idx = 0
            end_idx = 0
            for idx in range(0, len(diff_md) - 1):
                current_diff_md += diff_md[idx]
                if current_diff_md >= minimum_segment_length:
                    new_start_md.append(start_measure_depth[start_idx])
                    new_end_md.append(end_measure_depth[end_idx])
                    current_diff_md = 0.0
                    start_idx = idx + 1
                    end_idx = idx + 1
                else:
                    end_idx = idx + 1
            if current_diff_md < minimum_segment_length:
                new_start_md.append(start_measure_depth[start_idx])
                new_end_md.append(end_measure_depth[end_idx])
            start_measure_depth = np.array(new_start_md)
            end_measure_depth = np.array(new_end_md)
    elif method == SegmentCreationMethod.USER:
        # in this method we create tubing layer
        # based on the definition of COMPLETION keyword
        # in the case file
        # read all segments except PA which has no segment length
        df_temp = df_completion.copy(deep=True)
        start_measure_depth = df_temp["STARTMD"].to_numpy()
        end_measure_depth = df_temp["ENDMD"].to_numpy()
        # fix the start and end
        start_measure_depth[0] = max(df_reservoir["STARTMD"].iloc[0], start_measure_depth[0])
        end_measure_depth[-1] = min(df_reservoir["ENDMD"].iloc[-1], end_measure_depth[-1])
        if start_measure_depth[0] >= end_measure_depth[0]:
            start_measure_depth = np.delete(start_measure_depth, 0)
            end_measure_depth = np.delete(end_measure_depth, 0)
        if start_measure_depth[-1] >= end_measure_depth[-1]:
            start_measure_depth = np.delete(start_measure_depth, -1)
            end_measure_depth = np.delete(end_measure_depth, -1)
    elif method == SegmentCreationMethod.FIX:
        # in this method we create tubing layer
        # with fix interval according to the user input
        # in the case file keyword SEGMENTLENGTH
        min_measure_depth = df_reservoir["STARTMD"].min()
        max_measure_depth = df_reservoir["ENDMD"].max()
        if not isinstance(segment_length, (float, int)):
            raise ValueError(f"Segment length must be a number, " f"when using {method} (was {segment_length})")
        start_measure_depth = np.arange(min_measure_depth, max_measure_depth, segment_length)
        end_measure_depth = start_measure_depth + segment_length
        # update the end point of the last segment
        end_measure_depth[-1] = min(end_measure_depth[-1], max_measure_depth)
    elif method == SegmentCreationMethod.WELSEGS:
        # In this method we create the tubing layer
        # from segment measured depths in the WELSEGS keyword that are missing
        # from COMPSEGS.
        # WELSEGS segment depths are collected in the df_mdtvd dataframe, which
        # is available here. Completor interprets WELSEGS depths as segment
        # midpoint depths.
        #
        # Obtain the welsegs segment midpoint depth
        welsegs = df_mdtvd["MD"].to_numpy()
        end_welsegs_depth = 0.5 * (welsegs[:-1] + welsegs[1:])
        # The start of the very first segment in any branch is the actual start
        # MD of the first segment.
        start_welsegs_depth = np.insert(end_welsegs_depth[:-1], 0, welsegs[0], axis=None)
        start_compsegs_depth: npt.NDArray[np.float64] = df_reservoir["STARTMD"].to_numpy()
        end_compsegs_depth = df_reservoir["ENDMD"].to_numpy()
        # If there are gaps in compsegs and there are welsegs segments that fit
        # in the gaps, we will insert welsegs segments into the compsegs gaps
        gaps_compsegs = start_compsegs_depth[1:] - end_compsegs_depth[:-1]
        # Indices of gaps in compsegs
        indices_gaps = np.nonzero(gaps_compsegs)
        # Start of the gaps
        start_gaps_depth = end_compsegs_depth[indices_gaps[0]]
        # End of the gaps
        end_gaps_depth = start_compsegs_depth[indices_gaps[0] + 1]
        # First we need to check the gaps between compsegs
        # and fill it out with welsegs
        start = np.abs(start_welsegs_depth[:, np.newaxis] - start_gaps_depth).argmin(axis=0)
        end = np.abs(end_welsegs_depth[:, np.newaxis] - end_gaps_depth).argmin(axis=0)
        welsegs_to_add = np.setxor1d(start_welsegs_depth[start], end_welsegs_depth[end])
        start_welsegs_outside = start_welsegs_depth[np.argwhere(start_welsegs_depth < start_compsegs_depth[0])]
        end_welsegs_outside = end_welsegs_depth[np.argwhere(end_welsegs_depth > end_compsegs_depth[-1])]
        welsegs_to_add = np.append(welsegs_to_add, start_welsegs_outside)
        welsegs_to_add = np.append(welsegs_to_add, end_welsegs_outside)
        # Find welsegs start and end in gaps
        start_compsegs_depth = np.append(start_compsegs_depth, welsegs_to_add)
        end_compsegs_depth = np.append(end_compsegs_depth, welsegs_to_add)
        # Use completor syntax and sort
        start_measure_depth = np.sort(start_compsegs_depth)
        end_measure_depth = np.sort(end_compsegs_depth)
        # check for missing segment
        shift_start_md = np.append(start_measure_depth[1:], end_measure_depth[-1])
        missing_index = np.argwhere(shift_start_md > end_measure_depth).flatten()
        missing_index = missing_index + 1
        new_missing_startmd = end_measure_depth[missing_index - 1]
        new_missing_endmd = start_measure_depth[missing_index]
        start_measure_depth = np.sort(np.append(start_measure_depth, new_missing_startmd))
        end_measure_depth = np.sort(np.append(end_measure_depth, new_missing_endmd))
        # drop duplicate
        duplicate_idx = np.argwhere(start_measure_depth == end_measure_depth)
        start_measure_depth = np.delete(start_measure_depth, duplicate_idx)
        end_measure_depth = np.delete(end_measure_depth, duplicate_idx)
    else:
        raise ValueError(f"Unknown method '{method}'")

    # md for tubing segments
    md_ = 0.5 * (start_measure_depth + end_measure_depth)
    # estimate TVD
    tvd = np.interp(md_, df_mdtvd["MD"].to_numpy(), df_mdtvd["TVD"].to_numpy())
    # create data frame
    return as_data_frame({"STARTMD": start_measure_depth, "ENDMD": end_measure_depth, "TUB_MD": md_, "TUB_TVD": tvd})


def insert_missing_segments(df_tubing_segments: pd.DataFrame, well_name: str | None) -> pd.DataFrame:
    """
    Create segments for inactive cells.

    Sometimes inactive cells have no segments. It is required to create segments for
    these cells to get the scaling factor correct. Inactive cells are indicated if
    there are segments starting at MD deeper than the end MD of the previous cell.

    Args:
        df_tubing_segments: Must contain column ``STARTMD`` and ``ENDMD``
        well_name: Name of well

    Returns:
        Updated dataframe if missing cells are found

    Raises:
        SystemExit: If the Schedule file is missing data for one or more branches
                    in the case file

    The format of the DataFrame df_tubing_segments is shown in
    :ref:`create_wells.CreateWells.create_tubing_segments <df_tubing_segments>`.
    """
    if df_tubing_segments.empty:
        raise abort(
            "Schedule file is missing data for one or more branches defined in the "
            f"case file. Please check the data for Well {well_name}."
