"""Defines a class for generating output files."""

from __future__ import annotations

import getpass
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages  # type: ignore

import completor
from completor import prepare_outputs, read_schedule
from completor.constants import Headers, Keywords
from completor.create_wells import Wells
from completor.exceptions import CompletorError
from completor.logger import logger
from completor.pvt_model import CORRELATION_UDQ
from completor.read_casefile import ReadCasefile
from completor.visualize_well import visualize_well


class CreateOutput:
    """Create output files from completor.

    There are two output files from completor:
        1. Well schedule file (text file) for input to reservoir simulator.
        2. Well diagram (pdf file), i.e. a well completion schematic.

    # TODO: Attributes section.
    """

    def __init__(
        self,
        case: ReadCasefile,
        schedule_data: dict[str, dict[str, Any]],
        wells: Wells,
        well_name: str,
        well_number: int,
        show_figure: bool = False,
        figure_name: str | None = None,
        paths: tuple[str, str] | None = None,
        weller_man=None,
    ):
        """Initialize CreateOutput class.

        Args:
            case: Case file object.
            schedule_data: Data from schedule file.
            wells: Wells object.
            well_name: Name of well.
            well_number: Well number.
            show_figure: True if the user wants to create well diagram file. Defaults to False.
            figure_name: File name of the figure.
            paths: Paths to the original input case and schedule file.

        """
        self.wells = wells
        # self.well_name = well_name
        self.well_number = well_number
        # self.show_figure = show_figure

        # Prints the UDQ statement if a PVT file and PVT table are specified in the case file.
        finalprint = self.format_header(paths)

        if case.completion_table[Headers.DEVICE_TYPE].isin(["AICV"]).any():
            finalprint += CORRELATION_UDQ

        df_reservoir = weller_man.df_reservoir_all
        df_well = weller_man.df_well_all

        # Start printing per well.
        welsegs_header, _ = read_schedule.get_well_segments(schedule_data, well_name, branch=1)
        self.check_welsegs1(welsegs_header, df_reservoir[Headers.START_MEASURED_DEPTH].iloc[0])

        self.print_welsegs = f"{Keywords.WELSEGS}\n{prepare_outputs.dataframe_tostring(welsegs_header, True)}\n"
        self.print_wseglink = ""
        self.print_compsegs = ""
        self.print_compdat = ""
        self.print_wsegvalv = ""
        self.print_wsegicv = ""
        self.print_wsegaicd = ""
        self.print_wsegsicd = ""
        self.print_wsegdar = ""
        self.print_wsegaicv = ""

        self.start_segment = 2
        self.start_branch = 1
        # pre-preparations
        data = {}  # just a container. need to loop twice to make connect_lateral work

        for lateral in weller_man.my_new_laterals:
            df_tubing, top = prepare_outputs.prepare_tubing_layer(
                schedule_data, well_name, lateral, self.start_segment, self.start_branch, case.completion_table
            )
            df_device = prepare_outputs.prepare_device_layer(lateral.df_well, df_tubing)
            if df_device.empty:
                logger.warning(
                    "No connection from reservoir to tubing in Well : %s Lateral : %d",
                    well_name,
                    lateral.lateral_number,
                )
            df_annulus, df_wseglink = prepare_outputs.prepare_annulus_layer(well_name, lateral.df_well, df_device)
            if df_annulus.empty:
                logger.info("No annular flow in Well : %s Lateral : %d", well_name, lateral.lateral_number)

            self.start_segment, self.start_branch = self.update_segmentbranch(df_device, df_annulus)

            data[lateral.lateral_number] = (df_tubing, df_device, df_annulus, df_wseglink, top)

            df_tubing = self.connect_lateral(well_name, lateral.lateral_number, data, case)

            df_tubing, df_device, df_annulus, df_wseglink = data[lateral.lateral_number][:4]

            df_tubing[Headers.BRANCH] = lateral.lateral_number
            df_device, df_annulus = self.branch_revision(
                lateral.lateral_number, weller_man.active_laterals, df_device, df_annulus
            )

            completion_table_well = case.completion_table[case.completion_table[Headers.WELL] == well_name]
            completion_table_lateral = completion_table_well[
                completion_table_well[Headers.BRANCH] == lateral.lateral_number
            ]
            df_compsegs = prepare_outputs.prepare_compsegs(
                well_name,
                lateral.lateral_number,
                df_reservoir,
                df_device,
                df_annulus,
                completion_table_lateral,
                case.segment_length,
            )
            df_compdat = prepare_outputs.prepare_compdat(
                well_name, lateral.lateral_number, df_reservoir, completion_table_lateral
            )
            df_wsegvalv = prepare_outputs.prepare_wsegvalv(well_name, lateral.df_well, df_device)
            df_wsegsicd = prepare_outputs.prepare_wsegsicd(well_name, lateral.df_well, df_device)
            df_wsegaicd = prepare_outputs.prepare_wsegaicd(well_name, lateral.df_well, df_device)
            df_wsegdar = prepare_outputs.prepare_wsegdar(well_name, lateral.df_well, df_device)
            df_wsegaicv = prepare_outputs.prepare_wsegaicv(well_name, lateral.df_well, df_device)
            df_wsegicv = prepare_outputs.prepare_wsegicv(
                well_name,
                lateral.lateral_number,
                df_well,
                df_device,
                df_tubing,
                case.completion_icv_tubing,
                case.wsegicv_table,
            )
            self.print_compdat += self.make_compdat(well_name, lateral.lateral_number, df_compdat)
            self.print_welsegs += self.make_welsegs(well_name, lateral.lateral_number, df_tubing, df_device, df_annulus)
            self.print_wseglink += self.make_wseglink(well_name, lateral.lateral_number, df_wseglink)
            self.print_compsegs += self.make_compsegs(well_name, lateral.lateral_number, df_compsegs)
            self.print_wsegvalv += self.make_wsegvalv(well_name, lateral.lateral_number, df_wsegvalv)
            self.print_wsegsicd += self.make_wsegsicd(well_name, lateral.lateral_number, df_wsegsicd)
            self.print_wsegaicd += self.make_wsegaicd(well_name, lateral.lateral_number, df_wsegaicd)
            self.print_wsegicv += self.make_wsegicv(well_name, lateral.lateral_number, df_wsegicv)
            self.print_wsegdar += self.make_wsegdar(well_number, df_wsegdar)
            self.print_wsegaicv += self.make_wsegaicv(well_number, df_wsegaicv)

            if show_figure and figure_name is not None:
                logger.info(f"Creating figure for lateral {lateral.lateral_number}.")
                with PdfPages(figure_name) as figure:
                    figure.savefig(
                        visualize_well(well_name, df_well, df_reservoir, case.segment_length),
                        orientation="landscape",
                    )
                logger.info("creating schematics: %s.pdf", figure_name)
            elif show_figure and figure_name is None:
                raise ValueError("Cannot show figure without filename supplied.")
        self.print_welsegs += "/\n\n\n"

        finalprint += self.print_compdat
        finalprint += self.print_welsegs
        finalprint += self.print_wseglink
        finalprint += self.print_compsegs
        finalprint += self.print_wsegvalv
        finalprint += self.print_wsegsicd
        finalprint += self.print_wsegaicd
        finalprint += self.print_wsegdar
        finalprint += self.print_wsegaicv
        finalprint += self.print_wsegicv

        self.finalprint = finalprint

    @staticmethod
    def format_header(paths: tuple[str, str] | None) -> str:
        """Formats the header banner, with metadata.

        Args:
            paths: The paths to case and schedule files.

        Returns:
            Formatted header.
        """
        header = f"{'-' * 100}\n-- Output from completor {completor.__version__}\n"
        if paths is not None:
            header += f"-- Case file: {paths[0]}\n-- Schedule file: {paths[1]}\n"
        else:
            logger.warning("Could not resolve case-file path to output file.")
            header += "-- Case file: No path found\n-- Schedule file: No path found\n"

        header += (
            f"-- Created by : {(getpass.getuser()).upper()}\n"
            f"-- Created at : {datetime.now().strftime('%Y %B %d %H:%M')}\n"
            f"{'-' * 100}\n\n\n"
        )
        return header

    @staticmethod
    def check_welsegs1(welsegs_header: pd.DataFrame, start_measured_depths: pd.Series) -> pd.DataFrame:
        """Check whether the measured depth of the first segment is deeper than the first cells start measured depth.

        In this case, adjust segments measured depth to be 1 meter shallower.

        Args:
            welsegs_header: The header for well segments.
            start_measured_depths: The measured depths of the first cells from the reservoir.

        Returns:
            Corrected measured depths if well segments header.
        """
        if welsegs_header[Headers.MEASURED_DEPTH].iloc[0] > start_measured_depths:
            welsegs_header[Headers.MEASURED_DEPTH] = start_measured_depths - 1.0
        return welsegs_header

    @staticmethod
    def update_segmentbranch(df_device: pd.DataFrame, df_annulus: pd.DataFrame) -> tuple[int, int]:
        """Update the numbering of the tubing segment and branch.

        Args:
            df_device: Device data.
            df_annulus: Annulus data.

        Returns:
            The numbers for starting segment and branch.

        Raises:
            ValueError: If there is neither device nor annulus data.
        """
        if df_annulus.empty and df_device.empty:
            raise ValueError("Cannot determine starting segment and branch without device and annulus data.")
        if df_annulus.empty and not df_device.empty:
            start_segment = max(df_device[Headers.START_SEGMENT_NUMBER].to_numpy()) + 1
            start_branch = max(df_device[Headers.BRANCH].to_numpy()) + 1
        else:
            start_segment = max(df_annulus[Headers.START_SEGMENT_NUMBER].to_numpy()) + 1
            start_branch = max(df_annulus[Headers.BRANCH].to_numpy()) + 1
        return start_segment, start_branch

    @staticmethod
    def make_compdat(well_name: str, lateral: int, df_compdat: pd.DataFrame) -> str:
        """Print completion data to file.

        Args:
            well_name:
            lateral:
            df_compdat:

        Returns:

        """
        if df_compdat.empty:
            return ""
        nchar = prepare_outputs.get_number_of_characters(df_compdat)
        return (
            f"{Keywords.COMPDAT}\n"
            + prepare_outputs.get_header(well_name, Keywords.COMPDAT, lateral, "", nchar)
            + prepare_outputs.dataframe_tostring(df_compdat, True)
            + "\n/\n\n\n"
        )

    @staticmethod
    def make_welsegs(
        well_name: str, lateral: int, df_tubing: pd.DataFrame, df_device: pd.DataFrame, df_annulus: pd.DataFrame
    ) -> str:
        """Print well segments to file.

        Args:
            well_name:
            lateral:
            df_tubing:
            df_device:
            df_annulus:

        Returns:

        """
        print_welsegs = ""
        nchar = prepare_outputs.get_number_of_characters(df_tubing)
        if not df_device.empty:
            print_welsegs += (
                prepare_outputs.get_header(well_name, Keywords.WELSEGS, lateral, "Tubing", nchar)
                + prepare_outputs.dataframe_tostring(df_tubing, True)
                + "\n"
            )
        if not df_device.empty:
            print_welsegs += (
                prepare_outputs.get_header(well_name, Keywords.WELSEGS, lateral, "Device", nchar)
                + prepare_outputs.dataframe_tostring(df_device, True)
                + "\n"
            )
        if not df_annulus.empty:
            print_welsegs += (
                prepare_outputs.get_header(well_name, Keywords.WELSEGS, lateral, "Annulus", nchar)
                + prepare_outputs.dataframe_tostring(df_annulus, True)
                + "\n"
            )
        return print_welsegs

    @staticmethod
    def make_wseglink(well_name: str, lateral: int, df_wseglink: pd.DataFrame) -> str:
        """

        Args:
            well_name:
            lateral:
            df_wseglink:

        Returns:

        """
        if df_wseglink.empty:
            return ""
        nchar = prepare_outputs.get_number_of_characters(df_wseglink)
        return (
            f"{Keywords.WSEGLINK}\n"
            + prepare_outputs.get_header(well_name, Keywords.WSEGLINK, lateral, "", nchar)
            + prepare_outputs.dataframe_tostring(df_wseglink, True)
            + "\n/\n\n\n"
        )

    @staticmethod
    def make_compsegs(well_name: str, lateral: int, df_compsegs: pd.DataFrame) -> str:
        """

        Args:
            well_name:
            lateral:
            df_compsegs:

        Returns:

        """
        if df_compsegs.empty:
            return ""
        nchar = prepare_outputs.get_number_of_characters(df_compsegs)
        return (
            f"{Keywords.COMPSEGS}\n'{well_name}' /\n"
            + prepare_outputs.get_header(well_name, Keywords.COMPSEGS, lateral, "", nchar)
            + prepare_outputs.dataframe_tostring(df_compsegs, True)
            + "\n/\n\n\n"
        )

    @staticmethod
    def make_wsegaicd(well_name: str, lateral: int, df_wsegaicd: pd.DataFrame) -> str:
        """

        Args:
            well_name:
            lateral:
            df_wsegaicd:

        Returns:

        """
        if df_wsegaicd.empty:
            return ""
        nchar = prepare_outputs.get_number_of_characters(df_wsegaicd)
        return (
            f"{Keywords.WSEGAICD}\n"
            + prepare_outputs.get_header(well_name, Keywords.WSEGAICD, lateral, "", nchar)
            + prepare_outputs.dataframe_tostring(df_wsegaicd, True)
            + "\n/\n\n\n"
        )

    @staticmethod
    def make_wsegsicd(well_name: str, lateral: int, df_wsegsicd: pd.DataFrame) -> str:
        """

        Args:
            well_name:
            lateral:
            df_wsegsicd:

        Returns:

        """
        if df_wsegsicd.empty:
            return ""
        nchar = prepare_outputs.get_number_of_characters(df_wsegsicd)
        return (
            f"{Keywords.WSEGSICD}\n"
            + prepare_outputs.get_header(well_name, Keywords.WSEGSICD, lateral, "", nchar)
            + prepare_outputs.dataframe_tostring(df_wsegsicd, True)
            + "\n/\n\n\n"
        )

    @staticmethod
    def make_wsegvalv(well_name: str, lateral: int, df_wsegvalv) -> str:
        """

        Args:
            well_name:
            lateral:
            df_wsegvalv:

        Returns:

        """
        if df_wsegvalv.empty:
            return ""
        nchar = prepare_outputs.get_number_of_characters(df_wsegvalv)
        return (
            f"{Keywords.WSEGVALV}\n"
            + prepare_outputs.get_header(well_name, Keywords.WSEGVALV, lateral, "", nchar)
            + prepare_outputs.dataframe_tostring(df_wsegvalv, True)
            + "\n/\n\n\n"
        )

    @staticmethod
    def make_wsegicv(well_name: str, lateral: int, df_wsegicv: pd.DataFrame) -> str:
        """

        Args:
            well_name:
            lateral:
            df_wsegicv:

        Returns:

        """
        if df_wsegicv.empty:
            return ""
        nchar = prepare_outputs.get_number_of_characters(df_wsegicv)
        return (
            f"{Keywords.WSEGVALV}\n"  # TODO: Should this not be WSEGICV?
            + prepare_outputs.get_header(well_name, Keywords.WSEGVALV, lateral, "", nchar)
            + prepare_outputs.dataframe_tostring(df_wsegicv, True)
            + "\n/\n\n\n"
        )

    @staticmethod
    def make_wsegdar(well_number: int, df_wsegdar: pd.DataFrame) -> str:
        """

        Args:
            well_number:
            df_wsegdar:

        Returns:

        """
        if df_wsegdar.empty:
            return ""
        header = (
            f"{'-' * 100}"
            "-- This is how we model DAR technology using sets of ACTIONX keywords."
            "-- The segment dP curves changes according to the segment water-"
            "-- and gas volume fractions at downhole condition."
            "-- The value of Cv is adjusted according to the segment length and the number of"
            "-- devices per joint. The constriction area varies according to values of"
            "-- volume fractions."
            f"{'-' * 100}"
            "\n\n\n"
        )
        return header + prepare_outputs.print_wsegdar(df_wsegdar, well_number + 1) + "\n\n\n\n"

    @staticmethod
    def make_wsegaicv(well_number: int, df_wsegaicv: pd.DataFrame) -> str:
        """

        Args:
            well_number:
            df_wsegaicv:

        Returns:

        """
        if not df_wsegaicv.empty:
            return ""
        metadata = (
            f"{'-' * 100}"
            "-- This is how we model AICV technology using sets of ACTIONX keyword"
            "-- the DP parameters change according to the segment water cut (at downhole condition )"
            "-- and gas volume fraction (at downhole condition)"
            f"{'-' * 100}"
            "\n\n\n"
        )
        return metadata + prepare_outputs.print_wsegaicv(df_wsegaicv, well_number + 1) + "\n\n\n\n"

    @staticmethod
    def branch_revision(
        lateral_number: int,
        active_laterals: list[int],
        df_device: pd.DataFrame,
        df_annulus: pd.DataFrame,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Revises the order of branch numbers to be in agreement with common practice.

        This means that tubing layers will get branch numbers from 1 to the number of laterals.
        Device and lateral branch numbers are changed accordingly if they exist.

        Args:
            lateral_number: The lateral number being worked on.
            active_laterals: List of active lateral numbers.
            df_device: Dataframe containing device data.
            df_annulus: Dataframe containing annular data.

        Returns:
            Corrected device.
        """
        correction = max(active_laterals) - lateral_number
        try:
            df_device[Headers.BRANCH] += correction
        except KeyError:
            pass
        try:
            df_annulus[Headers.BRANCH] += correction
        except KeyError:
            pass
        return df_device, df_annulus

    @staticmethod
    def connect_lateral(
        well_name: str,
        lateral_number: int,
        data: dict[int, tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]],
        case: ReadCasefile,
    ) -> pd.DataFrame:
        """Connect lateral to main wellbore/branch.

        The main branch can either have a tubing- or device-layer connected.
        By default, the lateral will be connected to tubing-layer, but if connect_to_tubing is False,
        it will be connected to device-layer.
        Abort if it cannot find device layer at junction depth.

        Args:
            well_name: Well name.
            lateral_number: Lateral number.
            data: Dict with integer key 'lateral' containing:.
                df_tubing: DataFrame tubing layer.
                df_device: DataFrame device layer.
                df_annulus: DataFrame annulus layer.
                df_wseglink: DataFrame WSEGLINK.
                top: DataFrame of first connection.
            case: ReadCasefile object.

        Returns:
            Tubing data with modified outsegment.

        Raises:
            CompletorError: If there is no device layer at junction of lateral.
        """
        df_tubing, _, _, _, top = data[lateral_number]
        if top.empty:
            df_tubing.at[0, Headers.OUT] = 1
            return df_tubing

        lateral0 = top[Headers.TUBING_BRANCH].to_numpy()[0]
        md_junct = top[Headers.TUBING_MEASURED_DEPTH].to_numpy()[0]
        if md_junct > df_tubing[Headers.MEASURED_DEPTH][0]:
            logger.warning(
                "Found a junction above the start of the tubing layer, well %s, "
                "branch %s. Check the depth of segments pointing at the main stem "
                "in schedule-file",
                well_name,
                lateral_number,
            )
        if case.connect_to_tubing(well_name, lateral_number):
            df_segm0 = data[lateral0][0]  # df_tubing
        else:
            df_segm0 = data[lateral0][1]  # df_device
        try:
            if case.connect_to_tubing(well_name, lateral_number):
                # Since md_junct (top.TUBING_MEASURED_DEPTH) has segment tops and
                # segm0.MEASURED_DEPTH has grid block midpoints, a junction at the top of the
                # well may not be found. Therefore, we try the following:
                if (~(df_segm0.MEASURED_DEPTH <= md_junct)).all():
                    md_junct = df_segm0.MEASURED_DEPTH.iloc[0]
                    idx = np.where(df_segm0.MEASURED_DEPTH <= md_junct)[0][-1]
                else:
                    idx = np.where(df_segm0.MEASURED_DEPTH <= md_junct)[0][-1]
            else:
                # Add 0.1 to md_junct since md_junct refers to the tubing layer
                # junction md and the device layer md is shifted 0.1 m to the tubing layer.
                idx = np.where(df_segm0.MEASURED_DEPTH <= md_junct + 0.1)[0][-1]
        except IndexError as err:
            raise CompletorError(
                f"Cannot find a device layer at junction of lateral {lateral_number} in {well_name}"
            ) from err
        outsegm = df_segm0.at[idx, Headers.START_SEGMENT_NUMBER]

        df_tubing.at[0, Headers.OUT] = outsegm
        return df_tubing
