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
        well_number: The number of the well.
        case: Case file data.
        lateral_numbers: Numbers for each lateral.
        active_laterals: List of laterals.
        df_well_all_laterals: DataFrame containing all the laterals' well-layer data.
        df_reservoir_all_laterals: DataFrame containing all the laterals' reservoir-layer data.
        df_welsegs_header_all_laterals: DataFrame containing all the laterals' well-segments header data.
        df_welsegs_content_all_laterals: DataFrame containing all the laterals' well-segments content.
    """

    well_name: str
    well_number: int
    case: ReadCasefile
    df_well_all_laterals: pd.DataFrame
    df_reservoir_all_laterals: pd.DataFrame
    lateral_numbers: npt.NDArray[np.int64]
    active_laterals: list[Lateral]
    df_welsegs_header_all_laterals: pd.DataFrame
    df_welsegs_content_all_laterals: pd.DataFrame

    def __init__(self, well_name: str, well_number: int, case: ReadCasefile, schedule_data: dict[str, dict[str, Any]]):
        """Create well.

        Args:
            well_name: Well name.
            case: Data from case file.
            schedule_data: Data from schedule file.
        """
        self.well_name = well_name
        self.well_number = well_number
        self.case: ReadCasefile = case

        self.lateral_numbers = _get_active_laterals(well_name, self.case.completion_table)
        self.active_laterals = [Lateral(num, well_name, case, schedule_data) for num in self.lateral_numbers]

        self.df_well_all_laterals = pd.DataFrame()
        self.df_reservoir_all_laterals = pd.DataFrame()
        self.df_well_all_laterals = pd.concat([lateral.df_well for lateral in self.active_laterals], sort=False)
        self.df_reservoir_all_laterals = pd.concat(
            [lateral.df_reservoir for lateral in self.active_laterals], sort=False
        )
        self.df_welsegs_header_all_laterals = pd.concat(
            [lateral.df_welsegs_header for lateral in self.active_laterals], sort=False
        )
        self.df_welsegs_content_all_laterals = pd.concat(
            [lateral.df_welsegs_content for lateral in self.active_laterals], sort=False
        )


class Lateral:
    """Lateral containing data related to a specific well's branch.

    Attributes:
        lateral_number: Current lateral number.
        df_completion: Completion data.
        df_welsegs_header: Header for welsegs.
        df_welsegs_content: Content for welsegs.
        df_reservoir_header: Reservoir header data.
        df_mdtvd: Data for measured and true vertical depths.
        df_tubing: Data for tubing segments.
        df_well: Data for well-layer.
        df_reservoir: Data for reservoir-layer.
        df_tubing: Tubing data.
        df_device: Device data.
    """

    lateral_number: int
    df_completion: pd.DataFrame
    df_welsegs_header: pd.DataFrame
    df_welsegs_content: pd.DataFrame
    df_reservoir_header: pd.DataFrame
    df_mdtvd: pd.DataFrame
    df_well: pd.DataFrame
    df_reservoir: pd.DataFrame
    df_tubing: pd.DataFrame
    df_device: pd.DataFrame

    def __init__(
        self, lateral_number: int, well_name: str, case: ReadCasefile, schedule_data: dict[str, dict[str, Any]]
    ):
        """Create Lateral.

        Args:
            lateral_number: Number of the current lateral/branch.
            well_name: The well's name.
            case: The case data.
            schedule_data: The schedule data.
        """
        self.lateral_number = lateral_number
        self.df_completion = case.get_completion(well_name, lateral_number)
        self.df_welsegs_header, self.df_welsegs_content = read_schedule.get_well_segments(
            schedule_data, well_name, lateral_number
        )

        self.df_device = pd.DataFrame()

        self.df_reservoir = _select_well(well_name, schedule_data, lateral_number)
        self.df_mdtvd = completion.well_trajectory(self.df_welsegs_header, self.df_welsegs_content)
        self.df_completion = completion.define_annulus_zone(self.df_completion)
        self.df_tubing = _create_tubing_segments(
            self.df_reservoir, self.df_completion, self.df_mdtvd, case.method, case
        )
        self.df_tubing = completion.insert_missing_segments(self.df_tubing, well_name)
        self.df_well = completion.complete_the_well(self.df_tubing, self.df_completion, case.joint_length)
        self.df_well[Headers.ROUGHNESS] = self.df_well[Headers.ROUGHNESS].apply(lambda x: f"{x:.3E}")
        self.df_well = _get_devices(self.df_completion, self.df_well, case)
        self.df_well = completion.correct_annulus_zone(self.df_well)
        self.df_reservoir = _connect_cells_to_segments(self.df_reservoir, self.df_well, self.df_tubing, case.method)
        self.df_well[Headers.WELL] = well_name
        self.df_reservoir[Headers.WELL] = well_name
        self.df_well[Headers.LATERAL] = lateral_number
        self.df_reservoir[Headers.LATERAL] = lateral_number
