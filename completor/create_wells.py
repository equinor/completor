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
        self.active_wells = self._active_wells()
        self.method = self._method()

    def update(self, well_name: str, schedule: completion.WellSchedule) -> None:
        """Update class variables in CreateWells.

        Args:
            well_name: Well name.
            schedule: ReadSchedule object.
        """
        self.well_name = well_name
        active_laterals = self._active_laterals()
        for lateral in active_laterals:
            self.df_completion = self.case.get_completion(self.well_name, lateral)
            self.df_welsegs_header, self.df_welsegs_content = schedule.get_well_segments(self.well_name, lateral)

            self.df_reservoir = self.select_well(schedule, lateral)

            self.df_mdtvd = completion.well_trajectory(self.df_welsegs_header, self.df_welsegs_content)
            self.df_completion = completion.define_annulus_zone(self.df_completion)
            self.df_tubing_segments = self.create_tubing_segments(
                self.df_reservoir, self.df_completion, self.df_mdtvd, self.method, self.case
            )
            self.df_tubing_segments = completion.insert_missing_segments(self.df_tubing_segments, self.well_name)
            self.complete_the_well()
            self.get_devices()
            self.correct_annulus_zone()
            self.connect_cells_to_segments()
            self.add_well_lateral_column(lateral)

            self.df_well_all = pd.concat([self.df_well_all, self.df_well], sort=False)
            self.df_reservoir_all = pd.concat([self.df_reservoir_all, self.df_reservoir], sort=False)

    def _active_wells(self) -> npt.NDArray[np.unicode_]:
        """Get a list of active wells specified by users.

        If the well has annulus content with gravel pack and the well is perforated,
        Completor will not add a device layer.
        Completor does nothing to gravel-packed perforated wells by default.
        This behavior can be changed by setting the GP_PERF_DEVICELAYER keyword in the case file to true.

        Returns:
            Active wells.
        """
        # Need to check completion of all wells in completion table to remove GP-PERF type wells
        active_wells = list(set(self.case.completion_table[Headers.WELL]))
        # We cannot update a list while iterating of it
        for well_name in active_wells.copy():
            # Annulus content of each well
            ann_series = self.case.completion_table[self.case.completion_table[Headers.WELL] == well_name][
                Headers.ANNULUS
            ]
            type_series = self.case.completion_table[self.case.completion_table[Headers.WELL] == well_name][
                Headers.DEVICE_TYPE
            ]
            gp_check = not ann_series.isin(["OA"]).any()
            perf_check = not type_series.isin(["AICD", "AICV", "DAR", "ICD", "VALVE", "ICV"]).any()
            if gp_check and perf_check and not self.case.gp_perf_devicelayer:
                # De-activate wells with GP_PERF if instructed to do so:
                active_wells.remove(well_name)
            if not active_wells:
                logger.warning(
                    "There are no active wells for Completor to work on. E.g. all wells are defined with Gravel Pack "
                    "(GP) and valve type PERF. If you want these wells to be active set GP_PERF_DEVICELAYER to TRUE."
                )
                return np.array([])
        return np.array(active_wells)

    def _method(self) -> Method:
        """Define how the user wants to create segments.

        Returns:
            Creation method enum.

        Raises:
            ValueError: If method is not one of the defined methods.
        """
        if isinstance(self.case.segment_length, float):
            if float(self.case.segment_length) > 0.0:
                return Method.FIX
            if float(self.case.segment_length) == 0.0:
                return Method.CELLS
            if self.case.segment_length < 0.0:
                return Method.USER
            else:
                raise ValueError(
                    f"Unrecognized method '{self.case.segment_length}' in SEGMENTLENGTH keyword. "
                    "The value should be one of: 'WELSEGS', 'CELLS', 'USER', or a number: -1 for 'USER', "
                    "0 for 'CELLS', or a positive number for 'FIX'."
                )

        elif isinstance(self.case.segment_length, str):
            if "welsegs" in self.case.segment_length.lower() or "infill" in self.case.segment_length.lower():
                return Method.WELSEGS
            if "cell" in self.case.segment_length.lower():
                return Method.CELLS
            if "user" in self.case.segment_length.lower():
                return Method.USER
            else:
                raise ValueError(
                    f"Unrecognized method '{self.case.segment_length}' in SEGMENTLENGTH keyword. "
                    "The value should be one of: "
                    "'WELSEGS', 'CELLS', 'USER', or a number: -1 for 'USER', 0 for 'CELLS', positive number for 'FIX'."
                )
        else:
            raise ValueError(
                f"Unrecognized type of '{self.case.segment_length}' in SEGMENTLENGTH keyword. "
                "The keyword must either be float or string."
            )

    def _active_laterals(self) -> list[int]:
        """Get a list of lateral numbers for the well.

        ``get_active_laterals`` uses the case class DataFrame property
        ``completion_table`` with a format as shown in the function
        ``read_casefile.ReadCasefile.read_completion``.
        """
        return list(
            self.case.completion_table[self.case.completion_table[Headers.WELL] == self.well_name][
                Headers.BRANCH
            ].unique()
        )

    def select_well(self, schedule: completion.WellSchedule, lateral: int) -> pd.DataFrame:
        """Filter all the required DataFrames for this well and its laterals."""
        if self.well_name is None:
            raise ValueError("No well name given")

        df_compsegs = schedule.get_compsegs(self.well_name, lateral)
        df_compdat = schedule.get_compdat(self.well_name)
        df_reservoir = pd.merge(df_compsegs, df_compdat, how="inner", on=[Headers.I, Headers.J, Headers.K])

        # Remove WELL column in the df_reservoir.
        df_reservoir = df_reservoir.drop([Headers.WELL], axis=1)
        # If multiple occurrences of same IJK in compdat/compsegs --> keep the last one.
        df_reservoir = df_reservoir.drop_duplicates(subset=Headers.START_MEASURED_DEPTH, keep="last")
        return df_reservoir.reset_index()

    @staticmethod
    def create_tubing_segments(
        df_reservoir, df_completion, df_mdtvd, method, case  # segment_length, minimum_segment_length
    ) -> pd.DataFrame:
        """Create tubing segments as the basis.

        The function creates a class property DataFrame df_tubing_segments
        from the class property DataFrames df_reservoir, df_completion, and df_mdtvd.

        The behavior of the df_tubing_segments will vary depending on the existence of the ICV keyword.
        When the ICV keyword is present, it always creates a lumped tubing segment on its interval,
        whereas other types of devices follow the default input.
        If there is a combination of an ICV and other devices (with devicetype >1),
        this results in a combination of ICV segment length with segment lumping,
        and default segment length on other devices.
        """
        df_tubing_cells = completion.create_tubing_segments(
            df_reservoir,
            df_completion,
            df_mdtvd,
            method,
            case.segment_length,
            case.minimum_segment_length,
        )

        df_tubing_user = completion.create_tubing_segments(
            df_reservoir,
            df_completion,
            df_mdtvd,
            Method.USER,
            case.segment_length,
            case.minimum_segment_length,
        )

        if (len(df_completion[Headers.DEVICE_TYPE].unique()) > 1) & (
            (df_completion[Headers.DEVICE_TYPE] == "ICV") & (df_completion[Headers.VALVES_PER_JOINT] > 0)
        ).any():
            return fix_compsegs_by_priority(df_completion, df_tubing_cells, df_tubing_user)

        # If all the devices are ICVs, lump the segments.
        if (df_completion[Headers.DEVICE_TYPE] == "ICV").all():
            return df_tubing_user
        # If none of the devices are ICVs use defined method.
        return df_tubing_cells

    def complete_the_well(self) -> None:
        """Complete the well with users' completion design."""
        self.df_well = completion.complete_the_well(self.df_tubing_segments, self.df_completion, self.case.joint_length)
        self.df_well[Headers.ROUGHNESS] = self.df_well[Headers.ROUGHNESS].apply(lambda x: f"{x:.3E}")

    def get_devices(self) -> None:
        """Complete the well with the device information.

        Updates the class property DataFrame df_well described in ``complete_the_well``.
        """
        if not self.case.completion_icv_tubing.empty:
            active_devices = pd.concat(
                [self.df_completion[Headers.DEVICE_TYPE], self.case.completion_icv_tubing[Headers.DEVICE_TYPE]]
            ).unique()
        else:
            active_devices = self.df_completion[Headers.DEVICE_TYPE].unique()
        if "VALVE" in active_devices:
            self.df_well = completion.get_device(self.df_well, self.case.wsegvalv_table, "VALVE")
        if "ICD" in active_devices:
            self.df_well = completion.get_device(self.df_well, self.case.wsegsicd_table, "ICD")
        if "AICD" in active_devices:
            self.df_well = completion.get_device(self.df_well, self.case.wsegaicd_table, "AICD")
        if "DAR" in active_devices:
            self.df_well = completion.get_device(self.df_well, self.case.wsegdar_table, "DAR")
        if "AICV" in active_devices:
            self.df_well = completion.get_device(self.df_well, self.case.wsegaicv_table, "AICV")
        if "ICV" in active_devices:
            self.df_well = completion.get_device(self.df_well, self.case.wsegicv_table, "ICV")

    def correct_annulus_zone(self) -> None:
        """Remove the annulus zone if there is no connection to the tubing."""
        self.df_well = completion.correct_annulus_zone(self.df_well)

    def connect_cells_to_segments(self) -> None:
        """Connect cells to the well.

        We only need the following columns from the well DataFrame: MEASURED_DEPTH, NDEVICES, DEVICETYPE, and ANNULUS_ZONE.

        ICV placement forces different methods in segment creation as USER defined.
        """
        # drop BRANCH column, not needed
        self.df_reservoir.drop([Headers.BRANCH], axis=1, inplace=True)
        icv_device = (
            self.df_well[Headers.DEVICE_TYPE].nunique() > 1
            and (self.df_well[Headers.DEVICE_TYPE] == "ICV").any()
            and not self.df_well[Headers.NUMBER_OF_DEVICES].empty
        )
        method = Method.USER if icv_device else self.method
        self.df_reservoir = completion.connect_cells_to_segments(
            self.df_well[
                [Headers.TUBING_MEASURED_DEPTH, Headers.NUMBER_OF_DEVICES, Headers.DEVICE_TYPE, Headers.ANNULUS_ZONE]
            ],
            self.df_reservoir,
            self.df_tubing_segments,
            method,
        )

    def add_well_lateral_column(self, lateral: int) -> None:
        """Add well and lateral column in df_well and df_compsegs."""
        self.df_well[Headers.WELL] = self.well_name
        self.df_reservoir[Headers.WELL] = self.well_name
        self.df_well[Headers.LATERAL] = lateral
        self.df_reservoir[Headers.LATERAL] = lateral
