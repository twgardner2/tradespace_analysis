import csv
import subprocess
import sys
from constants import *
from lib import validate_config, determine_sensor_performance


# Assumptions/givens
AOI = AOI(
    length  = 100_000, # meters
    width   = 100_000, # meters
    ingress = 100_000, # meters
    egress  = 100_000 # meters
)

# Design parameters

# JOHNSON_CRITERIA = 2 # Recognize
JOHNSON_CRITERIA = 8 # Identify
# JOHNSON_CRITERIA = 13 # Classify
# JOHNSON_CRITERIA = 4 # Testing


TARGET = DesignTarget(
    type      = "Frigate",
    dims      = (150, 40), # m, (horizontal, vertical)
    max_speed = 25 # knots
)

SENSOR_ASSUMPTIONS = {
    Sensor.LOW: SensorAssumption(
        fov_deg     = (15, 15),
        resolution  = (640, 480),
        johnson_req = JOHNSON_CRITERIA,
        cost        = 0.05
    ),
    Sensor.MED: SensorAssumption(
        fov_deg     = (30, 30),
        resolution  = (1024, 768),
        johnson_req = JOHNSON_CRITERIA,
        cost        = 1
    ),
    Sensor.HIGH: SensorAssumption(
        fov_deg     = (60, 60),
        resolution  = (1920, 1080),
        johnson_req = JOHNSON_CRITERIA,
        cost        = 10
    ),
}

# def evaluate_aircraft(ac: Aircraft, aoi: tuple[float, float]) -> tuple[float, float, float]:
def evaluate_config(config: Config) -> tuple[float, float, float]:
    # Calc length of each leg - how much of the length of the box do we have to 
    # fly to detect target at the edge. Limiting case is a target showing an aspect
    # where the height is the largest dimension we see

    result = ModelResult(config=config)
    # result.config = config

    config_valid, reason = validate_config(config)
    if not config_valid:
        result.valid = config_valid
        result.reason = reason
        return result 

    

    # Instantiate the aircraft
    ac = Aircraft(config.altitude_kft, config.mach, config.sensor, config.sensor_assumption)

    # Determine sensor performance
    result.sensor_performance = determine_sensor_performance(config.sensor_assumption, config.target)

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
    # result = lib.evaluate_aircraft(lib.Aircraft(5, 0.9, lib.Sensor.Low), lib.AOI_LENGTH_BY_WIDTH)
    # print(result)

    # altitudes = range(15,20,5)
    # machs     = [0.6]
    # sensors   = [lib.Sensor['Med']]

    altitudes = range(5,30,5)
    altitudes = [100]
    machs     = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    sensors   = [Sensor['LOW'], Sensor['MED'], Sensor['HIGH']]

    results = []
    for altitude in altitudes:
        for mach in machs:
            for sensor in sensors:
                config = Config(
                    target            = TARGET,
                    altitude_kft      = altitude,
                    mach              = mach,
                    sensor            = sensor,
                    sensor_assumption = SENSOR_ASSUMPTIONS[sensor],
                    aoi               = AOI
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



