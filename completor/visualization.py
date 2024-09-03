from __future__ import annotations

import matplotlib.pyplot as plt  # type: ignore
import matplotlib.ticker as ticker  # type: ignore
from matplotlib import rcParams
from matplotlib.axes import Axes  # type: ignore
from matplotlib.figure import Figure  # type: ignore


def update_fonts(family: str = "DejaVu Serif", size: float = 12) -> None:
    """Update the font and size in the plot.

    Args:
        family: Font family name.
        size: Font sizes.
    """
    rcParams["font.family"] = family
    rcParams["font.size"] = size


def format_axis(subplot: Axes, title: str, xlabel: str, ylabel: str, categorical: bool = False) -> Axes:
    """Format axis of the subplot.

    Args:
        subplot: Plt subplot.
        title: Title of the subplot.
        xlabel: Name of the x axis.
        ylabel: Name of the y axis.
        categorical: If the x axis is not int or float set to True, otherwise False.

    Returns:
        Formatted matplotlib subplot.
    """
    min_val, max_val = subplot.get_ylim()
    subplot.set_xlabel(xlabel)
    subplot.set_ylabel(ylabel)
    if categorical:
        subplot.minorticks_on()
        subplot.tick_params(axis="both", which="major", direction="in", length=6, width=1.0)
        subplot.tick_params(axis="both", which="minor", direction="in", length=3, width=1.0)
        major = (max_val - min_val) / 5.0
        if major < 1.0:
            major = round(major, 1)
            if abs(major - 1.0) < abs(major - 0.5):
                major = 1.0
            else:
                if abs(major - 0.5) < abs(major - 0.25):
                    major = 0.5
                else:
                    major = 0.25
        else:
            major = round(major, 0)
        subplot.yaxis.set_major_locator(ticker.MultipleLocator(major))
        subplot.minorticks_off()
    else:
        subplot.minorticks_on()
        subplot.tick_params(axis="both", which="major", direction="in", length=6, width=1.0)
        subplot.tick_params(axis="both", which="minor", direction="in", length=3, width=1.0)
    subplot.yaxis.set_ticks_position("both")
    subplot.xaxis.set_ticks_position("both")
    subplot.grid(which="both", linestyle="-", linewidth=0.1, color="grey", alpha=0.1)
    subplot.set_title(title)
    return subplot


def format_scale(
    subplot: Axes,
    xscale: str = "linear",
    yscale: str = "linear",
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
) -> Axes:
    """Format axis scale.

    Args:
        subplot: matplotlib subplot.
        xscale: Scale type for x axis. Permitted value log/linear.
        yscale: Scale type for y axis. Permitted value log/linear.
        xlim: [Min, max] limit of the x axis, default=None.
        ylim: [Min, max] limit of the y axis, default=None.

    Returns:
        Reformatted matplotlib subplot.
    """
    subplot.set_xscale(xscale)
    subplot.set_yscale(yscale)
    if xlim is not None:
        subplot.set_xlim(xlim)
    if ylim is not None:
        subplot.set_ylim(ylim)
    return subplot


def format_legend(subplot: Axes, legend: bool = True, location: str = "right") -> Axes:
    """Format legend of subplot.

    Args:
        subplot: Matplotlib subplot.
        legend: True for on and False for off.
        location: Legend location.

    Returns:
        Reformatted matplotlib subplot.
    """
    if legend:
        if location == "top":
            subplot.legend(
                numpoints=1,
                bbox_to_anchor=(0.0, 1.02, 1.0, 0.102),
                loc=3,
                ncol=2,
                mode="expand",
                borderaxespad=0,
                framealpha=0.2,
            )
        elif location == "right":
            subplot.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    return subplot


def subplot_position(num_plots: int) -> tuple[int, int]:
    """Return the row and index of subplot position.

    Args:
        num_plots: Number of subplots in the figure.

    Returns:
        Row, column.
    """
    list_rows = [1, 1, 1, 2, 2, 2, 2, 2, 3, 3, 5]
    list_cols = [1, 2, 3, 2, 3, 3, 4, 4, 3, 4, 5]
    return list_rows[num_plots - 1], list_cols[num_plots - 1]


def create_figure(figsize: list[int] | tuple[int, int] | None = (18, 12)) -> Figure:
    """Create a matplotlib figure.

    Args:
        figsize: [Width, height].

    Returns:
        Matplotlib figure.
    """
    if figsize is None:
        return plt.figure()
    return plt.figure(figsize=figsize)


def close_figure() -> None:
    """Close all matplotlib figures."""
    plt.close("all")
