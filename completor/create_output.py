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
