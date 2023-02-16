"""Module for creating completion structure."""

from __future__ import annotations

import numpy as np
import pandas as pd

from completor import completion
from completor.constants import SegmentCreationMethod
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
        method (SegmentCreationMethod): Method for segment creation
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

