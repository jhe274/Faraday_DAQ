import os, sys
from time import time, sleep, perf_counter, strftime, gmtime, localtime
from datetime import datetime as dt
import nidaqmx.system
from toptica.lasersdk.dlcpro.v2_0_3 import DLCpro, SerialConnection, DeviceNotFoundError
from TopticaDLCpro.Laser import Laser
from Bristol871.Bristol_871A import Bristol871
from DSP7265.Lock_in_Mod import Mod
from DSP7265.Lock_in_2f import L2f
from DSP7265.Lock_in_DC import DC
import numpy as np

dir_path = os.path.join(os.getcwd(), 'Faraday rotation measurements')
K_vapor = os.path.join(dir_path, 'K vapor cell')
# Vivian = os.path.join(dir_path, 'Vivian')
lockin_file = os.path.join(K_vapor, 'Lock-ins data', 'Lock-ins_log.lvm')
bristol_file = os.path.join(K_vapor, 'Bristol data', 'Bristol_log.csv')

class Main:
    def __init__(self):
        self.system = nidaqmx.system.System.local()
        self.system.driver_version
        
        """
        TOPTICA DLC pro
        """
        self.dlc_port = 'COM5'                                                          # Serial port number
        self.laser = Laser(self.dlc_port)                                                      
        self.ScanOffset = 70                                                            # [V]
        self.ScanAmplitude = 0                                                          # [V]
        self.StartVoltage = 69                                                          # [V]
        self.EndVoltage = 71                                                            # [V]
        self.ScanSpeed = 0.2                                                            # [V/s]
        self.ScanDuration = np.abs(self.StartVoltage-self.EndVoltage) / self.ScanSpeed  # [s], (integer)
        
        """
        Bristol 871A
        """
        self.port_Bristol = 'COM6'                                                      # Serial port number

        """
        Mod lock-in amplifier, model DSP7265
        """
        self.mod = Mod(7)                                                               # GPIB address: 7
        self.TC_mod = 50E-3                                                             # Time Constant: [s]
        self.sens_mod = 50E-3                                                           # Sensitivity: [V]
        self.len_mod = 16384                                                            # Storage points
        self.STR_mod = 50E-3                                                            # Curve buffer Storage Interval: [s/point]

        """
        2f lock-in amplifier, model DSP7265
        """
        self.l2f = L2f(8)                                                               # GPIB address: 8
        self.TC_2f = 5E-3                                                               # Time Constant: [s]
        self.sens_2f = 50E-3                                                            # Sensitivity: [V]
        self.len_2f = 16384                                                             # Storage points
        self.STR_2f = 50E-3                                                              # Curve buffer Storage Interval: [s/point]

        """
        DC lock-in amplifier, model DSP7265
        """
        self.dc = DC(9)                                                                 # GPIB address: 9
        self.TC_dc = 50E-3                                                              # Time Constant: [s]
        self.sens_dc = 50E-3                                                            # Sensitivity: [V]
        self.len_dc = 16384                                                             # Storage points
        self.STR_dc = 50E-3                                                             # Curve buffer Storage Interval: [s/point]

        """
        Measurement settings
        """
        self.TIME_HIGH = 0.005                                                          # 5ms pulse
        self.TIME_LOW = 0.005                                                           # send every 5ms
        self.PERIOD = self.TIME_HIGH + self.TIME_LOW
        self.NPERIODS = int(self.ScanDuration / self.PERIOD)                            # number of periods
        self.onset_times = [ (self.PERIOD * i) for i in range(self.NPERIODS) ]          # Measurement time array
        self.INT_rise = [True, True]
        self.INT_fall = [False, False]
        self.EXT_rise = [True, True, True]
        self.EXT_fall = [True, False, True]
        self.All_fall = [False, False, False]

    def config_NIcDAQ(self):
        """
        NI-cDAQ-9172, using Mod4 for trigger signal control
        """
        for device in self.system.devices:
            print(device, '\r')
        print('Connected to NI-cDAQ-9172...')

    def config_DLCpro(self):
        """
        TOPTICA DLC pro
        """
        self.laser.WideScan()

    def config_Bristol(self):
        """
        Bristol wavelenght meter, model 871A-VIS4K
        """
        try:
            self.b = Bristol871(self.port_Bristol)
            print('Connected to Bristol871 wavelength meter...\n')
        except Exception as e:
            print('Could not connect to Bristol871 wavelength meter: {}'.format(e))
            exit(1)
            
        print('Detector type =          ', self.b.detector('CW'))                       # Detector type = CW
        print('Auto exposure =          ', self.b.auto_expo('OFF'))                     # Auto exposure = ON
        print('Calibration method =     ', self.b.calib_method('TEMP'))                 # Calibration method = Temperature
        self.b.calib_temp(5)                                                            # Temperature delta = 0.5°C
        print('Trigger method =         ', self.b.trigger_method('INT'))                # Trigger method = Rising edge
        print('Frame rate =             ', self.b.frame_rate(250), 'Hz')                # Auto adjust frame rate  
        print('Average method =         ', self.b.average_state('OFF'))                 # Average method = OFF
        # print('Average count =          ', self.b.average_count(2))                     # Number of readings to be averages = 2
        # print('Average data type =      ', self.b.average_data('WAV'))                  # Average data type = wavelength

    def config_lock_ins(self):
        """
        Configure triple modulation lock-ins and set buffer to trigger mode
        """
        self.mod.filters(self.TC_mod, self.sens_mod)
        self.l2f.filters(self.TC_2f, self.sens_2f)
        self.dc.filters(self.TC_dc, self.sens_dc)
        self.mod.trigger_buffer()
        self.l2f.trigger_buffer()
        self.dc.trigger_buffer()
    
    def init_buffer(self):
        """
        Initialize triple modulation lock-in buffers
        """
        self.mod.init_curve_buffer(self.len_mod, self.STR_mod)
        self.l2f.init_curve_buffer(self.len_2f, self.STR_2f)
        self.dc.init_curve_buffer(self.len_dc, self.STR_dc)

        """
        Initialize Bristol wavelength meter buffer
        """
        self.b.buffer('INIT')                                                           # Initilize buffer
        print('Bristol buffer initialized.\n')

    def EXT_trig_mea(self):
        """
        External trgiger mrthod for Bristol wavelength meter during FR measurements
        """
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan("cDAQ1Mod4/port0/line0")                       # DIO0: Gate12, Bristol
            task.do_channels.add_do_chan("cDAQ1Mod4/port0/line1")                       # DIO1: Gate16, lock-ins
            task.do_channels.add_do_chan("cDAQ1Mod4/port0/line2")                       # DIO2: Gate17, Toptica DLC pro
            task.start()

            i = 0
            timestamps = []
            timestamps_before_rise = []
            timestamps_after_rise = []
            try:
                with DLCpro(SerialConnection(self.dlc_port)) as dlc:
                    dlc.laser1.wide_scan.start()
                    print('Scan duration =          ', int(self.ScanDuration), 's')
                    print("========== Wide Scan Initiated ==========")

                    # Start a 5s countdown before initiating a wide scan
                    for i in range(5, 0, -1):
                        print(i)
                        sleep(1)

                    while i < self.NPERIODS:
                        if i == 0:
                            t0 = perf_counter()

                        # wait until the start of the next period
                        while perf_counter() - t0 < self.onset_times[i]:
                            pass
                        
                        # Record timestamp before writing the rise
                        timestamp_before_rise = time()
                        timestamps_before_rise.append(timestamp_before_rise)

                        self.b.buffer('OPEN')
                        task.write(self.EXT_rise)

                        # Record timestamp after writing the rise
                        timestamp_after_rise = time()
                        timestamps_after_rise.append(timestamp_after_rise)

                        # busy wait for 'TIME_HIGH' seconds. This should be more accurate than time.sleep(TIME_HIGH)
                        t1 = perf_counter()
                        while perf_counter() - t1 < (self.TIME_HIGH):
                            pass

                        task.write(self.EXT_fall)
                        i = i + 1
                        print(f"\r{i:4d}", end='')

                    sleep(self.TIME_LOW)
                    print()
                    self.mod.halt_buffer()
                    self.l2f.halt_buffer()
                    self.dc.halt_buffer()
                    self.b.buffer('CLOS')
                    task.write(self.All_fall)
                    print("========== Wide Scan Completed ==========")
                    dlc.laser1.wide_scan.stop()
            except DeviceNotFoundError:
                sys.stderr.write('TOPTICA DLC pro not found')

            print(f'{self.NPERIODS} periods of {self.PERIOD} seconds')
            elap_time = perf_counter() - t0
            task.stop()

            for j in range(len(timestamps_before_rise)):
                timestamp = (timestamps_before_rise[j] + timestamps_after_rise[j]) / 2  # Average of before and after write
                formatted_timestamp = strftime("%Y-%m-%dT%H:%M:%S.", localtime(timestamp)) + f"{timestamp % 1:.3f}".split(".")[1]
                timestamps.append(formatted_timestamp)

        return elap_time, timestamps
    
    def INT_trig_mea(self):
        """
        Internal trgiger mrthod for Bristol wavelength meter during FR measurements
        """
        with nidaqmx.Task() as task:
            # Logic TTL at the selected DIO channel gates
            task.do_channels.add_do_chan("cDAQ1Mod4/port0/line1")                       # DIO1: Gate16, lock-ins
            task.do_channels.add_do_chan("cDAQ1Mod4/port0/line2")                       # DIO2: Gate17, Toptica DLC pro
            task.start()
            try:
                with DLCpro(SerialConnection(self.dlc_port)) as dlc:
                    dlc.laser1.wide_scan.start()
                    print('Scan duration =          ', int(self.ScanDuration), 's')
                    print("========== Wide Scan Initiated ==========")

                    # Start a 5s countdown before initiating a wide scan
                    for i in range(5, 0, -1):
                        print(i)
                        sleep(1)

                    self.b.buffer('OPEN')
                    task.write(self.INT_rise)
                    sleep(self.ScanDuration)
                    self.mod.halt_buffer()
                    self.l2f.halt_buffer()
                    self.dc.halt_buffer()
                    self.b.buffer('CLOS')
                    task.write(self.INT_fall)

                    print("========== Wide Scan Completed ==========")
                    dlc.laser1.wide_scan.stop()
            except DeviceNotFoundError:
                sys.stderr.write('TOPTICA DLC pro not found')
            
            task.stop()
    
    def get_lock_in_buffer(self, path, filename):
        """
        Retrieve data from lock-in buffers
        """
        X_mod, Y_mod = self.mod.get_curve_buffer(self.sens_mod)
        X_2f, Y_2f = self.l2f.get_curve_buffer(self.sens_2f)
        X_dc, Y_dc = self.dc.get_curve_buffer(self.sens_dc)
        data = [X_mod, Y_mod, X_2f, Y_2f, X_dc, Y_dc]
        try:
            # Check for duplicate filenames
            original_filename = filename
            counter = 1
            while True:
                file_path = os.path.join(path, filename)
                if not os.path.isfile(file_path):
                    break
                # If the file already exists, add a number to the filename
                filename = f"{original_filename}_{counter}"
                counter += 1

            with open(file_path, "w") as file:
                header = 'X_mod,Y_mod,X_2f,Y_2f,X_dc,Y_dc\n'
                file.write(header)
                # Transpose the data array to write each array to its respective column
                for row in zip(*data):
                    file.write(','.join(map(str, row)) + '\n')

        except Exception as e:
            print(f"An error occurred while saving data to the file: {e}")
    
    def get_Bristol_buffer(self, elap_t, timestamps):
        """
        Retrieve data from Bristol wavelength meter buffer
        """
        if self.b.trigger_method('INT') == 'INT':
            self.b.get_buffer(bristol_file)
        else:
            self.b.timestamped_buffer(bristol_file ,elap_t, timestamps)

if __name__ == "__main__":
    m = Main()
    m.config_NIcDAQ()
    m.config_DLCpro()
    m.config_Bristol()
    m.config_lock_ins()
    m.init_buffer()
    if m.b.trigger_method('INT') == 'INT':
        m.INT_trig_mea()
        m.b.get_buffer(bristol_file)
    else:
        elap_time, timestamps = m.EXT_trig_mea()
        m.b.timestamped_buffer(bristol_file, elap_time, timestamps)
    m.get_lock_in_buffer(lockin_file, lockin_file)
