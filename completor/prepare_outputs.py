from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd

from completor.completion import WellSchedule
from completor.logger import logger
from completor.read_casefile import ReadCasefile
from completor.utils import abort, as_data_frame


def trim_pandas(df_temp: pd.DataFrame) -> pd.DataFrame:
    """
    Trim a pandas dataframe containing default values.

    Args:
        df_temp: DataFrame

    Returns:
        Updated DataFrame
    """
    header = df_temp.columns.to_numpy()
    start_trim = -1
    found_start = False
    for idx in range(df_temp.shape[1]):
        col_value = df_temp.iloc[:, idx].to_numpy().flatten().astype(str)
        find_star = all("*" in elem for elem in col_value)
        if find_star:
            if not found_start:
                start_trim = idx
                found_start = True
        else:
            start_trim = idx + 1
            found_start = False
    new_header = header[:start_trim]
    return df_temp[new_header]


def add_columns_first_last(df_temp: pd.DataFrame, add_first: bool = True, add_last: bool = True) -> pd.DataFrame:
    """
    Add the first and last column of DataFrame.

    Args:
        df_temp: E.g. WELSPECS, COMPSEGS, COMPDAT, WELSEGS, etc.
        add_first: Add the first column
        add_last: Add the last column

    Returns:
        Updated DataFrame
    """
    # first trim pandas
    df_temp = trim_pandas(df_temp)
    # add first and last column
    nline = df_temp.shape[0]
    if add_first:
        df_temp.insert(loc=0, column="--", value=np.full(nline, fill_value=" "))
    if add_last:
        df_temp[""] = ["/"] * nline
    return df_temp


def dataframe_tostring(
    df_temp: pd.DataFrame,
    format_column: bool = False,
    trim_df: bool = True,
    header: bool = True,
    formatters: Mapping[str | int, Callable[..., Any]] | None = None,
) -> str:
    """
    Convert DataFrame to string.

    Args:
        df_temp: COMPDAT, COMPSEGS, etc.
        format_column: If columns are formatted
        trim_df: To trim or not to trim. Default: True
        formatters: Dictionary of the column format. Default: None
        header: Keep header (True) or not (False)

    Returns:
        Text string of the DataFrame
    """
    if df_temp.empty:
        return ""
    # check if the dataframe has first = "--" and last column ""
    columns = df_temp.columns.to_numpy()
    if columns[-1] != "":
        if trim_df:
