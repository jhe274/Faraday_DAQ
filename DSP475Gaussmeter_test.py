from DSP475Gaussmeter.Lakeshore475 import LakeShore475
import time

gpib_address = "GPIB1::11::INSTR"
def test_lakeshore_475():
    """Test communication with the LakeShore 475 Gaussmeter."""
    try:
        gaussmeter = LakeShore475(gpib_address)
        gaussmeter.clear_interface()
        gaussmeter.reset()

        # Auto range
        gaussmeter.auto(1)
        print(f"Auto Range: {gaussmeter.get_auto()}")

        # Read current field value
        field_value = gaussmeter.read_field()
        print(f"Current Magnetic Field: {field_value} {gaussmeter.get_units()}")

        # # Change measurement unit to Gauss...")
        # gaussmeter.set_units("Gauss")
        # print(f"Updated Units: {gaussmeter.get_units()}")

        # Change measurement mode to DC
        print("Setting measurement mode to DC...")
        gaussmeter.set_mode("DC", "5 digits", "wide band", "periodic", "positive")
        print(f"Current Mode: {gaussmeter.get_mode()}")

        # Read probe temperature
        temperature = gaussmeter.get_temperature()
        print(f"Probe Temperature: {temperature} °C")

        # Get control parameters
        print("Fetching control parameters...")
        control_params = gaussmeter.get_control_params()
        print(f"Control Parameters: {control_params}")

        # Set logging rate to 10 readings per second
        print("Setting logging rate to 10 readings per second...")
        gaussmeter.set_logging_rate(10)

        # print("The current setpoint is: ", gaussmeter.get_setpoint())

        # Start logging
        print("Starting data logging for 2 seconds...")
        gaussmeter.data_log(1)
        time.sleep(2)
        gaussmeter.data_log(0)
        print("Data logging stopped.")

        # Retrieve and print data
        print("Retrieving logged data...")
        logged_data = gaussmeter.get_log_data(num_points=10)
        print(f"Logged Data: {logged_data}")

        # print("The data number of points is: ", gaussmeter.data_log_num_points())
        # gaussmeter.data_log(1)
        # # Test high-speed binary output
        # print("Testing high-speed binary data retrieval...")
        # fast_data = gaussmeter.read_fast_data(num_readings=10)
        # print(f"Fast Data: {fast_data}")

    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_lakeshore_475()

