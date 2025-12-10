from enum import Enum, auto
import math

# Assumptions/Givens
MARITIME_AOI_LENGTH = 100_000 # m
MARITIME_AOI_WIDTH  = 100_000 # m
AOI_LENGTH_BY_WIDTH = (MARITIME_AOI_LENGTH, MARITIME_AOI_WIDTH)
INGRESS_RANGE = 100_000 # m
EGRESS_RANGE = 100_000 # m

TARGET_CRITICAL_DIMENSION_M = 40 # Masthead height of Frigate
TARGET_MAX_SPEED_KTS = 15 # knots

LOW_SENSOR_CRITICAL_RESOLUTION  = 480
MED_SENSOR_CRITICAL_RESOLUTION  = 1024
HIGH_SENSOR_CRITICAL_RESOLUTION = 2048

LOW_SENSOR_CRITICAL_FOV_DEG  = 15
MED_SENSOR_CRITICAL_FOV_DEG  = 30
HIGH_SENSOR_CRITICAL_FOV_DEG = 60

JOHNSON_CRITERIA = 8

MACH_IN_M_PER_HR = 1.235e6


class Sensor(Enum):
    def __new__(cls, code, crit_res, crit_fov_deg):
        member = object.__new__(cls)
        member._value_ = code
        member.crit_res = crit_res
        member.crit_fov_deg = crit_fov_deg
        member.crit_fov_rad = crit_fov_deg * 2 * math.pi / 360
        member.ifov = member.crit_fov_rad / member.crit_res
        member.gsd = TARGET_CRITICAL_DIMENSION_M/JOHNSON_CRITERIA
        member.slant_range = member.gsd/member.ifov # slant range at which sensor achieves objective on design target
        return member

    def __str__(self):
        return(f'''{self.name} Sensor: Slant Range = {self.slant_range:.0f}
    '''
    )

    Low  = (1,  LOW_SENSOR_CRITICAL_RESOLUTION,  LOW_SENSOR_CRITICAL_FOV_DEG)
    Med  = (2,  MED_SENSOR_CRITICAL_RESOLUTION,  MED_SENSOR_CRITICAL_FOV_DEG)
    High = (3, HIGH_SENSOR_CRITICAL_RESOLUTION, HIGH_SENSOR_CRITICAL_FOV_DEG)


class Aircraft():
    def __init__(self, alt_kft: float, mach: float, sensor: Sensor) -> None:
        self.alt_kft = alt_kft
        self.alt_m   = alt_kft * 1000 / 3.2808
        self.mach    = mach
        self.sensor  = sensor

    def __str__(self) -> str:
        return(f'''{self.alt_kft}kft/{self.mach}M/{self.sensor}''')


    def sensor_ground_range(self) -> float:
        if self.alt_m >= self.sensor.slant_range:
            return None
        return math.sqrt((self.sensor.slant_range)**2 - (self.alt_m**2))

    def sensor_downtrack_coverage(self) -> float:
        return self.sensor_ground_range() * math.cos(self.sensor.crit_fov_rad/2)

    def sensor_width(self) -> float:
        return 2 * self.sensor_ground_range() * math.sin(self.sensor.crit_fov_rad/2)


def endurance(mach: float, alt_m: float) -> float:
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

    alt_kft = alt_m*3.28084/1000
    return -18.75*mach**2 + 8.0893*mach + 0.01*alt_kft**2 + 0.05*alt_kft + 9.2105

def cost(mach: float, alt_m: float, sensor: Sensor) -> float:
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
    
    match sensor:
        case Sensor.Low:
            sensor_cost = 0.05
        case Sensor.Med:
            sensor_cost = 1
        case Sensor.High:
            sensor_cost = 10


    alt_kft = alt_m*3.28084/1000
    return 50*mach**2 - 35*mach + 0.03*alt_kft**2 - 0.2*alt_kft + 11 + sensor_cost

def evaluate_aircraft(ac: Aircraft, aoi: tuple[float, float]) -> tuple[float, float, float]:
   
    # calc length of each leg
    leg_length = aoi[0] - 2*ac.sensor_downtrack_coverage()
    
    # Calc number of legs
    # Overlap to account for worst-case, cross-track VOI
    time_spent_on_leg = leg_length / ac.mach / MACH_IN_M_PER_HR
    effective_sensor_width = ac.sensor_width() - 2*(TARGET_MAX_SPEED_KTS*1852)*time_spent_on_leg
    n_legs = aoi[1]/effective_sensor_width
    

    # time spent on leg

    # calc time to complete legs
    flight_distance = INGRESS_RANGE + EGRESS_RANGE + n_legs*leg_length + aoi[0]
    flight_time = flight_distance/(ac.mach * MACH_IN_M_PER_HR)

    # calc # sorties required

    # calc cost
    ac_cost = cost(ac.mach, ac.alt_m, ac.sensor)

    # endurance
    ac_endurance = endurance(ac.mach, ac.alt_m)
    
    
    return (flight_time, ac_endurance, ac_cost)

# print(Sensor.Low)
# print(Sensor.Med)
# print(Sensor.High)




