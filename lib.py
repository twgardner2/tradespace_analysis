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

    TODO: validate that manx_min_mach < mach
    TODO: check manx_decel_gees is negative and probably within some reasonable bounds
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
    Calculates time elapsed for aircraft to turn arc_angle_rad radians 
    around a coordinated, level turn at a given speed and bank angle.

    Args:
        mach (float): aircraft speed in mach.
        bank_angle_rad (float): bank angle in radians for the turn.

    Returns:
        float: radius of turn circle.
    '''

    return arc_angle_rad*MACH_M_PER_SEC*mach/GEE/math.tan(bank_angle_rad)


def calc_straight_accelerating_leg(
        mach0: float,
        dist: float, 
        accel: float, 
        min_mach: float
    ) -> tuple[float, float]:
    '''
    Calculate time and final speed after a straight leg with constant
    acceleration.

    Args:
        mach0 (float): initial mach
        dist (float):  distance on this straight leg
        accel (float): acceleration on this leg, in Gs
        min_mach:      minimum mach allowed to decelerate to

    Returns:
        tuple[float, float]: [time on leg, final speed]
    '''
    ## Time to decelerate to min_mach
    t_min_mach = (min_mach-mach0)*MACH_M_PER_SEC/(accel*GEE)

    ## Time to reach dist under deceleration
    ## Quadratic equation: 0 = 1/2*a*t^2 + v0*t - s
    a = accel*GEE/2
    b = mach0*MACH_M_PER_SEC
    c = -dist
    discriminant = (b**2) - (4*a*c)
    if discriminant < 0:
        # Decelerating body would stop and turn around before reaching dist
        t_dist = None
    else:
        t1 = (-b + (discriminant)**0.5) / (2*a)
        t2 = (-b - (discriminant)**0.5) / (2*a)
        # Want the minimum, positive solution 
        t_dist = min([t for t in [t1, t2] if t > 0])
    
    
    # Possible cases:
    ## Decelerates and stops before reaching distance
    ## OR reaches min_mach before full distance
    if t_dist is None or t_min_mach < t_dist:
        # Portion of leg slowing down to min_mach
        t_decel = t_min_mach
        d2 = mach0*MACH_M_PER_SEC*t_decel + 0.5*accel*GEE*(t_decel**2)
        # Portion of leg after min_mach to dist
        d1 = dist-d2
        t_cruise = d1/mach0/MACH_M_PER_SEC
        # Total
        time  = t_decel + t_cruise
        machf = min_mach

    ## Decelerates while going dist without reaching min_mach
    else:
        time  = t_dist
        machf = (mach0*MACH_M_PER_SEC + accel*GEE*t_dist)/MACH_M_PER_SEC

    return (time, machf)


def calc_sensor_performance(sensor_assumption: SensorAssumption,
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
    # tuple of (slant range vs horizontal dimension, slant range vs. vertical dimension)
    slant_range = tuple([gsd/ifov for (gsd,ifov) in zip(gsd, ifov_rad)])

    return(
        SensorPerformance(
            slant_detection_range = slant_range
        )
    )


def calc_search_performance(
        alt_m: float, 
        slant_det_range: tuple[float, float],
        fov_rad: tuple[float, float],
        aoi: AOI
    ) -> AircraftSearchPerformance:
    
    # If altitude is greater than either of the detection slant ranges (vs. 
    # beaming target or vs. height of target - it'll be the latter if it happens),
    # then the result is invalid, stop evaluation
    if any([(alt_m-slant)>0 for slant in slant_det_range]):
        result = AircraftSearchPerformance(valid=False, reason='Alt > Slant detection range')
        return result


    ground_detection_range = tuple([(slant**2-alt_m**2)**0.5 for slant in slant_det_range])
    downtrack_detection_range = tuple([ground * math.cos(fov_rad[0]/2) for ground in ground_detection_range])#####!!!!!!!!!!!!!
    crosstrack_detection_width = tuple([2 * ground * math.sin(fov_rad[0]/2) for ground in ground_detection_range])

    # Length of a search leg is the length of the AOI minus the distance at which 
    # the sensor detects the design target against it's height on each end (x2) 
    leg_length = aoi.length - 2*downtrack_detection_range[1]

    # Determine search leg overlap required
    ## 2 limiting cases: 
    ### 1) 
    
    result = AircraftSearchPerformance(
        valid                      = True,
        ground_detection_range     = ground_detection_range,
        downtrack_detection_range  = downtrack_detection_range,
        crosstrack_detection_width = crosstrack_detection_width,
        leg_length                 = leg_length,
    )
    return result


def calc_coordinated_level_turnaround_time(
        ac: Aircraft, 
        lateral_offset: float, 
    ) -> float:
    '''
    Determines how the aircraft will execute a the turn from the end of one leg
    to the beginning of the next. Assumes aircraft decelerates at some constant
    rate and turns with a fixed bank angle (ac.manx_bank_angle_rad).
    
    Args:
        ac (Aircraft): aircraft making the turn.
        lateral_offset (float): required lateral offset for start of next leg.

    Returns:
        float: time, in hr, required to execute a reversal of heading with required 
        lateral offset.
    '''

    manx_mach = ac.manx_speed_coeff*ac.mach

    ac_manx_turn_radius = turn_radius(manx_mach, ac.manx_bank_angle_rad)

    if lateral_offset >= 2*ac_manx_turn_radius:
        # Lateral offset is on or outside the coordinated, level turn radius. 
        # If outside, add straight segment halfway through turn.
        length_of_straight_segment = lateral_offset - 2*ac_manx_turn_radius
        time_on_straight_segment = length_of_straight_segment/manx_mach/MACH_M_PER_SEC
        time_on_turn = const_turn_time(manx_mach, ac.manx_bank_angle_rad, math.pi) 
        total_time = time_on_straight_segment + time_on_turn

        answer = total_time

    else: 
        # Need less lateral offset than constant turn results in. Assume aircraft
        # snaps onto and off of it's maneuvering turn circle. Fly the arc distance 
        # around the circle until it comes around to the other side of a chord 
        # the distance of the required offset. That is, fly more than half the 
        # circle to achieve less lateral offset than twice the radius while getting
        # turned around to perform the next leg. 
        # angle_of_travel_around_circle = 2*(math.pi - math.asin(lateral_offset/2/ac_manx_turn_radius))
        # time_on_turn = const_turn_time(manx_mach, ac.manx_bank_angle_rad, angle_of_travel_around_circle) 
        
        # Need less lateral offset than semi-circle of manx turn radius results
        # in. Let manx turn radius be R. Construct 3 circles of radius R:
        # 1) Centered R distance away from the point perpendicular to the 
        #    aircraft's track when it completes a search leg in the direction 
        #    away from the next leg. Circle is tangent to where the aircraft 
        #    completes a leg.
        # 2) Centered R distance perpendicular to and past the point where the
        #    aircraft will start its next leg. Circle is tangent to where the
        #    aircraft starts the next leg.
        # 3) Centered on the extension of the centerline between the two legs
        #    and tangent to the other two circles. 
        #
        # Aircraft flys each of these circles until it reaches a tangent point,
        # at which point it turns onto the next circle. Assume the aircraft can 
        # transition smoothly and instantly from one circle to another. The
        # total angle (in radians) traveled around circles of radius R is:
        #
        # theta-total = pi + 4*acos( (R+S/2)/2R ), as derived in slides.
        # 
        # Inspection of this formula shows that the total angle is:
        #   - pi (180 deg to reverse heading), plus
        #   - 4 times the angle travelled around the first circle. That is, on 
        #     each side:
        #       - Far enough around the first circle to get onto the second
        #         circle
        #       - The same angle around the second circle to get back to the 
        #         original heading 

        total_angle_of_travel = math.pi + 4(math.acos( (ac_manx_turn_radius+lateral_offset/2)(2*ac_manx_turn_radius) ))

        distance = ac_manx_turn_radius * total_angle_of_travel
        time = distance/ manx_mach * MACH_IN_M_PER_HR


        answer = time

    return answer/3600


def calc_coordinated_level_turnaround_time2(
        ac: Aircraft, 
        lateral_offset: float,
        ac_search_performance: AircraftSearchPerformance
    ) -> float:

    '''
    Determines how the aircraft will execute a the turn from the end of one leg
    to the beginning of the next. The turn takes place entirely outside of the 
    search box. The aircraft has to be straight and level for the entire 
    downtrack detection range against the height of the design target before it 
    reenters the search box (otherwise there is a sensor gap, as shown in the 
    slides). The turn is calculated as follows:

    1) As the aircraft leaves the box, it continues straight the distance of its
    downtrack detection range against the height of the design target. This
    allows for the same on the return to the search box. On this leg, the 
    aircraft decelerates at ac.manx_decel_gees, to no less than some minimum 
    speed, ac.manx_min_speed, in order to reduce its turn radius and speed up
    the turn. 
    
    Its turn radius is based on ac.manx_bank_angle_rad and its speed at the end
    of this leg. 

    2) The next part depends on the ratio of the lateral offset, S, to the turn 
    radius, R:

    - 2R < S: 1 quadrant of coordinated, level turn radius circle, into straight 
    flight, then another quadrant of coordinated, level turn radius circle. 

    - 2R == S: Coordinated, level semi-circle. 

    - 2R > S: Flys portions of three coordinated, level semi-circles: first
    turning away from next leg, then turning onto a circle towards the next leg
    which will take it past the lateral offset of the new circle but will turn 
    it around to be facing generally back towards the search box, then onto a 
    final circle to steady out on the reverse of the original heading and at the 
    required lateral offset. 

    3) Straight and level the distance of the downtrack detection range against 
    the height of the design target, accelerating back up to cruise speed just 
    when it reenters the search box for the next leg.
    
    Args:
        ac (Aircraft): aircraft making the turn.
        lateral_offset (float): required lateral offset for start of next leg.

    Returns:
        float: time, in hr, required to execute a reversal of heading with 
        required lateral offset.
    '''

    # Initial straight, deceleration leg
    t1, manx_mach = calc_straight_accelerating_leg(
        mach0    = ac.mach,
        dist     = ac_search_performance.downtrack_detection_range[1], 
        accel    = ac.manx_decel_gees,
        min_mach = ac.manx_min_mach
    )

    # Turn around
    ac_manx_turn_radius = turn_radius(manx_mach, ac.manx_bank_angle_rad)

    if lateral_offset >= 2*ac_manx_turn_radius:
        # Lateral offset is on or outside the coordinated, level turn radius. 
        # If outside, add straight segment halfway through turn.
        length_of_straight_segment = lateral_offset - 2*ac_manx_turn_radius
        time_on_straight_segment = length_of_straight_segment/manx_mach/MACH_M_PER_SEC
        time_on_turn = const_turn_time(manx_mach, ac.manx_bank_angle_rad, math.pi) 
        t2 = time_on_straight_segment + time_on_turn


    else: 
        # Need less lateral offset than constant turn results in. Assume aircraft
        # snaps onto and off of it's maneuvering turn circle. Fly the arc distance 
        # around the circle until it comes around to the other side of a chord 
        # the distance of the required offset. That is, fly more than half the 
        # circle to achieve less lateral offset than twice the radius while getting
        # turned around to perform the next leg. 
        # angle_of_travel_around_circle = 2*(math.pi - math.asin(lateral_offset/2/ac_manx_turn_radius))
        # time_on_turn = const_turn_time(manx_mach, ac.manx_bank_angle_rad, angle_of_travel_around_circle) 
        
        # Need less lateral offset than semi-circle of manx turn radius results
        # in. Let manx turn radius be R. Construct 3 circles of radius R:
        # 1) Centered R distance away from the point perpendicular to the 
        #    aircraft's track when it completes a search leg in the direction 
        #    away from the next leg. Circle is tangent to where the aircraft 
        #    completes a leg.
        # 2) Centered R distance perpendicular to and past the point where the
        #    aircraft will start its next leg. Circle is tangent to where the
        #    aircraft starts the next leg.
        # 3) Centered on the extension of the centerline between the two legs
        #    and tangent to the other two circles. 
        #
        # Aircraft flys each of these circles until it reaches a tangent point,
        # at which point it turns onto the next circle. Assume the aircraft can 
        # transition smoothly and instantly from one circle to another. The
        # total angle (in radians) traveled around circles of radius R is:
        #
        # theta-total = pi + 4*acos( (R+S/2)/2R ), as derived in slides.
        # 
        # Inspection of this formula shows that the total angle is:
        #   - pi (180 deg to reverse heading), plus
        #   - 4 times the angle travelled around the first circle. That is, on 
        #     each side:
        #       - Far enough around the first circle to get onto the second
        #         circle
        #       - The same angle around the second circle to get back to the 
        #         original heading 

        total_angle_of_travel = math.pi + 4*(math.acos( (ac_manx_turn_radius+lateral_offset/2)/(2*ac_manx_turn_radius) ))

        distance = ac_manx_turn_radius * total_angle_of_travel
        t2 = distance/ manx_mach / MACH_M_PER_SEC


    # Final, straight, acceleration leg
    t3 = t1


    return t1 + t2 + t3
