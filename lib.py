import math
from dataclasses import fields
from constants import *


def validate_config(config: Config) -> tuple[bool, str]:
    '''
    Run basic validation on the config object. 

    Args:
    config: Config. The configuration object

    Returns:
    tuple[bool, str]. Whether is valid and, if not, why.

    TODO: check all aspects of config, return a report of everything that's 
    invalid, rather short-circuiting when first invalid aspect is found.
    '''

    if config.sensor_assumption.johnson_req <= 0:
        return((False, f'Johnson Criteria must be > 0, is {config.sensor_assumption.johnson_req}'))

    if any([res <= 0 for res in config.sensor_assumption.resolution]):
        return((False, f'Resolution value must be > 0, is {config.sensor_assumption.resolution}'))

    if any([fov <= 0 for fov in config.sensor_assumption.fov_deg]):
        return((False, f'FOV value must be > 0, is {config.sensor_assumption.fov_deg}'))

    if config.mach <= 0:
        return((False, f'Mach value must be > 0, is {config.mach}'))

    if config.altitude_kft <= 0:
        return((False, f'Altitude value must be > 0, is {config.altitude_kft}'))
    
    for field in fields(config.aoi):
        value = getattr(config.aoi, field.name)
        if value <= 0:
            return((False, f'AOI values must all be > 0, are {config.aoi}'))
        
    if any([dim <= 0 for dim in config.target.dims]):
        return((False, f'Target dims must be > 0, are {config.target.dims}'))
    
    if config.target.max_speed <= 0:
        return((False, f'Target speed value must be > 0, is {config.target.max_speed}'))


    return (True, None)

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

    alt_kft = alt_m*FEET_PER_METER/1000
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


    alt_kft = alt_m*FEET_PER_METER/1000
    return 50*mach**2 - 35*mach + 0.03*alt_kft**2 - 0.2*alt_kft + 11 + sensor_cost


def turn_radius(mach: float, bank_angle_rad: float):
    '''
    Calculates aircraft turning radius for a coordinated, level turn.

    Args:
        mach (float): aircraft speed in mach.
        bank_angle_rad (float): bank angle in radians for the turn.

    Returns:
        float: radius of turn circle.
    '''
    return (MACH_M_PER_SEC*mach)**2/GEE/math.tan(bank_angle_rad)


def const_turn_time(mach: float, bank_angle_rad: float, arc_angle_rad: float):
    '''
    Calculates time elapsed for aircraft to turn arc_angle_rad radians around a
    coordinated, level turn at a given speed and bank angle.

    Args:
        mach (float): aircraft speed in mach.
        bank_angle_rad (float): bank angle in radians for the turn.

    Returns:
        float: radius of turn circle.
    '''

    return arc_angle_rad*MACH_M_PER_SEC*mach/GEE/math.tan(bank_angle_rad)


def execute_turn(ac: Aircraft, lateral_offset: float):
    '''
    Determines how the aircraft will execute a the turn from the end of one leg
    to the beginning of the next. Assumes aircraft maneuvers at 70% of cruise 
    speed and turns with 35 deg bank angle.
    
    Args:
        ac (Aircraft): aircraft making the turn.
        lateral_offset (float): required lateral offset for start of next leg.

    Returns:
        float: time, in hr, required to execute a reversal of heading with required 
        lateral offset.
    '''

    MANX_SPEED_COEFFICIENT = 0.7
    MANX_BANK_ANGLE_RAD = 35 *2*math.pi/360
    MANX_MACH = MANX_SPEED_COEFFICIENT*ac.mach

    ac_manx_turn_radius = turn_radius(MANX_MACH, MANX_BANK_ANGLE_RAD)

    if lateral_offset >= 2*ac_manx_turn_radius:
        # Lateral offset is on or outside the coordinated, level turn radius. 
        # If outside, add straight segment halfway through turn.
        length_of_straight_segment = lateral_offset - 2*ac_manx_turn_radius
        time_on_straight_segment = length_of_straight_segment/MANX_MACH/MACH_M_PER_SEC
        time_on_turn = const_turn_time(MANX_SPEED_COEFFICIENT*ac.mach, MANX_BANK_ANGLE_RAD, math.pi) 
        total_time = time_on_straight_segment + time_on_turn

        answer = total_time

    else: 
        # Need less lateral offset than constant turn results in. Assume aircraft
        # snaps onto and off of it's maneuvering turn circle. Fly the arc distance 
        # around the circle until it comes around to the other side of a chord 
        # the distance of the required offset. That is, fly more than half the 
        # circle to achieve less lateral offset than twice the radius while getting
        # turned around to perform the next leg. 
        angle_of_travel_around_circle = 2*(math.pi - math.asin(lateral_offset/2/ac_manx_turn_radius))
        time_on_turn = const_turn_time(MANX_SPEED_COEFFICIENT*ac.mach, MANX_BANK_ANGLE_RAD, angle_of_travel_around_circle) 
        
        answer = time_on_turn

    return answer/3600
    

def determine_sensor_performance(sensor_assumption: SensorAssumption,
                          target: DesignTarget) -> SensorPerformance:
    
    # fov_rad: tuple of (horizontal fov in rad, vertical fov in rad)
    fov_rad = tuple([el*2*math.pi/360 for el in sensor_assumption.fov_deg]) 
    
    # ifov_rad: tuple of (horizontal ifov in rad, vertical ifov in rad)
    ifov_rad = tuple([fov/res for (fov, res) in zip(fov_rad, sensor_assumption.resolution)])
    
    # gsd: how much of a the target in a given dimension needs to be covered
    # by each pixel to achieve required detection 
    # tuple of (gsd against target's horizontal dimension, gsd against vertical dimension)
    gsd = tuple([tgt_dim/sensor_assumption.johnson_req for tgt_dim in target.dims])

    # slant_range at which we detect target: 
    # tuple (slant range vs horizontal dimension, slant range vs. vertical dimension)
    slant_range = tuple([gsd/ifov for (gsd,ifov) in zip(gsd, ifov_rad)])

    # return(slant_range)

    return(
        SensorPerformance(
            slant_detection_range = slant_range
        )
    )


