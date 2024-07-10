"""Define custom enumerations and methods."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Headers:
    """Headers for DataFrames."""

    # Well Segments Record 1 (WELSEGS)
    WELL = "WELL"
    SEGMENT_TRUE_VERTICAL_DEPTH = "SEGMENTTVD"
    SEGMENT_MEASURED_DEPTH = "SEGMENTMD"
    WELLBORE_VOLUME = "WBVOLUME"  # Effective wellbore volume of the top segment.
    # This quantity is used to calculate wellbore storage effects in the top segment.
    INFO_TYPE = "INFOTYPE"  # Either 'INC' for incremental values (not supported in completor) or 'ABS' absolute values.
    PRESSURE_DROP_COMPLETION = "PDROPCOMP"  # Components of the pressure drop to be included in the calculation for
    # each of the well’s segments, defaults to 'HFA' Hydrostatic + friction + acceleration.
    MULTIPHASE_FLOW_MODEL = "MPMODEL"
    # How to handle these, they are just placeholders for real things, but are entirely unused?
    X_COORDINATE_TOP_SEGMENT = (
        "DEFAULT_1"  # X coordinate of the top nodal point, relative to the grid origin. Default 0.0.
    )
    Y_COORDINATE_TOP_SEGMENT = (
        "DEFAULT_2"  # Y coordinate of the top nodal point, relative to the grid origin. Default 0.0.
    )
    THERMAL_CONDUCTIVITY_CROSS_SECTIONAL_AREA = "DEFAULT_3"  # Cross-sectional area of the pipe wall used in thermal
    # conductivity calculation. Default 0.0.
    VOLUMETRIC_HEAT_CAPACITY_PIPE_WALL = "DEFAULT_4"  # Volumetric heat capacity of the pipe wall. Default 0.0.
    THERMAL_CONDUCTIVITY_PIPE_WALL = "DEFAULT_5"  # Thermal conductivity of the pipe wall. Default 0.0.

    # Well Segments Record 2 (WELSEGS)
    TUBING_SEGMENT = "TUBINGSEGMENT"  # Segment number at the start of the range (nearest the top segment).
    TUBING_SEGMENT_2 = "TUBINGSEGMENT2"  # Segment number at the far end of the range.
    TUBING_BRANCH = "TUBINGBRANCH"  # Branch number.
    TUBING_OUTLET = "TUBINGOUTLET"
    TUBING_MEASURED_DEPTH = "TUBINGMD"
    TUBING_TRUE_VERTICAL_DEPTH = "TUBINGTVD"
    TUBING_INNER_DIAMETER = "TUBINGID"
    TUBING_ROUGHNESS = "TUBINGROUGHNESS"
    CROSS_SECTIONAL_AREA = "CROSS"  # Cross-sectional area for fluid flow.
    SEGMENT_VOLUME = "VSEG"
    X_COORDINATE_LAST_SEGMENT = "DEFAULT_6"  # X coordinate of the last nodal point in the range.
    Y_COORDINATE_LAST_SEGMENT = "DEFAULT_7"  # Y coordinate of the last nodal point in the range.

    # Completion segments (COMPSEGS)
    I = "I"  # noqa: E741
    J = "J"
    K = "K"
    BRANCH = "BRANCH"
    START_MEASURED_DEPTH = "STARTMD"
    END_MEASURED_DEPTH = "ENDMD"
    COMPSEGS_DIRECTION = "COMPSEGS_DIRECTION"  # Direction of penetration through the grid block or the range.
    # X or I for horizontal penetration in the x-direction, Y or J for horizontal penetration in the y-direction,
    # Z or K for vertical penetration.
    ENDGRID = "ENDGRID"
    PERFORATION_DEPTH = "PERFDEPTH"  # Depth of the well connections within the range,
    # that is the depth of the center of the perforations within each grid block in the range.
    THERMAL_CONTACT_LENGTH = "THERM"  # Thermal contact length, that is, the length of the well in the completion cell.
    SEGMENT = "SEGMENT"

    # Well specifications (WELSPECS)
    # WELL = "WELL"
    GROUP = "GROUP"
    # I = "I"  # noqa: E741
    # J = "J"
    BHP_DEPTH = "BHP_DEPTH"  # Bottom hole pressure depth?
    PHASE = "PHASE"
    DR = "DR"
    FLAG = "FLAG"  # This is actually a header, but OPEN, SHUT, and AUTO are its possible values, see manual on COMPDAT.
    SHUT = "SHUT"
    # CROSS = "CROSS"
    PRESSURE_TABLE = "PRESSURETABLE"
    DENSITY_CALCULATION = "DENSCAL"  # Type of density calculation for the wellbore hydrostatic head.
    REGION = "REGION"
    RESERVED_HEADER_1 = "RESERVED_1"
    RESERVED_HEADER_2 = "RESERVED_2"
    WELL_MODEL_TYPE = "WELL_MODEL_TYPE"
    POLYMER_MIXING_TABLE_NUMBER = "POLYMER_MIXING_TABLE_NUMBER"

    # TBD

    ANNULUS = "ANNULUS"
    ANNULUS_ZONE = "ANNULUS_ZONE"
    VALVES_PER_JOINT = "NVALVEPERJOINT"
    INNER_DIAMETER = "INNER_DIAMETER"
    OUTER_DIAMETER = "OUTER_DIAMETER"
    ROUGHNESS = "ROUGHNESS"
    DEVICE_TYPE = "DEVICETYPE"
    DEVICE_NUMBER = "DEVICENUMBER"
    WATER_CUT = "WCT"
    OPEN = "OPEN"
    RHO = "RHO"
    VISCOSITY = "VIS"
    DEVICE = "DEVICE"
    SF = "SF"  # Saturation functions?

    MARKER = "MARKER"
    SCALING_FACTOR = "SCALINGFACTOR"
    LENGTH = "LENGTH"
    ADDITIONAL_SEGMENT = "AdditionalSegment"
    ORIGINAL_SEGMENT = "OriginalSegment"
    SAT = "SAT"  # Saturation?
    DEF = "DEF"
    DIRECTION = "DIR"
    SEG = "SEG"  # Duplicate, ish
    SEG2 = "SEG2"
    OUT = "OUT"
    LATERAL = "LATERAL"
    NUMBER_OF_DEVICES = "NDEVICES"
    # I = "I"  # noqa: E741
    # J = "J"
    # K = "K"
    K2 = "K2"
    STATUS = "STATUS"
    SATURATION_FUNCTION_REGION_NUMBERS = "SATNUM"
    CONNECTION_FACTOR = "CF"  # Transmissibility factor for the connection. If defaulted or set to zero,
    # the connection transmissibility factor is calculated using the remaining items of data in this record. See "The
    # connection transmissibility factor" in the ECLIPSE Technical Description for an account of the methods used in
    # Cartesian and radial geometries. The well bore diameter must be set in item 9.

    DIAMETER = "DIAM"
    FORAMTION_PERMEABILITY_THICKNESS = "KH"  # The product of formation permeability, k, and producing formation
    # thickness, h, in a producing well, referred to as kh.
    SKIN = "SKIN"  # A dimensionless factor calculated to determine the production efficiency of a well by comparing
    # actual conditions with theoretical or ideal conditions. A positive skin value indicates some damage or
    # influences that are impairing well productivity. A negative skin value indicates enhanced productivity,
    # typically resulting from stimulation.
    DFACT = "DFACT"
    COMPDAT_DIRECTION = "COMPDAT_DIRECTION"
    RO = "RO"

    TUB_TVD = "TUB_TVD"  # Same as TUBINGTVD
    TVD = "TVD"
    SEGMENT_DESC = "SEGMENT_DESC"
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

    MD = "MD"

    # Completion

    # Well segments
    # SEGMENT_MEASURED_DEPTH = "SEGMENTMD"
    # SEGMENT_TRUE_VERTICAL_DEPTH = "SEGMENTTVD"
    # TUBING_SEGMENT2 = "TUBINGSEGMENT2"

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
