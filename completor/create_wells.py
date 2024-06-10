"""Module for creating completion structure."""

from __future__ import annotations

import numpy as np
import pandas as pd

from completor import completion
from completor.constants import Method
from completor.logger import logger
from completor.read_casefile import ReadCasefile
from completor.read_schedule import fix_compsegs_by_priority

try:
    import numpy.typing as npt
except ImportError:
    pass


class CreateWells:
    """
    Class for creating well completion structure.

    Inputs to this class are two objects:

    1. class ReadCasefile
    2. class ReadSchedule

    Args:
        case: ReadCasefile class

    Attributes:
        schedule: ReadSchedule class
        active_wells (List): Active wells defined in the case file
        method (Method): Method for segment creation
        well_name (str): Well name (in loop)
        laterals (np.ndarray[int]): List of lateral number of the well in loop
        df_completion (pd.DataFrame): Completion data frame in loop
        df_reservoir (pd.DataFrame): COMPDAT and COMPSEGS data frame fusion in loop
        df_welsegs_header (pd.DataFrame): WELSEGS first record
        df_welsegs_content (pd.DataFrame): WELSEGS second record
        df_mdtvd (pd.DataFrame): Data frame of MD and TVD relationship
        df_tubing_segments (pd.DataFrame): Tubing segment data frame
        df_well (pd.DataFrame): Data frame after completion
        df_well_all (pd.DataFrame): Data frame (df_well) for all laterals
            after completion
        df_reservoir_all (pd.DataFrame): df_reservoir for all laterals
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
        """
        Update class variables in CreateWells.

        Args:
            well_name: Well name
            schedule: ReadSchedule object

        """
        self.well_name = well_name
        self._active_laterals()
        for lateral in self.laterals:
            self.select_well(schedule, lateral)
            self.well_trajectory()
            self.define_annulus_zone()
            self.create_tubing_segments()
            self.insert_missing_segments()
            self.complete_the_well()
            self.get_devices()
            self.correct_annulus_zone()
            self.connect_cells_to_segments()
            self.add_well_lateral_column(lateral)
            self.combine_df(lateral)

    def _active_wells(self) -> npt.NDArray[np.unicode_]:
        """
        Get a list of active wells specified by users.

        If the well has annulus content set to gravel pack and the well is perforated,
        Completor will not add a device layer. In fact, completor do nothing to
        gravel-packed perforated wells by default. This behavior can be changed by
        setting the GP_PERF_DEVICELAYER keyword in the case file to true.

        ``get_activewells`` uses the case class DataFrame property ``completion_table``
        with a format as shown in the function
        ``read_casefile.ReadCasefile.read_completion``.

        Returns:
            Active wells
        """
        # Need to check completion of all wells in completion table to remove
        # GP-PERF type wells
        active_wells = list(set(self.case.completion_table["WELL"]))
        # We cannot update a list while iterating of it
        for well_name in active_wells.copy():
            # Annulus content of each well
            ann_series = self.case.completion_table[self.case.completion_table["WELL"] == well_name]["ANNULUS"]
            type_series = self.case.completion_table[self.case.completion_table["WELL"] == well_name]["DEVICETYPE"]
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
        """
        Define how the user wants to create segments.

        Returns:
            Creation method enum OR ValueError

        Raises:
            ValueError: If method is not one of the defined methods
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
                    f"Unrecognized method '{self.case.segment_length}' in "
                    "SEGMENTLENGTH keyword. The value should be one of: "
                    "'WELSEGS', 'CELLS', 'USER', or a number: -1 for 'USER', "
                    "0 for 'CELLS', positive number for 'FIX'."
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
                f"Unrecognized type of '{self.case.segment_length}' in "
                "SEGMENTLENGTH keyword. The keyword must either be float or string."
            )

    def _active_laterals(self) -> None:
        """
        Get a list of lateral numbers for the well.

        ``get_active_laterals`` uses the case class DataFrame property
        ``completion_table`` with a format as shown in the function
        ``read_casefile.ReadCasefile.read_completion``.
        """
        self.laterals = list(
            self.case.completion_table[self.case.completion_table["WELL"] == self.well_name]["BRANCH"].unique()
        )

    def select_well(self, schedule: completion.WellSchedule, lateral: int) -> None:
        """
        .. _select_well:

        Filter all of the required DataFrames for this well and its laterals.

        The function sets the class property DataFrames df_completion, df_well_segments_header
        and df_well_segments_content, and df_reservoir, with the following formats:

        .. _df_completion:
        .. list-table:: df_completion
           :widths: 10 10
           :header-rows: 1

           * - COLUMNS
             - TYPE
           * - WELL
             - str
           * - BRANCH
             - int
           * - STARTMD
             - float
           * - ENDMD
             - float
           * - INNER_DIAMETER
             - float
           * - OUTER_DIAMETER
             - float
           * - ROUGHNESS
             - float
           * - ANNULUS
             - str
           * - NVALVEPERJOINT
             - float
           * - DEVICETYPE
             - str
           * - ANNULUS_ZONE
             - int

        .. _df_welsegs_header:
        .. list-table:: df_well_segments_header (WELSEGS header)
           :widths: 10 10
           :header-rows: 1

           * - COLUMN
             - TYPE
           * - WELL
             - str
           * - SEGMENTTVD
             - float
           * - SEGMENTMD
             - float
           * - WBVOLUME
             - float
           * - INFOTYPES
             - str
           * - PDROPCOMP
             - str
           * - MPMODEL
             - str
           * - ITEM8
             - float
           * - ITEM9
             - float
           * - ITEM10
             - float
           * - ITEM11
             - float
           * - ITEM12
             - float

        .. _df_welsegs_content:
        .. list-table:: df_well_segments_content (WELSEGS record)
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
             - float
           * - ITEM12
             - float
           * - ITEM13
             - float
           * - ITEM14
             - float
           * - ITEM15
             - float

        .. _df_reservoir:
        .. list-table:: df_reservoir
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
           * - STARTMD
             - float
           * - ENDMD
             - float
           * - COMPSEGS_DIRECTION
             - str
           * - ENDGRID
             -
           * - PERFDEPTH
             - float
           * - THERM
             -
           * - SEGMENT
             - int
           * - K2
             - int
           * - STATUS
             - str
           * - SATNUM
             - int
           * - CF
             - float
           * - DIAM
             - float
           * - KH
             - float
           * - SKIN
             - float
           * - DFACT
             - float
           * - COMPDAT_DIRECTION
             - str
           * - RO
             - float
           * - MD
             - float
           * - TUB_MD
             - float
           * - NDEVICES
             - float
           * - ANNULUS_ZONE
             - int
           * - WELL
             - str
           * - LATERAL
             - int

        """
        if self.well_name is None:
            raise ValueError("No well name given")

        self.df_completion = self.case.get_completion(self.well_name, lateral)
        self.df_welsegs_header, self.df_welsegs_content = schedule.get_well_segments(self.well_name, lateral)
        df_compsegs = schedule.get_compsegs(self.well_name, lateral)
        df_compdat = schedule.get_compdat(self.well_name)
        self.df_reservoir = pd.merge(df_compsegs, df_compdat, how="inner", on=["I", "J", "K"])

        # Remove WELL column in the df_reservoir.
        self.df_reservoir.drop(["WELL"], inplace=True, axis=1)
        # If multiple occurrences of same IJK in compdat/compsegs --> keep the last one.
        self.df_reservoir.drop_duplicates(subset="STARTMD", keep="last", inplace=True)
        self.df_reservoir.reset_index(inplace=True)

    def well_trajectory(self) -> None:
        """
        Create trajectory DataFrame relations between MD and TVD.

        The function uses the class property DataFrames df_well_segments_header
        and df_well_segments_content with the following formats:

        .. list-table:: df_well_segments_header (WELSEGS header)
           :widths: 10 10
           :header-rows: 1

           * - COLUMN
             - TYPE
           * - WELL
             - str
           * - SEGMENTTVD
             - float
           * - SEGMENTMD
             - float
           * - WBVOLUME
             - float
           * - INFOTYPES
             - str
           * - PDROPCOMP
             - str
           * - MPMODEL
             - str
           * - ITEM8
             - float
           * - ITEM9
             - float
           * - ITEM10
             - float
           * - ITEM11
             - float
           * - ITEM12
             - float

        .. list-table:: df_well_segments_content (WELSEGS record)
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
             - float
           * - ITEM12
             - float
           * - ITEM13
             - float
           * - ITEM14
             - float
           * - ITEM15
             - float

        The function sets the class property df_mdtvd with the following format

        .. _df_mdtvd:
        .. list-table:: df_mdtvd
           :widths: 10 10
           :header-rows: 1

           * - COLUMNS
             - TYPE
           * - MD
             - float
           * - TVD
             - float

        """
        self.df_mdtvd = completion.well_trajectory(self.df_welsegs_header, self.df_welsegs_content)

    def define_annulus_zone(self) -> None:
        """
        Define an annulus zone if specified.

        The function adjusts the class property DataFrames df_completion,
        with the following format:

        .. list-table:: df_completion
           :widths: 10 10
           :header-rows: 1

           * - COLUMNS
             - TYPE
           * - WELL
             - str
           * - BRANCH
             - int
           * - STARTMD
             - float
           * - ENDMD
             - float
           * - INNER_DIAMETER
             - float
           * - OUTER_DIAMETER
             - float
           * - ROUGHNESS
             - float
           * - ANNULUS
             - str
           * - NVALVEPERJOINT
             - float
           * - DEVICETYPE
             - str
           * - ANNULUS_ZONE
             - int
        """
        self.df_completion = completion.define_annulus_zone(self.df_completion)

    def create_tubing_segments(self) -> None:
        """
        Create tubing segments as the basis.

        The function creates a class property DataFrame df_tubing_segments
        from the class property DataFrames df_reservoir, df_completion, and df_mdtvd.

        The behavior of the df_tubing_segments will vary depending on
        the existence of the ICV keyword. When the ICV keyword is present,
        it always creates a lumped tubing segment on its interval,
        whereas other types of devices follow the default input.
        If there is a combination of an ICV and other devices (with devicetype >1),
        this results in a combination of ICV segment length with
        segment lumping, and default segment length on other devices.

        The format of df_completion is shown in ``define_annuluszone`` and the
        format of df_mdtvd is given in ``well_trajectory``. The formats of
        df_reservoir and df_tubing_segments are as follows:

        .. list-table:: df_reservoir
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
           * - STARTMD
             - float
           * - ENDMD
             - float
           * - COMPSEGS_DIRECTION
             - str
           * - ENDGRID
             -
           * - PERFDEPTH
             - float
           * - THERM
             -
           * - SEGMENT
             - int
           * - K2
             - int
           * - STATUS
             - str
           * - SATNUM
             - int
           * - CF
             - float
           * - DIAM
             - float
           * - KH
             - float
           * - SKIN
             - float
           * - DFACT
             - float
           * - COMPDAT_DIRECTION
             - str
           * - RO
             - float
           * - MD
             - float
           * - TUB_MD
             - float
           * - NDEVICES
             - float
           * - ANNULUS_ZONE
             - int
           * - WELL
             - str
           * - LATERAL
             - int

        .. _df_tubing_segments:
        .. list-table:: df_tubing_segments
           :widths: 10 10
           :header-rows: 1

           * - COLUMNS
             - TYPE
           * - STARTMD
             - float
           * - ENDMD
             - float
           * - TUB_MD
             - float
           * - TUB_TVD
             - float
           * - SEGMENT_DESC
             - str
        """

        df_tubing_cells = completion.create_tubing_segments(
            self.df_reservoir,
            self.df_completion,
            self.df_mdtvd,
            self.method,
            self.case.segment_length,
            self.case.minimum_segment_length,
        )

        df_tubing_user = completion.create_tubing_segments(
            self.df_reservoir,
            self.df_completion,
            self.df_mdtvd,
            Method.USER,
            self.case.segment_length,
            self.case.minimum_segment_length,
        )

        if (len(self.df_completion["DEVICETYPE"].unique()) > 1) & (
            (self.df_completion["DEVICETYPE"] == "ICV") & (self.df_completion["NVALVEPERJOINT"] > 0)
        ).any():
            self.df_tubing_segments = fix_compsegs_by_priority(self.df_completion, df_tubing_cells, df_tubing_user)

        # If all the devices are ICVs, lump the segments.
        elif (self.df_completion["DEVICETYPE"] == "ICV").all():
            self.df_tubing_segments = df_tubing_user
        # If none of the devices are ICVs use defined method.
        else:
            self.df_tubing_segments = df_tubing_cells

    def insert_missing_segments(self) -> None:
        """
        Create a dummy segment for inactive cells.

        Uses the class property DataFrame df_tubing_segments, which is described in
        ``create_tubing_segments``.
        """
        self.df_tubing_segments = completion.insert_missing_segments(self.df_tubing_segments, self.well_name)

    def complete_the_well(self) -> None:
        """
        Complete the well with users completion design.

        Uses the class property DataFrames df_tubing_segments,
        see ``create_tubing_segments``, and df_completion, see ``select_well``.
        Sets the class property DataFrame df_well with the following format
        (for an AICD example):

        .. _df_well:
        .. list-table:: df_well
           :widths: 10 10
           :header-rows: 1

           * - COLUMNS
             - TYPE
           * - TUB_MD
             - float
           * - TUB_TVD
             - float
           * - LENGTH
             - float
           * - SEGMENT_DESC
             - str
           * - NDEVICES
             - float
           * - DEVICENUMBER
             - int
           * - DEVICETYPE
             - str
           * - INNER_DIAMETER
             - float
           * - OUTER_DIAMETER
             - float
           * - ROUGHNESS
             - float
           * - ANNULUS_ZONE
             - int
           * - SCALINGFACTOR
             - float
           * - ALPHA
             - float
           * - X
             - float
           * - Y
             - float
           * - A
             - float
           * - B
             - float
           * - C
             - float
           * - D
             - float
           * - E
             - float
           * - F
             - float
           * - RHOCAL_AICD
             - float
           * - VISCAL_AICD
             - float
           * - WELL
             - str
           * - LATERAL
             - int
        """
        self.df_well = completion.complete_the_well(self.df_tubing_segments, self.df_completion, self.case.joint_length)
        self.df_well["ROUGHNESS"] = self.df_well["ROUGHNESS"].apply(lambda x: f"{x:.3E}")

    def get_devices(self) -> None:
        """
        Complete the well with the device information.

        Uses the following class property DataFrames:

        * :ref:`df_completion <df_completion>`
        * :ref:`wsegvalv_table <wsegvalv_table>`
        * :ref:`wsegsicd_table <wsegsicd_table>`
        * :ref:`wsegaicd_table <wsegaicd_table>`
        * :ref:`wsegdar_table <wsegdar_table>`
        * :ref:`wsegaicv_table <wsegaicv_table>`
        * :ref:`wsegicv_table <wsegicv_table>`

        Updates the class property DataFrame df_well described in ``complete_the_well``.
        """
        if not self.case.completion_icv_tubing.empty:
            active_devices = pd.concat(
                [self.df_completion["DEVICETYPE"], self.case.completion_icv_tubing["DEVICETYPE"]]
            ).unique()
        else:
            active_devices = self.df_completion["DEVICETYPE"].unique()
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
        """
        Remove annulus zone if there is no connection to the tubing.

        Uses and updates the class property DataFrame df_well described in
        ``complete_the_well``.
        """
        self.df_well = completion.correct_annulus_zone(self.df_well)

    def connect_cells_to_segments(self) -> None:
        """
        Connect cells to the well.

        We only need the following columns from the well DataFrame:
        MD, NDEVICES, DEVICETYPE, and ANNULUS_ZONE

        ICV placement forces different method in segment creation as USER defined

        Updates the class property DataFrame :ref:`df_reservoir` and uses the
        class property DataFrame :ref:`df_well`.
        """
        # drop BRANCH column, not needed
        self.df_reservoir.drop(["BRANCH"], axis=1, inplace=True)
        icv_device = (
            self.df_well["DEVICETYPE"].nunique() > 1
            and (self.df_well["DEVICETYPE"] == "ICV").any()
            and not self.df_well["NDEVICES"].empty
        )
        method = Method.USER if icv_device else self.method
        self.df_reservoir = completion.connect_cells_to_segments(
            self.df_well[["TUB_MD", "NDEVICES", "DEVICETYPE", "ANNULUS_ZONE"]],
            self.df_reservoir,
            self.df_tubing_segments,
            method,
        )

    def add_well_lateral_column(self, lateral: int) -> None:
        """
        Add well and lateral column in df_well and df_compsegs.

        The format of the class property DataFrame df_well is described in
        ``complete_the_well`` and df_reservoir in ``select_well``.
        """
        self.df_well["WELL"] = self.well_name
        self.df_reservoir["WELL"] = self.well_name
        self.df_well["LATERAL"] = lateral
        self.df_reservoir["LATERAL"] = lateral

    def combine_df(self, lateral: int) -> None:
        """
        Combine all DataFrames for this well.

        The function uses the class property DataFrames :ref:`df_well`,
        and :ref:`df_reservoir`.
        """
        if lateral == self.laterals[0]:
            self.df_well_all = self.df_well.copy(deep=True)
            self.df_reservoir_all = self.df_reservoir.copy(deep=True)
        else:
            self.df_well_all = pd.concat([self.df_well_all, self.df_well], sort=False)
            self.df_reservoir_all = pd.concat([self.df_reservoir_all, self.df_reservoir], sort=False)
