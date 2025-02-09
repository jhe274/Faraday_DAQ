import os, datetime, sys, datetime
from time import time, perf_counter, sleep, strftime, localtime
import struct
import nidaqmx.system, nidaqmx.system.storage
from Lakeshore475DSPGaussmeter.Lakeshore475 import LakeShore475

gpib_address = "GPIB1::11::INSTR"
gaussmeter = LakeShore475(gpib_address)

trigger_period = 0.1 # [s]
trigger_NPeriods = 10 * 1
trigger_times = [(i*trigger_period) for i in range(trigger_NPeriods)]
MeasureDuration = trigger_NPeriods * trigger_period                    # [s]

dir_path = os.path.join(os.getcwd(), 'Faraday_rotation_measurements')
K_vapor = os.path.join(dir_path, 'K_vapor_cell')
Gaussmeter_path = os.path.join(K_vapor, 'Gaussmeter_data')

def measure():
    i = 0
    timestamps, fields, temps = [], [], []
    print("\n=============== Measurement Initiated ===============")
    start_time = time()
    while i < trigger_NPeriods:
        if i == 0:
            t0 = perf_counter()
        while perf_counter() - t0 < trigger_times[i]:
            pass
        fields.append(gaussmeter.field)
        temps.append(gaussmeter.temperature)
        t1 = perf_counter()
        while perf_counter() - t1 < (trigger_period/2):
            pass
        i = i + 1
        print(f"\rTime remaining:          {int(MeasureDuration-i*trigger_period):4d}", 's', end='')
    sleep(trigger_period / 2) 
    elap_time = perf_counter() - t0
    print("\n=============== Measurement Completed ===============")
    timestamp = [start_time + time for time in trigger_times]
    for j in range(trigger_NPeriods):
        formatted_timestamp = strftime("%Y-%m-%dT%H:%M:%S.", localtime(timestamp[j])) + f"{timestamp[j] % 1:.3f}".split(".")[1]
        timestamps.append(formatted_timestamp)

    print("Total time elapsed:", elap_time)
    return start_time, elap_time, timestamps, fields, temps

def save_data(path, filename, timestamps, fields, temps):
        # Generate file path with unique naming
        folder_name = datetime.datetime.now().strftime("%m-%d-%Y")
        folder_path = os.path.join(path, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        counter = 1
        original_filename = filename
        while os.path.isfile(os.path.join(folder_path, filename)):
            filename = f"{original_filename.split('.')[0]}_{counter}.csv"
            counter += 1

        file_path = os.path.join(folder_path, filename)

        try:
            with open(file_path, "w") as log:
                header = "Timestamp,Magnetic flux density (G),Temperature (°C)\n"
                log.write(header)
                for timestamp,field,temp in zip(timestamps,fields,temps):
                    log.write(f"{timestamp},{field},{temp}\n")

            print(f"Successfully saved {len(timestamps)} measurements to {file_path}.")
        except Exception as e:
            print(f"Error saving data: {e}")
    
def test_lakeshore_475():
    """Test communication with the LakeShore 475 Gaussmeter."""
    try:
        gaussmeter = LakeShore475(gpib_address)
        
        # Run a self-test
        test_result = gaussmeter.self_test()
        print(f"Self-Test Result: {test_result}")

        # Enable Auto Range
        print("\n=== Enabling Auto Range ===")
        gaussmeter.auto = True
        print(f"Auto Range: {gaussmeter.auto}")

        print("\n=== Setting Unit to Gauss ===")
        gaussmeter.units = 'Gauss'
        print(f"Current Units: {gaussmeter.units}")

        # Read current field value
        print("\n=== Reading Magnetic Field ===")
        print(f"Current Magnetic Field: {gaussmeter.field} {gaussmeter.units}")

        # Change measurement mode to DC
        print("\n=== Setting Measurement Mode to DC ===")
        gaussmeter.set_mode("DC", "5 digits", "wide band", "periodic", "positive")
        print(f"Current Mode: {gaussmeter.mode}")

        # Read probe temperature
        print("\n=== Reading Probe Temperature ===")
        print(f"Probe Temperature: {gaussmeter.temperature} {gaussmeter.temperature_units}")

        # Get control parameters
        print("\n=== Fetching Control Parameters ===")
        control_params = gaussmeter.control_params
        print(f"Control Parameters: {control_params}")

        # Set logging rate to 10 readings per second
        print("\n=== Setting Logging Rate to 10 Hz ===")
        gaussmeter.logging_rate = 10
        print(f"Logging Rate: {gaussmeter.logging_rate} Hz")

        # Read the current setpoint
        print("\n=== Checking Field Setpoint ===")
        print(f"The current setpoint is: {gaussmeter.setpoint}")
        
        # # Start logging
        # print("\n=== Starting Data Logging for 1 Seconds ===")
        # gaussmeter.data_log(True)
        # sleep(MeasureDuration)
        # gaussmeter.data_log(False)
        # print("Data logging stopped.")

        # # Get the number of points stored
        # print("\n=== Checking Data Buffer Size ===")
        # num_points = gaussmeter.data_log_num_points()
        # print(f"Data Points in Buffer: {num_points}")

        # # Retrieve and print data
        # print("\n=== Retrieving Logged Data ===")
        # logged_data = gaussmeter.get_log_data(num_points=10)
        # print(f"Logged Data: {logged_data}")

        # Testing high-speed binary output
        """
        The returned results is repetitive and not refreshing,
        the instrument seemed to be frozen after the command was sent.
        """
        # print("\n=== Testing High-Speed Binary Data Retrieval ===")
        # fast_data = gaussmeter.read_fast_data(num_readings=10)
        # gaussmeter.data_log(False)
        # print(f"Fast Data: {fast_data}")

        print("\n=== Test Completed Successfully ===")

    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    start_time, elap_time, timestamps, fields, temps = measure()
    # save_data(Gaussmeter_path, f"Gaussmeter_{datetime.now().strftime('%Y-%m-%d')}.csv", timestamps, fields, temps)
    test_lakeshore_475()


