from __future__ import annotations

import pandas as pd  # type: ignore
from matplotlib.axes import Axes  # type: ignore
from matplotlib.figure import Figure  # type: ignore

from completor import visualization
from completor.constants import Headers


def visualize_tubing(axs: Axes, df_well: pd.DataFrame) -> Axes:
    """
    Visualize the tubing layer.

    Args:
        axs: Pyplot axis
        df_well: Well information

    Returns:
        Pyplot axis

    Uses the DataFrame df_well with format shown in
    ``create_wells.CreateWells.complete_the_well``.
    """
    df_device = df_well[(df_well[Headers.NDEVICES] > 0) | (df_well[Headers.DEVICE_TYPE] == "PERF")]
    if df_device.shape[0] > 0:
        axs.plot(df_well[Headers.TUB_MD].to_numpy(), [1] * df_well.shape[0], "go-")
    return axs


def visualize_device(axs: Axes, df_well: pd.DataFrame) -> Axes:
    """
    Visualize device layer.

    Args:
        axs: Pyplot axis
        df_well: Well DataFrame

    Returns:
        Pyplot axis

    Uses the DataFrame df_well with format shown in
    ``create_wells.CreateWells.complete_the_well``.
    """
    df_device = df_well[(df_well[Headers.NDEVICES] > 0) | (df_well[Headers.DEVICE_TYPE] == "PERF")]
    for idx in range(df_device.shape[0]):
        xpar = [df_device[Headers.TUB_MD].iloc[idx]] * 2
        ypar = [1.0, 2.0]
        if df_device[Headers.DEVICE_TYPE].iloc[idx] == "PERF":
            axs.plot(xpar, ypar, "ro-", markevery=[1])
        elif df_device[Headers.DEVICE_TYPE].iloc[idx] == "AICD":
            axs.plot(xpar, ypar, "rD-", markevery=[1])
        elif df_device[Headers.DEVICE_TYPE].iloc[idx] == "ICD":
            axs.plot(xpar, ypar, "rs-", markevery=[1])
        elif df_device[Headers.DEVICE_TYPE].iloc[idx] == "VALVE":
            axs.plot(xpar, ypar, "rv-", markevery=[1])
        elif df_device[Headers.DEVICE_TYPE].iloc[idx] == "DAR":
            axs.plot(xpar, ypar, "rP-", markevery=[1])
        elif df_device[Headers.DEVICE_TYPE].iloc[idx] == "AICV":
            axs.plot(xpar, ypar, "r*-", markevery=[1])
    return axs


def visualize_annulus(axs: Axes, df_well: pd.DataFrame) -> Axes:
    """
    Visualize annulus layer.

    Args:
        axs: Pyplot axis
        df_well: Well DataFrame

    Returns:
        Pyplot axis

    Uses the DataFrame df_well with format shown in
    ``create_wells.CreateWells.complete_the_well``.
    """
    df_annulus = df_well[df_well[Headers.ANNULUS_ZONE] > 0]
    branches = df_well[Headers.ANNULUS_ZONE].unique()
    for branch in branches:
        df_branch = df_annulus[df_annulus[Headers.ANNULUS_ZONE] == branch]
        xpar = df_branch[Headers.TUB_MD].to_numpy()
        ypar = [3.0] * len(xpar)
        axs.plot(xpar, ypar, "bo-")
        # find the first connection in branches
        df_annulus_with_connection_to_tubing = df_branch[
            (df_branch[Headers.NDEVICES] > 0) | (df_branch[Headers.DEVICE_TYPE] == "PERF")
        ]
        for idx in range(df_annulus_with_connection_to_tubing.shape[0]):
            xpar = [df_annulus_with_connection_to_tubing[Headers.TUB_MD].iloc[idx]] * 2
            ypar = [2.0, 3.0]
            if idx == 0:
                axs.plot(xpar, ypar, "bo-", markevery=[1])
            else:
                axs.plot(xpar, ypar, "bo:", markevery=[1])
    return axs


def visualize_reservoir(axs: Axes, ax_twinx: Axes, df_reservoir: pd.DataFrame) -> tuple[Axes, Axes]:
    """
    Visualize reservoir layer.

    Args:
        axs: Pyplot axis
        ax_twinx: Pyplot axis
        df_reservoir: Reservoir DataFrame

    Returns:
        Pyplot axis

    Uses the DataFrame df_reservoir with format shown in
    ``create_wells.CreateWells.select_well``.
    """
    for idx in range(df_reservoir.shape[0]):
        xpar = [df_reservoir[Headers.START_MD].iloc[idx], df_reservoir[Headers.END_MEASURED_DEPTH].iloc[idx]]
        ypar = [4.0, 4.0]
        axs.plot(xpar, ypar, "k|-")
        if df_reservoir[Headers.ANNULUS_ZONE].iloc[idx] > 0:
            axs.annotate(
                "",
                xy=(df_reservoir[Headers.TUB_MD].iloc[idx], 3.0),
                xytext=(df_reservoir[Headers.MD].iloc[idx], 4.0),
                arrowprops=dict(facecolor="black", shrink=0.05, width=0.5, headwidth=4.0),
            )
        else:
            if df_reservoir[Headers.NDEVICES].iloc[idx] > 0 or df_reservoir[Headers.DEVICE_TYPE].iloc[idx] == "PERF":
                axs.annotate(
                    "",
                    xy=(df_reservoir[Headers.TUB_MD].iloc[idx], 2.0),
                    xytext=(df_reservoir[Headers.MD].iloc[idx], 4.0),
                    arrowprops=dict(facecolor="black", shrink=0.05, width=0.5, headwidth=4.0),
                )
    # get connection factor
    if "1*" not in df_reservoir[Headers.CF].to_numpy().tolist():
        max_cf = max(df_reservoir[Headers.CF].to_numpy())
        ax_twinx.plot(df_reservoir[Headers.MD], df_reservoir[Headers.CF], "k-")
        ax_twinx.invert_yaxis()
        ax_twinx.set_ylim([max_cf * 5.0 + 1e-5, 0])
        ax_twinx.fill_between(df_reservoir[Headers.MD], 0, df_reservoir[Headers.CF], alpha=0.5)

    return axs, ax_twinx


