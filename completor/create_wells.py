"""Module for creating completion structure."""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd

from completor import completion, read_schedule
from completor.constants import Headers, Method
from completor.logger import logger
from completor.read_casefile import ReadCasefile


class Wells:
    """Class for creating well completion structure.

    Attributes:
        df_completion: Completion data frame in loop.
        df_reservoir: COMPDAT and COMPSEGS data frame fusion in loop.
        df_welsegs_header: WELSEGS first record.
        df_welsegs_content: WELSEGS second record.
        df_mdtvd: Data frame of MEASURED_DEPTH and TRUE_VERTICAL_DEPTH relationship.
        df_tubing_segments: Tubing segment data frame.
        df_well: Data frame after completion.
        df_well_all: Data frame (df_well) for all laterals after completion.
        df_reservoir_all: df_reservoir for all laterals.
    """

    def __init__(self, well_name: str, case: ReadCasefile, schedule_data: dict[str, dict[str, Any]]):
        """Create completion structure.

        Args:
            well_name: Well name.
            case: Data from case file.
            schedule_data: Data from schedule file.
        """
        self.case: ReadCasefile = case
        self.df_well_all = pd.DataFrame()
        self.df_reservoir_all = pd.DataFrame()

        active_laterals = _get_active_laterals(well_name, self.case.completion_table)
        for lateral in active_laterals:
            self.df_completion = self.case.get_completion(well_name, lateral)
            self.df_welsegs_header, self.df_welsegs_content = read_schedule.get_well_segments(
                schedule_data, well_name, lateral
            )

            self.df_reservoir = _select_well(well_name, schedule_data, lateral)

            self.df_mdtvd = completion.well_trajectory(self.df_welsegs_header, self.df_welsegs_content)
            self.df_completion = completion.define_annulus_zone(self.df_completion)
            self.df_tubing_segments = _create_tubing_segments(
                self.df_reservoir, self.df_completion, self.df_mdtvd, self.case.method, self.case
            )
            self.df_tubing_segments = completion.insert_missing_segments(self.df_tubing_segments, well_name)
            self.df_well = completion.complete_the_well(
                self.df_tubing_segments, self.df_completion, self.case.joint_length
            )
            self.df_well[Headers.ROUGHNESS] = self.df_well[Headers.ROUGHNESS].apply(lambda x: f"{x:.3E}")
            self.df_well = _get_devices(self.df_completion, self.df_well, self.case)
            self.df_well = completion.correct_annulus_zone(self.df_well)
            self.df_reservoir = _connect_cells_to_segments(
                self.df_reservoir, self.df_well, self.df_tubing_segments, self.case.method
            )
            self.df_well[Headers.WELL] = well_name
            self.df_reservoir[Headers.WELL] = well_name
            self.df_well[Headers.LATERAL] = lateral
            self.df_reservoir[Headers.LATERAL] = lateral

            self.df_well_all = pd.concat([self.df_well_all, self.df_well], sort=False)
            self.df_reservoir_all = pd.concat([self.df_reservoir_all, self.df_reservoir], sort=False)


def get_active_wells(completion_table: pd.DataFrame, gp_perf_devicelayer: bool) -> npt.NDArray[np.str_]:
    """Get a list of active wells specified by users.

    Notes:
        No device layer will be added for perforated wells with gravel-packed annulus.
        Completor does nothing to gravel-packed perforated wells by default.
        This behavior can be changed by setting the GP_PERF_DEVICELAYER keyword in the case file to true.

    Args:
        completion_table: Completion information.
        gp_perf_devicelayer: Keyword denoting if the user wants a device layer for this type of completion.

    Returns:
        The active wells found.
    """
    # Need to check completion of all wells in the completion table to remove GP-PERF type wells
    wells = np.array(completion_table[Headers.WELL])
    annuli = completion_table[completion_table[Headers.WELL] == wells][Headers.ANNULUS]
    device_types = completion_table[completion_table[Headers.WELL] == wells][Headers.DEVICE_TYPE]

    # If the user wants a device layer for this type of completion.
    if not gp_perf_devicelayer:
        gp_check = annuli == "OA"
        perf_check = device_types.isin(["AICD", "AICV", "DAR", "ICD", "VALVE", "ICV"])
        # Where annuli is "OA" or perforation is in the list above.
        mask = gp_check | perf_check
        if not mask.any():
            logger.warning(
                "There are no active wells for Completor to work on. E.g. all wells are defined with Gravel Pack "
                "(GP) and valve type PERF. If you want these wells to be active set GP_PERF_DEVICELAYER to TRUE."
            )
        return np.array(completion_table[Headers.WELL][mask].unique())
    return np.array(completion_table[Headers.WELL].unique())


def _get_active_laterals(well_name: str, df_completion: pd.DataFrame) -> npt.NDArray[np.int_]:
    """Get a list of lateral numbers for the well.

    Args:
        well_name: The well name.
        df_completion: The completion information from case data.

    Returns:
        The active laterals.
    """
    return np.array(df_completion[df_completion[Headers.WELL] == well_name][Headers.BRANCH].unique())


