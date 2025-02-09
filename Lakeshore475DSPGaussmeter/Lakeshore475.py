import pyvisa
import struct
import time

# External Dictionary Mappings
MEASUREMENT_MODES = {"DC": "1", "RMS": "2", "Peak": "3"}
DC_RESOLUTION = {"3 digits": "1", "4 digits": "2", "5 digits": "3"}
RMS_FILTER_MODE = {"wide band": "1", "narrow band": "2", "low pass": "3"}
PEAK_MODE = {"periodic": "1", "pulse": "2"}
PEAK_DISPLAY = {"positive": "1", "negative": "2", "both": "3"}
FIELD_UNITS = {"1": "Gauss", "2": "Tesla", "3": "Oersted", "4": "A/m"}
TEMP_UNITS = {"1": "Celsius", "2": "Kelvin"}
LOGGING_RATES = {"1": 1, "2": 10, "3": 30, "4": 100, "5": 200, "6": 400, "7": 800, "8": 1000}

class LakeShore475:
    """Class for controlling the LakeShore 475 DSP Gaussmeter via GPIB."""

    def __init__(self, gpib_address: str):
        """
        Initialize the GPIB connection to the instrument.
        :param gpib_address: GPIB address string
        """
        self.rm = pyvisa.ResourceManager()
        self.device = self.rm.open_resource(gpib_address)
        self.device.timeout = 5000  # Timeout in milliseconds
        print(f"Connected to: {self.query('*IDN?')}")

    def self_test(self):
        """Runs a self-test query and returns the result."""
        response = self.query("*TST?")
        return "No errors found" if response == "0" else "Errors detected"

    def write(self, command: str):
        """Send a command to the instrument."""
        self.device.write(command)

    def query(self, command: str):
        """Send a query command and return the response."""
        return self.device.query(command).strip()

    def clear_interface(self):
        """Clears the instrument interface."""
        self.write("*CLS")

    def reset(self):
        """Resets the instrument and verifies it has restarted."""
        self.write("*RST")
        time.sleep(1)  # Allow time for reset
        return self.query("*IDN?")  # Verify reset

    @staticmethod
    def validate_input(value, valid_dict, error_message):
        """Validates if a value is in the allowed dictionary."""
        if value not in valid_dict:
            raise ValueError(error_message)

    @property
    def auto(self):
        """Gets the current auto range setting."""
        return "On" if self.query("AUTO?") == "1" else "Off"

    @auto.setter
    def auto(self, value: bool):
        """Sets auto range."""
        self.write(f"AUTO {int(value)}")

    @property
    def field(self):
        """Reads the magnetic field measurement in the currently set units."""
        return float(self.query("RDGFIELD?"))

    @property
    def units(self):
        """Gets the currently set field measurement units."""
        unit_code = self.query("UNIT?")
        return FIELD_UNITS.get(unit_code, "Unknown")

    @units.setter
    def units(self, unit: str):
        """Sets the field measurement units."""
        self.validate_input(unit, FIELD_UNITS.values(), "Invalid unit. Choose from: Gauss, Tesla, Oersted, A/m.")
        self.write(f"UNIT {list(FIELD_UNITS.keys())[list(FIELD_UNITS.values()).index(unit)]}")

    @property
    def mode(self):
        """Gets the current measurement mode."""
        return self.query("RDGMODE?")

    def set_mode(self, m_mode, resolution, filter, p_mode, p_disp):
        """Sets the measurement mode."""
        mode_settings = {
            "m_mode": (m_mode, MEASUREMENT_MODES),
            "resolution": (resolution, DC_RESOLUTION),
            "filter": (filter, RMS_FILTER_MODE),
            "p_mode": (p_mode, PEAK_MODE),
            "p_disp": (p_disp, PEAK_DISPLAY),
        }

        try:
            cmd_values = "".join(value_dict[value] for value, value_dict in mode_settings.values())
        except KeyError as e:
            raise ValueError(f"Invalid input: {e}. Please check your arguments.")

        self.write(f"RDGMODE {cmd_values}")

    @property
    def temperature_units(self):
        """Gets the temperature measurement unit (Celsius or Kelvin)."""
        temp_units = {"1": "Celsius", "2": "Kelvin"}
        return temp_units.get(self.query("TUNIT?"), "Unknown")

    @temperature_units.setter
    def temperature_units(self, unit: str):
        """Sets the temperature measurement unit."""
        self.validate_input(unit, TEMP_UNITS.values(), "Invalid temperature unit. Choose from: Celsius, Kelvin.")
        self.write(f"TUNIT {list(TEMP_UNITS.keys())[list(TEMP_UNITS.values()).index(unit)]}")

    @property
    def temperature(self):
        """Reads the probe temperature in Celsius."""
        return float(self.query("RDGTEMP?"))

    @property
    def field_control_mode(self):
        """Gets the current field control mode."""
        return "Closed Loop PI" if self.query("CMODE?") == "1" else "Off"

    @field_control_mode.setter
    def field_control_mode(self, mode: bool):
        """Sets field control mode."""
        self.write(f"CMODE {int(mode)}")

    @property
    def setpoint(self):
        """Gets the current setpoint for field control."""
        return float(self.query("CSETP?"))

    @setpoint.setter
    def setpoint(self, value):
        """Sets the field setpoint."""
        self.write(f"CSETP {value}")

    @property
    def control_params(self):
        """Gets the control parameters."""
        response = self.query("CPARAM?").split(',')
        return {"P": float(response[0]), "I": float(response[1]), "Ramp Rate": float(response[2]), "Control Slope Limit": float(response[3])}

    def set_control_params(self, p, i, ramp_rate, slope_limit):
        """Sets the control parameters."""
        self.write(f"CPARAM {p},{i},{ramp_rate},{slope_limit}")

    @property
    def logging_rate(self):
        """Returns the data logging rate in Hz."""
        response = self.query("DLOGSET?")
        return LOGGING_RATES.get(response, "Unknown")

    @logging_rate.setter
    def logging_rate(self, rate):
        """Sets the data logging rate."""
        self.validate_input(rate, LOGGING_RATES.values(), "Invalid rate. Choose from valid rates.")
        self.write(f"DLOGSET {list(LOGGING_RATES.keys())[list(LOGGING_RATES.values()).index(rate)]}")

    def trigger_event(self):
        """
        Trigger event.
        Starts the datalog capture mode. This command is equivalent in operation to the DLOG command.
        """
        self.write("*TRG")

    def data_log(self, value: bool):
        """Starts or stops data logging."""
        self.write(f"DLOG {int(value)}")

    def data_log_num_points(self):
        """Returns the number of data points stored in the Datalog buffer."""
        return int(self.query("DLOGNUM?"))

    def get_log_data(self, num_points: int):
        """Retrieves stored data from the buffer."""
        return [float(self.query(f"DLOGRDG? {i}")) for i in range(1, num_points + 1)]

    def read_fast_data(self, num_readings):
        """Reads high-speed binary data using RDGFAST? command."""
        self.device.write(f"RDGFAST? {num_readings}")
        raw_data = self.device.read_raw()

        print(f"Raw Binary Data: {raw_data.hex()}")  # Debugging output

        header_size = 2  
        num_bytes = len(raw_data) - header_size
        num_floats = num_bytes // 4  

        if num_floats != num_readings:
            print(f"Warning: Expected {num_readings} readings, but got {num_floats}")

        return [struct.unpack(">f", raw_data[header_size + (i * 4):header_size + (i + 1) * 4])[0] for i in range(num_floats)]
    
    @property
    def trigger(self):
        """Gets the current trigger out state."""
        return "On" if self.query("TRIG?") == "1" else "Off"

    @trigger.setter
    def trigger(self, value: bool):
        """Specifies hardware trigger off or on."""
        self.write(f"TRIG {int(value)}")

    def __del__(self):
        """Ensures the connection is closed when the object is deleted."""
        try:
            self.device.close()
            print(f"Connection closed.")
        except Exception as e:
            print(f"Error closing connection: {e}")

if __name__ == "__main__":
    ls475 = LakeShore475()
    # LakeShore475(gpib_address="GPIB1::XX::INSTR") # Replace XX with the actual GPIB address of the instrument