def visualize_annotation(axs: Axes, ax_twinx: Axes, max_md: float, min_md: float) -> tuple[Axes, Axes]:
    """
    Add annotation in the plot.

    Args:
        axs: Pyplot axis
        ax_twinx: Pyplot axis
        max_md: Maximum measured depth
        min_md: Minimum measured depth

    Returns:
        Pyplot axis
    """
    axs.annotate(
        "Tubing Layer", xy=(max_md + 0.1 * (max_md - min_md), 1.0), xytext=(max_md + 0.1 * (max_md - min_md), 1.0)
    )
    axs.annotate(
        "Device/Screen Layer",
        xy=(max_md + 0.1 * (max_md - min_md), 2.0),
        xytext=(max_md + 0.1 * (max_md - min_md), 2.0),
    )
    axs.annotate(
        "Annulus Layer", xy=(max_md + 0.1 * (max_md - min_md), 3.0), xytext=(max_md + 0.1 * (max_md - min_md), 3.0)
    )
    axs.annotate(
        "Reservoir Layer", xy=(max_md + 0.1 * (max_md - min_md), 4.0), xytext=(max_md + 0.1 * (max_md - min_md), 4.0)
    )
    axs.set_ylim([0, 5])
    axs.set_xlim([min_md - 0.1 * (max_md - min_md), max_md + 0.3 * (max_md - min_md)])
    axs.set_xlabel("mMD")
    ax_twinx.set_ylabel(Headers.CF)
    axs.minorticks_on()
    return axs, ax_twinx


def visualize_well(
    well_name: str, df_well: pd.DataFrame, df_reservoir: pd.DataFrame, segment_length: float | str
) -> Figure:
    """
    Visualizing well completion schematic.

    Args:
        well_name: Well name
        df_well: Well DataFrame
        df_reservoir: Reservoir DataFrame for the well
        segment_length: Segment length

    Returns:
        Matplotlib figure

    | Uses DataFrames with formats as shown in
    | :ref:`df_reservoir`
    | :ref:`df_well`
    """
    figure = visualization.create_figure()
    laterals = df_well[Headers.LATERAL].unique()
    if isinstance(segment_length, float):
        if segment_length >= 0.0:
            max_md = max(df_well[Headers.TUB_MD].to_numpy())
            min_md = min(df_well[Headers.TUB_MD].to_numpy())
        else:
            max_md = max(df_reservoir[Headers.MD].to_numpy())
            min_md = min(df_reservoir[Headers.MD].to_numpy())
    elif isinstance(segment_length, str):
        max_md = max(df_well[Headers.TUB_MD].to_numpy())
        min_md = min(df_well[Headers.TUB_MD].to_numpy())
    else:
        raise TypeError(f"segment_length has invalid type ({type(segment_length)})")
    for lateral_idx, lateral in enumerate(laterals):
        df_this_well = df_well[df_well[Headers.LATERAL] == lateral]
        df_this_reservoir = df_reservoir[df_reservoir[Headers.LATERAL] == lateral]
        axs = figure.add_subplot(len(laterals), 1, lateral_idx + 1)
        axs.get_yaxis().set_visible(False)
        axs.set_title(f" Well : {well_name} : Lateral : {lateral}")
        ax_twinx = axs.twinx()
        axs.tick_params(which="both", direction="in")
        ax_twinx.tick_params(which="both", direction="in")
        # Tubing layer
        axs = visualize_tubing(axs, df_this_well)
        # Device / screen layer
        axs = visualize_device(axs, df_this_well)
        # Annulus layer
        axs = visualize_annulus(axs, df_this_well)
        # Reservoir layer
        axs, ax_twinx = visualize_reservoir(axs, ax_twinx, df_this_reservoir)
        # print annotation in the plot
        axs, ax_twinx = visualize_annotation(axs, ax_twinx, max_md, min_md)
    figure.subplots_adjust(hspace=0.5, wspace=0.5)
    figure.set_size_inches(18, 3 * len(laterals))
    return figure