def _select_well(well_name: str, schedule_data: dict[str, dict[str, Any]], lateral: int) -> pd.DataFrame:
    """Filter the reservoir data for this well and its laterals.

    Args:
        well_name: The name of the well.
        schedule_data: Multisegmented well segment data.
        lateral: The lateral number.

    Returns:
        Filtered reservoir data.
    """
    df_compsegs = read_schedule.get_completion_segments(schedule_data, well_name, lateral)
    df_compdat = read_schedule.get_completion_data(schedule_data, well_name)
    df_reservoir = pd.merge(df_compsegs, df_compdat, how="inner", on=[Headers.I, Headers.J, Headers.K])

    # Remove WELL column in the df_reservoir.
    df_reservoir = df_reservoir.drop([Headers.WELL], axis=1)
    # If multiple occurrences of same IJK in compdat/compsegs --> keep the last one.
    df_reservoir = df_reservoir.drop_duplicates(subset=Headers.START_MEASURED_DEPTH, keep="last")
    return df_reservoir.reset_index()


def _create_tubing_segments(
    df_reservoir: pd.DataFrame, df_completion: pd.DataFrame, df_mdtvd: pd.DataFrame, method: Method, case: ReadCasefile
) -> pd.DataFrame:
    """Create tubing segments based on the method and presence of Inflow Control Valves (ICVs).

    The behavior of the df_tubing_segments will vary depending on the existence of the ICV keyword.
    When the ICV keyword is present, it always creates a lumped tubing segment on its interval,
    whereas other types of devices follow the default input.
    If there is a combination of ICV and other devices (with devicetype > 1),
    it results in a combination of ICV segment length with segment lumping,
    and default segment length on other devices.

    Args:
        df_reservoir: Reservoir data.
        df_completion: Completion information.
        df_mdtvd: Measured and true vertical depths.
        method: The method to use for creating segments.
        case: Case data.

    Returns:
        Tubing data.
    """
    df_tubing_segments_cells = completion.create_tubing_segments(
        df_reservoir, df_completion, df_mdtvd, method, case.segment_length, case.minimum_segment_length
    )

    df_tubing_segments_user = completion.create_tubing_segments(
        df_reservoir, df_completion, df_mdtvd, Method.USER, case.segment_length, case.minimum_segment_length
    )

    if (pd.unique(df_completion[Headers.DEVICE_TYPE]).size > 1) & (
        (df_completion[Headers.DEVICE_TYPE] == "ICV") & (df_completion[Headers.VALVES_PER_JOINT] > 0)
    ).any():
        return read_schedule.fix_compsegs_by_priority(df_completion, df_tubing_segments_cells, df_tubing_segments_user)

    # If all the devices are ICVs, lump the segments.
    if (df_completion[Headers.DEVICE_TYPE] == "ICV").all():
        return df_tubing_segments_user
    # If none of the devices are ICVs use defined method.
    return df_tubing_segments_cells


def _get_devices(df_completion: pd.DataFrame, df_well: pd.DataFrame, case: ReadCasefile) -> pd.DataFrame:
    """Complete the well with the device information.

    Args:
        df_completion: Completion information.
        df_well: Well data.
        case: Case data.

    Returns:
        Well data with device information.
    """
    if not case.completion_icv_tubing.empty:
        active_devices = pd.concat(
            [df_completion[Headers.DEVICE_TYPE], case.completion_icv_tubing[Headers.DEVICE_TYPE]]
        ).unique()
    else:
        active_devices = df_completion[Headers.DEVICE_TYPE].unique()
    if "VALVE" in active_devices:
        df_well = completion.get_device(df_well, case.wsegvalv_table, "VALVE")
    if "ICD" in active_devices:
        df_well = completion.get_device(df_well, case.wsegsicd_table, "ICD")
    if "AICD" in active_devices:
        df_well = completion.get_device(df_well, case.wsegaicd_table, "AICD")
    if "DAR" in active_devices:
        df_well = completion.get_device(df_well, case.wsegdar_table, "DAR")
    if "AICV" in active_devices:
        df_well = completion.get_device(df_well, case.wsegaicv_table, "AICV")
    if "ICV" in active_devices:
        df_well = completion.get_device(df_well, case.wsegicv_table, "ICV")
    return df_well


def _connect_cells_to_segments(
    df_reservoir: pd.DataFrame, df_well: pd.DataFrame, df_tubing_segments: pd.DataFrame, method: Method
) -> pd.DataFrame:
    """Connect cells to the well.

    Notes:
        Only some columns from well DataFrame are needed: MEASURED_DEPTH, NDEVICES, DEVICETYPE, and ANNULUS_ZONE.
        ICV placement forces different methods in segment creation as USER defined.

    Args:
        df_reservoir: Reservoir data.
        df_well: Well data.
        df_tubing_segments: Tubing information.
        method: The method to use for creating segments.

    Returns:
        Reservoir data with additional info on connected cells.
    """
    # drop BRANCH column, not needed
    df_reservoir = df_reservoir.drop([Headers.BRANCH], axis=1)
    icv_device = (
        df_well[Headers.DEVICE_TYPE].nunique() > 1
        and (df_well[Headers.DEVICE_TYPE] == "ICV").any()
        and not df_well[Headers.NUMBER_OF_DEVICES].empty
    )
    method = Method.USER if icv_device else method
    df_well = df_well[
        [Headers.TUBING_MEASURED_DEPTH, Headers.NUMBER_OF_DEVICES, Headers.DEVICE_TYPE, Headers.ANNULUS_ZONE]
    ]
    return completion.connect_cells_to_segments(df_well, df_reservoir, df_tubing_segments, method)
