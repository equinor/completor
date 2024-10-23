"""Classes to keep track of Well objects."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
import pandas as pd

from completor import completion, read_schedule
from completor.constants import Content, Headers, Method, WellData
from completor.read_casefile import ReadCasefile


class Well:
    """A well containing one or more laterals.

    Attributes:
        well_name: The name of the well.
        well_number: The number of the well.
        lateral_numbers: Numbers for each lateral.
        active_laterals: List of laterals.
        df_well_all_laterals: DataFrame containing all the laterals' well-layer data.
        df_reservoir_all_laterals: DataFrame containing all the laterals' reservoir-layer data.
        df_welsegs_header_all_laterals: DataFrame containing all the laterals' well-segments header data.
        df_welsegs_content_all_laterals: DataFrame containing all the laterals' well-segments content.
    """

    well_name: str
    well_number: int
    df_well_all_laterals: pd.DataFrame
    df_reservoir_all_laterals: pd.DataFrame
    lateral_numbers: npt.NDArray[np.int64]
    active_laterals: list[Lateral]
    df_welsegs_header_all_laterals: pd.DataFrame
    df_welsegs_content_all_laterals: pd.DataFrame

    def __init__(
        self,
        well_name: str,
        well_number: int,
        case: ReadCasefile,
        well_data: dict[str, pd.DataFrame | tuple[pd.DataFrame, pd.DataFrame]],
    ):
        """Create well.

        Args:
            well_name: Well name.
            case: Data from the case file.
            well_data: Data from the schedule file.
        """
        self.well_name = well_name
        self.well_number = well_number

        lateral_numbers = self._get_active_laterals(well_name, case.completion_table)
        self.active_laterals = [Lateral(num, well_name, case, well_data) for num in lateral_numbers]

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

    @staticmethod
    def _get_active_laterals(well_name: str, df_completion: pd.DataFrame) -> npt.NDArray[np.int_]:
        """Get a list of lateral numbers for the well.

        Args:
            well_name: The well name.
            df_completion: The completion information from case data.

        Returns:
            The active laterals.
        """
        return np.array(df_completion[df_completion[Headers.WELL] == well_name][Headers.BRANCH].unique())


class Lateral:
    """Lateral containing data related to a specific well's branch.

    Attributes:
        lateral_number: Current lateral number.
        df_completion: Completion data.
        df_welsegs_header: Header for welsegs.
        df_welsegs_content: Content for welsegs.
        df_reservoir_header: Reservoir header data.
        df_measured_true_vertical_depth: Data for measured and true vertical depths.
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
    df_measured_true_vertical_depth: pd.DataFrame
    df_well: pd.DataFrame
    df_reservoir: pd.DataFrame
    df_tubing: pd.DataFrame
    df_device: pd.DataFrame

    def __init__(self, lateral_number: int, well_name: str, case: ReadCasefile, well_data: WellData):
        """Create Lateral.

        Args:
            lateral_number: Number of the current lateral/branch.
            well_name: The well's name.
            case: The case data.
            well_data: This wells' schedule data.
        """
        self.lateral_number = lateral_number
        self.df_completion = case.get_completion(well_name, lateral_number)
        self.df_welsegs_header, self.df_welsegs_content = read_schedule.get_well_segments(well_data, lateral_number)

        self.df_device = pd.DataFrame()

        self.df_reservoir = self._select_well(well_name, well_data, lateral_number)
        if self.df_reservoir.empty:
            print("")
        self.df_measured_true_vertical_depth = completion.well_trajectory(
            self.df_welsegs_header, self.df_welsegs_content
        )
        self.df_completion = completion.define_annulus_zone(self.df_completion)
        self.df_tubing = self._create_tubing_segments(
            self.df_reservoir, self.df_completion, self.df_measured_true_vertical_depth, case
        )
        self.df_tubing = completion.insert_missing_segments(self.df_tubing, well_name)
        self.df_well = completion.complete_the_well(self.df_tubing, self.df_completion, case.joint_length)
        self.df_well = self._get_devices(self.df_completion, self.df_well, case)
        self.df_well = completion.correct_annulus_zone(self.df_well)
        self.df_reservoir = self._connect_cells_to_segments(
            self.df_reservoir, self.df_well, self.df_tubing, case.method
        )
        self.df_well[Headers.WELL] = well_name
        self.df_reservoir[Headers.WELL] = well_name
        self.df_well[Headers.LATERAL] = lateral_number
        self.df_reservoir[Headers.LATERAL] = lateral_number

    @staticmethod
    def _select_well(well_name: str, well_data: WellData, lateral: int) -> pd.DataFrame:
        """Filter the reservoir data for this well and its laterals.

        Args:
            well_name: The name of the well.
            well_data: Multisegmented well segment data.
            lateral: The lateral number.

        Returns:
            Filtered reservoir data.
        """
        df_compsegs = read_schedule.get_completion_segments(well_data, well_name, lateral)
        df_compdat = read_schedule.get_completion_data(well_data)
        df_reservoir = pd.merge(df_compsegs, df_compdat, how="inner", on=[Headers.I, Headers.J, Headers.K])

        # Remove WELL column in the df_reservoir.
        df_reservoir = df_reservoir.drop([Headers.WELL], axis=1)
        # If multiple occurrences of same IJK in compdat/compsegs --> keep the last one.
        df_reservoir = df_reservoir.drop_duplicates(subset=Headers.START_MEASURED_DEPTH, keep="last")
        return df_reservoir.reset_index()

    @staticmethod
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
            and (df_well[Headers.DEVICE_TYPE] == Content.INFLOW_CONTROL_VALVE).any()
            and not df_well[Headers.NUMBER_OF_DEVICES].empty
        )
        method = Method.USER if icv_device else method
        df_well = df_well[
            [Headers.TUBING_MEASURED_DEPTH, Headers.NUMBER_OF_DEVICES, Headers.DEVICE_TYPE, Headers.ANNULUS_ZONE]
        ]
        return completion.connect_cells_to_segments(df_well, df_reservoir, df_tubing_segments, method)

    @staticmethod
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
        if Content.VALVE in active_devices:
            df_well = completion.get_device(df_well, case.wsegvalv_table, Content.VALVE)
        if Content.INFLOW_CONTROL_DEVICE in active_devices:
            df_well = completion.get_device(df_well, case.wsegsicd_table, Content.INFLOW_CONTROL_DEVICE)
        if Content.AUTONOMOUS_INFLOW_CONTROL_DEVICE in active_devices:
            df_well = completion.get_device(df_well, case.wsegaicd_table, Content.AUTONOMOUS_INFLOW_CONTROL_DEVICE)
        if Content.DENSITY_ACTIVATED_RECOVERY in active_devices:
            df_well = completion.get_device(df_well, case.wsegdar_table, Content.DENSITY_ACTIVATED_RECOVERY)
        if Content.AUTONOMOUS_INFLOW_CONTROL_VALVE in active_devices:
            df_well = completion.get_device(df_well, case.wsegaicv_table, Content.AUTONOMOUS_INFLOW_CONTROL_VALVE)
        if Content.INFLOW_CONTROL_VALVE in active_devices:
            df_well = completion.get_device(df_well, case.wsegicv_table, Content.INFLOW_CONTROL_VALVE)
        return df_well

    @staticmethod
    def _create_tubing_segments(
        df_reservoir: pd.DataFrame, df_completion: pd.DataFrame, df_mdtvd: pd.DataFrame, case: ReadCasefile
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
            case: Case data, including the Method used to create segments.

        Returns:
            Tubing data.
        """
        df_tubing_segments_cells = completion.create_tubing_segments(
            df_reservoir, df_completion, df_mdtvd, case.method, case.segment_length, case.minimum_segment_length
        )

        df_tubing_segments_user = completion.create_tubing_segments(
            df_reservoir, df_completion, df_mdtvd, Method.USER, case.segment_length, case.minimum_segment_length
        )

        if (pd.unique(df_completion[Headers.DEVICE_TYPE]).size > 1) & (
            (df_completion[Headers.DEVICE_TYPE] == Content.INFLOW_CONTROL_VALVE)
            & (df_completion[Headers.VALVES_PER_JOINT] > 0)
        ).any():
            return read_schedule.fix_compsegs_by_priority(
                df_completion, df_tubing_segments_cells, df_tubing_segments_user
            )

        # If all the devices are ICVs, lump the segments.
        if (df_completion[Headers.DEVICE_TYPE] == Content.INFLOW_CONTROL_VALVE).all():
            return df_tubing_segments_user
        # If none of the devices are ICVs use defined method.
        return df_tubing_segments_cells
