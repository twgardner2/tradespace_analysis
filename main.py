import pandas as pd
from dataclasses import asdict
import subprocess
import sys
from constants import *
from lib import (
    validate_config, 
    calc_sensor_performance, 
    calc_search_performance,
    calc_coordinated_level_turnaround_time,
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
    result.ac_search_perf = calc_search_performance(
        alt_m           = config.altitude_kft * 1000 / FEET_PER_METER,
        slant_det_range = result.sensor_performance.slant_detection_range,
        fov_rad         = tuple([fov_deg * RAD_PER_DEG for fov_deg in config.sensor_assumption.fov_deg]),
        aoi             = config.aoi
    )

    if not result.ac_search_perf.valid:
        result.valid = False
        result.reason = result.ac_search_perf.reason
        return(result)

    # Calc time ac to reverse heading and offset for next leg with a 
    # coordinated, level turn
    result.ac_turn_time = calc_coordinated_level_turnaround_time(
        ac, 
        result.ac_search_perf.xtrack_detection_width[1],
        result.ac_search_perf
    )

    # Check if overlap of successive legs is necessary:
    # Limiting cases to consider:
    ##   - "Beaming": design target traveling perpendicular to ac's track: makes
    ##     most progress across legs ac is searching, could evade detection if 
    ##     made it entirely across tracks while ac is traveling down and back. 
    ##     However, displays horizontal dimension and is detectable from further
    ##     away.
    
    ### time between when this target is barely missed and when ac would 
    ### potentially see it on the next leg. The time to make a full leg, plus
    ### time to turn around (approx because we don't know the exact overlap 
    ### required yet), plus the time to drive the next leg to the beaming target
    ### detection range

    time_downtrack = (2*config.aoi.length)/ac.mach/MACH_M_PER_SEC
    time_turning   = result.ac_turn_time
    time           = time_downtrack + time_turning

    tgt_beaming_dist_trav_cross_track = time * config.target.max_speed * KTS_IN_M_PER_SEC
    sweep_width_beaming_tgt           = result.ac_search_perf.xtrack_detection_width[0] - tgt_beaming_dist_trav_cross_track

    ##   - "Glancing": design target traveling across ac's legs at an aspect 
    ##     where the horizontal dimension presented is equal to the height -
    ##     minimal detection range while still traveling across ac's legs and
    ##     could potentially evade detection in worst case. 

    aob = math.acos(config.target.dims[1]/config.target.dims[0])
    tgt_speed_cross_track = config.target.max_speed * math.cos(aob)
    tgt_speed_down_track  = config.target.max_speed * math.sin(aob)

    time_downtrack = (2*config.aoi.length-tgt_speed_down_track)/ac.mach/MACH_M_PER_SEC
    time_turning   = result.ac_turn_time
    time           = time_downtrack + time_turning

    tgt_glancing_dist_trav_cross_track  = time * tgt_speed_cross_track * KTS_IN_M_PER_SEC
    sweep_width_glancing_tgt            = result.ac_search_perf.xtrack_detection_width[1] - tgt_glancing_dist_trav_cross_track


    effective_sweep_width = min(sweep_width_beaming_tgt, sweep_width_glancing_tgt)

    result.effective_sweep_width = effective_sweep_width





    return(result)



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

    # Run model - evaluate_config for various inputs
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
                
                result = evaluate_config(config)
                results.append(result)

    # Write results to output.csv
    results_dicts = [asdict(r) for r in results]
    df = pd.json_normalize(results_dicts, sep='_')
    df.to_csv('output.csv')

    # Run R script to do analysis
    subprocess.call([r'Rscript', r'./plots.R'])

if __name__ == '__main__':
    main()



