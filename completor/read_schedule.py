from __future__ import annotations

import numpy as np
import pandas as pd

from completor import parse
from completor.constants import Completion, WellSegment
from completor.logger import logger
from completor.utils import clean_file_lines, sort_by_midpoint


def fix_welsegs(df_header: pd.DataFrame, df_content: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Convert a WELSEGS DataFrame specified in INC to ABS.

    Args:
        df_header: First record table of WELSEGS
        df_content: Second record table of WELSEGS

    Returns:
        tuple: (Updated header DataFrame, Updated content DataFrame)

    The formats of df_header and df_content are shown as df_welsegs_header and
    df_welsegs_content respectively in the function
    :ref:`create_wells.CreateWells.select_well <select_well>`.
    """
    df_header = df_header.copy()
    df_content = df_content.copy()

    if df_header["INFOTYPE"].iloc[0] == "ABS":
        return df_header, df_content

    ref_tvd = df_header["SEGMENTTVD"].iloc[0]
    ref_md = df_header["SEGMENTMD"].iloc[0]
    inlet_segment = df_content[WellSegment.TUBING_SEGMENT].to_numpy()
    outlet_segment = df_content[WellSegment.TUBING_OUTLET].to_numpy()
    md_inc = df_content[WellSegment.TUBING_MD].to_numpy()
    tvd_inc = df_content[WellSegment.TUBING_TVD].to_numpy()
    md_new = np.zeros(inlet_segment.shape[0])
    tvd_new = np.zeros(inlet_segment.shape[0])

    for idx, idx_segment in enumerate(outlet_segment):
        if idx_segment == 1:
            md_new[idx] = ref_md + md_inc[idx]
            tvd_new[idx] = ref_tvd + tvd_inc[idx]
        else:
            out_idx = np.where(inlet_segment == idx_segment)[0][0]
            md_new[idx] = md_new[out_idx] + md_inc[idx]
            tvd_new[idx] = tvd_new[out_idx] + tvd_inc[idx]

    # update data frame
    df_header["INFOTYPE"] = ["ABS"]
    df_content[WellSegment.TUBING_MD] = md_new
    df_content[WellSegment.TUBING_TVD] = tvd_new
    return df_header, df_content


def fix_compsegs(df_compsegs: pd.DataFrame, well_name: str) -> pd.DataFrame:
    """
    Fix the problem of having multiple connections in one cell.

    The issue occurs when one cell is penetrated more than once by a well, and happens
    when there are big cells and the well path is complex.
    The issue can be observed from a COMPSEGS definition that has overlapping start and
    end measured depth.

    Args:
        df_compsegs: DataFrame
        well_name: Well name

    Returns:
        Sorted DataFrame

    The DataFrame df is obtained from`` msws[well_name]['compsegs']``
    and has the following format:

        .. _compsegs_format:
        .. list-table:: df
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
             - str
           * - ENDGRID
             - object
           * - PERFDEPTH
             - float
           * - THERM
             - object
           * - SEGMENT
             - int
    """
    df_compsegs = df_compsegs.copy(deep=True)
    start_md = df_compsegs[Completion.START_MD].to_numpy()
    end_md = df_compsegs[Completion.END_MD].to_numpy()
    data_length = len(start_md)
    start_md_new = np.zeros(data_length)
    end_md_new = np.zeros(data_length)

    if len(start_md) > 0:
        start_md_new[0] = start_md[0]
        end_md_new[0] = end_md[0]

    # Check the cells connection
    for idx in range(1, len(start_md)):
        if (start_md[idx] - end_md_new[idx - 1]) < -0.1:
            if end_md[idx] > end_md_new[idx - 1]:
                # fix the start of current cells
                start_md_new[idx] = end_md_new[idx - 1]
                end_md_new[idx] = end_md[idx]

            # fix the end of the previous cells
            elif start_md[idx] > start_md_new[idx - 1]:
                end_md_new[idx - 1] = start_md[idx]
                start_md_new[idx - 1] = start_md_new[idx - 1]
                start_md_new[idx] = start_md[idx]
                end_md_new[idx] = end_md[idx]
            else:
                logger.info(
                    "Overlapping in COMPSEGS for %s. Sorts the depths accordingly",
                    well_name,
                )
                comb_depth = np.append(start_md, end_md)
                comb_depth = np.sort(comb_depth)
                start_md_new = np.copy(comb_depth[::2])
                end_md_new = np.copy(comb_depth[1::2])
                break
        else:
            start_md_new[idx] = start_md[idx]
            end_md_new[idx] = end_md[idx]
    # In some instances with complex overlapping segments, the algorithm above
    # creates segments where start == end. To overcome this, the following is added.
    for idx in range(1, len(start_md_new) - 1):
        if start_md_new[idx] == end_md_new[idx]:
            if start_md_new[idx + 1] >= end_md_new[idx]:
                end_md_new[idx] = start_md_new[idx + 1]
            if start_md_new[idx] >= end_md_new[idx - 1]:
                start_md_new[idx] = end_md_new[idx - 1]
            else:
                logger.error("Cannot construct COMPSEGS segments based on current input")
    return sort_by_midpoint(df_compsegs, end_md_new, start_md_new)


def fix_compsegs_by_priority(
    df_completion: pd.DataFrame, df_compsegs: pd.DataFrame, df_custom_compsegs: pd.DataFrame
) -> pd.DataFrame:
    """
    Fixes a dataframe of composition segments, prioritizing the custom compseg.

    Args:
        df_completion: ..
        df_compsegs: Containing composition segments data.
        df_custom_compsegs: Containing custom composition segments data with priority.

    Returns:
        Fixed composition segments dataframe.

    """
    # slicing two dataframe for user and cells segment length
    start_md_comp = df_completion[(df_completion["DEVICETYPE"] == "ICV") & (df_completion["NVALVEPERJOINT"] > 0)][
        "STARTMD"
    ].reset_index(drop=True)
    df_custom_compsegs = df_custom_compsegs[df_custom_compsegs["STARTMD"].isin(start_md_comp)]
    df_compsegs["priority"] = 1
    df_custom_compsegs = df_custom_compsegs.copy(deep=True)
    df_custom_compsegs["priority"] = 2
    start_end = df_custom_compsegs[["STARTMD", "ENDMD"]]
    # Remove the rows that are between the STARTMD and ENDMD
    # values of the custom composition segments.
    for start, end in start_end.values:
        between_lower_upper = (df_compsegs["STARTMD"] >= start) & (df_compsegs["ENDMD"] <= end)
        df_compsegs = df_compsegs[~between_lower_upper]

    # Concatenate the fixed df_compsegs dataframe and the df_custom_compsegs
    # dataframe and sort it by the STARTMD column.
    df = pd.concat([df_compsegs, df_custom_compsegs]).sort_values(by=["STARTMD"]).reset_index(drop=True)
    # Filter the dataframe to get only rows where the "priority" column has a value of 2
    for idx in df[df["priority"] == 2].index:
        # Set previous row's ENDMD to correct value.
        df.loc[idx - 1, "ENDMD"] = df.loc[idx, "STARTMD"]
        # Set next row's STARTMD to correct value.
        df.loc[idx + 1, "STARTMD"] = df.loc[idx, "ENDMD"]
    df = fix_compsegs(df, "Fix compseg after prioriry")
    df = df.dropna()

    return df.drop("priority", axis=1)


class ReadSchedule:
    """
    Class for reading and processing of schedule/well files.

    This class reads the schedule/well file.
    It reads the following keywords WELSPECS, COMPDAT, WELSEGS, COMPSEGS.
    The program also reads other keywords, but the unrelated keywords
    will just be printed in the output file.

    Attributes:
        content (List[str]): List of strings
        collections (List[completor.parser.ContentCollection]):
            Content collection of keywords in schedule file
        unused_keywords (np.ndarray[str]): Array of strings of unused keywords
            in the schedule file
        welspecs (pd.DataFrame): Table of WELSPECS keyword
        compdat (pd.DataFrame): Table of COMPDAT keyword
        compsegs (pd.DataFrame): Table of COMPSEGS keyword
        wsegvalv (pd.DataFrame): Table of WSEGVALV keyword

    See the following functions for a description of DataFrame formats:
        :ref:`welspecs <welspecs_format>`.
        :ref:`compdat <compdat_table>` (See: ref:`update_connection_factor <update_connection_factor>` for more details).
        :ref:`welsegs_header <df_welsegs_header>`.
        :ref:`welsegs_content <df_welsegs_content>`.
        compsegs `get_compsegs_table`.
    """

    def __init__(
        self,
        schedule_file: str,
        keywords: list[str] = ["WELSPECS", "COMPDAT", "WELSEGS", "COMPSEGS"],
        optional_keywords: list[str] = ["WSEGVALV"],
    ):
        """
        Initialize the class.

        Args:
            schedule_file: Schedule/well file which contains at least
                      ``COMPDAT``, ``COMPSEGS`` and ``WELSEGS``
            keywords: List of necessary keywords to find tables for.
            optional_keywords: List of optional keywords to find tables for.
        """
        # read the file
        self.content = clean_file_lines(schedule_file.splitlines(), "--")

        # get contents of the listed keywords
        # and the content of the not listed keywords
        self.collections, self.unused_keywords = parse.read_schedule_keywords(self.content, keywords, optional_keywords)
        # initiate values
        self.welspecs = pd.DataFrame()
        self.compdat = pd.DataFrame()
        self.compsegs = pd.DataFrame()
        self.wsegvalv = pd.DataFrame()
        self._welsegs_header: pd.DataFrame | None = None
        self._welsegs_content: pd.DataFrame | None = None

        # extract tables
        """
        This procedures gets tables of the listed keywords.

        It also formats the data type of the columns, which will be used
        in the completor program.
        """
        # get dataframe table
        self.welspecs = parse.get_welspecs_table(self.collections)
        self.compdat = parse.get_compdat_table(self.collections)
        self.compsegs = parse.get_compsegs_table(self.collections)
        self.wsegvalv = parse.get_wsegvalv_table(self.collections)

        self.compsegs = self.compsegs.astype(
            {
                "I": np.int64,
                "J": np.int64,
                "K": np.int64,
                "BRANCH": np.int64,
                "STARTMD": np.float64,
                "ENDMD": np.float64,
            }
        )
        self.compdat = self.compdat.astype(
            {"I": np.int64, "J": np.int64, "K": np.int64, "K2": np.int64, "SKIN": np.float64}
        )

        # If CF and KH are defaulted by users, type conversion fails and
        # we deliberately ignore it:
        self.compdat = self.compdat.astype({"CF": np.float64, "KH": np.float64}, errors="ignore")

    @property
    def welsegs_header(self) -> pd.DataFrame:
        """Table of the WELSEGS header, the first record of WELSEGS keyword."""
        if self._welsegs_header is None:
            welsegs_header, _ = self._compute_welsegs()
            self._welsegs_header = welsegs_header
        return self._welsegs_header

    @property
    def welsegs_content(self) -> pd.DataFrame:
        """Table of the WELSEGS content, the second record of WELSEGS keyword."""
        if self._welsegs_content is None:
            _, welsegs_content = self._compute_welsegs()
            self._welsegs_content = welsegs_content
        return self._welsegs_content

    def _compute_welsegs(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Set correct types for information in WELSEGS header and content."""
        welsegs_header, welsegs_content = parse.get_welsegs_table(self.collections)
        self._welsegs_content = welsegs_content.astype(
            {
                "TUBINGSEGMENT": np.int64,
                "TUBINGSEGMENT2": np.int64,
                "TUBINGBRANCH": np.int64,
                "TUBINGOUTLET": np.int64,
                "TUBINGMD": np.float64,
                "TUBINGTVD": np.float64,
                "TUBINGROUGHNESS": np.float64,
            }
        )

        self._welsegs_header = welsegs_header.astype({"SEGMENTTVD": np.float64, "SEGMENTMD": np.float64})
        return self._welsegs_header, self._welsegs_content  # type: ignore

    def get_welspecs(self, well_name: str) -> pd.DataFrame:
        """
        Return the WELSPECS table of the selected well.

        Args:
            well_name: Name of the well

        Returns:
            WELSPECS table for that well
        """
        df_temp = self.welspecs[self.welspecs["WELL"] == well_name]
        # reset index after filtering
        df_temp.reset_index(drop=True, inplace=True)
        return df_temp

    def get_compdat(self, well_name: str) -> pd.DataFrame:
        """
        Return the COMPDAT table for that well.

        Args:
            well_name: Name of the well

        Returns:
            COMPDAT table for that well
        """
        df_temp = self.compdat[self.compdat["WELL"] == well_name]
        # reset index after filtering
        df_temp.reset_index(drop=True, inplace=True)
        return df_temp

    def get_welsegs(self, well_name: str, branch: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Return WELSEGS table for both header and content for the selected well.

        Args:
            well_name: Name of the well
            branch: Branch/lateral number

        Returns:
            | WELSEGS first record (df_header)
            | WELSEGS second record (df_content)
        """
        df1_welsegs = self.welsegs_header[self.welsegs_header["WELL"] == well_name]
        df2_welsegs = self.welsegs_content[self.welsegs_content["WELL"] == well_name].copy()
        if branch is not None:
            df2_welsegs = df2_welsegs[df2_welsegs["TUBINGBRANCH"] == branch]
        # remove the well column because it does not exist
        # in the original input
        df2_welsegs.drop(["WELL"], inplace=True, axis=1)
        # reset index after filtering
        df1_welsegs.reset_index(drop=True, inplace=True)
        df2_welsegs.reset_index(drop=True, inplace=True)
        df_header, df_content = fix_welsegs(df1_welsegs, df2_welsegs)
        return df_header, df_content

    def get_compsegs(self, well_name: str, branch: int | None = None) -> pd.DataFrame:
        """
        Return COMPSEGS table for the selected well.

        Args:
            well_name: Name of the well
            branch: Branch/lateral number

        Returns:
            COMPSEGS table
        """
        df_temp = self.compsegs[self.compsegs["WELL"] == well_name].copy()
        if branch is not None:
            df_temp = df_temp[df_temp["BRANCH"] == branch]
        # remove the well column because it does not exist
        # in the original input
        df_temp.drop(["WELL"], inplace=True, axis=1)
        # reset index after filtering
        df_temp.reset_index(drop=True, inplace=True)
        return fix_compsegs(df_temp, well_name)
