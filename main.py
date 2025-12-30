import csv
import subprocess
import sys
from constants import *
from lib import (
    validate_config, 
    calc_sensor_performance, 
    calc_search_performance,
    calc_coordinated_level_turnaround_time,
    calc_coordinated_level_turnaround_time2
)


# Assumptions/givens
AOI = AOI(
    ingress = 100_000, # meters
    length  = 100_000, # meters
    width   = 100_000, # meters
    egress  = 100_000 # meters
)

# Design parameters
# altitudes = range(5,30,5)
altitudes = [100]
machs     = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
sensors   = [Sensor['LOW'], Sensor['MED'], Sensor['HIGH']]

# JOHNSON_CRITERIA = 2 # Recognize
JOHNSON_CRITERIA = 8 # Identify
# JOHNSON_CRITERIA = 13 # Classify
# JOHNSON_CRITERIA = 4 # Testing

MANX_BANK_ANGLE_DEG = 35
MANX_BANK_ANGLE_RAD = MANX_BANK_ANGLE_DEG * RAD_PER_DEG
MANX_DECEL_GEES = -0.7
MANX_MIN_MACH = 0.15
MANX_SPEED_COEFFICIENT = 0.7 # TODO remove if switching to more complex turn calculation

TARGET = DesignTarget(
    type      = "Frigate",
    dims      = (150, 40), # m, (horizontal, vertical)
    max_speed = 25 # knots
)

SENSOR_ASSUMPTIONS = {
    Sensor.LOW: SensorAssumption(
        fov_deg     = (15, 15),
        resolution  = (640, 640),
        johnson_req = JOHNSON_CRITERIA,
        cost        = 0.05
    ),
    Sensor.MED: SensorAssumption(
        fov_deg     = (30, 30),
        resolution  = (1024, 1024),
        johnson_req = JOHNSON_CRITERIA,
        cost        = 1
    ),
    Sensor.HIGH: SensorAssumption(
        fov_deg     = (60, 60),
        resolution  = (1920, 1920),
        johnson_req = JOHNSON_CRITERIA,
        cost        = 10
    ),
}

