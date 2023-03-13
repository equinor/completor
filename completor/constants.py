"""Define custom enumerations and methods."""

from __future__ import annotations

from enum import Enum, auto


class _Keywords:
    """
    Define keywords used in the schedule file.

    Used as constants, and to check if a given word / string is a keyword.

    **NOTE**: This class should not be used directly, rather, use its instantiation i.e.
    >>> from completor.constants import Keywords

    Attributes:
        WELSPECS (str): Constant representing the keyword 'WELSPECS'
        COMPDAT (str): Constant representing the keyword 'COMPDAT'
        WELSEGS (str): Constant representing the keyword 'WELSEGS'
        COMPSEGS (str): Constant representing the keyword 'COMPSEGS'

        _items (List[str]]): Private helper to iterate through all keywords
        _members (Set[str]): Private helper to check membership

        segments (Set[str]): Set of keywords that are used in a segment
    """

    WELSPECS = "WELSPECS"
    COMPDAT = "COMPDAT"
    WELSEGS = "WELSEGS"
    COMPSEGS = "COMPSEGS"

    _items = [WELSPECS, COMPDAT, WELSEGS, COMPSEGS]
    _members = set(_items)

    segments = {WELSEGS, COMPSEGS}

    def __iter__(self):
        return self._items.__iter__()

    def __contains__(self, item):
        return item in self._members


Keywords = _Keywords()


class SegmentCreationMethod(Enum):
    """An enumeration of legal methods for ``create_wells.CreateWells``."""

    CELLS = auto()
    FIX = auto()
    USER = auto()
    WELSEGS = auto()
