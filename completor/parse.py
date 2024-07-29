"""Functions for reading files."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Literal, overload

import numpy as np
import numpy.typing as npt
import pandas as pd

from completor.constants import Headers, Keywords
from completor.exceptions.clean_exceptions import CompletorError


class ContentCollection(list):
    """A subclass of list that can accept additional attributes. To be used like a regular list."""

    def __new__(cls, *args, **kwargs):
        """Override new method of list."""
        return super().__new__(cls, args, kwargs)

    def __init__(self, *args, name: str, well: pd.DataFrame | str | None = None):
        """Override init method of list."""
        if len(args) == 1 and hasattr(args[0], "__iter__"):
            list.__init__(self, args[0])
        else:
            list.__init__(self, args)
        self.name = name
        self.well = well

    def __call__(self, **kwargs):
        """Override call method of list."""
        self.__dict__.update(kwargs)
        return self


@overload
def locate_keyword(
    content: list[str], keyword: str, end_char: str = ..., take_first: Literal[True] = ...
) -> tuple[int, int]: ...


@overload
def locate_keyword(
    content: list[str], keyword: str, end_char: str = ..., *, take_first: Literal[False]
) -> tuple[npt.NDArray[np.int64], npt.NDArray[np.int64]]: ...


@overload
def locate_keyword(
    content: list[str], keyword: str, end_char: str, take_first: Literal[False]
) -> tuple[npt.NDArray[np.int64], npt.NDArray[np.int64]]: ...


def locate_keyword(
    content: list[str], keyword: str, end_char: str = "/", take_first: bool = True
) -> tuple[int, int] | tuple[npt.NDArray[np.int64], npt.NDArray[np.int64]]:
    """Find the start and end of a keyword.

    The start of the keyword is the keyword itself.
    The end of the keyword is end_char if specified.

    Args:
        content: List of strings.
        keyword: Keyword name.
        end_char: String which ends the keyword. Defaults to '/' Because it's the most used in this code base.
        take_first: Flag to toggle whether to return the first elements of the arrays.

    Returns:
        start_index - array that located the keyword (or its first element).
        end_index - array that locates the end of the keyword (or its first element).

    Raises:
        CompletorError: If keyword had no end record.
        ValueError: If keyword cannot be found in case file.
    """
    content_length = len(content)
    start_index: npt.NDArray[np.int64] = np.where(np.asarray(content) == keyword)[0]
    if start_index.size == 0:
        # the keyword is not found
        return np.asarray([-1]), np.asarray([-1])

    end_index: npt.NDArray[np.int64] = np.array([], dtype="int64")
    idx = 0
    for istart in start_index:
        if end_char != "":
            idx = istart + 1
            for idx in range(istart + 1, content_length):
                if content[idx] == end_char:
                    break
            if (idx == content_length - 1) and content[idx] != end_char:
                # error if until the last line the end char is not found
                raise CompletorError(f"Keyword {keyword} has no end record")
        else:
            # if there is no end character is specified, then the end of a record is the next keyword or end of line
            for idx in range(istart + 1, content_length):
                first_char = content[idx][0]
                if first_char.isalpha():
                    # end is before the new keyword
                    idx -= 1
                    break

        try:
            end_index = np.append(end_index, idx)
        except NameError as err:
            raise ValueError(f"Cannot find keyword {keyword} in file") from err
    # return all in a numpy array format
    end_index = np.asarray(end_index)
    if take_first:
        return start_index[0], end_index[0]
    return start_index, end_index


def take_first_record(
    start_index: list[float] | npt.NDArray[np.float64], end_index: list[float] | npt.NDArray[np.float64]
) -> tuple[float | int, float | int]:
    """Take the first record of a list.

    Args:
        start_index:
        end_index:

    Returns:
        Tuple of floats.
    """
    return start_index[0], end_index[0]


def unpack_records(record: list[str]) -> list[str]:
    """Unpack the keyword content.

    E.g. 3* --> 1* 1* 1*

    Args:
        record: List of strings.

    Returns:
        Updated record of strings.
    """
    record = deepcopy(record)
    record_length = len(record)
    i = -1
    while i < record_length - 1:
        # Loop and find if default records are found
        i += 1
        if "*" in str(record[i]):
            # default is found and get the number before the star *
            ndefaults = re.search(r"\d+", record[i])
            record[i] = "1*"
            if ndefaults:
                _ndefaults = int(ndefaults.group())
                idef = 0
                while idef < _ndefaults - 1:
                    record.insert(i, "1*")
                    idef += 1
            record_length = len(record)
    return record


def complete_records(record: list[str], keyword: str) -> list[str]:
    """Complete the record.

    Args:
        record: List of strings.
        keyword: Keyword name.

    Returns:
        Completed list of strings.
    """
    if keyword == Keywords.WSEGVALV:
        return complete_wsegvalv_record(record)

    dict_ncolumns = {
        Keywords.WELSPECS: 17,
        Keywords.COMPDAT: 14,
        Keywords.WELSEGS_H: 12,
        Keywords.WELSEGS: 15,
        Keywords.COMPSEGS: 11,
    }
    max_column = dict_ncolumns[keyword]
    ncolumn = len(record)
    if ncolumn < max_column:
        extension = ["1*"] * (max_column - ncolumn)
        record.extend(extension)
    elif ncolumn > max_column:
        record = record[:max_column]
    return record


def complete_wsegvalv_record(record: list[str]) -> list[str]:
    """Complete the WSEGVALV record.

    Columns PIPE_DIAMETER, ABSOLUTE_PIPE_ROUGHNESS, PIPE_CROSS_SECTION_AREA, FLAG, and MAX_FLOW_CROSS_SECTIONAL_AREA
    might not be provided and need to be filled in with default values.

    Args:
        record: List of strings.

    Returns:
        Completed list of strings.
    """
    wsegvalv_columns = 10
    ac_index = 3
    default_state = "OPEN"

    if len(record) < 8:
        # add defaults
        record.extend(["1*"] * (8 - len(record)))

    if len(record) < 9:
        # append default state
        record.append(default_state)

    if len(record) < wsegvalv_columns:
        # append default ac_max
        record.append(record[ac_index])

    if len(record) > wsegvalv_columns:
        record = record[:wsegvalv_columns]

    return record


def read_schedule_keywords(
    content: list[str], keywords: list[str], optional_keywords: list[str] = []
) -> tuple[list[ContentCollection], npt.NDArray[np.str_]]:
    """Read schedule keywords or all keywords in table format.

    E.g. WELSPECS, COMPDAT, WELSEGS, COMPSEGS, WSEGVALV.

    Args:
        content: List of strings. Lines from the schedule file.
        keywords: List of keywords to find data for.
        optional_keywords: List of optional keywords. Will not raise error if not found.

    Returns:
        df_collection - Object collection (pd.DataFrame).
        remaining_content - List of strings of un-listed keywords.

    Raises:
        CompletorError: If keyword is not found.
    """
    content = deepcopy(content)
    used_index = np.asarray([-1])
    collections = []
    # get the contents that correspond with the list_keywords
    for keyword in keywords + optional_keywords:
        start_index, end_index = locate_keyword(content, keyword, take_first=False)
        if start_index[0] == end_index[0] and keyword not in optional_keywords:
            raise CompletorError(f"Keyword {keyword} is not found")
        for idx, start in enumerate(start_index):
            end = end_index[idx]
            used_index = np.append(used_index, np.arange(start, end + 1))
            keyword_content = [_create_record(content, keyword, irec, start) for irec in range(start + 1, end)]
            collection = ContentCollection(keyword_content, name=keyword)
            if keyword in [Keywords.WELSEGS, Keywords.COMPSEGS]:
                # remove string characters
                collection.well = remove_string_characters(keyword_content[0][0])
            collections.append(collection)
    # get anything that is not listed in the keywords
    # ignore the first record -1
    used_index = used_index[1:]
    mask = np.full(len(content), True, dtype=bool)
    mask[used_index] = False
    return collections, np.asarray(content)[mask]


def _create_record(content: list[str], keyword: str, irec: int, start: int) -> list[str]:
    _record = content[irec]
    # remove / sign at the end
    _record = list(filter(None, _record.rsplit("/", 1)))[0]
    # split each column
    record = list(filter(None, _record.split(" ")))
    # unpack records
    record = unpack_records(record)
    # complete records
    record = complete_records(
        record, Keywords.WELSEGS_H if keyword == Keywords.WELSEGS and irec == start + 1 else keyword
    )
    return record


def get_welsegs_table(collections: list[ContentCollection]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return dataframe table of WELSEGS.

    Args:
        collections: ContentCollection class.

    Returns:
        header_table - The header of WELSEGS.
        record_table - The record of WELSEGS.

    Raises:
        ValueError: If collection does not contain the 'WELSEGS' keyword.
    """
    header_columns = [
        Headers.WELL,
        Headers.TRUE_VERTICAL_DEPTH,
        Headers.MEASURED_DEPTH,
        Headers.WELLBORE_VOLUME,
        Headers.INFO_TYPE,
        Headers.PRESSURE_DROP_COMPLETION,
        Headers.MULTIPHASE_FLOW_MODEL,
        Headers.X_COORDINATE_TOP_SEGMENT,
        Headers.Y_COORDINATE_TOP_SEGMENT,
        Headers.THERMAL_CONDUCTIVITY_CROSS_SECTIONAL_AREA,
        Headers.VOLUMETRIC_HEAT_CAPACITY_PIPE_WALL,
        Headers.THERMAL_CONDUCTIVITY_PIPE_WALL,
    ]
    content_columns = [
        Headers.WELL,
        Headers.TUBING_SEGMENT,
        Headers.TUBING_SEGMENT_2,
        Headers.TUBING_BRANCH,
        Headers.TUBING_OUTLET,
        Headers.TUBING_MEASURED_DEPTH,
        Headers.TRUE_VERTICAL_DEPTH,
        Headers.TUBING_INNER_DIAMETER,
        Headers.TUBING_ROUGHNESS,
        Headers.FLOW_CROSS_SECTIONAL_AREA,
        Headers.SEGMENT_VOLUME,
        Headers.X_COORDINATE_LAST_SEGMENT,
        Headers.Y_COORDINATE_LAST_SEGMENT,
        Headers.THERMAL_CONDUCTIVITY_CROSS_SECTIONAL_AREA,
        Headers.VOLUMETRIC_HEAT_CAPACITY_PIPE_WALL,
        Headers.THERMAL_CONDUCTIVITY_PIPE_WALL,
    ]
    for collection in collections:
        if collection.name == Keywords.WELSEGS:
            header_collection = np.asarray(collection[:1])
            record_collection = np.asarray(collection[1:])
            # add additional well column on the second collection
            well_column = np.full(record_collection.shape[0], collection.well)
            record_collection = np.column_stack((well_column, record_collection))
            try:
                header_table: npt.NDArray[np.unicode_] | pd.DataFrame
                record_table: npt.NDArray[np.unicode_] | pd.DataFrame
                header_table = np.row_stack((header_table, header_collection))
                record_table = np.row_stack((record_table, record_collection))
            except NameError:
                # First iteration
                header_table = np.asarray(header_collection)
                record_table = np.asarray(record_collection)
    try:
        header_table = pd.DataFrame(header_table, columns=header_columns)
        record_table = pd.DataFrame(record_table, columns=content_columns)
    except NameError as err:
        raise ValueError("Collection does not contain the 'WELSEGS' keyword") from err

    # replace string component " or ' in the columns
    header_table = remove_string_characters(header_table)
    record_table = remove_string_characters(record_table)
    return header_table, record_table


