"""Functions for reading files."""

from __future__ import annotations

import re
from copy import deepcopy
from typing import Literal, overload

import numpy as np

# Requires NumPy 1.20 or newer
import numpy.typing as npt
import pandas as pd

from completor.utils import abort


class ContentCollection(list):
    """
    A subclass of list that can accept additional attributes.

    To be used like a regular list.
    """

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
    """
    Find the start and end of a keyword.

    The start of the keyword is the keyword itself.
    The end of the keyword is end_char if specified

    Args:
        content: List of strings
        keyword: Keyword name
        end_char: String which ends the keyword. By default '/'
                  Because it's the most used in this code base
        take_first: Flag to toggle whether to return the first elements
                    of the arrays

    Returns:
            | start_index - np.array that located the keyword (or its first element)
            | end_index - np.array that locates the end of the keyword
                          (or its first element)
    Raises:
        SystemExit: If keyword had no end record
        ValueError: If keyword cannot be found in case file
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
                raise abort(f"Keyword {keyword} has no end record")
        else:
            # if there is no end character is specified
            # then the end of a record is the next keyword or end of line
            for idx in range(istart + 1, content_length):
                first_char = content[idx][0]
                if first_char.isalpha():
                    # end is before the new keyword
                    idx -= 1
                    break

        try:
            end_index = np.append(end_index, idx)
        except NameError as err:
            # TODO: check which function it was called from, in order
            #       to determine if case file or schedule file
            raise ValueError(f"Cannot find keyword {keyword} in file") from err
    # return all in a numpy array format
    end_index = np.asarray(end_index)
    if take_first:
        return start_index[0], end_index[0]
    return start_index, end_index


def take_first_record(
    start_index: list[float] | npt.NDArray[np.float64], end_index: list[float] | npt.NDArray[np.float64]
) -> tuple[float | int, float | int]:
    """
    Take the first record of a list.

    Args:
        start_index
        end_index

    Returns:
        Tuple of floats
    """
    return start_index[0], end_index[0]


def unpack_records(record: list[str]) -> list[str]:
    """
    Unpack the keyword content.

    E.g. 3* --> 1* 1* 1*

    Args:
        record: List of strings

    Returns:
        Updated record of strings
    """
    record = deepcopy(record)
    record_length = len(record)
    idx = -1
    while idx < record_length - 1:
        # Loop and find if default records are found
        idx = idx + 1
        if "*" in str(record[idx]):
            # default is found and get the number before the star *
            ndefaults = re.search(r"\d+", record[idx])
            record[idx] = "1*"
            if ndefaults:
                _ndefaults = int(ndefaults.group())
                idef = 0
                while idef < _ndefaults - 1:
                    record.insert(idx, "1*")
                    idef = idef + 1
            record_length = len(record)
    return record


def complete_records(record: list[str], keyword: str) -> list[str]:
    """
    Complete the record.

    Args:
        record: List of strings
        keyword: Keyword name

    Returns:
        List of updated string
    """
    dict_ncolumns = {"WELSPECS": 17, "COMPDAT": 14, "WELSEGS_H": 12, "WELSEGS": 15, "COMPSEGS": 11}
    max_column = dict_ncolumns[keyword]
    ncolumn = len(record)
    if ncolumn < max_column:
        extension = ["1*"] * (max_column - ncolumn)
        record.extend(extension)
    return record


def read_schedule_keywords(
    content: list[str], keywords: list[str]
) -> tuple[list[ContentCollection], npt.NDArray[np.str_]]:
    """
    Read schedule keywords or all keywords in table format.

    E.g. WELSPECS, COMPDAT, WELSEGS, COMPSEGS.

    Args:
        content: List of strings
        keywords: List of keywords to be found

    Returns:
        df_collection - Object collection (pd.DataFrame)
        remaining_content - List of strings of un-listed keywords

    Raises:
        SystemExit: If keyword is not found
    """
    content = deepcopy(content)
    used_index = np.asarray([-1])
    collections = []
    # get the contents correspond to the list_keywords
    for keyword in keywords:
        start_index, end_index = locate_keyword(content, keyword, take_first=False)
        if start_index[0] == end_index[0]:
            raise abort(f"Keyword {keyword} is not found")
        for idx, start in enumerate(start_index):
            end = end_index[idx]
            used_index = np.append(used_index, np.arange(start, end + 1))
            keyword_content = [_create_record(content, keyword, irec, start) for irec in range(start + 1, end)]
            collection = ContentCollection(keyword_content, name=keyword)
            if keyword in ["WELSEGS", "COMPSEGS"]:
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
    record = complete_records(record, "WELSEGS_H" if keyword == "WELSEGS" and irec == start + 1 else keyword)
    return record


def get_welsegs_table(collections: list[ContentCollection]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Return dataframe table of WELSEGS.

    Args:
        collections:  ContentCollection class

    Returns:
        | header_table - The header of WELSEGS
        | record_table - the record of WELSEGS
    Raises:
        ValueError: If collection does not contain the 'WELSEGS' keyword

    The first DataFrame has the following format:

    .. list-table:: First DataFrame (WELSEGS header)
       :widths: 10 10
       :header-rows: 1

       * - COLUMNS
         - TYPE
       * - WELL
         - str
       * - SEGMENTTVD
         - float
       * - SEGMENTMD
         - float
       * - WBVOLUME
         - float
       * - INFOTYPE
         - str
       * - PDROPCOMP
         - str
       * - MPMODEL
         - str
       * - ITEM8
         - object
       * - ITEM9
         - object
       * - ITEM10
         - object
       * - ITEM11
         - object
       * - ITEM12
         - object

    The second DataFrame has the following format:

    .. list-table:: Second DataFrame (WELSEGS record)
       :widths: 10 10
       :header-rows: 1

       * - COLUMNS
         - TYPE
       * - WELL
         - str
       * - TUBINGSEGMENT
         - int
       * - TUBINGSEGMENT2
         - int
       * - TUBINGBRANCH
         - int
       * - TUBINGOUTLET
         - int
       * - TUBINGMD
         - float
       * - TUBINGTVD
         - float
       * - TUBINGID
         - float
       * - TUBINGROUGHNESS
         - float
       * - CROSS
         - float
       * - VSEG
         - float
       * - ITEM11
         - object
       * - ITEM12
         - object
       * - ITEM13
         - object
       * - ITEM14
         - object
       * - ITEM15
         - object
    """
    header_columns = [
        "WELL",
        "SEGMENTTVD",
        "SEGMENTMD",
        "WBVOLUME",
        "INFOTYPE",
        "PDROPCOMP",
        "MPMODEL",
        "ITEM8",
        "ITEM9",
        "ITEM10",
        "ITEM11",
        "ITEM12",
    ]
    content_columns = [
        "WELL",
        "TUBINGSEGMENT",
        "TUBINGSEGMENT2",
        "TUBINGBRANCH",
        "TUBINGOUTLET",
        "TUBINGMD",
        "TUBINGTVD",
        "TUBINGID",
        "TUBINGROUGHNESS",
        "CROSS",
        "VSEG",
        "ITEM11",
        "ITEM12",
        "ITEM13",
        "ITEM14",
        "ITEM15",
    ]
    for collection in collections:
        if collection.name == "WELSEGS":
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
    """
    Return dataframe table of WELSPECS.

    Args:
        collections: ContentCollection class

    Returns:
        WELSPECS table

    Raises:
        ValueError: If collection does not contain the 'WELSPECS' keyword

    The return DataFrame welspecs_table has the following format:

    TODO: Which one is correct; this or the one in ``completion.set_welspecs``?

    .. list-table:: welspecs_table
       :widths: 10 10
       :header-rows: 1

       * - COLUMNS
         - TYPE
       * - WELL
         - str
       * - GROUP
         - str
       * - I
         - int
       * - J
         - int
       * - BHP_DEPTH
         - float
       * - PHASE
         - str
       * - DR
         - float
       * - FLAG
         - str
       * - SHUT
         - object
       * - CROSS
         - object
       * - PRESSURETABLE
         - int
       * - DENSCAL
         - float
       * - REGION
         - object
       * - ITEM14
         - object
       * - ITEM15
         - object
       * - ITEM16
         - object
       * - ITEM17
         - object
    """
    columns = [
        "WELL",
        "GROUP",
        "I",
        "J",
        "BHP_DEPTH",
        "PHASE",
        "DR",
        "FLAG",
        "SHUT",
        "CROSS",
        "PRESSURETABLE",
        "DENSCAL",
        "REGION",
        "ITEM14",
        "ITEM15",
        "ITEM16",
        "ITEM17",
    ]
    welspecs_table = None
    for collection in collections:
        if collection.name == "WELSPECS":
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
    """
    Return dataframe table of COMPDAT.

    Args:
        collections: ContentCollection class

    Returns:
        COMPDAT table

    Raises:
        ValueError: If collection does not contain the 'COMPDAT' keyword

    The return DataFrame has the following format:

    .. _compdat_table:
    .. list-table:: compdat_table
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
       * - STATUS
         - str
       * - SATNUM
         - int
       * - CF
         - float
       * - DIAM
         - float
       * - KH
         - float
       * - SKIN
         - float
       * - DFACT
         - object
       * - COMPDAT_DIRECTION
         - object
       * - RO
         - float
    """
    compdat_table = None
    for collection in collections:
        if collection.name == "COMPDAT":
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
            "WELL",
            "I",
            "J",
            "K",
            "K2",
            "STATUS",
            "SATNUM",
            "CF",
            "DIAM",
            "KH",
            "SKIN",
            "DFACT",
            "COMPDAT_DIRECTION",
            "RO",
        ],
    )
    # replace string component " or ' in the columns
    compdat_table = remove_string_characters(compdat_table)
    return compdat_table


