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

    def __eq__(self, other: object) -> bool:
        """
        Implement the equality function to compare enums with their string literal.

        Arguments:
            other (SegmentCreationMethod, str): other item to be compared with

        Returns:
            bool: Whether enums are equal

        Example:
            >>>SegmentCreationMethod.CELLS == "CELLS"
            >>>True

        """
        if isinstance(other, Enum):
            return self.__class__ == other.__class__ and self.value == other.value and self.name == other.name
        elif isinstance(other, str):
            return self.name == other
        return False


class WellSegment:
    """Columns for WellSegments."""

    TUBING_MD = "TUBINGMD"
    TUBING_TVD = "TUBINGTVD"
    SEGMENT_MD = "SEGMENTMD"
    SEGMENT_TVD = "SEGMENTTVD"
    TUBING_OUTLET = "TUBINGOUTLET"
    TUBING_SEGMENT = "TUBINGSEGMENT"
    TUBING_SEGMENT2 = "TUBINGSEGMENT2"
    TUBING_BRANCH = "TUBINGBRANCH"
    TUBING_ID = "TUBINGID"
    TUBING_ROUGHNESS = "TUBINGROUGHNESS"

    @classmethod
    def data_records(cls) -> list[str]:
        """Return column names for a WellSegment."""
        return [
            cls.TUBING_SEGMENT,
            cls.TUBING_SEGMENT2,
            cls.TUBING_BRANCH,
            cls.TUBING_OUTLET,
            cls.TUBING_MD,
            cls.TUBING_TVD,
            cls.TUBING_ID,
            cls.TUBING_ROUGHNESS,
            "CROSS",
            "VSEG",
            "ITEM11",
            "ITEM12",
            "ITEM13",
            "ITEM14",
            "ITEM15",
        ]


class Completion:
    """Columns for Completion."""

    START_MD = "STARTMD"
    END_MD = "ENDMD"
    ANNULUS = "ANNULUS"
    ANNULUS_ZONE = "ANNULUS_ZONE"
    NUM_VALVES_PER_JOINT = "NVALVEPERJOINT"
    INNER_ID = "INNER_ID"
    OUTER_ID = "OUTER_ID"
    ROUGHNESS = "ROUGHNESS"
    DEVICE_TYPE = "DEVICETYPE"
    DEVICE_NUMBER = "DEVICENUMBER"
    WELL = "WELL"
