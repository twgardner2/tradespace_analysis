from enum import Enum, auto
import math

# Assumptions/Givens
MARITIME_AOI_LENGTH = 100_000 # m
MARITIME_AOI_WIDTH  = 100_000 # m
AOI_LENGTH_BY_WIDTH = (MARITIME_AOI_LENGTH, MARITIME_AOI_WIDTH)
INGRESS_RANGE = 100_000 # m
EGRESS_RANGE = 100_000 # m

TARGET_DIMENSION = (150, 40) # horizontal, vertical
TARGET_MAX_SPEED_KTS = 25 # knots

LOW_SENSOR_RESOLUTION = (480, 480) # horizontal, vertical
MED_SENSOR_RESOLUTION = (1024, 1024) # horizontal, vertical
HIGH_SENSOR_RESOLUTION = (2048, 2048) # horizontal, vertical

LOW_SENSOR_FOV_DEG  = (15, 15)
MED_SENSOR_FOV_DEG  = (30, 30)
HIGH_SENSOR_FOV_DEG = (60, 60)

JOHNSON_CRITERIA = 8

MACH_IN_M_PER_HR = 1.235e6


class Sensor(Enum):
    def __new__(cls, code, resolution, fov, tgt_dims, tgt_speed, johnson):
        '''
        Enumerated type to define different sensors: Low, Med, High

        Arguments:
        resolution: tuple of (horizontal res, vertical res)
        fov: tuple of (horizontal fov, vertical fov)
        tgt_dims: tuple of (horizontal length in m, vertical height in m)
        johnson: johnson criteria, number of pixels across target for required detection


        Resulting member: retains arguments as attributes, has additional attributes
        for ifov (in radians), gsd, and slant_range for detecting target's horizontal 
        and vertical dimensions
        '''


        member = object.__new__(cls)
        member._value_ = code
        member.resolution = resolution
        member.fov = fov
        member.tgt_dims = tgt_dims
        member.tgt_speed = tgt_speed
        member.johnson = johnson

        # Derived attributes
        # fov_rad: tuple of (horizontal fov in rad, vertical fov in rad)
        member.fov_rad = tuple([el*2*math.pi/360 for el in fov]) 
        
        # ifov_rad: tuple of (horizontal ifov in rad, vertical ifov in rad)
        member.ifov_rad = tuple([fov/res for (fov, res) in zip(member.fov_rad, resolution)])
        
        # gsd: how much of a the target in a given dimension needs to be covered
        # by each pixel to achieve required detection 
        # tuple of (gsd against target's horizontal dimension, gsd against vertical dimension)
        member.gsd = tuple([tgt_dim/johnson for tgt_dim in tgt_dims])

        # slant_range at which we detect target: 
        # tuple (slant range vs horizontal dimension, slant range vs. vertical dimension)
        member.slant_range = tuple([gsd/ifov for (gsd,ifov) in zip(member.gsd, member.ifov_rad)])

        return member

    def __str__(self):
        # return(f'''{self.name} Sensor: Slant Range = {self.slant_range:.0f}
        return(f'''{self.name} Sensor: IFOV = {self.ifov_rad}, Slant Range: {self.slant_range}
    '''
    )

    Low  = (1,  LOW_SENSOR_RESOLUTION,  LOW_SENSOR_FOV_DEG, TARGET_DIMENSION, TARGET_MAX_SPEED_KTS, JOHNSON_CRITERIA)
    Med  = (2,  MED_SENSOR_RESOLUTION,  MED_SENSOR_FOV_DEG, TARGET_DIMENSION, TARGET_MAX_SPEED_KTS, JOHNSON_CRITERIA)
    High = (3, HIGH_SENSOR_RESOLUTION, HIGH_SENSOR_FOV_DEG, TARGET_DIMENSION, TARGET_MAX_SPEED_KTS, JOHNSON_CRITERIA)


class Aircraft():
    '''
    Class to represent a given aircraft performance, factoring in its: Altitude,
    Mach, and Sensor.

    Arguments:
    alt_kft: altitude in kft
    mach: speed in mach
    sensor: Sensor enum type

    Resulting member retains arguments as attributes. Derived attributes include:
    
    alt_m: altitude in meters, used for calculations
    
    ground_range: tuple of ground range at which detections are made against design 
    target's horizontal and vertical dimensions

    downtrack_range: tuple of downtrack coverage achieved against design target's 
    horizontal and vertical dimensions. This is the downtrack component of the 
    edges of the "fov cone."

    beam_width: tuple of the width of the "fov cone" at the downtrack detection 
    range against the horizontal dimension and vertical dimension of the design
    target. 
    
    '''
    def __init__(self, alt_kft: float, mach: float, sensor: Sensor) -> None:
        self.alt_kft = alt_kft
        self.alt_m   = alt_kft * 1000 / 3.2808
        self.mach    = mach
        self.sensor  = sensor
        self.ground_range = tuple(math.sqrt(slant**2 - self.alt_m**2) for slant in self.sensor.slant_range)
        self.downtrack_range = tuple([ground*math.cos(fov/2) for (ground, fov) in zip(self.ground_range, self.sensor.fov_rad)])
        self.beam_width = tuple([2*ground*math.sin(fov/2) for (ground, fov) in zip(self.ground_range, self.sensor.fov_rad)])


    def __str__(self) -> str:
        return(f'''{self.alt_kft}kft/{self.mach}M/{self.sensor}''')


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
   
    # Calc length of each leg - how much of the length of the box do we have to 
    # fly to detect target at the edge. Limiting case is a target showing an aspect
    # where the height is the largest dimension we see
    leg_length = aoi[0] - 2*ac.downtrack_range[1]

    # Check if overlap of successive legs is necessary:
    # Limiting cases to consider:
    ##   - design target traveling perpendicular to ac's track: makes most progress
    ##     across legs ac is searching, could evade detection if made it far enough 
    ##     across tracks while ac is traveling down and back. However, displays
    ##     horizontal dimension and is detectable from further away.
    
    ### time between when this target is barely missed and when ac would 
    ### potentially see it on the next leg. The time to make a full leg, plus
    ### the time to drive the next leg to the beaming target detection range
    time = (2*leg_length-ac.ground_range[0])/ac.mach/MACH_IN_M_PER_HR
    tgt_dist_travelled_cross_track = time * ac.sensor.tgt_speed * 1852
    overlap1 = tgt_dist_travelled_cross_track - (ac.ground_range[0]-ac.ground_range[1])
    overlap1 = 0 if overlap1 < 0 else overlap1


    ##   - design target traveling across ac's legs at an aspect where the horizontal
    ##     dimension presented is equal to the height - minimal detection range 
    ##     while still traveling across ac's legs and could evade detection in worst
    ##     case. 

    aob = math.acos(ac.sensor.tgt_dims[1]/ac.sensor.tgt_dims[0])
    tgt_speed_cross_track = ac.sensor.tgt_speed * math.cos(aob)
    overlap2 = tgt_speed_cross_track * 1852 * (2*leg_length-ac.ground_range[1])/ac.mach/MACH_IN_M_PER_HR
    

     
    
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

    result = {
        'altitude':          ac.alt_kft,
        'mach':                 ac.mach,
        'sensor':             ac.sensor.name,
        'flight_time':      round(flight_time, 2),
        'ac_endurance':    round(ac_endurance, 2),
        'ac_cost':              round(ac_cost, 2),

    }
    
    
    return (result)

# print(Sensor.Low)
# print(Sensor.Med)
# print(Sensor.High)




