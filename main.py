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
    calc_effective_sweep_width
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

    # Calc effective sweep width, accounting for overlap required for limiting 
    # targets
    effective_sweep_width, ac_turn_time = calc_effective_sweep_width(
        config, ac, result.ac_search_perf, debug=True
    )



    result.effective_sweep_width = effective_sweep_width
    result.ac_turn_time = ac_turn_time


    if effective_sweep_width < 0:
        result.valid  = False
        result.reason = 'Effective sweep width is negative, design target can evade detection'
        return result

    # How many aircraft needed to search entire area given endurance?
    n_legs = math.ceil(config.aoi.width/result.effective_sweep_width)





    return(result)

    

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