def get_welspecs_table(collections: list[ContentCollection]) -> pd.DataFrame:
    """Return dataframe table of WELSPECS.

    Args:
        collections: ContentCollection class.

    Returns:
        WELSPECS table.

    Raises:
        ValueError: If collection does not contain the 'WELSPECS' keyword.
    """
    columns = [
        Headers.WELL,
        Headers.GROUP,
        Headers.I,
        Headers.J,
        Headers.BHP_DEPTH,
        Headers.PHASE,
        Headers.DR,
        Headers.FLAG,
        Headers.SHUT,
        Headers.FLOW_CROSS_SECTIONAL_AREA,
        Headers.PRESSURE_TABLE,
        Headers.DENSITY_CALCULATION_TYPE,
        Headers.REGION,
        Headers.RESERVED_HEADER_1,
        Headers.RESERVED_HEADER_2,
        Headers.WELL_MODEL_TYPE,
        Headers.POLYMER_MIXING_TABLE_NUMBER,
    ]
    welspecs_table = None
    for collection in collections:
        if collection.name == Keywords.WELSPECS:
            the_collection = np.asarray(collection)
            if welspecs_table is None:
                welspecs_table = np.copy(the_collection)
            else:
                welspecs_table = np.row_stack((welspecs_table, the_collection))

    if welspecs_table is None:
        raise ValueError("Collection does not contain the 'WELSPECS' keyword")

    welspecs_table = pd.DataFrame(welspecs_table, columns=columns)
    # replace string component " or ' in the columns
    welspecs_table = remove_string_characters(welspecs_table)
    return welspecs_table


