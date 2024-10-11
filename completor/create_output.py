"""Defines a class for generating output files."""

from __future__ import annotations

import getpass
from datetime import datetime

import numpy as np
import numpy.typing as npt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages  # type: ignore

from completor import prepare_outputs
from completor.constants import Content, Headers, Keywords
from completor.exceptions import CompletorError
from completor.get_version import get_version
from completor.logger import logger
from completor.pvt_model import CORRELATION_UDQ
from completor.read_casefile import ReadCasefile
from completor.visualize_well import visualize_well
from completor.wells import Lateral, Well


class Output:
    """TODO: Attrs"""

    def __init__(self, well: Well, case: ReadCasefile, figure_name: str | None = None):
        """Formats the finished output string to be written to a file.

        Args:
            well: Well data.
            case: Case data.
            figure_name: The name of the figure, if None, no figure is printed. Defaults to None.

        Returns:
            Properly formatted output string ready to be written to file.

        """

        df_reservoir = well.df_reservoir_all_laterals
        df_well = well.df_well_all_laterals

        self.print_well_segments = ""
        self.print_completion_segments = ""
        self.print_completion_data = ""
        completion_data_list = []
        print_well_segments_link = ""
        print_valve = ""
        print_inflow_control_valve = ""
        print_autonomous_inflow_control_device = ""
        print_inflow_control_device = ""
        print_density_activated_recovery = ""
        print_autonomous_inflow_control_valve = ""

        self.bonus_data = ""

        start_segment = 2
        start_branch = 1

        header_written = False
        for lateral in well.active_laterals:
            _check_well_segments_header(lateral.df_welsegs_header, df_reservoir[Headers.START_MEASURED_DEPTH].iloc[0])

            if not header_written:
                self.print_well_segments += (
                    f"{Keywords.WELL_SEGMENTS}\n{prepare_outputs.dataframe_tostring(lateral.df_welsegs_header, True)}"
                )
                header_written = True

            df_tubing, top = prepare_outputs.prepare_tubing_layer(
                well, lateral, start_segment, start_branch, case.completion_table
            )
            lateral.df_tubing = df_tubing
            df_device = prepare_outputs.prepare_device_layer(lateral.df_well, df_tubing)
            lateral.df_device = df_device

            if df_device.empty:
                logger.warning(
                    "No connection from reservoir to tubing in Well : %s Lateral : %d",
                    well.well_name,
                    lateral.lateral_number,
                )
            df_annulus, df_well_segments_link = prepare_outputs.prepare_annulus_layer(
                well.well_name, lateral.df_well, df_device
            )
            if df_annulus.empty:
                logger.info("No annular flow in Well : %s Lateral : %d", well.well_name, lateral.lateral_number)

            start_segment, start_branch = _update_segmentbranch(df_device, df_annulus)

            df_tubing = _connect_lateral(well.well_name, lateral, top, well, case)

            df_tubing[Headers.BRANCH] = lateral.lateral_number
            active_laterals = [lateral.lateral_number for lateral in well.active_laterals]
            df_device, df_annulus = _branch_revision(lateral.lateral_number, active_laterals, df_device, df_annulus)

            completion_table_well = case.completion_table[case.completion_table[Headers.WELL] == well.well_name]
            completion_table_lateral = completion_table_well[
                completion_table_well[Headers.BRANCH] == lateral.lateral_number
            ]
            df_completion_segments = prepare_outputs.prepare_completion_segments(
                well.well_name,
                lateral.lateral_number,
                df_reservoir,
                df_device,
                df_annulus,
                completion_table_lateral,
                case.segment_length,
            )
            df_completion_data = prepare_outputs.prepare_completion_data(
                well.well_name, lateral.lateral_number, df_reservoir, completion_table_lateral
            )
            df_valve = prepare_outputs.prepare_valve(well.well_name, lateral.df_well, df_device)
            df_inflow_control_device = prepare_outputs.prepare_inflow_control_device(
                well.well_name, lateral.df_well, df_device
            )
            df_autonomous_inflow_control_device = prepare_outputs.prepare_autonomous_inflow_control_device(
                well.well_name, lateral.df_well, df_device
            )
            df_density_activated_recovery = prepare_outputs.prepare_density_activated_recovery(
                well.well_name, lateral.df_well, df_device
            )
            df_autonomous_inflow_control_valve = prepare_outputs.prepare_autonomous_inflow_control_valve(
                well.well_name, lateral.df_well, df_device
            )
            df_inflow_control_valve = prepare_outputs.prepare_inflow_control_valve(
                well.well_name,
                lateral.lateral_number,
                df_well,
                df_device,
                df_tubing,
                case.completion_icv_tubing,
                case.wsegicv_table,
            )
            completion_data_list.append(
                _format_completion_data(well.well_name, lateral.lateral_number, df_completion_data)
            )
            self.print_well_segments += _format_well_segments(
                well.well_name, lateral.lateral_number, df_tubing, df_device, df_annulus
            )
            self.print_completion_segments += _format_completion_segments(
                well.well_name, lateral.lateral_number, df_completion_segments
            )
            print_well_segments_link += _format_well_segments_link(
                well.well_name, lateral.lateral_number, df_well_segments_link
            )
            print_valve += _format_valve(well.well_name, lateral.lateral_number, df_valve)
            print_inflow_control_device += _format_inflow_control_device(
                well.well_name, lateral.lateral_number, df_inflow_control_device
            )
            print_autonomous_inflow_control_device += _format_autonomous_inflow_control_device(
                well.well_name, lateral.lateral_number, df_autonomous_inflow_control_device
            )
            print_inflow_control_valve += _format_inflow_control_valve(
                well.well_name, lateral.lateral_number, df_inflow_control_valve
            )
            print_density_activated_recovery += _format_density_activated_recovery(
                well.well_number, df_density_activated_recovery
            )
            print_autonomous_inflow_control_valve += _format_autonomous_inflow_control_valve(
                well.well_number, df_autonomous_inflow_control_valve
            )

            if figure_name is not None:
                logger.info("Creating figure for lateral %s.", lateral.lateral_number)
                with PdfPages(figure_name) as figure:
                    figure.savefig(
                        visualize_well(well.well_name, df_well, df_reservoir, case.segment_length),
                        orientation="landscape",
                    )
                logger.info("Creating schematics: %s.pdf", figure_name)

        if completion_data_list:
            self.print_completion_data = "\n".join(completion_data_list)

        if self.print_well_segments:
            self.print_well_segments = f"{self.print_well_segments}\n/\n\n"

        if self.print_completion_segments:
            self.print_completion_segments = (
                f"{Keywords.COMPLETION_SEGMENTS}\n'{well.well_name}' /{self.print_completion_segments}\n/\n\n\n"
            )

        mask = case.completion_table[Headers.DEVICE_TYPE] == Content.AUTONOMOUS_INFLOW_CONTROL_VALVE
        if any(well.well_name == case.completion_table[mask][Headers.WELL]):
            self.bonus_data += CORRELATION_UDQ
        if print_well_segments_link:
            self.bonus_data += f"{Keywords.WELL_SEGMENTS_LINK}{print_well_segments_link}\n/\n\n\n"
        if print_valve:
            self.bonus_data += f"{Keywords.WELL_SEGMENTS_VALVE}{print_valve}\n/\n\n\n"

        if print_inflow_control_device:
            self.bonus_data += f"{Keywords.INFLOW_CONTROL_DEVICE}{print_inflow_control_device}\n/\n\n\n"
        if print_autonomous_inflow_control_device:
            self.bonus_data += (
                f"{Keywords.AUTONOMOUS_INFLOW_CONTROL_DEVICE}{print_autonomous_inflow_control_device}\n/\n\n\n"
            )
        if print_inflow_control_valve:
            self.bonus_data += f"{Keywords.WELL_SEGMENTS_VALVE}{print_inflow_control_valve}\n/\n\n\n"
        if print_density_activated_recovery:
            metadata = (
                f"{'-' * 100}\n"
                "-- This is how we model DAR technology using sets of ACTIONX keywords.\n"
                "-- The segment dP curves changes according to the segment water-\n"
                "-- and gas volume fractions at downhole condition.\n"
                "-- The value of Cv is adjusted according to the segment length and the number of\n"
                "-- devices per joint. The constriction area varies according to values of\n"
                "-- volume fractions.\n"
                f"{'-' * 100}\n\n\n"
            )
            self.bonus_data += metadata + print_density_activated_recovery + "\n\n\n\n"
        if print_autonomous_inflow_control_valve:
            metadata = (
                f"{'-' * 100}\n"
                "-- This is how we model AICV technology using sets of ACTIONX keyword\n"
                "-- the DP parameters change according to the segment water cut (at downhole condition )\n"
                "-- and gas volume fraction (at downhole condition)\n"
                f"{'-' * 100}\n\n\n"
            )
            self.bonus_data += metadata + print_autonomous_inflow_control_valve + "\n\n\n\n"


def metadata_banner(paths: tuple[str, str] | None) -> str:
    """Formats the header banner, with metadata.

    Args:
        paths: The paths to case and schedule files.

    Returns:
        Formatted header.
    """
    header = f"{'-' * 100}\n-- Output from completor {get_version()}\n"
    if paths is not None:
        header += f"-- Case file: {paths[0]}\n-- Schedule file: {paths[1]}\n"
    else:
        logger.warning("Could not resolve case-file path to output file.")
        header += "-- Case file: No path found\n-- Schedule file: No path found\n"

    header += (
        f"-- Created by : {(getpass.getuser()).upper()}\n"
        f"-- Created at : {datetime.now().strftime('%Y %B %d %H:%M')}\n"
        f"{'-' * 100}\n\n"
    )
    return header


def _check_well_segments_header(welsegs_header: pd.DataFrame, start_measured_depths: pd.Series) -> pd.DataFrame:
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


def _update_segmentbranch(df_device: pd.DataFrame, df_annulus: pd.DataFrame) -> tuple[int, int]:
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


def _format_completion_data(well_name: str, lateral_number: int, df_compdat: pd.DataFrame) -> str:
    """Print completion data to file.

    Args:
        well_name: Name of well.
        lateral_number: Current laterals number.
        df_compdat: Completion data.

    Returns:
        Formatted string.
    """
    if df_compdat.empty:
        return ""
    nchar = prepare_outputs.get_number_of_characters(df_compdat)
    # TODO: Bit unrelated but reduce vspace of this get_header to only take one line with LATERAL X in middle?
    return prepare_outputs.get_header(
        well_name, Keywords.COMPLETION_DATA, lateral_number, "", nchar
    ) + prepare_outputs.dataframe_tostring(df_compdat, True)


