from telnetlib import Telnet
from serial import Serial
import struct
import numpy as np
import os, datetime
from time import strftime, localtime

class Bristol871(object):
    """Class representing a Bristol 871 wavelength meter.

    Attributes:
        serial_port (Serial): Serial connection instance.
        tn (Telnet): Telnet connection instance.
        dev_addr (str): Device IP address.
    """

    START_TOKEN = 0x7E
    ESCAPE_TOKEN = 0x7D
    ESCAPE_XOR = 0x20

    def __init__(self, port_number: str, ip_addr: str = "10.199.199.1", quiet: bool = False):
        """Initializes the Bristol 871 device with Telnet and Serial connections."""
        self.serial_port = Serial(port=port_number, baudrate=921600, timeout=5)
        self.dev_addr = ip_addr
        self.tn = Telnet(ip_addr, 23)

        try:
            # Flush telnet buffer on initialization
            [self.readline() for _ in range(8)]

            if not quiet:
                self.tn.write(b"*IDN?\r\n")
                print(self.readline(), "\n")
        except Exception as e:
            print(f"Error initializing Bristol 871: {e}")
            self.__del__()
    
    def readline(self) -> str:
        """Reads a line from the Telnet buffer."""
        response = self.tn.read_until(b"\n", timeout=3).decode("utf-8")
        if not response:
            raise self.EmptyBuffer()
        return response.strip()
    
    def __del__(self):
        """Ensures the connection is closed when the object is deleted."""
        try:
            self.tn.close()
            print(f"\nConnection to {self.dev_addr} closed.")
        except Exception as e:
            print(f"Error closing connection: {e}")
    
    class EmptyBuffer(Exception):
        """Exception raised when attempting to read from an empty Telnet buffer."""
        def __init__(self, message="Telnet buffer was empty, read timed out.") -> None:
            super().__init__(message)

    def write(self, message: str) -> None:
        """Sends WRITE command to the Bristol 871 device."""
        self.tn.write(f'{message}\r\n'.encode('utf-8'))

    def query(self, message: str) -> str:
        """Sends QUERY command and reads the response."""
        self.write(message)
        return self.readline()
    
    @staticmethod
    def validate_input(value, valid_values, error_message):
        """Validates if a value is within allowed values."""
        if value not in valid_values:
            raise ValueError(error_message)
    
    def instr(self, command: str) -> str:
        """Validates and returns a valid instrument command."""
        commands = {"MEAS", "READ", "FETC"}
        self.validate_input(command, commands, f"Invalid measurement instruction: {commands}")
        return command

    def all(self, command: str) -> str:
        """
        Returns the scan index, the instrument status, an input laser reading, and a power
        reading for the highest measured peak.
        """
        # print('Scan index:           ', self.query(f':{self.instr(command)}:ALL?').split(',')[0])
        # print('Instrument status:   ', self.query(f':{self.instr(command)}:ALL?').split(',')[1])
        # print('Laser reading:       ', self.query(f':{self.instr(command)}:ALL?').split(',')[2])
        # print('Power:               ', self.query(f':{self.instr(command)}:ALL?').split(',')[3])

        return self.query(f':{self.instr(command)}:ALL?')
    
    def environment(self, command: str) -> float:
        """
        Returns the instrument's internal temperature in degrees Celsius (ºC) and
        pressure in millimeters of mercury (mm Hg).
        """
        return self.query(f':{self.instr(command)}:ENV?')
    
    def frequency(self, command: str) -> float:
        """
        Returns an input laser reading in units of THz.
        """
        return float(self.query(f':{self.instr(command)}:FREQ?').strip())
    
    def power(self, command: str) -> float:
        """
        Queries a power reading in either mW (milliwatts) or dBm as specified by the
        :UNIT:POWer function.
        """
        return self.query(f':{self.instr(command)}:POW?')
    
    def wavelength(self, command: str) -> float:
        """
        Returns an input laser wavelength value in units of nm.
        """
        return float(self.query(f':{self.instr(command)}:WAV?').strip())
        
    def wavenumber(self, command: str) -> float:
        """
        Returns an input laser reading in units of cm^-1.
        """
        return float(self.query(f':{self.instr(command)}:WNUM?').strip())

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # CALCulate Subsystem
    #
    # The CALCulate subsystem is used to read and control the instrument's calculated
    # values. The instrument continuously updates delta values based on the specified
    # method desired. To retrieve CALCulate subsystem data, first choose a calculate
    # data type, and then perform a calculate query.
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def get_value(self, value: str):
        """
        Returns a calculated value based on the :DELTa:METHod setting.
        """
        values = {'POW', 'FREQ', 'WAV', 'WNUM'}
        self.validate_input(value, values, f'Input value must be one of {values}.')

        return self.query(f':CALC:DATA? {value}')
    
    def delta_method(self, value: str):
        """
        Sets the state of the method of the delta calculation to either STARt or MAXMin.
        """
        values = {'STAR', 'MAXM'}
        self.validate_input(value, values, f'Input value must be one of {values}.')
        self.write(f':CALC:DELT:METH {value}')

        return self.query(':CALC:DELT:METH?')
    
    def reset(self):
        """
        Resets the minimum, maximum, and start values to the current reading. Resets
        the deltas and drifts to zero, and sets the elapsed time to 00:00:00.
        """
        return self.write(':CALC:RES')

    def elap_time(self, value='?'):
        """
        Queries the elapsed time since the instrument was turned on or was reset using
        the CALC:RES command.
        """
        values = {'?', ':ELAP?'}
        self.validate_input(value, values, f'Input value must be one of {values}.')

        return self.query(f':CALC:TIM{value}')

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # MMEMory Subsystem
    #
    # The MMEMory subsystem controls the instruments buffer. As many as 1 million
    # measurements can be internally stored and retrieved.
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def buffer(self, command: str):
        commands = {'INIT', 'OPEN', 'CLOS', 'DATA?'}
        if command in commands:
            self.write(f':MMEM:{command}\r\n')
        else:
            self.validate_input(command, commands, f'Buffer instruction must be one of {commands}.')

    def get_buffer(self, path: str, filename: str, acq_time: float, timestamps: list):
        """
        Retrieves buffered data from the instrument and saves it as a CSV file.
        """
        self.buffer('CLOS')
        self.buffer('DATA?')
        print('\nRetrieving data from Bristol buffer...')
        print('Getting first character:', self.tn.rawq_getchar())

        # Extract the total number of bytes in the buffer
        num_bytes_char = int(self.tn.rawq_getchar())
        total_bytes = sum(int(self.tn.rawq_getchar()) * 10 ** (num_bytes_char - i - 1) for i in range(num_bytes_char))

        print("Total bytes:", total_bytes)
        num_samples = total_bytes // 20
        print("Number of Samples:", num_samples)
        print("Total time elapsed:", acq_time)
        print("Sample Rate:", num_samples / acq_time)

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

        # Retrieve and save data
        try:
            with open(file_path, "w") as log:
                log.write("Timestamp,Status,Wavelength,Intensity\n")
                for timestamp in timestamps:
                    raw_data = b"".join(self.tn.rawq_getchar() for _ in range(20))
                    wvl, pwr, status, _ = struct.unpack("<dfII", raw_data)
                    log.write(f"{timestamp},{str(status).zfill(5)},{wvl:.7f},{pwr:.3f}\n")

            print(f"Successfully saved {len(timestamps)} measurements from Bristol buffer.")
        except Exception as e:
            print(f"Error saving data: {e}")

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # SENSe Subsystem
    #
    # The SENSe subsystem allows changes in parameters that affect how the instrument makes
    # measurements.
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def average_count(self, value):
        """
        Sets/Queries the number of readings to be averaged.
        """
        values = range(2,129)
        if value in values:
            self.write(f':SENS:AVER:COUN {value}')                              # RST Value = 2
        else:
            self.validate_input(value, values, f'Input value must be one of {values}.')

        return self.query(':SENS:AVER:COUN?')
    
    def average_data(self, value):
        """
        Returns averaged wavelength or power data for the last N number of
        measurements. The value of N is set by :AVERage: COUNt command. If
        averaging is not turned on then the most recent data is returned.
        """
        values = {'POW', 'FREQ', 'WAV', 'WNUM'}
        if value not in values:
            self.validate_input(value, values, f'Input value must be one of {values}.')

        return self.query(f':SENS:AVER:DATA? {value}')
    
    def average_state(self, value):
        """
        Sets/Queries if data is currently being averaged.
        """
        values = {'OFF', 'ON'}
        if value not in values:
            self.validate_input(value, values, f'Input value must be one of {values}.')

        self.write(f':SENS:AVER:STAT {value}')

        return self.query(f':SENS:AVER:STAT?')
    def calib(self):
        """
        Initiates a calibration of the instrument.
        """
        return self.write(':SENS:CALI')
    
    def calib_method(self, value):
        """
        Sets/Queries the method of automatic calibration for the instrument to be OFF or
        on a specified TIME or TEMPerature interval. The time interval between automatic
        calibrations is set with the :SENSe:CALIbrate:TIME command and the
        temperature interval is set with the :SENSe:CALIbrate:TEMPerature command.
        """
        values = {'TIME', 'TEMP'}
        if value not in values:
            self.validate_input(value, values, f'Input value must be one of {values}.')
        else:
            self.write(f':SENS:CALI:METH {value}')                              # RST = TEMPerature

        return self.query(':SENS:CALI:METH?')
    
    def calib_temp(self, value):
        """
        Sets/Queries the minimum change in internal temperature that will trigger a
        calibration of the instrument. The change is specified in 1/10th°C increments so a
        value of 10 corresonds to a 1 °C change.
        """
        values = range(1,51)
        if self.query(':SENS:CALI:METH?') == 'TEMPerature':
            if value not in values:
                self.validate_input(value, values, f'Input value must be in the range{min(values), max(values)}.')
            else:
                self.write(f':SENS:CALI:TEMP {value}')                          # RST Value = 5
                print(f'Temperature delta =       {value / 10}°C.')
        else:
            raise ValueError('Calibration method incorrect.')

        return self.query(':SENS:CALI:TEMP?')

    def calib_timer(self, value):
        """
        Sets/Queries the time between automatic calibrations of the instrument. The time
        is specified in minutes.
        """
        values = range(5,1441)
        if self.query(':SENS:CALI:METH?') == 'TIME':
            if value not in values:
                self.validate_input(value, values, f'Input value must be in the range{min(values), max(values)}.')
            else:
                self.write(f':SENS:CALI:TIM {value}')                           # RST Value = 30
                print(f'Time delta is {value} min.')
        else:
            raise ValueError('Calibration method incorrect.')

        return self.query(':SENS:CALI:TIM?')
    
    def detector(self, value):
        """
        Sets/Queries whether the instrument is detecting a continuous wave (CW) or
        pulsed laser source. For a pulsed laser source, measurements without sufficient
        intensity on the detector are not reported.
        """
        values = {'CW', 'PULS'}
        if value not in values:
            self.validate_input(value, values, f'Input value must be one of {values}.')
        else:
            self.write(f":SENS:DET:FUNC {value}")                               # RST Value = CW

        return self.query(':SENS:DET:FUNC?')
    
    def auto_expo(self, value):
        """
        Sets/Queries the state of the Auto Exposure function. When Auto Exposure is
        turned on the instrument modifies the exposure time dynamically to maintain the
        optimal detector signal.
        """
        values = {'ON', 'OFF'}
        if value not in values:
            self.validate_input(value, values, f'Input value must be one of {values}.')
        else:
            self.write(f':SENS:EXP:AUTO {value}')                               # RST Value = ON

        return self.query(':SENS:EXP:AUTO?')
    
    def PID_error(self):
        """
        Queries the last PID output error, expressed in nanometers.
        """
        return self.query(':SENS:PID:ERR?')
    
    def PID_check(self):
        """
        Queries if the instrument has PID functionality.
        """
        return self.query(':SENS:PID:FUNC?')
    
    def set_PID(self, type, value):
        """
        Sets/Queries the specified PID constant for the PID calculation.
        """
        types = {'PROP', 'INT', 'DER'}
        values = np.arange(0, 50.1, .1)
        if type in types:
            if value in values:
                self.write(f':SENS:PID:LCON:{type} {str(value)}')
            else:
                self.validate_input(value, values, f'Input value must be in the range{min(values), max(values)}.')
        else:
            self.validate_input(type, types, f'Input value must be one of {types}.')
        
        return self.query(f':SENS:PID:LCON:{type}?')
    
    def PID_output(self):
        """
        Queries the last PID output voltage, expressed in volts
        """
        return self.query(':SENS:PID:OUT?')
    
    def PID_setpoint(self, setPoint: float = ''):
        """
        Sets/Queries the target wavelength of the PID calculation. All values expressed in
        nanometers. Range from (350 ... 14000).
        """
        values = range(350, 14001)
        if type(setPoint) == float:
            self.write(f':SENSe:PID:SPO {setPoint}')                            # RST Value = 1000
        else:
            self.validate_input(setPoint, values, f'Input value must be in the range{min(values), max(values)}.')

        return self.query(':SENSe:PID:SPO?')
    
    def PID_state(self, value):
        """
        Sets/Queries whether the PID calculation is enabled. If set to OFF the PID output
        voltage will be set to the default value defined by the SENSe:PID:VOLTage:DEFault command.
        """
        values = {'OFF', 'ON'}
        if value not in values:
            self.validate_input(value, values, f'Input value must be one of {values}.')
        else:
            self.write(f':SENS:PID:STAT {value}')                               # RST Value = OFF

        return self.query(':SENS:PID:STAT?')
    
    def PID_dafault(self, value):
        """
        Sets/Queries the voltage output when the PID calculation is disabled, expressed
        in volts.
        """
        values = np.arange(-5., 5.1, 0.1)
        if value in values:
            self.write(f':SENS:PID:VOLT:DEF {value}')                           # RST Value = -5.0
        else:
            self.validate_input(value, values, f'Input value must be in the range{min(values), max(values)}.')

        return self.query(':SENS:PID:VOLT:DEF?')
    
    def PID_max(self, value):
        """
        Sets/Queries the maximum output voltage for the PID calculation, expressed in
        volts. The instrument automatically limits this voltage to a maximum of 5.0 volts.
        """
        values = np.arange(.1, 5.1, .1)
        if value in values:
            self.write(f':SENS:PID:VOLT:MAX {value}')                           # RST Value = 5.0
        else:
            self.validate_input(value, values, f'Input value must be in the range{min(values), max(values)}.')

        return self.query(':SENS:PID:VOLT:MAX?')
    
    def PID_min(self, value):
        """
        Sets/Queries the minimum output voltage for the PID calculation, expressed in
        volts. The instrument automatically limits this voltage to a maximum of -5.0 volts.
        """
        values = np.arange(-5., .1, .1)
        if value in values:
            self.write(f':SENS:PID:VOLT:MIN {value}')                           # RST Value = 5.0
        else:
            self.validate_input(value, values, f'Input value must be in the range{min(values), max(values)}.')

        return self.query(':SENS:PID:VOLT:MIN?')
    
    def PID_offset(self, value):
        """
        Sets/Queries the voltage offset (centering position) for the PID calculation,
        expressed in volts. The instrument automatically limits this voltage to ± 5.0 volts.
        """
        values = np.arange(-5., 5.1, .1)
        if value in values:
            self.write(f':SENS:PID:VOLT:OFFS {value}')                          # RST Value = 0.0
        else:
            self.validate_input(value, values, f'Input value must be in the range{min(values), max(values)}.')

        return self.query(':SENS:PID:VOLT:OFFS?')
    
    def PID_scale(self, value):
        """
        Sets/Queries the voltage/gain scale for the PID calculation, expressed in volts per
        nanometer.
        """
        values = np.arange(-500., 500.1, .1)
        if value in values:
            self.write(f':SENSE:PID:VOLT:SCAL {value}')                         # RST Value = 1.0
        else:
            self.validate_input(value, values, f'Input value must be in the range{min(values), max(values)}.')

        return self.query(':SENS:PID:VOLT:SCAL?')

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # TRIGger Subsystem
    #
    # The TRIGger subsystem is used to define the length of a measurement and how a measurement is
    # initiated. The values for the TRIGger subsystem are INTernal, external FALL, or external RISE.
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def trigger_method(self, value):
        """
        Sets/Queries the trigger method being used for data collection.
        """
        values = {'INT', 'RISE', 'FALL'}
        if value in values:
            self.write(f':TRIG:SEQ:METH {value}')
        else:
            self.validate_input(value, values, f'Input value must be one of {values}.')

        return self.query(':TRIG:SEQ:METH?')

    def frame_rate(self, value):
        """
        Sets the measurement rate of the internal trigger used for data collection. The
        INTernal TRIGger is specified as the number of measurements per second. The
        integration time set by the measurement rate will be used for external triggering.
        The available rates will depend on the instrument model as defined below.
        VIS \ NIR Model: { 20 | 50 | 100 | 250 | 500 | 1000}
        NIR2 Model: { 250 | 500 | 750 | 1000 | 1250 | 1500}
        """
        values = {20, 50, 100, 250, 500, 1000}
        if value in values:
            self.write(f':TRIG:SEQ:RATE {value}')                               # RST Value = 500
        else:
            self.validate_input(value, values, f'Input value must be one of {values}.')

        return self.query(f':TRIG:SEQ:RATE?')
    
    def auto_frame_rate(self):
        """
        When Adjust Frame Rate is selected, the instrument chooses a frame rate between
        12 and 1000 Hz (250 to 1500 Hz for the NIR2) to illuminate the detector at approximately
        50% saturation.
        """
        self.write(':TRIG:SEQ:RATE:ADJ')
        
        return self.query(':TRIG:SEQ:RATE:ADJ?')

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # STATus Subsystem
    #
    # The STATus subsystem is used to retrieve status information from the instrument and to mask or
    # screen what status can be retrieved. Status registers give information about the instrument and the
    # latest measurement. Status enable registers allow some status information to be ignored. Status
    # information disabled though the status enable registers will not show up in the status registers
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    def check_status(self):
        """
        Queries the SCPI Questionable Status Register which contains bits that indicate
        that one or more measurement types are of questionable accuracy. The bits in the
        register are described in the table below.
        """
        return self.query(':STAT:QUES:COND?')

    def enable_status(self, value):
        """
        Used to set and clear bits in the SCPI Questionable Enable Register. This register
        contains bits that are used to mask one or more conditions indicated in the
        Questionable Status Register. Clearing a bit (setting it to zero) causes that
        condition to be masked so that, even if the condition is true, its associated bit will
        not get set in the Questionable Status Register. The Questionable Enable
        Register has the same format as the Questionable Status Register. See table
        above.
        """
        values = {1 << i for i in range(12)}
        if value in values:
            self.write(f':STAT:QUES:ENAB {value}')
        else:
            self.validate_input(value, values, f"Input value must be one of {sorted(values)}.")

        return self.query(':STAT:QUES:ENAB?')
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # SYSTem Subsystem
    #
    # The SYSTem subsystem supplies information and status about the SCPI command parser
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    def system_error(self):
        """
        Reads error strings from the SCPI Error Queue. If the Error Queue has any
        entries, the Error Queue bit is set in the Status Byte. The instrument has a 30
        entry, first-in, first-out queue. Repeatedly sending the query :SYST:ERR? returns
        the error numbers and descriptions in the order in which they occurred until the
        queue is empty. Any further queries return 0, "No error" until another error occurs.
        A table of possible errors is shown below.
        """
        return self.query(':SYST:ERR?')
    
    def system_help(self):
        """
        Reads a list of all commands and queries supported by the instrument. Each line
        of the response is terminated by a linefeed. The first line indicates the number of
        bytes of help data that follow. The remaining lines are strings of help data. All lines
        of data must be read before continuing normal operations.
        """
        return self.query(':SYSTem:HELP:HEADers?')
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # Complementary functions
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def displayStatus(self):
        statusBin = [int(i) for i in "{:b}".format(int(self.MeasAll().split(',')[1]))]
        statusBin = np.array(list(np.zeros(32-len(statusBin), int)) + statusBin)

        print("Status Decoded:")
        for i in range(31,0, -1):
            if statusBin[i] == 1:
                print("               ", np.arange(31, 0,-1)[i])

if __name__ == "__main__":
    Bristol871()
    # Bristol871(port_number="/dev/ttyUSB0")  # Example serial port