def get_compdat_table(collections: list[ContentCollection]) -> pd.DataFrame:
    """Return dataframe table of COMPDAT.

    Args:
        collections: ContentCollection class.

    Returns:
        COMPDAT table.

    Raises:
        ValueError: If a collection does not contain the 'COMPDAT' keyword.
    """
    compdat_table = None
    for collection in collections:
        if collection.name == Keywords.COMPDAT:
            the_collection = np.asarray(collection)
            if compdat_table is None:
                compdat_table = np.copy(the_collection)
            else:
                compdat_table = np.row_stack((compdat_table, the_collection))
    if compdat_table is None:
        raise ValueError("Collection does not contain the 'COMPDAT' keyword")
    compdat_table = pd.DataFrame(
        compdat_table,
        columns=[
            Headers.WELL,
            Headers.I,
            Headers.J,
            Headers.K,
            Headers.K2,
            Headers.STATUS,
            Headers.SATURATION_FUNCTION_REGION_NUMBERS,
            Headers.CONNECTION_FACTOR,
            Headers.WELL_BORE_DIAMETER,
            Headers.FORMATION_PERMEABILITY_THICKNESS,
            Headers.SKIN,
            Headers.D_FACTOR,
            Headers.COMPDAT_DIRECTION,
            Headers.RO,
        ],
    )
    # replace string component " or ' in the columns
    compdat_table = remove_string_characters(compdat_table)
    return compdat_table


