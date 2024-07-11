"""Utilities for tests."""

from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import numpy as np
import pandas as pd

from completor import main, parse  # type: ignore
from completor.constants import Headers, Keywords
from completor.exceptions import CompletorError
from completor.read_schedule import fix_compsegs, fix_welsegs  # type: ignore
from completor.utils import abort, clean_file_lines  # type: ignore


def open_files_run_create(
    case: Path | str, schedule: Path | str, output: Path | str, show_figure: bool = False
) -> None:
    """Open files supplied as a path and convert the data to a string.

    Then run main.py's create function with the data.
    """
    if isinstance(case, Path):
        with open(case, encoding="utf-8") as file:
            case = file.read()

    if isinstance(schedule, Path):
        with open(schedule, encoding="utf-8") as file:
            schedule = file.read()

    if isinstance(output, Path):
        with open(output, encoding="utf-8") as file:
            output = file.read()

        main.create(case, schedule, output, show_figure)
    else:
        main.create(case, schedule, output)


def assert_results(true_file: str | Path, test_file: str | Path, check_exact=False, relative_tolerance=0.0001) -> None:
    """Assert the final Completor output.

    Args:
        true_file: True solution file.
        test_file: Completor output file.
        check_exact: Whether to compare number exactly.
        relative_tolerance: Relative tolerance, only used when check_exact is False.

    Notes:
        1. The dfs are sorted so that the order of input is *not* important.
           Also, the index is set to well so that the original order is not used as index.
        2. We do the comparison numerically, so we dont care about 4th decimal place.
           Use global variables CHECK_EXACT and N_DIGITS for this purpose.
        3. WELSPECS is not included in the comparison since this keyword is left untouched by completor.
    """

    if isinstance(true_file, Path):
        with open(true_file, encoding="utf-8") as file:
            true_output = ReadSchedule(file.read())
    else:
        true_output = ReadSchedule(true_file)

    # test COMPDAT, COMPSEGS and WELSEGS
    with open(test_file, encoding="utf-8") as file:
        test_output = ReadSchedule(file.read())

    # COMPDAT
    pd.testing.assert_frame_equal(
        true_output.compdat, test_output.compdat, check_exact=check_exact, rtol=relative_tolerance
    )
    # WELSEGS header
    wsh_true = true_output.welsegs_header
    wsh_true.set_index(Headers.WELL, inplace=True)
    wsh_true.sort_values(Headers.WELL, inplace=True)
    wsh_test = test_output.welsegs_header
    wsh_test.set_index(Headers.WELL, inplace=True)
    wsh_test.sort_values(Headers.WELL, inplace=True)
    pd.testing.assert_frame_equal(wsh_true, wsh_test, check_exact=check_exact, rtol=relative_tolerance)
    # WELSEGS content
    wsc_true = true_output.welsegs_content
    wsc_true.set_index(Headers.WELL, inplace=True)
    wsc_true.sort_values([Headers.WELL, Headers.TUBING_MEASURED_DEPTH], inplace=True)
    wsc_test = test_output.welsegs_content
    wsc_test.set_index(Headers.WELL, inplace=True)
    wsc_test.sort_values([Headers.WELL, Headers.TUBING_MEASURED_DEPTH], inplace=True)
    pd.testing.assert_frame_equal(wsc_true, wsc_test, check_exact=check_exact, rtol=relative_tolerance)

    # COMPSEGS
    cs_true = true_output.compsegs.set_index(Headers.WELL)
    cs_true.sort_values([Headers.WELL, Headers.START_MEASURED_DEPTH], inplace=True)
    cs_test = test_output.compsegs.set_index(Headers.WELL)
    cs_test.sort_values([Headers.WELL, Headers.START_MEASURED_DEPTH], inplace=True)
    pd.testing.assert_frame_equal(cs_true, cs_test, check_exact=check_exact, rtol=relative_tolerance)


