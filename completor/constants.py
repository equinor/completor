"""Define custom enumerations and methods."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Header:
    """Custom class for DataFrame columns."""

    ...


class Headers:
    """Headers for DataFrames."""

    # Autoadded / To be triaged.

    TUBINGROUGHNESS = "TUBINGROUGHNESS"
    TUBINGSEGMENT2 = "TUBINGSEGMENT2"
    INFOTYPE = "INFOTYPE"
    TUBINGSEGMENT = "TUBINGSEGMENT"
    TUBINGOUTLET = "TUBINGOUTLET"
    SAT = "SAT"
    FLAG = "FLAG"
    DEF = "DEF"
    DIR = "DIR"
    SEG = "SEG"
    SEG2 = "SEG2"
    OUT = "OUT"
    COMPSEGS_DIRECTION = "COMPSEGS_DIRECTION"
    LATERAL = "LATERAL"
    NDEVICES = "NDEVICES"
    I = "I"  # noqa: E741
    J = "J"
    K = "K"
    K2 = "K2"
    STATUS = "STATUS"
    SATNUM = "SATNUM"
    CF = "CF"
    DIAM = "DIAM"
    KH = "KH"
    SKIN = "SKIN"
    DFACT = "DFACT"
    COMPDAT_DIRECTION = "COMPDAT_DIRECTION"
    RO = "RO"

    TUB_TVD = "TUB_TVD"  # Same as TUBINGTVD
    TVD = "TVD"
    TUBINGMD = "TUBINGMD"
    TUBINGTVD = "TUBINGTVD"
    SEGMENTTVD = "SEGMENTTVD"
    SEGMENTMD = "SEGMENTMD"
    SEGMENT_DESC = "SEGMENT_DESC"
    SEGMENT = "SEGMENT"
    WCUT = "WCUT"
    VISCAL_ICD = "VISCAL_ICD"
    RHOCAL_ICD = "RHOCAL_ICD"
    STRENGTH = "STRENGTH"

    WCT_AICV = "WCT_AICV"
    GHF_AICV = "GHF_AICV"
    RHOCAL_AICV = "RHOCAL_AICV"
    VISCAL_AICV = "VISCAL_AICV"
    ALPHA_MAIN = "ALPHA_MAIN"
    X_MAIN = "X_MAIN"
    Y_MAIN = "Y_MAIN"
    A_MAIN = "A_MAIN"
    B_MAIN = "B_MAIN"
    C_MAIN = "C_MAIN"
    D_MAIN = "D_MAIN"
    E_MAIN = "E_MAIN"
    F_MAIN = "F_MAIN"
    ALPHA_PILOT = "ALPHA_PILOT"
    X_PILOT = "X_PILOT"
    Y_PILOT = "Y_PILOT"
    A_PILOT = "A_PILOT"
    B_PILOT = "B_PILOT"
    C_PILOT = "C_PILOT"
    D_PILOT = "D_PILOT"
    E_PILOT = "E_PILOT"
    F_PILOT = "F_PILOT"

    CV_DAR = "CV_DAR"
    AC_OIL = "AC_OIL"
    AC_GAS = "AC_GAS"
    AC_WATER = "AC_WATER"
    WHF_LCF_DAR = "WHF_LCF_DAR"
    WHF_HCF_DAR = "WHF_HCF_DAR"
    GHF_LCF_DAR = "GHF_LCF_DAR"
    GHF_HCF_DAR = "GHF_HCF_DAR"

    ALPHA = "ALPHA"
    X = "X"
    Y = "Y"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    RHOCAL_AICD = "RHOCAL_AICD"
    VISCAL_AICD = "VISCAL_AICD"

    CV_DAR = "CV_DAR"
    AC_OIL = "AC_OIL"
    AC_GAS = "AC_GAS"
    AC_WATER = "AC_WATER"
    WHF_LCF_DAR = "WHF_LCF_DAR"
    WHF_HCF_DAR = "WHF_HCF_DAR"
    GHF_LCF_DAR = "GHF_LCF_DAR"
    GHF_HCF_DAR = "GHF_HCF_DAR"
    DEFAULTS = "DEFAULTS"
    AC_MAX = "AC_MAX"

    CV = "CV"
    AC = "AC"
    AC_MAX = "AC_MAX"
    L = "L"

    BRANCH = "BRANCH"

    TUBINGBRANCH = "TUBINGBRANCH"
    MD = "MD"
    DIAM = "DIAM"

    # from `test_completion.py`
    TUB_MD = "TUB_MD"

    # Completion
    START_MEASURED_DEPTH = "STARTMD"
    END_MEASURED_DEPTH = "ENDMD"
    ANNULUS = "ANNULUS"
    ANNULUS_ZONE = "ANNULUS_ZONE"
    VALVES_PER_JOINT = "NVALVEPERJOINT"
    INNER_DIAMETER = "INNER_DIAMETER"
    OUTER_DIAMETER = "OUTER_DIAMETER"
    ROUGHNESS = "ROUGHNESS"
    DEVICE_TYPE = "DEVICETYPE"
    DEVICE_NUMBER = "DEVICENUMBER"
    WELL = "WELL"

    # Well segments
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


class Completion:
    """Columns for Completion."""

    START_MD = "STARTMD"
    END_MD = "ENDMD"
    ANNULUS = "ANNULUS"
    ANNULUS_ZONE = "ANNULUS_ZONE"
    NUM_VALVES_PER_JOINT = "NVALVEPERJOINT"
    INNER_DIAMETER = "INNER_DIAMETER"
    OUTER_ID = "OUTER_DIAMETER"
    ROUGHNESS = "ROUGHNESS"
    DEVICE_TYPE = "DEVICETYPE"
    DEVICE_NUMBER = "DEVICENUMBER"
    WELL = "WELL"


@dataclass(frozen=True)
class _Keywords:
    """Define keywords used in the schedule file.

    Used as constants, and to check if a given word / string is a keyword.

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


class Method(Enum):
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
            >>>Method.CELLS == "CELLS"
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