def get_compsegs_table(collections: list[ContentCollection]) -> pd.DataFrame:
    """Return data frame table of COMPSEGS.

    Args:
        collections: ContentCollection class.

    Returns:
        COMPSEGS table.

    Raises:
        ValueError: If collection does not contain the 'COMPSEGS' keyword.

    """
    compsegs_table = None
    for collection in collections:
        if collection.name == Keywords.COMPSEGS:
            the_collection = np.asarray(collection[1:])
            # add additional well column
            well_column = np.full(the_collection.shape[0], collection.well)
            the_collection = np.column_stack((well_column, the_collection))
            if compsegs_table is None:
                compsegs_table = np.copy(the_collection)
            else:
                compsegs_table = np.row_stack((compsegs_table, the_collection))

    if compsegs_table is None:
        raise ValueError("Collection does not contain the 'COMPSEGS' keyword")

    compsegs_table = pd.DataFrame(
        compsegs_table,
        columns=[
            Headers.WELL,
            Headers.I,
            Headers.J,
            Headers.K,
            Headers.BRANCH,
            Headers.START_MEASURED_DEPTH,
            Headers.END_MEASURED_DEPTH,
            Headers.COMPSEGS_DIRECTION,
            Headers.ENDGRID,
            Headers.PERFORATION_DEPTH,
            Headers.THERMAL_CONTACT_LENGTH,
            Headers.SEGMENT,
        ],
    )
    # replace string component " or ' in the columns
    compsegs_table = remove_string_characters(compsegs_table)
    return compsegs_table


