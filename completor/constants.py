"""Define custom enumerations and methods."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import TypeAlias

import pandas as pd

WellData: TypeAlias = dict[str, pd.DataFrame | tuple[pd.DataFrame, pd.DataFrame]]
ScheduleData: TypeAlias = dict[str, WellData]


@dataclass(frozen=True)
class _Headers:
    """Headers for DataFrames."""

    # Well Segments Record 1 (WELSEGS)
    WELL = "WELL"
    TRUE_VERTICAL_DEPTH = "TRUE_VERTICAL_DEPTH"
    # MEASURED_DEPTH = "SEGMENTMD"
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
    TUBING_MEASURED_DEPTH = "TUBING_MEASURED_DEPTH"
    # TUBING_TRUE_VERTICAL_DEPTH = "TUBINGTVD"
    TUBING_INNER_DIAMETER = "TUBINGID"
    TUBING_ROUGHNESS = "TUBINGROUGHNESS"
    FLOW_CROSS_SECTIONAL_AREA = "CROSS"  # Cross-sectional area for fluid flow.
    SEGMENT_VOLUME = "VSEG"
    X_COORDINATE_LAST_SEGMENT = "DEFAULT_6"  # X coordinate of the last nodal point in the range.
    Y_COORDINATE_LAST_SEGMENT = "DEFAULT_7"  # Y coordinate of the last nodal point in the range.

    # Completion segments (COMPSEGS)
    I = "I"  # noqa: E741
    J = "J"
    K = "K"
    BRANCH = "BRANCH"
    START_MEASURED_DEPTH = "START_MEASURED_DEPTH"
    END_MEASURED_DEPTH = "END_MEASURED_DEPTH"
    COMPSEGS_DIRECTION = "COMPSEGS_DIRECTION"  # Direction of penetration through the grid block or the range.
    # X or I for horizontal penetration in the x-direction, Y or J for horizontal penetration in the y-direction,
    # Z or K for vertical penetration.
    ENDGRID = "ENDGRID"
    PERFORATION_DEPTH = "PERFDEPTH"  # Depth of the well connections within the range,
    # that is the depth of the center of the perforations within each grid block in the range.
    THERMAL_CONTACT_LENGTH = "THERM"  # Thermal contact length, that is, the length of the well in the completion cell.
    SEGMENT = "SEGMENT"

    # Well specifications (WELL_SPECIFICATION)
    # WELL = "WELL"
    GROUP = "GROUP"
    # I = "I"  # noqa: E741
    # J = "J"
    BHP_DEPTH = "BHP_DEPTH"  # Bottom hole pressure depth?
    PHASE = "PHASE"
    DR = "DR"
    FLAG = "FLAG"  # This is actually a header, but OPEN, SHUT, and AUTO are its possible values, see manual on COMPLETION_DATA.
    SHUT = "SHUT"
    CROSS = "CROSS"
    PRESSURE_TABLE = "PRESSURETABLE"
    DENSITY_CALCULATION_TYPE = "DENSCAL"  # Type of density calculation for the wellbore hydrostatic head.
    REGION = "REGION"
    RESERVED_HEADER_1 = "RESERVED_1"
    RESERVED_HEADER_2 = "RESERVED_2"
    WELL_MODEL_TYPE = "WELL_MODEL_TYPE"
    POLYMER_MIXING_TABLE_NUMBER = "POLYMER_MIXING_TABLE_NUMBER"

    # Completion Data (COMPDAT)
    # WELL NAME
    # I
    # J
    # K
    K2 = "K2"
    STATUS = "STATUS"
    SATURATION_FUNCTION_REGION_NUMBERS = "SATNUM"
    CONNECTION_FACTOR = "CF"  # Transmissibility factor for the connection. If defaulted or set to zero,
    # the connection transmissibility factor is calculated using the remaining items of data in this record. See "The
    # connection transmissibility factor" in the ECLIPSE Technical Description for an account of the methods used in
    # Cartesian and radial geometries. The well bore diameter must be set in item 9.
    WELL_BORE_DIAMETER = "DIAM"
    FORMATION_PERMEABILITY_THICKNESS = "KH"  # The product of formation permeability, k, and producing formation
    # thickness, h, in a producing well, referred to as kh.
    SKIN = "SKIN"  # A dimensionless factor calculated to determine the production efficiency of a well by comparing
    # actual conditions with theoretical or ideal conditions. A positive skin value indicates some damage or
    # influences that are impairing well productivity. A negative skin value indicates enhanced productivity,
    # typically resulting from stimulation.
    D_FACTOR = "DFACT"  # Non-darcy flow of free gas.
    COMPDAT_DIRECTION = "COMPDAT_DIRECTION"
    RO = "RO"  # Pressure equivalent radius, R_o.

    # Inflow Control Device Well Segments (WSEGSICD) and Autonomous (WSEGAICD)
    # Well name
    DEVICE_NUMBER = "DEVICENUMBER"
    START_SEGMENT_NUMBER = "START_SEGMENT_NUMBER"  # Duplicate, ish
    END_SEGMENT_NUMBER = "END_SEGMENT_NUMBER"
    STRENGTH = "STRENGTH"
    SCALE_FACTOR = "SCALE_FACTOR"
    CALIBRATION_FLUID_DENSITY = "CALIBRATION_FLUID_DENSITY"
    CALIBRATION_FLUID_VISCOSITY = "CALIBRATION_FLUID_VISCOSITY"
    DEF = "DEF"  # The critical value of the local water in liquid fraction
    # used to select between a water-in-oil or oil-in-water equation for the emulsion viscosity;
    # this is described in Emulsion viscosity.

    # This stops making sense from here on out?
    X = "X"
    Y = "Y"
    Z = "Z"
    # FLAG
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    EMPTY = ""

    # Sub critical valve well segment (WSEGVALV)
    # 1. WELL_NAME
    # 2. START_SEGMENT_NUMBER
    FLOW_COEFFICIENT = "FLOW_COEFFICIENT"  # The dimensionless flow coefficient for the valve, Cv.
    # FLOW_CROSS_SECTIONAL_AREA # Cross-section area for flow in the constriction, Ac.
    ADDITIONAL_PIPE_LENGTH_FRICTION_PRESSURE_DROP = (
        "ADDITIONAL_PIPE_LENGTH"  # Additional length of pipe for the friction pressure drop, L.
    )
    PIPE_DIAMETER = "PIPE_DIAMETER"  # The pipe diameter, D, for the frictional pressure drop calculation.
    ABSOLUTE_PIPE_ROUGHNESS = "ABSOLUTE_PIPE_ROUGHNESS"  # The absolute roughness of the pipe wall.
    PIPE_CROSS_SECTION_AREA = "PIPE_CROSS_SECTION_AREA"  # The pipe cross-section area, Ap.
    # FLAG # Flag to indicate whether the device is open or shut.
    MAX_FLOW_CROSS_SECTIONAL_AREA = (
        "MAX_FLOW_CROSS_SECTIONAL_AREA"  # The maximum cross-sectional area for flow in the constriction, Amax.
    )
    # 11. The length of the valve, lVAL (Scale factor).
    # 12. An integer which determines how the flow scaling factor is calculated.

    # Density Driven Well Segments (WSEGDENSITY)
    # DEVICE_NUMBER
    # FLOW_COEFFICIENT / Cv
    # FLOW_CROSS_SECTIONAL_AREA
    OIL_FLOW_CROSS_SECTIONAL_AREA = "OIL_FLOW_CROSS_SECTIONAL_AREA"
    GAS_FLOW_CROSS_SECTIONAL_AREA = "GAS_FLOW_CROSS_SECTIONAL_AREA"
    WATER_FLOW_CROSS_SECTIONAL_AREA = "WATER_FLOW_CROSS_SECTIONAL_AREA"
    WATER_HOLDUP_FRACTION_LOW_CUTOFF = "WATER_HOLDUP_FRACTION_LOW_CUTOFF"
    WATER_HOLDUP_FRACTION_HIGH_CUTOFF = "WATER_HOLDUP_FRACTION_HIGH_CUTOFF"
    GAS_HOLDUP_FRACTION_LOW_CUTOFF = "GAS_HOLDUP_FRACTION_LOW_CUTOFF"
    GAS_HOLDUP_FRACTION_HIGH_CUTOFF = "GAS_HOLDUP_FRACTION_HIGH_CUTOFF"

    # Miscellaneous
    DEFAULTS = "DEFAULTS"
    MEASURED_DEPTH = "MEASURED_DEPTH"
    ANNULUS = "ANNULUS"
    ANNULUS_ZONE = "ANNULUS_ZONE"
    VALVES_PER_JOINT = "VALVES_PER_JOINT"
    INNER_DIAMETER = "INNER_DIAMETER"
    OUTER_DIAMETER = "OUTER_DIAMETER"
    ROUGHNESS = "ROUGHNESS"
    DEVICE_TYPE = "DEVICETYPE"
    WATER_CUT = "WATER_CUT"
    OPEN = "OPEN"
    DEVICE = "DEVICE"
    MARKER = "MARKER"
    LENGTH = "LENGTH"
    ADDITIONAL_SEGMENT = "AdditionalSegment"
    ORIGINAL_SEGMENT = "OriginalSegment"
    OUT = "OUT"
    LATERAL = "LATERAL"
    NUMBER_OF_DEVICES = "NUMBER_OF_DEVICES"
    SEGMENT_DESC = "SEGMENT_DESC"
    DUALRCP_WATER_CUT = "DUALRCP_WATER_CUT"
    DUALRCP_GAS_HOLDUP_FRACTION = "DUALRCP_GAS_HOLDUP_FRACTION"
    DUALRCP_CALIBRATION_FLUID_DENSITY = "DUALRCP_CALIBRATION_FLUID_DENSITY"
    DUALRCP_FLUID_VISCOSITY = "DUALRCP_FLUID_VISCOSITY"
    AICD_CALIBRATION_FLUID_DENSITY = "AICD_CALIBRATION_FLUID_DENSITY"
    AICD_FLUID_VISCOSITY = "AICD_FLUID_VISCOSITY"
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


Headers = _Headers()


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

    WELL_SPECIFICATION = "WELSPECS"
    COMPLETION_DATA = "COMPDAT"
    WELL_SEGMENTS = "WELSEGS"
    COMPLETION_SEGMENTS = "COMPSEGS"

    COMPLETION = "COMPLETION"

    WELL_SEGMENTS_HEADER = "WELSEGS_H"
    WELL_SEGMENTS_LINK = "WSEGLINK"
    WELL_SEGMENTS_VALVE = "WSEGVALV"
    AUTONOMOUS_INFLOW_CONTROL_DEVICE = "WSEGAICD"
    DUAL_RATE_CONTROLLED_PRODUCTION = "WSEGDUALRCP"
    AUTONOMOUS_INFLOW_CONTROL_VALVE = "WSEGAICV"
    INFLOW_CONTROL_VALVE = "WSEGICV"
    INFLOW_CONTROL_DEVICE = "WSEGSICD"
    DENSITY = "WSEGDENSITY"
    DENSITY_PY = "WSEGDENSITY_PY"
    DENSITY_ACTIVATED_RECOVERY = "WSEGDAR"
    LATERAL_TO_DEVICE = "LATERAL_TO_DEVICE"
    JOINT_LENGTH = "JOINTLENGTH"
    SEGMENT_LENGTH = "SEGMENTLENGTH"
    USE_STRICT = "USE_STRICT"
    GRAVEL_PACKED_PERFORATED_DEVICELAYER = "GP_PERF_DEVICELAYER"  # suggestion: GRAVEL_PACKED_PERFORATION_DEVICE_LAYER
    MINIMUM_SEGMENT_LENGTH = "MINIMUM_SEGMENT_LENGTH"
    MAP_FILE = "MAPFILE"
    SCHEDULE_FILE = "SCHFILE"
    OUT_FILE = "OUTFILE"

    # Note: Alphabetically sorted, which matters for check vs. missing keys in input data.
    main_keywords = [COMPLETION_DATA, COMPLETION_SEGMENTS, WELL_SEGMENTS, WELL_SPECIFICATION]

    _items = [WELL_SPECIFICATION, COMPLETION_DATA, WELL_SEGMENTS, COMPLETION_SEGMENTS]
    _members = set(_items)

    segments = {WELL_SEGMENTS, COMPLETION_SEGMENTS}

    def __iter__(self):
        return self._items.__iter__()

    def __contains__(self, item):
        return item in self._members


Keywords = _Keywords()


@dataclass(frozen=True)
class _Content:
    """ """

    PACKER = "PA"
    GRAVEL_PACKED = "GP"
    OPEN_ANNULUS = "OA"
    ANNULUS_TYPES = [GRAVEL_PACKED, OPEN_ANNULUS, PACKER]

    PERFORATED = "PERF"
    INFLOW_CONTROL_VALVE = "ICV"
    DUAL_RATE_CONTROLLED_PRODUCTION = "DUALRCP"
    AUTONOMOUS_INFLOW_CONTROL_VALVE = "AICV"
    INFLOW_CONTROL_DEVICE = "ICD"
    AUTONOMOUS_INFLOW_CONTROL_DEVICE = "AICD"
    DENSITY = "DENSITY"
    DENSITY_ACTIVATED_RECOVERY = "DAR"
    VALVE = "VALVE"
    DEVICE_TYPES = [
        AUTONOMOUS_INFLOW_CONTROL_DEVICE,
        DUAL_RATE_CONTROLLED_PRODUCTION,
        AUTONOMOUS_INFLOW_CONTROL_VALVE,
        DENSITY,
        DENSITY_ACTIVATED_RECOVERY,
        INFLOW_CONTROL_DEVICE,
        VALVE,
        INFLOW_CONTROL_VALVE,
        PERFORATED,
    ]


Content = _Content()


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
