from dataclasses import dataclass
from enum import Enum, auto

# Constants
GEE = 9.80665 # m/s^2
MACH_IN_M_PER_HR = 1.2348e6
MACH_M_PER_SEC = 343
FEET_PER_METER = 3.2808

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
    sensor: Sensor
    sensor_assumption: SensorAssumption

    def slant_detection_range(self, target: DesignTarget) -> float:
        pass



@dataclass(frozen = True)
class Config:
    target: DesignTarget
    altitude_kft: float
    mach: float
    sensor: Sensor
    sensor_assumption: SensorAssumption
    aoi: AOI

@dataclass
class ModelResult:
    sensor_perfomance: SensorPerformance = None
    detection_downtrack_range: tuple[float, float] = (None, None)
    detection_crosstrack_width: tuple[float, float] = (None, None)
    required_overlap: float = None
    effective_sweep_width: float = None