class ReadSchedule:
    """Class for reading and processing of schedule/well files.

    This class reads the schedule/well file.
    It reads the following keywords WELSPECS, COMPDAT, WELSEGS, COMPSEGS.
    The program also reads other keywords, but the unrelated keywords will just be printed in the output file.

    Attributes:
        content (List[str]): The data.
        collections (List[completor.parser.ContentCollection]): Content collection of keywords in schedule file.
        unused_keywords (np.ndarray[str]): Array of strings of unused keywords in the schedule file.
        welspecs (pd.DataFrame): Table of WELSPECS keyword.
        compdat (pd.DataFrame): Table of COMPDAT keyword.
        compsegs (pd.DataFrame): Table of COMPSEGS keyword.
    """

    def __init__(
        self,
        schedule_file: str,
        optional_keywords: list[str] = ["WSEGVALV"],
    ):
        """Initialize the class.

        Args:
            schedule_file: Schedule/well file which contains at least `COMPDAT`, `COMPSEGS` and `WELSEGS`.
            optional_keywords: List of optional keywords to find tables for.
        """
        # read the file
        self.content = clean_file_lines(schedule_file.splitlines(), "--")

        # get contents of the listed keywords
        # and the content of the not listed keywords
        self.collections, self.unused_keywords = parse.read_schedule_keywords(
            self.content, Keywords.main_keywords, optional_keywords
        )
        # initiate values
        self.welspecs = pd.DataFrame()
        self.compdat = pd.DataFrame()
        self.compsegs = pd.DataFrame()
        self.wsegvalv = pd.DataFrame()
        self._welsegs_header: pd.DataFrame | None = None
        self._welsegs_content: pd.DataFrame | None = None

        # extract tables
        """This procedures gets tables of the listed keywords.

        It also formats the data type of the columns, which will be used in the completor program.
        """
        # get dataframe table
        self.welspecs = parse.get_welspecs_table(self.collections)
        self.compdat = parse.get_compdat_table(self.collections)
        self.compsegs = parse.get_compsegs_table(self.collections)
        self.wsegvalv = parse.get_wsegvalv_table(self.collections)

        self.compsegs = self.compsegs.astype(
            {
                Headers.I: np.int64,
                Headers.J: np.int64,
                Headers.K: np.int64,
                Headers.BRANCH: np.int64,
                Headers.START_MEASURED_DEPTH: np.float64,
                Headers.END_MEASURED_DEPTH: np.float64,
            }
        )
        self.compdat = self.compdat.astype(
            {
                Headers.I: np.int64,
                Headers.J: np.int64,
                Headers.K: np.int64,
                Headers.K2: np.int64,
                Headers.SKIN: np.float64,
            }
        )

        # If CONNECTION_FACTOR and FORMATION_PERMEABILITY_THICKNESS are defaulted by users, type conversion fails and
        # we deliberately ignore it:
        self.compdat = self.compdat.astype(
            {Headers.CONNECTION_FACTOR: np.float64, Headers.FORMATION_PERMEABILITY_THICKNESS: np.float64},
            errors="ignore",
        )

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
                Headers.TUBING_SEGMENT: np.int64,
                Headers.TUBING_SEGMENT_2: np.int64,
                Headers.TUBING_BRANCH: np.int64,
                Headers.TUBING_OUTLET: np.int64,
                Headers.TUBING_MEASURED_DEPTH: np.float64,
                Headers.TUBING_TRUE_VERTICAL_DEPTH: np.float64,
                Headers.TUBING_ROUGHNESS: np.float64,
            }
        )

        self._welsegs_header = welsegs_header.astype(
            {Headers.SEGMENT_TRUE_VERTICAL_DEPTH: np.float64, Headers.SEGMENT_MEASURED_DEPTH: np.float64}
        )
        return self._welsegs_header, self._welsegs_content  # type: ignore

    def get_welspecs(self, well_name: str) -> pd.DataFrame:
        """Return the WELSPECS table of the selected well.

        Args:
            well_name: Name of the well.

        Returns:
            WELSPECS table for that well.
        """
        df_temp = self.welspecs[self.welspecs[Headers.WELL] == well_name]
        # reset index after filtering
        df_temp.reset_index(drop=True, inplace=True)
        return df_temp

    def get_compdat(self, well_name: str) -> pd.DataFrame:
        """Return the COMPDAT table for that well.

        Args:
            well_name: Name of the well.

        Returns:
            COMPDAT table for that well.
        """
        df_temp = self.compdat[self.compdat[Headers.WELL] == well_name]
        # reset index after filtering
        df_temp.reset_index(drop=True, inplace=True)
        return df_temp

    def get_welsegs(self, well_name: str, branch: int | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Return WELSEGS table for both header and content for the selected well.

        Args:
            well_name: Name of the well.
            branch: Branch/lateral number.

        Returns:
            WELSEGS first record (df_header).
            WELSEGS second record (df_content).
        """
        df1_welsegs = self.welsegs_header[self.welsegs_header[Headers.WELL] == well_name]
        df2_welsegs = self.welsegs_content[self.welsegs_content[Headers.WELL] == well_name].copy()
        if branch is not None:
            df2_welsegs = df2_welsegs[df2_welsegs[Headers.TUBING_BRANCH] == branch]
        # remove the well column because it does not exist
        # in the original input
        df2_welsegs.drop([Headers.WELL], inplace=True, axis=1)
        # reset index after filtering
        df1_welsegs.reset_index(drop=True, inplace=True)
        df2_welsegs.reset_index(drop=True, inplace=True)
        df_header, df_content = fix_welsegs(df1_welsegs, df2_welsegs)
        return df_header, df_content

    def get_compsegs(self, well_name: str, branch: int | None = None) -> pd.DataFrame:
        """Return COMPSEGS table for the selected well.

        Args:
            well_name: Name of the well.
            branch: Branch/lateral number.

        Returns:
            COMPSEGS table.
        """
        df_temp = self.compsegs[self.compsegs[Headers.WELL] == well_name].copy()
        if branch is not None:
            df_temp = df_temp[df_temp[Headers.BRANCH] == branch]
        # remove the well column because it does not exist
        # in the original input
        df_temp.drop([Headers.WELL], inplace=True, axis=1)
        # reset index after filtering
        df_temp.reset_index(drop=True, inplace=True)
        return fix_compsegs(df_temp, well_name)


def _mock_parse_args(**kwargs):

    # Set default values.
    kwargs["loglevel"] = 0 if kwargs.get("loglevel") is None else kwargs["loglevel"]
    kwargs["figure"] = False if kwargs.get("figure") is None else kwargs["figure"]
    kwargs["schedulefile"] = None if kwargs.get("schedulefile") is None else kwargs["schedulefile"]
    kwargs["outputfile"] = None if kwargs.get("outputfile") is None else kwargs["outputfile"]

    def _mock_get_parser():
        class MockObject:
            @staticmethod
            def parse_args() -> Namespace:
                return Namespace(**kwargs)

        return MockObject

    setattr(main, "get_parser", _mock_get_parser)


def completor_runner(**kwargs) -> None:
    """Helper function to run completor as if it was launched as a CLI program.

    Function mocks args_parser and makes it return the values specified in **kwargs.

    Args:
        kwargs: Keyword arguments to run completor with.
    """
    _mock_parse_args(**kwargs)
    try:
        main.main()
    except CompletorError as e:
        raise abort(str(e))