def _format_well_segments(
    well_name: str, lateral_number: int, df_tubing: pd.DataFrame, df_device: pd.DataFrame, df_annulus: pd.DataFrame
) -> str:
    """Print well segments to file.

    Args:
        well_name: Name of well.
        lateral_number: Current lateral number.
        df_tubing: Tubing data.
        df_device: Device data.
        df_annulus: Annulus data.

    Returns:
        Formatted string.
    """
    print_welsegs = ""
    nchar = prepare_outputs.get_number_of_characters(df_tubing)
    if not df_device.empty:
        print_welsegs += (
            "\n"
            + prepare_outputs.get_header(well_name, Keywords.WELL_SEGMENTS, lateral_number, "Tubing", nchar)
            + prepare_outputs.dataframe_tostring(df_tubing, True)
        )
        print_welsegs += (
            "\n"
            + prepare_outputs.get_header(well_name, Keywords.WELL_SEGMENTS, lateral_number, "Device", nchar)
            + prepare_outputs.dataframe_tostring(df_device, True)
        )
    if not df_annulus.empty:
        print_welsegs += (
            "\n"
            + prepare_outputs.get_header(well_name, Keywords.WELL_SEGMENTS, lateral_number, "Annulus", nchar)
            + prepare_outputs.dataframe_tostring(df_annulus, True)
        )
    return print_welsegs