def evaluate_config(config: Config) -> ModelResult:
    '''
    Given a particular configuration of the scenario, perform calculations to 
    determine aircraft/sensor performance.

    Args:
    config: Config: instance of the Config dataclass specifying all necessary
    attributes of the scenario to do calculations

    Returns:
    ModelResult: instance of ModelResult dataclass containing the Config (inputs)
    used to calculate this result, along with intermediate and final calculations
    
    '''
    # Calc length of each leg - how much of the length of the box do we have to 
    # fly to detect target at the edge. Limiting case is a target showing an aspect
    # where the height is the largest dimension we see

    # region: Validate config ----
    result = ModelResult(config=config)

    config_valid, reason = validate_config(config)
    if not config_valid:
        result.valid = config_valid
        result.reason = reason
        return result 

    # endregion ----

    # Instantiate the aircraft
    ac = Aircraft(
        alt_kft             = config.altitude_kft, 
        mach                = config.mach,
        manx_bank_angle_rad = config.manx_bank_angle_rad,
        manx_speed_coeff    = config.manx_speed_coeff,
        manx_decel_gees     = config.manx_decel_gees,
        manx_min_mach       = config.manx_min_mach,
        sensor              = config.sensor, 
        sensor_assumption   = config.sensor_assumption
    )

    # Calc sensor performance
    result.sensor_performance = calc_sensor_performance(
        config.sensor_assumption, 
        config.target
    )

    # Calc aircraft sensor coverage
    result.ac_search_performance = calc_search_performance(
        alt_m           = config.altitude_kft * 1000 / FEET_PER_METER,
        slant_det_range = result.sensor_performance.slant_detection_range,
        fov_rad         = tuple([fov_deg * RAD_PER_DEG for fov_deg in config.sensor_assumption.fov_deg]),
        aoi             = config.aoi
    )

    if not result.ac_search_performance.valid:
        result.valid = False
        result.reason = result.ac_search_performance.reason
        return(result)

    # Calc time ac to reverse heading and offset for next leg with a 
    # coordinated, level turn
    result.ac_turn_time = calc_coordinated_level_turnaround_time2(
        ac, 
        result.ac_search_performance.crosstrack_detection_width[1],
        result.ac_search_performance
    )


    return(result)

    if ac.downtrack_range[1].valid:
        leg_length = Result(
            valid = True,
            value = config.aoi_l_by_w[0] - 2*ac.downtrack_range[1].value,
            reason = None
        )
    else:
        leg_length = Result(
            valid = False,
            value = None,
            reason = 'No downtrack distance because plane\'s altitude > sensor\'s slant detection range. '
        )


    # Check if overlap of successive legs is necessary:
    # Limiting cases to consider:
    ##   - design target traveling perpendicular to ac's track: makes most progress
    ##     across legs ac is searching, could evade detection if made it entirely 
    ##     across tracks while ac is traveling down and back. However, displays
    ##     horizontal dimension and is detectable from further away.
    
    ### time between when this target is barely missed and when ac would 
    ### potentially see it on the next leg. The time to make a full leg, plus
    ### time to turn around (approx because we don't know the exact overlap 
    ### required yet), plus the time to drive the next leg to the beaming target
    ### detection range

    return
    time_downtrack = (2*leg_length-ac.ground_range[0].value)/ac.mach/MACH_IN_M_PER_HR
    time_turning = execute_turn(ac, ac.beam_width[1].value)
    time = time_downtrack + time_turning

    tgt_dist_travelled_cross_track = time * ac.sensor.tgt_speed * 1852
    overlap1 = tgt_dist_travelled_cross_track - (ac.ground_range[0].value-ac.ground_range[1].value)
    overlap1 = 0 if overlap1 < 0 else overlap1


    ##   - design target traveling across ac's legs at an aspect where the horizontal
    ##     dimension presented is equal to the height - minimal detection range 
    ##     while still traveling across ac's legs and could potentially evade 
    ##     detection in worst case. 

    aob = math.acos(ac.sensor.tgt_dims[1]/ac.sensor.tgt_dims[0])
    tgt_speed_cross_track = ac.sensor.tgt_speed * math.cos(aob)

    time_downtrack = (2*leg_length-ac.ground_range[1].value)/ac.mach/MACH_IN_M_PER_HR
    time_turning = execute_turn(ac, ac.beam_width[1].value)
    time = time_downtrack + time_turning

    overlap2 = tgt_speed_cross_track * 1852 * time
    
    overlap = max(overlap1, overlap2)

    sweep_width = ac.beam_width[1].value - overlap
    print(f'sweep_width: {sweep_width:0.1f} = {ac.beam_width[1].value:0.1f}-{overlap:0.1f}')
    
    # Calc number of legs (n_legs) required to search AOI
    n_legs = math.ceil(aoi[1]/sweep_width) if sweep_width > 0 else None
    


    # # time spent on leg

    # # calc time to complete legs
    # flight_distance = INGRESS_RANGE + EGRESS_RANGE + n_legs*leg_length + aoi[0]
    # flight_time = flight_distance/(ac.mach * MACH_IN_M_PER_HR)

    # # calc # sorties required

    # # calc cost
    # ac_cost = cost(ac.mach, ac.alt_m, ac.sensor)

    # # endurance
    # ac_endurance = endurance(ac.mach, ac.alt_m)

    result = {
        'altitude':         ac.alt_kft,
        'mach':             ac.mach,
        'sensor':           ac.sensor.name,
        'sweep_width':      round(sweep_width,2),
        'n_legs':           round(n_legs,2),
        # 'flight_time':      round(flight_time, 2),
        # 'ac_endurance':    round(ac_endurance, 2),
        # 'ac_cost':              round(ac_cost, 2),

    }
    
    
    return (result)


def main():

    results = []
    for altitude in altitudes:
        for mach in machs:
            for sensor in sensors:
                config = Config(
                    altitude_kft        = altitude,
                    mach                = mach,
                    manx_bank_angle_rad = MANX_BANK_ANGLE_RAD,
                    manx_speed_coeff    = MANX_SPEED_COEFFICIENT,
                    manx_decel_gees     = MANX_DECEL_GEES,
                    manx_min_mach       = MANX_MIN_MACH,
                    sensor              = sensor,
                    sensor_assumption   = SENSOR_ASSUMPTIONS[sensor],
                    target              = TARGET,
                    aoi                 = AOI
                )
                print('-------')

                
                # lib.evaluate_aircraft(lib.Aircraft(altitude, mach, sensor), lib.AOI_LENGTH_BY_WIDTH)
                result = evaluate_config(config)
                results.append(result)

    sys.exit()


    # fieldnames = ['altitude', 'mach', 'sensor', 'flight_time', 'ac_endurance', 'ac_cost']
    # fieldnames = ['altitude', 'mach', 'sensor', 'flight_time', 'ac_endurance', 'ac_cost']
    fieldnames = results[0].keys()

    with open('output.csv', 'w', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)


    subprocess.call([r'Rscript', r'./plots.R'])

if __name__ == '__main__':
    main()



