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