def _format_well_segments_link(well_name: str, lateral_number: int, df_well_segments_link: pd.DataFrame) -> str:
    """Formats well-segments for links.

    Args:
        well_name: Name of well.
        lateral_number: Current lateral number.
        df_well_segments_link: Well-segmentation data with links.

    Returns:
        Formatted string.
    """
    if df_well_segments_link.empty:
        return ""
    nchar = prepare_outputs.get_number_of_characters(df_well_segments_link)
    return (
        "\n"
        + prepare_outputs.get_header(well_name, Keywords.WELL_SEGMENTS_LINK, lateral_number, "", nchar)
        + prepare_outputs.dataframe_tostring(df_well_segments_link, True)
    )


def _format_completion_segments(well_name: str, lateral_number: int, df_compsegs: pd.DataFrame) -> str:
    """Formats completion segments.

    Args:
        well_name: Name of well.
        lateral_number: Current lateral number.
        df_compsegs: Completion data.

    Returns:
        Formatted string.
    """
    if df_compsegs.empty:
        return ""
    nchar = prepare_outputs.get_number_of_characters(df_compsegs)
    return (
        " \n"
        + prepare_outputs.get_header(well_name, Keywords.COMPLETION_SEGMENTS, lateral_number, "", nchar)
        + prepare_outputs.dataframe_tostring(df_compsegs, True)
    )


def _format_autonomous_inflow_control_device(well_name: str, lateral_number: int, df_wsegaicd: pd.DataFrame) -> str:
    """Formats well-segments for autonomous inflow control devices.

    Args:
        well_name: Name of well.
        lateral_number: Current lateral number.
        df_wsegaicd: Well-segments data for autonomous inflow control devices.

    Returns:
        Formatted string.
    """
    if df_wsegaicd.empty:
        return ""
    nchar = prepare_outputs.get_number_of_characters(df_wsegaicd)
    return (
        "\n"
        + prepare_outputs.get_header(well_name, Keywords.INFLOW_CONTROL_DEVICE, lateral_number, "", nchar)
        + prepare_outputs.dataframe_tostring(df_wsegaicd, True)
    )


def _format_inflow_control_device(well_name: str, lateral_number: int, df_wsegsicd: pd.DataFrame) -> str:
    """Formats well-segments for inflow control devices.

    Args:
        well_name: Name of well.
        lateral_number: Current lateral number.
        df_wsegsicd: Well-segment data for inflow control devices.

    Returns:
        Formatted string.
    """
    if df_wsegsicd.empty:
        return ""
    nchar = prepare_outputs.get_number_of_characters(df_wsegsicd)
    return (
        "\n"
        + prepare_outputs.get_header(well_name, Keywords.INFLOW_CONTROL_DEVICE, lateral_number, "", nchar)
        + prepare_outputs.dataframe_tostring(df_wsegsicd, True)
    )


def _format_valve(well_name: str, lateral_number: int, df_wsegvalv) -> str:
    """Formats well-segments for valves.

    Args:
        well_name: Name of well.
        lateral_number: Current lateral number.
        df_wsegvalv: Well-segment data for valves.

    Returns:
        Formatted string.
    """
    if df_wsegvalv.empty:
        return ""
    nchar = prepare_outputs.get_number_of_characters(df_wsegvalv)
    return (
        "\n"
        + prepare_outputs.get_header(well_name, Keywords.WELL_SEGMENTS_VALVE, lateral_number, "", nchar)
        + prepare_outputs.dataframe_tostring(df_wsegvalv, True)
    )


def _format_inflow_control_valve(well_name: str, lateral_number: int, df_wsegicv: pd.DataFrame) -> str:
    """Formats well-segments for inflow control valve.

    Args:
        well_name: Name of well.
        lateral_number: Current lateral number.
        df_wsegicv: Well-segment data for inflow control valves.

    Returns:
        Formatted string.
    """
    if df_wsegicv.empty:
        return ""
    nchar = prepare_outputs.get_number_of_characters(df_wsegicv)
    return (
        "\n"
        + prepare_outputs.get_header(well_name, Keywords.WELL_SEGMENTS_VALVE, lateral_number, "", nchar)
        + prepare_outputs.dataframe_tostring(df_wsegicv, True)
    )


