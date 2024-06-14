"""Define custom enumerations and methods."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Headers:
    """Headers for DataFrames."""

    WATER_CUT = "WCT"  # Though used once, meaning Water cut.
    OPEN = "OPEN"
    RHO = "RHO"
    VISCOSITY = "VIS"
    DEVICE = "DEVICE"
    SF = "SF"
    THERM = "THERM"
    PERFDEPTH = "PERFDEPTH"
    ENDGRID = "ENDGRID"
    ITEM13 = "ITEM13"
    VSEG = "VSEG"
    TUBINGID = "TUBINGID"
    MPMODEL = "MPMODEL"
    PDROPCOMP = "PDROPCOMP"
    WBVOLUME = "WBVOLUME"
    ITEM8 = "ITEM8"
    ITEM9 = "ITEM9"
    ITEM10 = "ITEM10"
    ITEM11 = "ITEM11"
    ITEM12 = "ITEM12"
    ITEM14 = "ITEM14"
    ITEM15 = "ITEM15"
    ITEM16 = "ITEM16"
    ITEM17 = "ITEM17"
    REGION = "REGION"
    DENSCAL = "DENSCAL"
    PRESSURETABLE = "PRESSURETABLE"
    CROSS = "CROSS"
    SHUT = "SHUT"
    DR = "DR"
    PHASE = "PHASE"
    BHP_DEPTH = "BHP_DEPTH"
    GROUP = "GROUP"
    MARKER = "MARKER"
    SCALINGFACTOR = "SCALINGFACTOR"
    LENGTH = "LENGTH"
    ADDITIONALSEGMENT = "AdditionalSegment"
    ORIGINALSEGMENT = "OriginalSegment"
    START_MD = "STARTMD"
    TUBINGROUGHNESS = "TUBINGROUGHNESS"
    TUBINGSEGMENT2 = "TUBINGSEGMENT2"
    INFOTYPE = "INFOTYPE"
    TUBINGSEGMENT = "TUBINGSEGMENT"
    TUBINGOUTLET = "TUBINGOUTLET"
    SAT = "SAT"
    FLAG = "FLAG"
    DEF = "DEF"
    DIR = "DIR"  # Only used in COMPSEGS, in prepare_outputs.py
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

    DEFAULTS = "DEFAULTS"
    AC_MAX = "AC_MAX"

    CV = "CV"
    AC = "AC"
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

    EMPTY = ""


@dataclass(frozen=True)
class _Keywords:
    """Define keywords used in the schedule file.

    Used as constants, and to check if a given word / string is a keyword.

    Attributes:
        _items: Private helper to iterate through all keywords.
        _members: Private helper to check membership.
        main_keywords: collection of the main keywords: welspecs, compdat, welsegs, and compsegs.
        segments: Set of keywords that are used in a segment.
    """

    WELSPECS = "WELSPECS"
    COMPDAT = "COMPDAT"
    WELSEGS = "WELSEGS"
    COMPSEGS = "COMPSEGS"

    COMPLETION = "COMPLETION"

    WELSEGS_H = "WELSEGS_H"
    WSEGLINK = "WSEGLINK"
    WSEGVALV = "WSEGVALV"
    WSEGAICD = "WSEGAICD"
    WSEGAICV = "WSEGAICV"
    WSEGICV = "WSEGICV"
    WSEGSICD = "WSEGSICD"
    WSEGDAR = "WSEGDAR"

    SCHFILE = "SCHFILE"
    OUTFILE = "OUTFILE"

    main_keywords = [WELSPECS, COMPDAT, WELSEGS, COMPSEGS]

    _items = [WELSPECS, COMPDAT, WELSEGS, COMPSEGS]
    _members = set(_items)

    segments = {WELSEGS, COMPSEGS}

    def __iter__(self):
        return self._items.__iter__()

    def __contains__(self, item):
        return item in self._members


Keywords = _Keywords()


class Method(Enum):
    """An enumeration of legal methods to create wells."""

    CELLS = auto()
    FIX = auto()
    USER = auto()
    WELSEGS = auto()

    def __eq__(self, other: object) -> bool:
        """Implement the equality function to compare enums with their string literal.

        Arguments:
            other: Item to compare with.

        Returns:
            Whether enums are equal.

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
