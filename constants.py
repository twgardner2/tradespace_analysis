from dataclasses import dataclass, field
from enum import Enum, auto
import math

# Constants
## Physics
GEE               = 9.80665       # m/s^2
## Time
SEC_PER_HR        = 3600          # sec/hr
## Speed
MACH_IN_M_PER_HR  = 1.2348e6      # (meters/hour)/mach
MACH_M_PER_SEC    = 343           # (meters/s)/mach
KTS_IN_M_PER_SEC  = 0.51444       # (meters/s)/knot
## Length
FEET_PER_METER    = 3.2808        # ft/m
## Angles
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
    alt_kft:             float
    mach:                float
    manx_bank_angle_rad: float
    manx_decel_gees:     float
    manx_min_mach:       float
    sensor:              Sensor
    sensor_assumption:   SensorAssumption
    alt_m:               float = field(init=False)
    cost:                float = field(init=False) 
    endurance_hr:        float = field(init=False)
    endurance_sec:       float = field(init=False)

    def calc_endurance(self) -> float:
        '''
        Calculates aircraft endurance in hours.

        Note: The stipulated endurance model takes altitude in kft, but I plan to 
        work in SI units, so I'm accepting meters and converting to kft.

        Args:
            mach (float): aircraft speed in mach.
            alt_m (float): aircraft altitude in kft.

        Returns:
            float: aircraft endurance in hours.
        '''

        # alt_kft = self.alt_m*FEET_PER_METER/1000
        return -18.75*self.mach**2 + 8.0893*self.mach + 0.01*self.alt_kft**2 + 0.05*self.alt_kft + 9.2105

    def calc_cost(self) -> float:
        '''
        Calculates aircraft cost in millions of dollars.

        Note: The stipulated cost model takes altitude in kft, but I plan to 
        work in SI units, so I'm accepting meters and converting to kft.

        Args:
            mach (float): aircraft speed in mach.
            alt_m (float): aircraft altitude in kft.
            sensor (enum Sensor): EO/IR sensor on aircraft.

        Returns:
            float: aircraft cost in millions of dollars.
        '''
        
        match self.sensor:
            case Sensor.LOW:
                sensor_cost = 0.05
            case Sensor.MED:
                sensor_cost = 1
            case Sensor.HIGH:
                sensor_cost = 10


        return 50*self.mach**2 - 35*self.mach + 0.03*self.alt_kft**2 - 0.2*self.alt_kft + 11 + sensor_cost


    def __post_init__(self):
        self.alt_m         = self.alt_kft*1000/FEET_PER_METER
        self.cost          = self.calc_cost()
        self.endurance_hr  = self.calc_endurance()
        self.endurance_sec = self.endurance_hr*SEC_PER_HR


@dataclass(frozen = True)
class Config:
    # Aircraft
    altitude_kft: float
    mach: float
    manx_bank_angle_rad: float
    manx_decel_gees: float
    manx_min_mach: float

    # Sensor
    sensor: Sensor
    sensor_assumption: SensorAssumption

    # Target
    target: DesignTarget

    # AOI
    aoi: AOI
    aoi_revisit_time_hr: float

@dataclass
class ModelResult:
    config: Config
    valid: bool                               = True
    reason: str                               = None
    sensor_performance: SensorPerformance     = None
    ac_search_perf: AircraftSearchPerformance = None
    ac_turn_time: float                       = None
    required_overlap: float                   = None
    effective_sweep_width: float              = None
    search_rate: float                        = None
    onsta_req_n: float                        = None
    onsta_req_cost: float                     = None