def get_compsegs_table(collections: list[ContentCollection]) -> pd.DataFrame:
    """
    Return data frame table of COMPSEGS.

    Args:
        collections: ContentCollection class

    Returns:
        COMPSEGS table

    Raises:
        ValueError: If collection does not contain the 'COMPSEGS' keyword

    The return DataFrame compsegs_table has the following format:

    .. list-table:: compsegs_table
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
       * - BRANCH
         - int
       * - STARTMD
         - float
       * - ENDMD
         - float
       * - COMPSEGS_DIRECTION
         - object
       * - ENDGRID
         - object
       * - PERFDEPTH
         - float
       * - THERM
         - object
       * - SEGMENT
         - int
    """
    compsegs_table = None
    for collection in collections:
        if collection.name == "COMPSEGS":
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
            "WELL",
            "I",
            "J",
            "K",
            "BRANCH",
            "STARTMD",
            "ENDMD",
            "COMPSEGS_DIRECTION",
            "ENDGRID",
            "PERFDEPTH",
            "THERM",
            "SEGMENT",
        ],
    )
    # replace string component " or ' in the columns
    compsegs_table = remove_string_characters(compsegs_table)
    return compsegs_table


@overload
def remove_string_characters(df: pd.DataFrame, columns: list[str] | None = ...) -> pd.DataFrame: ...


@overload
def remove_string_characters(df: str, columns: list[str] | None = ...) -> str: ...


def remove_string_characters(df: pd.DataFrame | str, columns: list[str] | None = None) -> pd.DataFrame | str:
    """
    Remove string characters `"` and `'`.

    Args:
        df: DataFrame or string
        columns: List of column names to be checked

    Returns:
        DataFrame without string characters

    Raises:
        Exception: If an unexpected error occurred
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
            if columns is None:
                iterator = []  # Makes MyPy happy
            else:
                iterator = columns
        for column in iterator:
            try:
                df.iloc[:, column] = remove_quotes(df.iloc[:, column].str)
            except ValueError:
                df[column] = remove_quotes(df[column].str)
            except AttributeError:
                # Some dataframes contains numeric data, which we ignore
                pass
