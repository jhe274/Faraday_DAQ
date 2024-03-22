import os, sys
from time import time, sleep, perf_counter, strftime, localtime
from datetime import datetime as dt
import nidaqmx.system, nidaqmx.system.storage
from toptica.lasersdk.dlcpro.v2_5_4 import DLCpro, SerialConnection, DeviceNotFoundError
from TopticaDLCpro.Laser import Laser
from Bristol871.Bristol_871A import Bristol871
from DSP7265.Lock_in_1f import L1f
from DSP7265.Lock_in_2f import L2f
from DSP7265.Lock_in_DC import DC
from DSP7265.Lock_in_Mod import Mod
from instruments.lakeshore import Lakeshore475
from Thorlabs.TC300.TC300_COMMAND_LIB import TC300
import numpy as np

dir_path = os.path.join(os.getcwd(), 'Faraday rotation measurements')
K_vapor = os.path.join(dir_path, 'K vapor cell')
# Vivian = os.path.join(dir_path, 'Vivian')
DLCpro_path = os.path.join(K_vapor, 'TopticaDLCpro data')
DLCpro_file = f'DLCpro_WideScan_{dt.now().strftime("%Y-%m-%d")}.csv'
lockin_path = os.path.join(K_vapor, 'Lockins data')
lockin_file = f'Faraday_lockins_{dt.now().strftime("%Y-%m-%d")}.lvm'
bristol_path = os.path.join(K_vapor, 'Bristol data')
bristol_file = f'Bristol_{dt.now().strftime("%Y-%m-%d")}.csv'

