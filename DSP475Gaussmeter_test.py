from DSP475Gaussmeter.Lakeshore475 import LakeShore475
from time import time, perf_counter, sleep

gpib_address = "GPIB1::11::INSTR"
period = 1 # [s]
NPeriods = 10
times_array = [(i*period) for i in range(NPeriods)]
MeasureDuration = NPeriods*period

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
        
        # Start logging
        print("\n=== Starting Data Logging for 1 Seconds ===")
        gaussmeter.data_log(True)
        i = 0
        while i < NPeriods:
                if i == 0:
                    t0 = perf_counter()
                while perf_counter() - t0 < times_array[i]:
                    pass
                t1 = perf_counter()
                while perf_counter() - t1 < (period/2):
                    pass

                i = i + 1
                print(f"\rTime remaining:          {int(MeasureDuration-i*period):4d}", 's', end='')

        sleep(period / 2)                                                     # Wait until the end of the last half period   
        gaussmeter.data_log(False)
        print("Data logging stopped.")

        # Get the number of points stored
        print("\n=== Checking Data Buffer Size ===")
        num_points = gaussmeter.data_log_num_points()
        print(f"Data Points in Buffer: {num_points}")

        # Retrieve and print data
        print("\n=== Retrieving Logged Data ===")
        logged_data = gaussmeter.get_log_data(num_points=10)
        print(f"Logged Data: {logged_data}")

        # Testing high-speed binary output
        """
        The returned results is repetitive and not refreshing,
        the instrument seemed to be freezed after the command was sent.
        """
        # print("\n=== Testing High-Speed Binary Data Retrieval ===")
        # fast_data = gaussmeter.read_fast_data(num_readings=10)
        # gaussmeter.data_log(False)
        # print(f"Fast Data: {fast_data}")

        print("\n=== Test Completed Successfully ===")

    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_lakeshore_475()