def get_wsegvalv_table(collections: list[ContentCollection]) -> pd.DataFrame:
    """Return a dataframe of WSEGVALV.

    Args:
        collections: ContentCollection class.

    Returns:
        WSEGVALV table.
    """
    columns = [
        Headers.WELL,
        Headers.SEGMENT,
        Headers.FLOW_COEFFICIENT,
        Headers.FLOW_CROSS_SECTIONAL_AREA,
        Headers.ADDITIONAL_PIPE_LENGTH_FRICTION_PRESSURE_DROP,
        Headers.PIPE_DIAMETER,
        Headers.ABSOLUTE_PIPE_ROUGHNESS,
        Headers.PIPE_CROSS_SECTION_AREA,
        Headers.FLAG,
        Headers.MAX_FLOW_CROSS_SECTIONAL_AREA,
    ]

    wsegvalv_collections = [np.asarray(collection) for collection in collections if collection.name == "WSEGVALV"]
    wsegvalv_table = np.vstack(wsegvalv_collections)

    if wsegvalv_table.size == 0:
        return pd.DataFrame(columns=columns)

    wsegvalv_table = pd.DataFrame(wsegvalv_table, columns=columns)
    wsegvalv_table = wsegvalv_table.astype(
        {
            Headers.WELL: "string",
            Headers.SEGMENT: "int",
            Headers.FLOW_COEFFICIENT: "float",
            Headers.FLOW_CROSS_SECTIONAL_AREA: "float",
            Headers.ADDITIONAL_PIPE_LENGTH_FRICTION_PRESSURE_DROP: "string",
            Headers.PIPE_DIAMETER: "string",
            Headers.ABSOLUTE_PIPE_ROUGHNESS: "string",
            Headers.PIPE_CROSS_SECTION_AREA: "string",
            Headers.FLAG: "string",
            Headers.MAX_FLOW_CROSS_SECTIONAL_AREA: "float",
        }
    )
    return remove_string_characters(wsegvalv_table)


@overload
def remove_string_characters(df: pd.DataFrame, columns: list[str] | None = ...) -> pd.DataFrame: ...


@overload
def remove_string_characters(df: str, columns: list[str] | None = ...) -> str: ...


def remove_string_characters(df: pd.DataFrame | str, columns: list[str] | None = None) -> pd.DataFrame | str:
    """Remove string characters `"` and `'`.

    Args:
        df: DataFrame or string.
        columns: List of column names to be checked.

    Returns:
        DataFrame without string characters.

    Raises:
        Exception: If an unexpected error occurred.
    """
    if columns is None:
        columns = []

    def remove_quotes(item: str):
        return item.replace("'", "").replace('"', "")

    if isinstance(df, str):
        df = remove_quotes(df)
    elif isinstance(df, pd.DataFrame):
        if len(columns) == 0:
            iterator: range | list[str] = range(df.shape[1])
        else:
            iterator = [] if columns is None else columns
        for column in iterator:
            try:
                df.iloc[:, column] = remove_quotes(df.iloc[:, column].str)
            except ValueError:
                df[column] = remove_quotes(df[column].str)
            except AttributeError:
                # Some dataframes contains numeric data, which we ignore
                pass
            except Exception as err:
                raise err
    return df