class Main:
    def __init__(self):
        self.NI_channel = 'cDAQ1Mod4'
        self.system = nidaqmx.system.System.local()
        self.device = nidaqmx.system.Device(f'{self.NI_channel}')
        self.system.driver_version
        
        """
        Bristol 871A-VIS
        """
        self.port_Bristol = 'COM6'                                                              # Serial port number
        self.auto_expo = 'ON'                                                                   # 'ON' or 'OFF'
        self.cali_meth = 'TEMP'                                                                 # 'TIME' or 'TEMP'
        self.delta_temp = 5                                                                     # Delta T = 0.5°C
        self.trig_meth = 'INT'                                                                  # 'INT' or 'RISE' or 'FALL'
        self.fram_rate = 100                                                                    # [Hz]
        self.aver_stat = 'OFF'                                                                  # 'ON' or 'OFF'
        self.aver_type = 'WAV'
        self.aver_coun = 20

        """
        Mod lock-in amplifier, model DSP7265
        Reference frequency = 10 Hz
        """
        # self.mod = Mod(6)                                                                       # GPIB address: 7
        # self.harm_mod = 1                                                                       # Reference Haromnic: 1st
        # self.phase_mod = 144.37                                                                 # Reference Phase: [°]
        # self.gain_mod = 0                                                                       # AC Gain: 0dB
        # self.sens_mod = 1                                                                       # Sensitivity: [V]
        # self.TC_mod = 100E-3                                                                    # Time Constant: [s]
        # self.len_mod = 16384                                                                    # Storage points
        # self.STR_mod = 100E-3                                                                   # Curve buffer Storage Interval: [s/point]

        """
        1f lock-in amplifier, model DSP7265
        Reference frequency = 50,000 Hz
        """
        self.l1f = L1f(7)                                                                       # GPIB address: 7
        self.harm_1f = 1                                                                        # Reference Haromnic: 1st
        self.phase_1f = 75.94                                                                   # Reference Phase: [°]
        self.gain_1f = 10                                                                       # AC Gain: [dB]
        self.sens_1f = 1E-3                                                                     # Sensitivity: [V]
        self.TC_1f = 50E-3                                                                      # Time Constant: [s]
        self.len_1f = 16384                                                                     # Storage points
        self.STR_1f = 100E-3                                                                    # Curve buffer Storage Interval: [s/point]

        """
        2f lock-in amplifier, model DSP7265
        Reference frequency = 50,000 Hz
        """
        self.l2f = L2f(8)                                                                       # GPIB address: 8
        self.harm_2f = 2                                                                        # Reference Haromnic: 2nd
        self.phase_2f = 131.58                                                                  # Reference Phase: [°]
        self.gain_2f = 10                                                                       # AC Gain: [dB]
        self.sens_2f = 200E-3                                                                   # Sensitivity: [V]
        self.TC_2f = 50E-3                                                                      # Time Constant: [s]
        self.len_2f = 16384                                                                     # Storage points
        self.STR_2f = 100E-3                                                                    # Curve buffer Storage Interval: [s/point]

        """
        DC lock-in amplifier, model DSP7265
        Reference frequency = 977 Hz
        """
        self.dc = DC(9)                                                                         # GPIB address: 9
        self.harm_dc = 1                                                                        # Reference Haromnic: 1st
        self.phase_dc = 65.37                                                                   # Reference Phase: [°]
        self.gain_dc = 10                                                                       # AC Gain: [dB]
        self.sens_dc = 200e-3                                                                   # Sensitivity: [V]
        self.TC_dc = 50E-3                                                                      # Time Constant: [s]
        self.len_dc = 16384                                                                     # Storage points
        self.STR_dc = 100E-3                                                                    # Curve buffer Storage Interval: [s/point]

        """
        Measurement settings
        The computer clock determines the timestamps for EXT trigger method
        the pulse period should not be shorter than 5ms
        """
        self.EXT_H = 0.005                                                                      # 5ms pulse
        self.EXT_L = 0.005                                                                      # send every 5ms
        self.MeasureDuration = 10                                                               # [s]
        self.INT_peri = 1 / self.fram_rate                                                      # Bristol measurement period while using EXTERNAL trigger
        self.EXT_peri = self.EXT_H + self.EXT_L                                                 # Bristol measurement period while using EXTERNAL trigger
        self.INT_NPeri = int(self.MeasureDuration / self.INT_peri)                              # Number of periods while using INTERNAL trigger
        self.EXT_NPeri = int(self.MeasureDuration / self.EXT_peri)                              # Number of periods while using EXTERNAL trigger
        self.INT_times = [ (i*self.INT_peri) for i in range(self.INT_NPeri) ]                   # Measurement time array while using INTERNAL trigger
        self.EXT_times = [ (i*self.EXT_peri) for i in range(self.EXT_NPeri) ]                   # Measurement time array while using EXTERNAL trigger
        self.INT_rise = [True, True]
        self.INT_fall = [False, False]
        self.EXT_rise = [True, True, True]
        self.EXT_fall = [False, True, True]
        self.All_fall = [False, False, False]

    def config_NIcDAQ(self):
        """
        NI-cDAQ-9172, using Mod4 for trigger signal control
        """
        device_found = False
        for device in self.system.devices:
            if device.name == self.NI_channel:
                device_found = True
                try:
                    device.reset_device()
                    device.self_test_device()
                    print(f'NI-cDAQ-9172 {self.NI_channel} Initialized.')
                except Exception as e:
                    print(f"Error initializing NI-cDAQ-9172 {self.NI_channel}: {e}")
                    sys.exit(1)                                                                 # Abort script execution
        
        if not device_found:
            print(f"NI-cDAQ-9172 {self.NI_channel} not found.")
            sys.exit(1)

    def config_Bristol(self):
        """
        Bristol wavelenght meter, model 871A-VIS4K
        """
        try:
            self.b = Bristol871(self.port_Bristol)
        except Exception as e:
            print('Could not connect to Bristol871 wavelength meter: {}\n'.format(e))
            sys.exit(1)
            
        print('Detector type =          ', self.b.detector('CW'))                               # Detector type = CW
        print('Auto exposure =          ', self.b.auto_expo(self.auto_expo))
        print('Calibration method =     ', self.b.calib_method(self.cali_meth))
        self.b.calib_temp(self.delta_temp)                                                      # Temperature delta = 0.5°C
        print('Trigger method =         ', self.b.trigger_method(self.trig_meth))
        if self.trig_meth == 'INT':
            print('Frame rate =             ', self.b.frame_rate(self.fram_rate), 'Hz\n')
            # print('Average method =         ', self.b.average_state(self.aver_stat))
            # print('Average data type =      ', self.b.average_data(self.aver_type))
            # print('Average count =          ', self.b.average_count(self.aver_coun))
        else:
            print('Frame rate =             ', round(1/self.EXT_peri), 'Hz\n')
        
    def config_lock_ins(self):
        """
        Configure triple modulation lock-ins and set buffer to trigger mode
        """
        # self.mod.reference_channel(self.phase_mod, self.harm_mod)
        self.l1f.reference_channel(self.phase_1f, self.harm_1f)
        self.l2f.reference_channel(self.phase_2f, self.harm_2f)
        self.dc.reference_channel(self.phase_dc, self.harm_dc)

        # self.mod.filters(self.gain_mod, self.TC_mod, self.sens_mod)
        self.l1f.filters(self.gain_1f, self.TC_1f, self.sens_1f)
        self.l2f.filters(self.gain_2f, self.TC_2f, self.sens_2f)
        self.dc.filters(self.gain_dc, self.TC_dc, self.sens_dc)

        # self.mod.trigger_buffer()
        self.l1f.trigger_buffer()
        self.l2f.trigger_buffer()
        self.dc.trigger_buffer()
    
    def init_buffer(self):
        """
        Initialize triple modulation lock-in buffers
        """
        # self.mod.init_curve_buffer(self.len_mod, self.STR_mod)
        self.l1f.init_curve_buffer(self.len_1f, self.STR_1f)
        self.l2f.init_curve_buffer(self.len_2f, self.STR_2f)
        self.dc.init_curve_buffer(self.len_dc, self.STR_dc)
        
        """
        Initialize Bristol wavelength meter buffer
        """
        self.b.buffer('INIT')                                                                   # Initilize buffer
        print('Bristol buffer initialized.\n')

    def EXT_trig_mea(self):
        """
        External trgiger mrthod for Bristol wavelength meter during FR measurements
        """
        print('Bristol wavelength meter is operating at EXTERNAL trigger mode...')
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan(f"{self.NI_channel}/port0/line0")                      # DIO0: Gate12, Bristol
            task.do_channels.add_do_chan(f"{self.NI_channel}/port0/line1")                      # DIO1: Gate16, lock-ins
            task.start()
            i = 0
            timestamps = []
            timestamps_before_rise = []
            timestamps_after_rise = []
            print(f'Measurement duration =   {int(self.MeasureDuration):4d}', 's')
            self.countdown(5)
            print("\n=============== Measurement Initiated ===============")
            self.b.buffer('OPEN')
            while i < self.EXT_NPeri:
                if i == 0:
                    t0 = perf_counter()
                while perf_counter() - t0 < self.EXT_times[i]:
                    pass
                timestamps_before_rise.append(time())
                task.write(self.EXT_rise)
                timestamps_after_rise.append(time())
                t1 = perf_counter()
                while perf_counter() - t1 < (self.EXT_H):
                    pass
                task.write(self.EXT_fall)
                i = i + 1
                print(f"\rTime remaining:          {int(self.MeasureDuration-i*self.EXT_peri):4d}", 's', end='')
            sleep(self.EXT_L)
            print()
            # self.mod.halt_buffer()
            self.l1f.halt_buffer()
            self.l2f.halt_buffer()
            self.dc.halt_buffer()
            self.b.buffer('CLOS')
            elap_time = perf_counter() - t0
            task.write(self.All_fall)
            print("=============== Measurement Completed ===============")
            print(f'{self.EXT_NPeri} periods of {self.EXT_peri} seconds')
            task.stop()
            start_time = (timestamps_before_rise[0]+timestamps_after_rise[0]) / 2
            for j in range(len(timestamps_before_rise)):
                timestamp = (timestamps_before_rise[j] + timestamps_after_rise[j]) / 2          # Average of before and after write
                formatted_timestamp = strftime("%Y-%m-%dT%H:%M:%S.", localtime(timestamp)) + f"{timestamp % 1:.3f}".split(".")[1]
                timestamps.append(formatted_timestamp)

        return start_time, elap_time, timestamps
    
    def INT_trig_mea(self):
        """
        Internal trgiger mrthod for Bristol wavelength meter during FR measurements
        """
        print('Bristol wavelength meter is operating at INTERNAL trigger mode...')
        with nidaqmx.Task() as task:
            # Logic TTL at the selected DIO channel gates
            task.do_channels.add_do_chan(f"{self.NI_channel}/port0/line1")                      # DIO1: Gate16, lock-ins
            task.start()
            i = 0
            timestamps = []
            print(f'Measurement duration =   {int(self.MeasureDuration):4d}', 's')
            # self.countdown(5)
            print("\n=============== Measurement Initiated ===============")
            self.b.buffer('OPEN')
            start_time = time()
            task.write(self.INT_rise)
            while i < self.INT_NPeri:
                if i == 0:
                    t0 = perf_counter()
                while perf_counter() - t0 < self.INT_times[i]:
                    pass
                t1 = perf_counter()
                while perf_counter() - t1 < (self.INT_peri/2):
                    pass
                i = i + 1
                print(f"\rTime remaining:          {int(self.MeasureDuration-i*self.INT_peri):4d}", 's', end='')
            # self.mod.halt_buffer()
            self.l1f.halt_buffer()
            self.l2f.halt_buffer()
            self.dc.halt_buffer()
            self.b.buffer('CLOS')
            elap_time = perf_counter() - t0
            task.write(self.INT_fall)
            print("=============== Measurement Completed ===============")
            task.stop()
            timestamp = [start_time + INT_time for INT_time in self.INT_times]
            for j in range(self.INT_NPeri):
                formatted_timestamp = strftime("%Y-%m-%dT%H:%M:%S.", localtime(timestamp[j])) + f"{timestamp[j] % 1:.3f}".split(".")[1]
                timestamps.append(formatted_timestamp)

        return start_time, elap_time, timestamps
    
    def get_lock_in_buffer(self, path, filename, t0):
        """
        Retrieve data from lock-in buffers
        """
        print('\nRetrieving data from Lock-ins buffer...')
        buffers = [self.l1f, self.l2f, self.dc]
        sensors = [self.sens_1f, self.sens_2f, self.sens_dc]
        
        data = []
        buffer_status = []
        timestamps = []

        for buffer, sensor in zip(buffers, sensors):
            X, Y, status = buffer.get_curve_buffer(sensor)
            data.extend([X, Y])
            buffer_status.append(status)

        # Create a list of timestamps for lock-ins
        L_times = [n * self.STR_2f for n in range(len(data[3]))]
        timestamp = [t0 + t for t in L_times]

        formatted_timestamps = [strftime("%Y-%m-%dT%H:%M:%S.", localtime(t)) + f"{t % 1:.3f}".split(".")[1] for t in timestamp]
        timestamps.extend(formatted_timestamps)

        data.insert(0, timestamps)

        try:
            counter = 1
            original_filename = filename
            folder_name = strftime("%m-%d-%Y", localtime(t0))
            folder_path = os.path.join(path, folder_name)
            os.makedirs(folder_path, exist_ok=True)

            while os.path.isfile(os.path.join(folder_path, filename)):
                filename = f"{original_filename.split('.')[0]}_{counter}.lvm"
                counter += 1

            file_path = os.path.join(folder_path, filename)

            with open(file_path, "w") as log:
                for attribute, value in zip(['TC_1f[s]', 'SENS_1f[V]', 'TC_2f[s]', 'SENS_2f[V]', 'TC_dc[s]', 'SENS_dc[V]'],
                                            [self.TC_1f, self.sens_1f, self.TC_2f, self.sens_2f, self.TC_dc, self.sens_dc]):
                    log.write(f'#{attribute} {value}\n')

                log.write('#Field Input Voltage\n')
                log.write('#Preamp gain\n')
                header = 'Timestamp,X_1f,Y_1f,X_2f,Y_2f,X_dc,Y_dc\n'
                log.write(header)

                for row in zip(*data):
                    log.write(','.join(map(str, row)) + '\n')
        except Exception as e:
            print(f"An error occurred while saving data to the file: {e}")

    def countdown(self, seconds):
        for i in range(seconds, -1, -1):
            print(f"\rWide Scan starts in:        {i}", end="")
            sleep(1)

if __name__ == "__main__":
    m = Main()
    m.config_NIcDAQ()
    m.config_Bristol()
    m.config_lock_ins()
    m.init_buffer()
    if (m.MeasureDuration / m.STR_1f > m.len_1f) or (m.MeasureDuration / m.STR_2f > m.len_2f) or (m.MeasureDuration / m.STR_dc > m.len_dc):
        print('Number of data points exceeds lock-ins buffer length.')
        pass
    else:
        trig_mode = m.b.trigger_method(m.trig_meth)
        if trig_mode == 'INT':
            start_time, elap_time, timestamps = m.INT_trig_mea()
        elif trig_mode == 'RISE' or trig_mode == 'FALL':
            start_time, elap_time, timestamps = m.EXT_trig_mea()
        m.b.get_buffer(bristol_path, bristol_file, elap_time, timestamps)
        m.get_lock_in_buffer(lockin_path, lockin_file, start_time)