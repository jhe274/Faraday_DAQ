from DSP475Gaussmeter.Lakeshore475 import LakeShore475
import time

gpib_address = "GPIB1::11::INSTR"

def test_lakeshore_475():
    """Test communication with the LakeShore 475 Gaussmeter."""
    try:
        gaussmeter = LakeShore475(gpib_address)
        
        # Run a self-test
        test_result = gaussmeter.self_test()
        print(f"Self-Test Result: {test_result}")

        print("\n=== Clearing Interface ===")
        gaussmeter.clear_interface()

        print("\n=== Resetting Instrument ===")
        reset_response = gaussmeter.reset()
        print(f"Reset Response: {reset_response}")

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

        print(f'The current trigger state is: {gaussmeter.trigger}')

        # Start logging
        print("\n=== Starting Data Logging for 2 Seconds ===")
        gaussmeter.data_log(True)
        time.sleep(2)
        gaussmeter.data_log(False)
        print("Data logging stopped.")

        # Get the number of points stored
        print("\n=== Checking Data Buffer Size ===")
        num_points = gaussmeter.data_log_num_points()
        print(f"Data Points in Buffer: {num_points}")

        # Retrieve and print data
        print("\n=== Retrieving Logged Data ===")
        logged_data = gaussmeter.get_log_data(num_points=1024)
        print(f"Logged Data: {logged_data}")

        # Testing high-speed binary output
        print("\n=== Testing High-Speed Binary Data Retrieval ===")
        fast_data = gaussmeter.read_fast_data(num_readings=20)
        print(f"Fast Data: {fast_data}")

        print("\n=== Test Completed Successfully ===")

    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_lakeshore_475()


