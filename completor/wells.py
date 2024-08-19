"""Classes to keep track of Well objects."""

from __future__ import annotations

from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd

from completor import completion, read_schedule
from completor.constants import Headers
from completor.create_wells import (
    _connect_cells_to_segments,
    _create_tubing_segments,
    _get_active_laterals,
    _get_devices,
    _select_well,
)
from completor.read_casefile import ReadCasefile


class Well:
    """A well containing one or more laterals.

    Attributes:
        well_name: The name of the well.
        ... TODO:

    """

    well_name: str
    well_number: int
    case: ReadCasefile
    df_well_all_laterals: pd.DataFrame
    df_reservoir_all_laterals: pd.DataFrame
    lateral_numbers: npt.NDArray[np.int64]
    active_laterals: list[Lateral]
    df_well_active_laterals: pd.DataFrame
    df_reservoir_active_laterals: pd.DataFrame
    df_welsegs_header_all_laterals: pd.DataFrame
    df_welsegs_content_all_laterals: pd.DataFrame

    def __init__(self, well_name: str, well_number: int, case: ReadCasefile, schedule_data: dict[str, dict[str, Any]]):
        """Create completion structure.

        Args:
            well_name: Well name.
            case: Data from case file.
            schedule_data: Data from schedule file.
        """
        self.well_name = well_name
        self.well_number = well_number
        self.case: ReadCasefile = case
        self.df_well_all_laterals = pd.DataFrame()
        self.df_reservoir_all_laterals = pd.DataFrame()

        self.lateral_numbers = _get_active_laterals(well_name, self.case.completion_table)
        self.active_laterals = [Lateral(l, well_name, case, schedule_data) for l in self.lateral_numbers]

        self.df_well_all_laterals = pd.concat([l.df_well for l in self.active_laterals], sort=False)
        self.df_reservoir_all_laterals = pd.concat([l.df_reservoir for l in self.active_laterals], sort=False)
        self.df_welsegs_header_all_laterals = pd.concat([l.df_welsegs_header for l in self.active_laterals], sort=False)
        self.df_welsegs_content_all_laterals = pd.concat(
            [l.df_welsegs_content for l in self.active_laterals], sort=False
        )


class Lateral:
    """TODO:"""

    lateral_number: int
    df_completion: pd.DataFrame
    df_welsegs_header: pd.DataFrame
    df_reservoir_header: pd.DataFrame
    df_mdtvd: pd.DataFrame
    df_tubing_segments: pd.DataFrame
    df_well: pd.DataFrame
    df_reservoir: pd.DataFrame
    prepared_tubing: pd.DataFrame
    prepared_device: pd.DataFrame

    def __init__(self, lateral_number, well_name, case, schedule_data):
        self.lateral_number = lateral_number
        self.df_completion = case.get_completion(well_name, lateral_number)
        self.df_welsegs_header, self.df_welsegs_content = read_schedule.get_well_segments(
            schedule_data, well_name, lateral_number
        )

        self.df_reservoir = _select_well(well_name, schedule_data, lateral_number)

        self.df_mdtvd = completion.well_trajectory(self.df_welsegs_header, self.df_welsegs_content)
        self.df_completion = completion.define_annulus_zone(self.df_completion)
        self.df_tubing_segments = _create_tubing_segments(
            self.df_reservoir, self.df_completion, self.df_mdtvd, case.method, case
        )
        self.df_tubing_segments = completion.insert_missing_segments(self.df_tubing_segments, well_name)
        self.df_well = completion.complete_the_well(self.df_tubing_segments, self.df_completion, case.joint_length)
        self.df_well[Headers.ROUGHNESS] = self.df_well[Headers.ROUGHNESS].apply(lambda x: f"{x:.3E}")
        self.df_well = _get_devices(self.df_completion, self.df_well, case)
        self.df_well = completion.correct_annulus_zone(self.df_well)
        self.df_reservoir = _connect_cells_to_segments(
            self.df_reservoir, self.df_well, self.df_tubing_segments, case.method
        )
        self.df_well[Headers.WELL] = well_name
        self.df_reservoir[Headers.WELL] = well_name
        self.df_well[Headers.LATERAL] = lateral_number
        self.df_reservoir[Headers.LATERAL] = lateral_number

    def set_prepared_tubing(self, df_tubing: pd.DataFrame):
        """TODO:

        Args:
            df_tubing:

        Returns:

        """
        self.prepared_tubing = df_tubing

    def set_prepared_device(self, df_device: pd.DataFrame):
        """TODO:

        Args:
            df_device:

        Returns:

        """
        self.prepared_device = df_device
