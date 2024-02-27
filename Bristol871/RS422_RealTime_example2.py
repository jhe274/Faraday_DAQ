# Bristol 871 sample code
#
# This script will open a connection to the Bristol 871 device on COM port 10,
# read 1,000 measurements, and write them in CSV format to the `output_file`.
#
# This code is released into the public domain. See the "License" section of
# README.md for more information.


from __future__ import print_function
from RS422_RealTime_example1 import Bristol871
from sys import exit
import os


# Configuration options

port_number = 'COM6'
cwd = os.getcwd()
dir_path = os.path.join(cwd, 'Faraday rotation measurements', 'Data_acquisition', 'FR_DAQ', 'Bristol871')
output_file = os.path.join(dir_path, 'test_log.csv')

# Connect to the instrument

try:
	device = Bristol871(port_number)
except Exception as e:
	print('Could not connect to the instrument: {}'.format(e))
	exit(1)

print('Connected to the instrument')

# Read the specified number of measurements

with open(output_file, 'w') as log:
	measurements = 0
	while measurements < 300:
		wavelength, power, status, scan_index = device.get_measurement()
		log.write('{},{},{:f},{:3f}\n'.format(scan_index, status, wavelength, power))

		measurements += 1
		if measurements % 100 == 0:
			print('Read {} measurements'.format(measurements))

print('Done.')
