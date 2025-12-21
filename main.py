import lib
import csv
import subprocess
import sys

# result = lib.evaluate_aircraft(lib.Aircraft(5, 0.9, lib.Sensor.Low), lib.AOI_LENGTH_BY_WIDTH)
# print(result)

# result = evaluate_aircraft(Aircraft(5, 0.9, Sensor.Med), AOI_LENGTH_BY_WIDTH)
# print(result)

# result = evaluate_aircraft(Aircraft(5, 0.9, Sensor['High']), AOI_LENGTH_BY_WIDTH)
# print(result)


# ac = lib.Aircraft(5, 0.5, lib.Sensor['Low'])

# sys.exit()


# altitudes = range(15,20,5)
# machs     = [0.6]
# sensors   = [lib.Sensor['Med']]
altitudes = range(5,30,5)
machs     = [0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
sensors   = [lib.Sensor['Low'], lib.Sensor['Med'], lib.Sensor['High']]

results = []
for altitude in altitudes:
    for mach in machs:
        for sensor in sensors:
            print('-------')
            print(f'alt: {altitude}, mach: {mach}, sensor: {sensor.name}')
            
            # lib.evaluate_aircraft(lib.Aircraft(altitude, mach, sensor), lib.AOI_LENGTH_BY_WIDTH)
            result = lib.evaluate_aircraft(lib.Aircraft(altitude, mach, sensor), lib.AOI_LENGTH_BY_WIDTH)
            results.append(result)

# sys.exit()


# fieldnames = ['altitude', 'mach', 'sensor', 'flight_time', 'ac_endurance', 'ac_cost']
# fieldnames = ['altitude', 'mach', 'sensor', 'flight_time', 'ac_endurance', 'ac_cost']
fieldnames = results[0].keys()

with open('output.csv', 'w', newline='') as outfile:
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)



subprocess.call([r'Rscript', r'./plots.R'])