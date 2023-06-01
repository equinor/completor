"""Defines a class for generating output files."""

from __future__ import annotations

import getpass
from datetime import datetime

import matplotlib  # type: ignore

from completor import prepare_outputs as po
from completor.completion import WellSchedule
from completor.create_wells import CreateWells
from completor.logger import logger
from completor.pvt_model import CORRELATION_UDQ
from completor.read_casefile import ReadCasefile
from completor.visualize_well import visualize_well


class CreateOutput:
    """
    Create output files from completor.

    There are two output files from completor:
        1. Well schedule file (text file) for input to eclipse
        2. Well diagram (pdf file), i.e. a well completion schematic

    Args:
        case: ReadCasefile object
        schedule: ReadSchedule object
        wells: CreateWells object
        well_name: Well name
        iwell: Well number used in creating WSEGAICV and WSEGDAR output
        version: Completor version information
        show_figure: Flag for pdf export of well completion schematic
        figure_no: Figure number
        write_welsegs: Flag to write WELSEGS

    | The class uses DataFrames with formats described in the following
      functions:
    | :ref:`df_reservoir`
    | :ref:`df_well`

    The class creates property DataFrames with the following formats:

    .. _df_tubing:
    .. list-table:: df_tubing
       :widths: 10 10
       :header-rows: 1

       * - COLUMNS
         - TYPE
       * - SEG
         - int
       * - SEG2
         - int
       * - BRANCH
         - int
       * - OUT
         - int
       * - MD
         - float
       * - TVD
         - float
       * - DIAM
         - float
       * - ROUGHNESS
         - float

    .. _df_device:
    .. list-table:: df_device
       :widths: 10 10
       :header-rows: 1

       * - COLUMNS
         - TYPE
       * - SEG
         - int
       * - SEG2
         - int
       * - BRANCH
         - int
       * - OUT
         - int
       * - MD
         - float
       * - TVD
         - float
       * - DIAM
         - float
       * - ROUGHNESS
         - float

    .. _df_annulus:
    .. list-table:: df_annulus
       :widths: 10 10
       :header-rows: 1

       * - SEG
         - int
       * - SEG2
         - int
       * - BRANCH
         - int
       * - OUT
         - int
       * - MD
         - float
       * - TVD
         - float
       * - DIAM
         - float
       * - ROUGHNESS
         - float

    .. list-table:: df_wseglink
       :widths: 10 10
       :header-rows: 1

       * - COLUMNS
         - TYPE
       * - WELL
         - str
       * - ANNULUS
         - int
       * - DEVICE
         - int

    .. _df_compsegs:
    .. list-table:: df_compsegs
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
       * - DIR
         - str
       * - DEF
         - object
       * - SEG
         - int

    .. list-table:: df_compdat
       :widths: 10 10
       :header-rows: 1

       * - COLUMNS
         - TYPE
       * - WELL
         - str
       * - I
         - int
       * - J
         - int
       * - K
         - int
       * - K2
         - int
       * - FLAG
         - str
       * - SAT
         - object
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
       * - DIR
         - object
       * - RO
         - float

    .. _df_wsegvalv:
    .. list-table:: df_wsegvalv
       :widths: 10 10
       :header-rows: 1

       * - COLUMNS
         - TYPE
       * - WELL
         - str
       * - SEG
         - int
       * - CV
         - float
       * - AC
         - float
       * - L
         - str
       * - AC_MAX
         - float

    .. _df_wsegsicd:
    .. list-table:: df_wsegsicd
       :widths: 10 10
       :header-rows: 1

       * - COLUMNS
         - TYPE
       * - WELL
         - str
       * - SEG
         - int
       * - SEG2
         - int
       * - ALPHA
         - float
       * - SF
         - float
       * - RHO
         - float
       * - VIS
         - float
       * - WCT
         - float

    .. _df_wsegaicd:
    .. list-table:: df_wsegaicd
       :widths: 10 10
       :header-rows: 1

       * - COLUMNS
         - TYPE
       * - WELL
         - str
       * - SEG
         - int
       * - SEG2
         - int
       * - ALPHA
         - float
       * - SF
         - float
       * - RHO
         - float
       * - VIS
         - float
       * - DEF
         - object
       * - X
         - float
       * - Y
         - float
       * - FLAG
         - object
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

    .. _df_wsegdar:
    .. list-table:: df_wsegdar
       :widths: 10 10
       :header-rows: 1

       * - COLUMNS
         - TYPE
       * - WELL
         - str
       * - SEG
         - int
       * - CV_DAR
         - float
       * - AC_OIL
         - float
       * - AC_GAS
         - float
       * - AC_WATER
         - float
       * - AC_MAX
         - float
       * - WVF_LCF_DAR
         - float
       * - WVF_HCF_DAR
         - float
       * - GVF_LCF_DAR
         - float
       * - GVF_HCF_DAR
         - float

    .. _df_wsegaicv:
    .. list-table:: df_wsegaicv
       :widths: 10 10
       :header-rows: 1

       * - COLUMNS
         - TYPE
       * - WELL
         - str
       * - SEG
         - int
       * - SEG2
         - int
       * - ALPHA_MAIN
         - float
       * - SF
         - float
       * - RHO
         - float
       * - VIS
         - float
       * - DEF
         - object
       * - X_MAIN
         - float
       * - Y_MAIN
         - float
       * - FLAG
         - object
       * - A_MAIN
         - float
       * - B_MAIN
         - float
       * - C_MAIN
         - float
       * - D_MAIN
         - float
       * - E_MAIN
         - float
       * - F_MAIN
         - float
       * - ALPHA_PILOT
         - float
       * - X_PILOT
         - float
       * - Y_PILOT
         - float
       * - A_PILOT
         - float
       * - B_PILOT
         - float
       * - C_PILOT
         - float
       * - D_PILOT
         - float
       * - E_PILOT
         - float
       * - F_PILOT
         - float
       * - WCT_AICV
         - float
       * - GVF_AICV
         - float

    .. _df_wsegicv:
    .. list-table:: df_wsegicv
       :widths: 10 10
       :header-rows: 1

       * - COLUMNS
         - TYPE
       * - WELL
         - str
       * - SEG
         - int
       * - CV
         - float
       * - AC
         - float
       * - DEFAULTS
         - str
       * - AC_MAX
         - float
    """

    def __init__(
        self,
        case: ReadCasefile,
        schedule: WellSchedule,
        wells: CreateWells,
        well_name: str,
        iwell: int,
        completor_version: str,
        show_figure: bool = False,
        figure_name: matplotlib.backends.backend_pdf.PdfPages | None = None,  # type: ignore
        write_welsegs: bool = True,
        paths: tuple[str, str] | None = None,
    ):
        """
        Initialize CreateOutput class.

        Args:
            case: ReadCasefile object
            schedule: ReadSchedule object
            wells: CreateWells object
            completor_version: Completor version information
            figure_no: Must be set if show_figure
            show_figure: True if the user wants to create well diagram file
        """
        self.case = case
        self.schedule = schedule
        self.case_path: str | None
        self.schedule_path: str | None
        if paths:
            self.case_path, self.schedule_path = paths
        else:
            self.case_path = None
            self.schedule_path = None
        self.wells = wells
        self.well_name = well_name
        self.iwell = iwell
        self.version = completor_version
        self.write_welsegs = write_welsegs
        self.show_figure = show_figure

        # different line connection
        self.newline1 = "\n\n\n"
        self.newline2 = "\n/" + self.newline1
        self.newline3 = "/" + self.newline1

        # create final print
        self.header = self.make_completor_header()

        # Prints the UDQ statement if a PVT file and
        # PVT table are specified in the case file.
        self.print_udq = False
        self.udq_correlation = ""
        self.udq_parameter: dict[str, str] = {}
        if self.case.completion_table["DEVICETYPE"].isin(["AICV"]).any():
            self.print_udq = True
            self.udq_correlation = CORRELATION_UDQ

        # Start printing all wells
        self.finalprint = self.header
        # print udq equation if relevant
        if self.print_udq:
            self.finalprint += self.udq_correlation

        self.df_reservoir = wells.df_reservoir_all[wells.df_reservoir_all["WELL"] == self.well_name]
        self.df_well = wells.df_well_all[wells.df_well_all["WELL"] == self.well_name]
        self.laterals = self.df_well[self.df_well["WELL"] == self.well_name]["LATERAL"].unique()

        """Start printing per well."""
        self.welsegs_header, _ = self.schedule.get_welsegs(self.well_name, branch=1)
        self.check_welsegs1()
        self.print_welsegs = "WELSEGS\n" + po.dataframe_tostring(self.welsegs_header, True) + "\n"
        self.print_welsegsinit = self.print_welsegs
        self.print_wseglink = "WSEGLINK\n"
        self.print_wseglinkinit = self.print_wseglink
        self.print_compsegs = "COMPSEGS\n" + "'" + self.well_name + "' /\n"
        self.print_compsegsinit = self.print_compsegs
        self.print_compdat = "COMPDAT\n"
        self.print_compdatinit = self.print_compdat
        self.print_wsegvalv = "WSEGVALV\n"
        self.print_wsegvalvinit = self.print_wsegvalv
        self.print_wsegicv = "WSEGVALV\n"
        self.print_wsegicvinit = self.print_wsegicv
        self.print_wsegaicd = "WSEGAICD\n"
        self.print_wsegaicdinit = self.print_wsegaicd
        self.print_wsegsicd = "WSEGSICD\n"
        self.print_wsegsicdinit = self.print_wsegsicd
        self.print_wsegdar = f"""\
{'-' * 100}
-- This is how we model DAR technology using sets of ACTIONX keywords.
-- The segment dP curves changes according to the segment water-
-- and gas volume fractions at downhole condition.
-- The value of Cv is adjusted according to the segment length and the number of
-- devices per joint. The constriction area varies according to values of
-- volume fractions.
{"-" * 100}{self.newline1}"""

        self.print_wsegdarinit = self.print_wsegdar
        self.print_wsegaicv = f"""\
{"-" * 100}
-- This is how we model AICV technology using sets of ACTIONX keyword
-- the DP parameters change according to the segment water cut (at downhole condition )
-- and gas volume fraction (at downhole condition)
{"-" * 100}{self.newline1}"""
        self.print_wsegaicvinit = self.print_wsegaicv

        (self.start_segment, self.start_branch) = (2, 1)
        #
        # pre-preparations
        data = {}  # just a container. need to to loop twice to make connect_lateral work
        for lateral in self.laterals:
            self.df_tubing, top = po.prepare_tubing_layer(
                self.schedule,
                self.well_name,
                lateral,
                self.df_well,
                self.start_segment,
                self.start_branch,
                self.case.completion_table,
            )
            self.df_device = po.prepare_device_layer(self.well_name, lateral, self.df_well, self.df_tubing)
            self.df_annulus, self.df_wseglink = po.prepare_annulus_layer(
                self.well_name, lateral, self.df_well, self.df_device
            )
            self.update_segmentbranch()
            self.check_segments(lateral)
            data[lateral] = (self.df_tubing, self.df_device, self.df_annulus, self.df_wseglink, top)
        # attach lateral to their proper segments (in overburden, potentially)
        for lateral in data:
            po.connect_lateral(self.well_name, lateral, data, self.case)
        # main preparations
        for lateral in self.laterals:
            self.df_tubing, self.df_device, self.df_annulus, self.df_wseglink = data[lateral][:4]

            self.branch_revision(lateral)

            completion_table_well = case.completion_table[case.completion_table["WELL"] == self.well_name]
            completion_table_lateral = completion_table_well[completion_table_well["BRANCH"] == lateral]
            self.df_compsegs = po.prepare_compsegs(
                self.well_name,
                lateral,
                self.df_reservoir,
                self.df_device,
                self.df_annulus,
                completion_table_lateral,
                self.case.segment_length,
            )
            self.df_compdat = po.prepare_compdat(self.well_name, lateral, self.df_reservoir, completion_table_lateral)
            self.df_wsegvalv = po.prepare_wsegvalv(self.well_name, lateral, self.df_well, self.df_device)
            self.df_wsegsicd = po.prepare_wsegsicd(self.well_name, lateral, self.df_well, self.df_device)
            self.df_wsegaicd = po.prepare_wsegaicd(self.well_name, lateral, self.df_well, self.df_device)
            self.df_wsegdar = po.prepare_wsegdar(self.well_name, lateral, self.df_well, self.df_device)
            self.df_wsegaicv = po.prepare_wsegaicv(self.well_name, lateral, self.df_well, self.df_device)
            self.df_wsegicv = po.prepare_wsegicv(
                self.well_name,
                lateral,
                self.df_well,
                self.df_device,
                self.df_tubing,
                self.case.completion_icv_tubing,
                self.case.wsegicv_table,
            )
            self.make_compdat(lateral)
            self.make_welsegs(lateral)
            self.make_wseglink(lateral)
            self.make_compsegs(lateral)
            self.make_wsegvalv(lateral)
            self.make_wsegsicd(lateral)
            self.make_wsegaicd(lateral)
            self.make_wsegicv(lateral)
            self.make_wsegdar()
            self.make_wsegaicv()

            if show_figure and figure_name is not None:
                logger.info(f"Creating figure for lateral {lateral}.")
                figure_name.savefig(
                    visualize_well(self.well_name, self.df_well, self.df_reservoir, self.case.segment_length),
                    orientation="landscape",
                )
                logger.info("creating schematics: %s.pdf", figure_name)
            elif show_figure and figure_name is None:
                raise ValueError("Cannot show figure without filename supplied.")
        self.fix_printing()
        self.print_per_well()

    def make_completor_header(self) -> str:
        """Print header note."""
        header = f"{'-' * 100}\n"
        header += f"-- Output from completor {self.version}\n"
        try:
            header += f"-- Case file : {self.case_path}\n"
        except AttributeError:
            header += "-- Case file : No path found \n"
            logger.warning("Could not resolve case-file path to output file")
        header += f"-- Schedule file : {self.schedule_path}\n"

        header += f"""\
-- Created by : {(getpass.getuser()).upper()}
-- Created at : {datetime.now().strftime('%Y %B %d %H:%M')}
{'-' * 100}{self.newline1}
"""
        return header

    def check_welsegs1(self) -> None:
        """
        Check whether the MD of the first segment is deeper than first cell STARTMD.

        If this is the case, adjust SEGMENTMD to be 1 meter shallower.

        Uses DataFrame df_reservoir with format shown in ``CreateOutput``.
        """
        start_md = self.df_reservoir["STARTMD"].iloc[0]
        if self.welsegs_header["SEGMENTMD"].iloc[0] > start_md:
            self.welsegs_header["SEGMENTMD"] = start_md - 1.0

    def check_segments(self, lateral: int) -> None:
        """
        Check whether there is annular flow in the well.

        Also checks if there are any connections from the reservoir to the tubing
        in a well.

        Uses DataFrame :ref:`df_annulus` and :ref:`df_device`
        with formats shown in ``CreateOutput``.
        """
        if self.df_annulus.shape[0] == 0:
            logger.info("No annular flow in Well : %s Lateral : %d", self.well_name, lateral)
        if self.df_device.shape[0] == 0:
            logger.warning(
                "No connection from reservoir to tubing in " "Well : %s Lateral : %d", self.well_name, lateral
            )

    def update_segmentbranch(self) -> None:
        """
        Update the numbering of the tubing segment and branch.

        Uses DataFrame :ref:`df_annulus` and :ref:`df_device`
        with formats shown in ``CreateOutput``.
        """
        if self.df_annulus.shape[0] == 0 and self.df_device.shape[0] > 0:
            self.start_segment = max(self.df_device["SEG"].to_numpy()) + 1
            self.start_branch = max(self.df_device["BRANCH"].to_numpy()) + 1
        elif self.df_annulus.shape[0] > 0:
            self.start_segment = max(self.df_annulus["SEG"].to_numpy()) + 1
            self.start_branch = max(self.df_annulus["BRANCH"].to_numpy()) + 1

    def make_compdat(self, lateral: int) -> None:
        """
        Print COMPDAT to file.

        Uses DataFrame df_compdat with format shown in ``CreateOutput``.
        """
        nchar = po.get_number_of_characters(self.df_compdat)
        if self.df_compdat.shape[0] > 0:
            self.print_compdat += (
                po.get_header(self.well_name, "COMPDAT", lateral, "", nchar)
                + po.dataframe_tostring(self.df_compdat, True)
                + "\n"
            )

    def make_welsegs(self, lateral: int) -> None:
        """
        Print WELSEGS to file.

        Uses DataFrame :ref:`df_tubing` and :ref:`df_device`
        with formats shown in ``CreateOutput``.
        """
        nchar = po.get_number_of_characters(self.df_tubing)
        if self.df_device.shape[0] > 0:
            self.print_welsegs += (
                po.get_header(self.well_name, "WELSEGS", lateral, "Tubing", nchar)
                + po.dataframe_tostring(self.df_tubing, True)
                + "\n"
            )
        if self.df_device.shape[0] > 0:
            nchar = po.get_number_of_characters(self.df_tubing)
            self.print_welsegs += (
                po.get_header(self.well_name, "WELSEGS", lateral, "Device", nchar)
                + po.dataframe_tostring(self.df_device, True)
                + "\n"
            )
        if self.df_annulus.shape[0] > 0:
            nchar = po.get_number_of_characters(self.df_tubing)
            self.print_welsegs += (
                po.get_header(self.well_name, "WELSEGS", lateral, "Annulus", nchar)
                + po.dataframe_tostring(self.df_annulus, True)
                + "\n"
            )

    def make_wseglink(self, lateral: int) -> None:
        """
        Print WSEGLINK to file.

        Uses DataFrame df_wseglink with format shown in ``CreateOutput``.
        """
        if self.df_wseglink.shape[0] > 0:
            nchar = po.get_number_of_characters(self.df_wseglink)
            self.print_wseglink += (
                po.get_header(self.well_name, "WSEGLINK", lateral, "", nchar)
                + po.dataframe_tostring(self.df_wseglink, True)
                + "\n"
            )

    def make_compsegs(self, lateral: int) -> None:
        """
        Print COMPSEGS to file.

        Uses DataFrame :ref:`df_compsegs` with format shown in ``CreateOutput``.
        """
        nchar = po.get_number_of_characters(self.df_compsegs)
        if self.df_compsegs.shape[0] > 0:
            self.print_compsegs += (
                po.get_header(self.well_name, "COMPSEGS", lateral, "", nchar)
                + po.dataframe_tostring(self.df_compsegs, True)
                + "\n"
            )

    def make_wsegaicd(self, lateral: int) -> None:
        """
        Print WSEGAICD to file.

        Uses DataFrame :ref:`df_wsegaicd` with format shown in ``CreateOutput``.
        """
        if self.df_wsegaicd.shape[0] > 0:
            nchar = po.get_number_of_characters(self.df_wsegaicd)
            self.print_wsegaicd += (
                po.get_header(self.well_name, "WSEGAICD", lateral, "", nchar)
                + po.dataframe_tostring(self.df_wsegaicd, True)
                + "\n"
            )

    def make_wsegsicd(self, lateral: int) -> None:
        """
        Print WSEGSICD to file.

        Uses DataFrame :ref:`df_wsegsicd` with format shown in ``CreateOutput``.
        """
        if self.df_wsegsicd.shape[0] > 0:
            nchar = po.get_number_of_characters(self.df_wsegsicd)
            self.print_wsegsicd += (
                po.get_header(self.well_name, "WSEGSICD", lateral, "", nchar)
                + po.dataframe_tostring(self.df_wsegsicd, True)
                + "\n"
            )

    def make_wsegvalv(self, lateral: int) -> None:
        """
        Print WSEGVALV to file.

        Uses DataFrame :ref:`df_wsegvalv` with format shown in ``CreateOutput``.
        """
        if self.df_wsegvalv.shape[0] > 0:
            nchar = po.get_number_of_characters(self.df_wsegvalv)
            self.print_wsegvalv += (
                po.get_header(self.well_name, "WSEGVALV", lateral, "", nchar)
                + po.dataframe_tostring(self.df_wsegvalv, True)
                + "\n"
            )

    def make_wsegicv(self, lateral: int) -> None:
        """
        Print WSEGICV to file.

        Uses DataFrame :ref:`df_wsegicv` with format shown in ``CreateOutput``.
        """
        if self.df_wsegicv.shape[0] > 0:
            nchar = po.get_number_of_characters(self.df_wsegicv)
            self.print_wsegicv += (
                po.get_header(self.well_name, "WSEGVALV", lateral, "", nchar)
                + po.dataframe_tostring(self.df_wsegicv, True)
                + "\n"
            )

    def make_wsegdar(self) -> None:
        """
        Print WSEGDAR to file.

        Uses DataFrame :ref:`df_wsegdar` with format shown in ``CreateOutput``.
        """
        if self.df_wsegdar.shape[0] > 0:
            self.print_wsegdar += po.print_wsegdar(self.df_wsegdar, self.iwell + 1) + "\n"

    def make_wsegaicv(self) -> None:
        """
        Print WSEGAICV to file.

        Uses DataFrame :ref:`df_wsegaicv` with format shown in ``CreateOutput``.
        """
        if self.df_wsegaicv.shape[0] > 0:
            self.print_wsegaicv += po.print_wsegaicv(self.df_wsegaicv, self.iwell + 1) + "\n"

    def fix_printing(self) -> None:
        """Avoid printing non-existing keywords."""
        # if no compdat then dont print it
        if self.print_compdat == self.print_compdatinit:
            self.print_compdat = ""
        else:
            self.print_compdat += self.newline3
        # if no welsegs then dont print it
        if self.print_welsegs == self.print_welsegsinit:
            self.print_welsegs = ""
        else:
            self.print_welsegs += self.newline3
        # if no compsegs then dont print it
        if self.print_compsegs == self.print_compsegsinit:
            self.print_compsegs = ""
        else:
            self.print_compsegs += self.newline3
        # if no weseglink then dont print it
        if self.print_wseglink == "WSEGLINK\n":
            self.print_wseglink = ""
        else:
            self.print_wseglink += self.newline3
        # if no VALVE then dont print
        if self.print_wsegvalv == "WSEGVALV\n":
            self.print_wsegvalv = ""
        else:
            self.print_wsegvalv += self.newline3
        # if no ICD then dont print
        if self.print_wsegsicd == "WSEGSICD\n":
            self.print_wsegsicd = ""
        else:
            self.print_wsegsicd += self.newline3
        # if no AICD then dont print
        if self.print_wsegaicd == "WSEGAICD\n":
            self.print_wsegaicd = ""
        else:
            self.print_wsegaicd += self.newline3
        # if no DAR then dont print
        if self.print_wsegdar == self.print_wsegdarinit:
            self.print_wsegdar = ""
        else:
            self.print_wsegdar += self.newline1
        # if no DAR then dont print
        if self.print_wsegaicv == self.print_wsegaicvinit:
            self.print_wsegaicv = ""
        else:
            self.print_wsegaicv += self.newline1
        # if no ICV then dont print
        if self.print_wsegicv == "WSEGVALV\n":
            self.print_wsegicv = ""
        else:
            self.print_wsegicv += self.newline3

    def print_per_well(self) -> None:
        """Collect final printing for all wells."""
        # here starts active wells
        finalprint = self.finalprint + self.print_compdat
        if self.write_welsegs:
            finalprint += self.print_welsegs
        finalprint += self.print_wseglink
        finalprint += self.print_compsegs
        # print udq parameter if relevant
        if self.well_name in self.udq_parameter and self.print_udq:
            finalprint += self.udq_parameter[self.well_name]

        finalprint += (
            self.print_wsegvalv
            + self.print_wsegsicd
            + self.print_wsegaicd
            + self.print_wsegdar
            + self.print_wsegaicv
            + self.print_wsegicv
