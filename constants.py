from dataclasses import dataclass
from enum import Enum, auto
import math

# Constants
GEE               = 9.80665       # m/s^2
MACH_IN_M_PER_HR  = 1.2348e6      # (meters/hour)/mach
MACH_M_PER_SEC    = 343           # (meters/s)/mach
KTS_IN_M_PER_SEC  = 0.51444       # (meters/s)/knot
FEET_PER_METER    = 3.2808        # ft/m
RAD_PER_DEG       = 2*math.pi/360 # radians/degree

# Data Classes
@dataclass(frozen=True)
class DesignTarget:
    type: str
    dims: tuple[float, float] # horizontal, vertical
    max_speed: float # knots

@dataclass(frozen=True)
class AOI:
    length:  float # meters
    width:   float # meters
    ingress: float # meters
    egress:  float # meters

@dataclass(frozen=True)
class SensorAssumption:
    fov_deg: tuple[float, float]
    resolution: tuple[int, int]
    johnson_req: int
    cost: float

@dataclass(frozen=True)
class SensorPerformance:
    slant_detection_range: tuple[float, float]

@dataclass(frozen=True)
class AircraftSearchPerformance:
    valid:                      bool = None
    reason:                     str = None
    ground_detection_range:     tuple[float, float] = None
    downtrack_detection_range:  tuple[float, float] = None
    xtrack_detection_width:     tuple[float, float] = None

@dataclass
class Result:
    valid: bool
    value: float | None
    reason: str | None = None


class Sensor(Enum):
    LOW  = auto()
    MED  = auto()
    HIGH = auto()


@dataclass
class Aircraft:
    alt_kft: float
    mach: float
    manx_bank_angle_rad: float
    manx_decel_gees: float
    manx_min_mach: float
    manx_speed_coeff: float # TODO remove if switching to more complex turn calculation
    sensor: Sensor
    sensor_assumption: SensorAssumption

    def slant_detection_range(self, target: DesignTarget) -> float:
        pass


@dataclass(frozen = True)
class Config:
    # Aircraft
    altitude_kft: float
    mach: float
    manx_bank_angle_rad: float
    manx_speed_coeff: float # TODO remove if switching to more complex turn calculation
    manx_decel_gees: float
    manx_min_mach: float

    # Sensor
    sensor: Sensor
    sensor_assumption: SensorAssumption

    # Target
    target: DesignTarget

    # AOI
    aoi: AOI

@dataclass
class ModelResult:
    config: Config
    valid: bool                               = None
    reason: str                               = None
    sensor_performance: SensorPerformance     = None
    ac_search_perf: AircraftSearchPerformance = None
    ac_turn_time: float                       = None
    required_overlap: float                   = None
    effective_sweep_width: float              = None