def _format_density_activated_recovery(well_number: int, df_wsegdar: pd.DataFrame) -> str:
    """Formats well-segments for density activated recovery valve.

    Args:
        well_number: The well's number
        df_wsegdar: Data to print.

    Returns:
        Formatted string.
    """
    if df_wsegdar.empty:
        return ""
    return prepare_outputs.print_wsegdar(df_wsegdar, well_number + 1)


def _format_autonomous_inflow_control_valve(well_number: int, df_wsegaicv: pd.DataFrame) -> str:
    """Formats the AICV section.

    Args:
        well_number: The well's number
        df_wsegaicv: Data to print.

    Returns:
        Formatted string.
    """
    if df_wsegaicv.empty:
        return ""
    return prepare_outputs.print_wsegaicv(df_wsegaicv, well_number + 1)


def _branch_revision(
    lateral_number: int,
    active_laterals: list[int] | npt.NDArray[np.int64],
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
    if df_device.get(Headers.BRANCH) is not None:
        df_device[Headers.BRANCH] += correction
    if df_annulus.get(Headers.BRANCH) is not None:
        df_annulus[Headers.BRANCH] += correction
    return df_device, df_annulus


def _connect_lateral(
    well_name: str, lateral: Lateral, top: pd.DataFrame, well: Well, case: ReadCasefile
) -> pd.DataFrame:
    """Connect lateral to main wellbore/branch.

    The main branch can either have a tubing- or device-layer connected.
    By default, the lateral will be connected to tubing-layer, but if connect_to_tubing is False,
    it will be connected to device-layer.
    Abort if it cannot find device layer at junction depth.

    Args:
        well_name: Well name.
        lateral: Current lateral to connect.
        top: DataFrame of first connection.
        well: Well object containing data from whole well.

    Returns:
        Tubing data with modified outsegment.

    Raises:
        CompletorError: If there is no device layer at junction of lateral.
    """
    if top.empty:
        lateral.df_tubing.at[0, Headers.OUT] = 1  # Default out segment.
        return lateral.df_tubing

    first_lateral_in_top = top[Headers.TUBING_BRANCH].to_numpy()[0]
    top_lateral = [lateral for lateral in well.active_laterals if lateral.lateral_number == first_lateral_in_top][0]
    junction_measured_depth = float(top[Headers.TUBING_MEASURED_DEPTH].to_numpy()[0])
    if junction_measured_depth > lateral.df_tubing[Headers.MEASURED_DEPTH][0]:
        logger.warning(
            "Found a junction above the start of the tubing layer, well %s, branch %s. "
            "Check the depth of segments pointing at the main stem in schedulefile.",
            well_name,
            lateral.lateral_number,
        )
    if case.connect_to_tubing(well_name, lateral.lateral_number):
        layer_to_connect = top_lateral.df_tubing
        measured_depths = top_lateral.df_tubing[Headers.MEASURED_DEPTH]
    else:
        layer_to_connect = top_lateral.df_device
        measured_depths = top_lateral.df_device[Headers.MEASURED_DEPTH]
    try:
        if case.connect_to_tubing(well_name, lateral.lateral_number):
            # Since the junction_measured_depth has segment tops and layer_to_connect has grid block midpoints,
            # a junction at the top of the well may not be found. Therefore, we try the following:
            if (np.array(~(measured_depths <= junction_measured_depth))).all():
                junction_measured_depth = measured_depths.iloc[0]
                idx = np.where(measured_depths <= junction_measured_depth)[0][-1]

            else:
                idx = np.where(measured_depths <= junction_measured_depth)[0][-1]
        else:
            # Add 0.1 to junction measured depth since it refers to the tubing layer junction measured depth,
            # and the device layer measured depth is shifted 0.1 m to the tubing layer.
            idx = np.where(measured_depths <= junction_measured_depth + 0.1)[0][-1]
    except IndexError as err:
        raise CompletorError(
            f"Cannot find a device layer at junction of lateral {lateral.lateral_number} in {well_name}"
        ) from err
    out_segment = layer_to_connect.at[idx, Headers.START_SEGMENT_NUMBER]
    lateral.df_tubing.at[0, Headers.OUT] = out_segment
    return lateral.df_tubing
