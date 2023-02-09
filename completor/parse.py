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
