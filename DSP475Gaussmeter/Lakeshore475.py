import pyvisa
import struct
import time

class LakeShore475:
    """Class for controlling the LakeShore 475 DSP Gaussmeter via GPIB."""

    def __init__(self, gpib_address: str):
        """
        Initialize the GPIB connection to the instrument.
        :param gpib_address: GPIB address string
        """
        self.rm = pyvisa.ResourceManager()
        self.device = self.rm.open_resource(gpib_address)
        self.dev_addr = gpib_address
        self.device.timeout = 5000  # Timeout in milliseconds
        print(f"Connected to: {self.query('*IDN?')}")

    def write(self, command):
        """Send a command to the instrument."""
        self.device.write(command)

    def query(self, command):
        """Send a query command and return the response."""
        return self.device.query(command).strip()
    
    def clear_interface(self):
        """Clears the instrument interface."""
        return self.write("*CLS")
    
    def reset(self):
        """Resets the instrument."""
        return self.write("*RST")
    
    @staticmethod
    def validate_input(value, valid_values, error_message):
        """Validates if a value is within allowed values."""
        if value not in valid_values:
            raise ValueError(error_message)

    def auto(self, value: bool):
        """Initiates a auto range command."""
        return self.write(f"AUTO {value}")
    
    def get_auto(self):
        """Gets the current auto range setting."""
        if self.query("AUTO?") == "1":
            return "On"
        else:
            return "Off"

    def read_field(self):
        """Reads the magnetic field measurement in the currently set units."""
        return float(self.query("RDGFIELD?"))

    def get_units(self):
        """Gets the currently set field measurement units."""
        units = {
            "1": "Gauss",
            "2": "Tesla",
            "3": "Oersted",
            "4": "A/m"
        }
        return units.get(self.query("UNIT?"), "Unknown")

    def set_units(self, unit):
        """Sets the field measurement units."""
        unit_map = {
            "Gauss": "1",
            "Tesla": "2",
            "Oersted": "3",
            "A/m": "4"
        }
        if unit in unit_map:
            self.write(f"UNIT {unit_map[unit]}")
        else:
            raise ValueError("Invalid unit. Choose from: Gauss, Tesla, Oersted, A/m.")

    def get_mode(self):
        """Gets the current measurement mode (DC, RMS, or Peak)."""
        modes = {"1": "DC", "2": "RMS", "3": "Peak"}
        return self.query("RDGMODE?")

    def set_mode(self, m_mode, resolution, filter, p_mode, p_disp):
        """Sets the measurement mode (DC, RMS, or Peak)."""

        # Define valid options as lookup dictionaries
        measurement_modes = {"DC": "1", "RMS": "2", "Peak": "3"}
        dc_resolution = {"3 digits": "1", "4 digits": "2", "5 digits": "3"}
        rms_filter_mode = {"wide band": "1", "narrow band": "2", "low pass": "3"}
        peak_mode = {"periodic": "1", "pulse": "2"}
        peak_disp = {"positive": "1", "negative": "2", "both": "3"}

        # Validate all inputs first
        try:
            c1 = measurement_modes[m_mode]
            c2 = dc_resolution[resolution]
            c3 = rms_filter_mode[filter]
            c4 = peak_mode[p_mode]
            c5 = peak_disp[p_disp]
        except KeyError as e:
            raise ValueError(f"Invalid input: {e}. Please check your arguments.")

        return self.write(f"RDGMODE {c1}{c2}{c3}{c4}{c5}")

    def get_temperature(self):
        """Reads the probe temperature in Celsius."""
        return float(self.query("RDGTEMP?"))

    def set_temperature_units(self, unit):
        """Sets the temperature measurement units."""
        temp_units = {"Celsius": "1", "Kelvin": "2"}
        if unit in temp_units:
            self.write(f"TUNIT {temp_units[unit]}")
        else:
            raise ValueError("Invalid unit. Choose from: Celsius, Kelvin.")
    
    def field_control_mode(self, mode: bool):
        """Enables or disables field control mode."""
        return self.write(f"CMODE {mode}")
    
    def get_field_control_mode(self):
        """Gets the current field control mode."""
        if self.query("CMODE?") == "1":
            return "Closed Loop PI"
        elif self.query("CMODE?") == "0":
            return "Off"

    def get_setpoint(self):
        """Gets the current setpoint for field control."""
        return float(self.query("CSETP?"))

    def set_setpoint(self, value):
        """Sets the field setpoint."""
        self.write(f"CSETP {value}")

    def get_control_params(self):
        """Gets the control parameters (P, I, ramp rate, control slope limit)."""
        response = self.query("CPARAM?").split(',')
        return {
            "P": float(response[0]),
            "I": float(response[1]),
            "Ramp Rate": float(response[2]),
            "Control Slope Limit": float(response[3])
        }

    def set_control_params(self, p, i, ramp_rate, slope_limit):
        """Sets the control parameters (P, I, ramp rate, control slope limit)."""
        self.write(f"CPARAM {p},{i},{ramp_rate},{slope_limit}")

    def logging_rate(self):
        """Returns the data logging rate."""
        return self.query("DLOGSET?")

    def set_logging_rate(self, rate):
        """
        Sets the data logging rate.
        Valid rates: {1, 10, 30, 100, 200, 400, 800, 1000} readings per second.
        """
        rate_map = {1: 1, 10: 2, 30: 3, 100: 4, 200: 5, 400: 6, 800: 7, 1000: 8}
        if rate in rate_map:
            self.write(f"DLOGSET {rate_map[rate]}")
        else:
            raise ValueError("Invalid rate. Choose from {1, 10, 30, 100, 200, 400, 800, 1000} Hz.")

    def flush_buffer(self):
        """Flushes the data logging buffer."""
        return self.write("TRIG")
    
    def data_log(self, value: bool):
        """
        Data logging command.
        0 =  stop, 1 = start.
        """
        if value == 1:
            return self.write(f"DLOG {value}")
        elif value == 0:
            return self.write(f"DLOG {value}")

    def data_log_num_points(self):
        """Returns the number of data points stored in the Datalog buffer."""
        return self.query("DLOGNUM?")
    
    def get_log_data(self, num_points=10):
        """
        Retrieves stored data from the buffer.
        :param num_points: Number of data points to read (max 1024).
        """
        data = []
        for i in range(1, num_points + 1):
            try:
                reading = float(self.query(f"DLOGRDG? {i}"))
                data.append(reading)
            except Exception as e:
                print(f"Error reading point {i}: {e}")
        return data

    def read_fast_data(self, num_readings):
        """
        Reads high-speed binary data using RDGFAST? command.
        Returns a list of field readings.
        """
        self.device.write(f"RDGFAST? {num_readings}")
        time.sleep(0.05)  # Ensure the data is received fully
        raw_data = self.device.read_raw()

        print(f"Raw Binary Data: {raw_data.hex()}")  # Debugging: Print raw binary response

        # Correct header size (from debug, seems to be 2 bytes)
        header_size = 2  
        num_bytes = len(raw_data) - header_size
        num_floats = num_bytes // 4  # Each reading is a 4-byte IEEE-754 float

        print(f"Total Bytes Received: {len(raw_data)}, Expected Readings: {num_readings}, Parsed Floats: {num_floats}")

        if num_floats != num_readings:
            print(f"Warning: Expected {num_readings} readings, but got {num_floats}")

        readings = []
        for i in range(num_floats):
            start_idx = header_size + (i * 4)
            end_idx = start_idx + 4
            float_bytes = raw_data[start_idx:end_idx]

            # Debug: Print extracted bytes for verification
            print(f"Reading {i}: {float_bytes.hex()}")

            # Try both big-endian and little-endian and see which works
            try:
                reading = struct.unpack(">f", float_bytes)[0]  # Big-endian IEEE-754
            except struct.error:
                reading = struct.unpack("<f", float_bytes)[0]  # Little-endian if big-endian fails

            readings.append(reading)

        print(f"Parsed Readings: {readings}")  # Debugging: Print extracted readings
        return readings

    def get_trigger(self):
        """Gets the current trigger out state."""
        return self.query("TRIG?")
    
    def trigger(self, value):
        """
        Hardware trigger out command.
        0 = Off, 1 = On.
        """
        if value == 1:
            return self.write(f"TRIG {value}")
        elif value == 0:
            return self.write(f"TRIG {value}")
    
    def __del__(self):
        """Ensures the connection is closed when the object is deleted."""
        try:
            self.device.close()
            print(f"Connection to {self.dev_addr} closed.")
        except Exception as e:
            print(f"Error closing connection: {e}")

if __name__ == "__main__":
    ls475 = LakeShore475()
    # LakeShore475(gpib_address="GPIB1::XX::INSTR") # Replace XX with the actual GPIB address of the instrument