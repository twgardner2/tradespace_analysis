import pandas as pd
import numpy as np
from dataclasses import asdict
import subprocess
import sys
import os
from constants import *
from lib import (
    validate_config, 
    calc_sensor_performance, 
    calc_search_performance,
    calc_effective_sweep_width,
    calc_ac_search_rate,
    calc_onsta_requirement
)


# region Design Parameters
AOI = AOI(
    ingress = 100_000, # meters
    length  = 100_000, # meters
    width   = 100_000, # meters
    egress  = 100_000 # meters
)

AOI_REVISIT_TIME_HR = 6 # hours

altitudes = np.arange(5, 25.00001, 0.5)
machs     = np.arange(0.4, 0.90001, 0.025)
sensors   = [Sensor['LOW'], Sensor['MED'], Sensor['HIGH']]

# JOHNSON_CRITERIA = 2 # Recognize
JOHNSON_CRITERIA = 6 # Identify
# JOHNSON_CRITERIA = 12 # Classify
# JOHNSON_CRITERIA = 14 # Testing

MANX_BANK_ANGLE_DEG = 35
MANX_BANK_ANGLE_RAD = MANX_BANK_ANGLE_DEG * RAD_PER_DEG
MANX_DECEL_GEES = -0.7
MANX_MIN_MACH = 0.15
# endregion

TARGET = DesignTarget(
    type      = "Frigate",
    dims      = (160, 40), # m, (horizontal, vertical)
    max_speed = 25 # knots
)

SENSOR_ASSUMPTIONS = {
    Sensor.LOW: SensorAssumption(
        fov_deg     = (15, 15),
        resolution  = (480, 480),
        johnson_req = JOHNSON_CRITERIA,
        cost        = 0.05
    ),
    Sensor.MED: SensorAssumption(
        fov_deg     = (30, 30),
        resolution  = (960, 960),
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

# region evaluate_config
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

    # Validate config ----
    result = ModelResult(config=config)

    config_valid, reason = validate_config(config)
    if not config_valid:
        result.valid = config_valid
        result.reason = reason
        return result 


    # Instantiate the aircraft
    ac = Aircraft(
        alt_kft             = config.altitude_kft, 
        mach                = config.mach,
        manx_bank_angle_rad = config.manx_bank_angle_rad,
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

    # Calc effective sweep width, account for overlap for limiting targets
    effective_sweep_width, ac_turn_time = calc_effective_sweep_width(
        config         = config, 
        ac             = ac, 
        ac_search_perf = result.ac_search_perf, 
        # debug          = True
    )

    if effective_sweep_width <= 0:
        result.valid  = False
        result.reason = 'Aircraft/sensor pairing has negative effective sweep width against design target'
        return result
    
    result.effective_sweep_width = effective_sweep_width
    result.ac_turn_time          = ac_turn_time

    # Calc number of legs an aircraft can support with its endurance
    search_rate = calc_ac_search_rate(
        ac        = ac,
        aoi       = result.config.aoi,
        turn_time = result.ac_turn_time,
        eff_width = result.effective_sweep_width
    )

    if search_rate is None:
        result.valid = False
        result.reason = 'Aircraft endurance cannot support any search legs'

    result.search_rate = search_rate

    # Calculate fleet size
    onsta = calc_onsta_requirement(
        aoi = config.aoi,
        ac_search_rate = result.search_rate,
        revisit_time = config.aoi_revisit_time_hr*SEC_PER_HR 
        )
    
    # print(f'{ac.mach:0.1f}M/{ac.alt_kft}kft/{ac.sensor}: {onsta:0.2f} on-station')

    result.onsta_req_n = onsta
    result.onsta_req_cost = onsta * ac.cost

    return result


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
                    manx_decel_gees     = MANX_DECEL_GEES,
                    manx_min_mach       = MANX_MIN_MACH,
                    sensor              = sensor,
                    sensor_assumption   = SENSOR_ASSUMPTIONS[sensor],
                    target              = TARGET,
                    aoi                 = AOI,
                    aoi_revisit_time_hr = AOI_REVISIT_TIME_HR
                )
                
                result = evaluate_config(config)
                results.append(result)

    # Write results to output.csv
    results_dicts = [asdict(r) for r in results]
    df = pd.json_normalize(results_dicts, sep='_')
    df.to_csv('output/model_output.csv')

    # Run R script to do analysis
    subprocess.call([r'Rscript', r'./r/analysis.R'], cwd=os.getcwd())

    sys.exit()


if __name__ == '__main__':
    main()



