"""Module for creating completion structure."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
import pandas as pd

from completor import completion
from completor.constants import Headers, Method
from completor.logger import logger
from completor.read_casefile import ReadCasefile
from completor.read_schedule import fix_compsegs_by_priority


class CreateWells:
    """Class for creating well completion structure.

    Args:
        case: ReadCasefile class.

    Attributes:
        active_wells: Active wells defined in the case file.
        method: Method for segment creation.
        well_name: Well name (in loop).
        laterals: List of lateral number of the well in loop.
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

    def __init__(self, case: ReadCasefile):
        """Initialize CreateWells."""
        self.well_name: str | None = None
        self.df_reservoir = pd.DataFrame()
        self.df_mdtvd = pd.DataFrame()
        self.df_completion = pd.DataFrame()
        self.df_tubing_segments = pd.DataFrame()
        self.df_well = pd.DataFrame()
        self.df_compdat = pd.DataFrame()
        self.df_well_all = pd.DataFrame()
        self.df_reservoir_all = pd.DataFrame()
        self.df_welsegs_header = pd.DataFrame()
        self.df_welsegs_content = pd.DataFrame()
        self.laterals: list[int] = []

        self.case: ReadCasefile = case
        self.active_wells = self._active_wells(self.case)
        self.method = self._method(self.case)

    def update(self, well_name: str, schedule: completion.WellSchedule) -> None:
        """Update class variables in CreateWells.

        Args:
            well_name: Well name.
            schedule: ReadSchedule object.
        """
        if well_name is None:
            raise ValueError("Cannot update well without well name.")
        self.well_name = well_name
        active_laterals = self._active_laterals(well_name, self.case.completion_table)
        for lateral in active_laterals:
            self.df_completion = self.case.get_completion(well_name, lateral)
            self.df_welsegs_header, self.df_welsegs_content = schedule.get_well_segments(well_name, lateral)

            self.df_reservoir = self.select_well(well_name, schedule, lateral)

            self.df_mdtvd = completion.well_trajectory(self.df_welsegs_header, self.df_welsegs_content)
            self.df_completion = completion.define_annulus_zone(self.df_completion)
            self.df_tubing_segments = self.create_tubing_segments(
                self.df_reservoir, self.df_completion, self.df_mdtvd, self.method, self.case
            )
            self.df_tubing_segments = completion.insert_missing_segments(self.df_tubing_segments, well_name)
            self.df_well = completion.complete_the_well(
                self.df_tubing_segments, self.df_completion, self.case.joint_length
            )
            self.df_well[Headers.ROUGHNESS] = self.df_well[Headers.ROUGHNESS].apply(lambda x: f"{x:.3E}")
            self.df_well = self.get_devices(self.df_completion, self.df_well, self.case)
            self.df_well = completion.correct_annulus_zone(self.df_well)
            self.df_reservoir = self.connect_cells_to_segments(
                self.df_reservoir, self.df_well, self.df_tubing_segments, self.method
            )
            self.df_well[Headers.WELL] = well_name
            self.df_reservoir[Headers.WELL] = well_name
            self.df_well[Headers.LATERAL] = lateral
            self.df_reservoir[Headers.LATERAL] = lateral

            self.df_well_all = pd.concat([self.df_well_all, self.df_well], sort=False)
            self.df_reservoir_all = pd.concat([self.df_reservoir_all, self.df_reservoir], sort=False)

    @staticmethod
    def _active_wells(case: ReadCasefile) -> npt.NDArray[np.str_]:
        """Get a list of active wells specified by users.

        Notes:
            No device layer will be added for perforated wells with gravel-packed annulus.
            Completor does nothing to gravel-packed perforated wells by default.
            This behavior can be changed by setting the GP_PERF_DEVICELAYER keyword in the case file to true.

        Args:
            case: Case data.

        Returns:
            The active wells found.
        """
        # Need to check completion of all wells in the completion table to remove GP-PERF type wells
        active_wells = np.array(case.completion_table[Headers.WELL].unique())
        # We cannot update a list while iterating of it
        for well_name in active_wells:
            # Annulus content of each well
            ann_series = case.completion_table[case.completion_table[Headers.WELL] == well_name][Headers.ANNULUS]
            type_series = case.completion_table[case.completion_table[Headers.WELL] == well_name][Headers.DEVICE_TYPE]
            gp_check = not ann_series.isin(["OA"]).any()
            perf_check = not type_series.isin(["AICD", "AICV", "DAR", "ICD", "VALVE", "ICV"]).any()
            if gp_check and perf_check and not case.gp_perf_devicelayer:
                # De-activate wells with GP_PERF if instructed to do so:
                active_wells = np.setdiff1d(active_wells, well_name, assume_unique=True)
            if active_wells.size == 0:
                logger.warning(
                    "There are no active wells for Completor to work on. E.g. all wells are defined with Gravel Pack "
                    "(GP) and valve type PERF. If you want these wells to be active set GP_PERF_DEVICELAYER to TRUE."
                )
                return np.array([])
        return active_wells

    @staticmethod
    def _method(case: ReadCasefile) -> Method:
        """Define how the user wants to create segments.

        Args:
            case: Case data.

        Returns:
            Creation method enum.

        Raises:
            ValueError: If method is not one of the defined methods.
        """
        if isinstance(case.segment_length, float):
            if float(case.segment_length) > 0.0:
                return Method.FIX
            if float(case.segment_length) == 0.0:
                return Method.CELLS
            if case.segment_length < 0.0:
                return Method.USER
            raise ValueError(
                f"Unrecognized method '{case.segment_length}' in SEGMENTLENGTH keyword. "
                "The value should be one of: 'WELSEGS', 'CELLS', 'USER', or a number: -1 for 'USER', "
                "0 for 'CELLS', or a positive number for 'FIX'."
            )

        if isinstance(case.segment_length, str):
            if "welsegs" in case.segment_length.lower() or "infill" in case.segment_length.lower():
                return Method.WELSEGS
            if "cell" in case.segment_length.lower():
                return Method.CELLS
            if "user" in case.segment_length.lower():
                return Method.USER
            raise ValueError(
                f"Unrecognized method '{case.segment_length}' in SEGMENTLENGTH keyword. The value should be one of: "
                "'WELSEGS', 'CELLS', 'USER', or a number: -1 for 'USER', 0 for 'CELLS', positive number for 'FIX'."
            )

        raise ValueError(
            f"Unrecognized type of '{case.segment_length}' in SEGMENTLENGTH keyword. "
            "The keyword must either be float or string."
        )

    @staticmethod
    def _active_laterals(well_name: str, df_completion: pd.DataFrame) -> npt.NDArray[np.int_]:
        """Get a list of lateral numbers for the well.

        Args:
            well_name: The well name.
            df_completion: The completion information from case data.

        Returns:
            The active laterals.
        """
        return np.array(df_completion[df_completion[Headers.WELL] == well_name][Headers.BRANCH].unique())

    @staticmethod
    def select_well(well_name: str, schedule: completion.WellSchedule, lateral: int) -> pd.DataFrame:
        """Filter the reservoir data for this well and its laterals.

        Args:
            well_name: The name of the well.
            schedule: Schedule data.
            lateral: The lateral number.

        Returns:
            Filtered reservoir data.
        """
        df_compsegs = schedule.get_compsegs(well_name, lateral)
        df_compdat = schedule.get_compdat(well_name)
        df_reservoir = pd.merge(df_compsegs, df_compdat, how="inner", on=[Headers.I, Headers.J, Headers.K])

        # Remove WELL column in the df_reservoir.
        df_reservoir = df_reservoir.drop([Headers.WELL], axis=1)
        # If multiple occurrences of same IJK in compdat/compsegs --> keep the last one.
        df_reservoir = df_reservoir.drop_duplicates(subset=Headers.START_MEASURED_DEPTH, keep="last")
        return df_reservoir.reset_index()

    @staticmethod
    def create_tubing_segments(
        df_reservoir: pd.DataFrame,
        df_completion: pd.DataFrame,
        df_mdtvd: pd.DataFrame,
        method: Method,
        case: ReadCasefile,
    ) -> pd.DataFrame:
        """Create tubing segments based on the method and presence of Inflow Control Valves (ICVs).

        The behavior of the df_tubing_segments will vary depending on the existence of the ICV keyword.
        When the ICV keyword is present, it always creates a lumped tubing segment on its interval,
        whereas other types of devices follow the default input.
        If there is a combination of ICV and other devices (with devicetype > 1),
        it results in a combination of ICV segment length with segment lumping,
        and default segment length on other devices.

        Args:
            df_reservoir: Reservoir data
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
            return fix_compsegs_by_priority(df_completion, df_tubing_segments_cells, df_tubing_segments_user)

        # If all the devices are ICVs, lump the segments.
        if (df_completion[Headers.DEVICE_TYPE] == "ICV").all():
            return df_tubing_segments_user
        # If none of the devices are ICVs use defined method.
        return df_tubing_segments_cells

    @staticmethod
    def get_devices(df_completion: pd.DataFrame, df_well: pd.DataFrame, case: ReadCasefile) -> pd.DataFrame:
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

    @staticmethod
    def connect_cells_to_segments(
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
