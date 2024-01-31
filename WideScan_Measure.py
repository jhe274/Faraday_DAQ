import os, sys
from time import time, sleep, perf_counter, strftime, localtime
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
DLCpro_path = os.path.join(K_vapor, 'TopticaDLCpro data', f'{dt.now().strftime("%m-%d-%Y")}')
DLCpro_file = f'DLCpro_WideScan_{dt.now().strftime("%Y-%m-%d")}.csv'
lockin_path = os.path.join(K_vapor, 'Lockins data', f'{dt.now().strftime("%m-%d-%Y")}')
lockin_file = f'Faraday_lockins_{dt.now().strftime("%Y-%m-%d")}.lvm'
bristol_path = os.path.join(K_vapor, 'Bristol data', f'{dt.now().strftime("%m-%d-%Y")}')
bristol_file = f'Bristol_{dt.now().strftime("%Y-%m-%d")}.csv'

class Main:
    def __init__(self):
        self.system = nidaqmx.system.System.local()
        self.system.driver_version
        
        """
        TOPTICA DLC pro
        """
        self.dlc_port = 'COM5'                                                                  # Serial port number
        self.laser = Laser(self.dlc_port)
        self.OutputChannel = 50                                                                 # 51 -> CC, 50 -> PC, 57 -> TC                                                 
        self.ScanOffset = 69                                                                    # [V]
        self.ScanAmplitude = 0                                                                  # [V]
        self.StartVoltage = 74                                                                  # [V]
        self.EndVoltage = 64                                                                    # [V]
        self.ScanSpeed = 0.05                                                                   # [V/s]
        self.WideScanDuration = np.abs(self.StartVoltage-self.EndVoltage)/self.ScanSpeed        # [s], (integer)
        self.ScanShape = 0                                                                      # 0 -> Sawtooth, 1 -> Traingle
        self.InputTrigger = True                                                                # True -> Enable, False -> Disable
        self.RecorderStepsize = 0.00005                                                          # [V]
        
        """
        Bristol 871A-VIS
        """
        self.port_Bristol = 'COM6'                                                              # Serial port number
        self.auto_expo = 'ON'                                                                   # 'ON' or 'OFF'
        self.cali_meth = 'TEMP'                                                                 # 'TIME' or 'TEMP'
        self.trig_meth = 'INT'                                                                  # 'INT' or 'RISE' or 'FALL'
        self.fram_rate = 100                                                                    # [Hz]
        self.aver_stat = 'OFF'                                                                  # 'ON' or 'OFF'
        self.aver_type = 'WAV'
        self.aver_coun = 20
        
        """
        Mod lock-in amplifier, model DSP7265
        Reference frequency = 10 Hz
        Harmonic = 1st
        """
        self.mod = Mod(7)                                                                       # GPIB address: 7
        self.gain_mod = 10                                                                      # AC Gain: 0dB
        self.TC_mod = 5E-3                                                                      # Time Constant: [s]
        self.sens_mod = 200E-3                                                                  # Sensitivity: [V]
        self.len_mod = 16384                                                                    # Storage points
        self.STR_mod = 100E-3                                                                   # Curve buffer Storage Interval: [s/point]

        """
        2f lock-in amplifier, model DSP7265
        Reference frequency = 50,000 Hz
        Harmonic = 2nd
        """
        self.l2f = L2f(8)                                                                       # GPIB address: 8
        self.gain_2f = 30                                                                       # AC Gain: 10dB
        self.TC_2f = 5E-3                                                                       # Time Constant: [s]
        self.sens_2f = 1E-3                                                                     # Sensitivity: [V]
        self.len_2f = 16384                                                                     # Storage points
        self.STR_2f = 100E-3                                                                    # Curve buffer Storage Interval: [s/point]

        """
        DC lock-in amplifier, model DSP7265
        Reference frequency = 977 Hz
        Harmonic = 1st
        """
        self.dc = DC(9)                                                                         # GPIB address: 9
        self.gain_dc = 30                                                                       # AC Gain: 0dB
        self.TC_dc = 5E-3                                                                       # Time Constant: [s]
        self.sens_dc = 20E-3                                                                    # Sensitivity: [V]
        self.len_dc = 16384                                                                     # Storage points
        self.STR_dc = 100E-3                                                                    # Curve buffer Storage Interval: [s/point]

        """
        Measurement settings
        The computer clock determines the timestamps
        the pulse should not be shorter than 5ms
        since it reduces 
        """
        self.EXT_H = 0.005                                                                      # 5ms pulse
        self.EXT_L = 0.005                                                                      # send every 5ms
        self.INT_peri = 1 / self.fram_rate                                                      # Bristol measurement period while using EXTERNAL trigger
        self.EXT_peri = self.EXT_H + self.EXT_L                                                 # Bristol measurement period while using EXTERNAL trigger
        self.INT_NPeri = int(self.WideScanDuration / self.INT_peri)                             # Number of periods while using INTERNAL trigger
        self.EXT_NPeri = int(self.WideScanDuration / self.EXT_peri)                             # Number of periods while using EXTERNAL trigger
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
        for device in self.system.devices:
            print(device, '\r')
        print('Connected to NI-cDAQ-9172...')

    def config_DLCpro(self):
        """
        TOPTICA DLC pro
        """
        self.laser.WideScan(self.OutputChannel, self.ScanOffset, self.StartVoltage,
                            self.EndVoltage, self.ScanSpeed, self.ScanShape,
                            self.WideScanDuration, self.InputTrigger, self.RecorderStepsize)

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
            
        print('Detector type =          ', self.b.detector('CW'))                               # Detector type = CW
        print('Auto exposure =          ', self.b.auto_expo(self.auto_expo))
        print('Calibration method =     ', self.b.calib_method(self.cali_meth))
        self.b.calib_temp(5)                                                                    # Temperature delta = 0.5°C
        print('Trigger method =         ', self.b.trigger_method(self.trig_meth))
        if self.trig_meth == 'INT':
            print('Frame rate =             ', self.b.frame_rate(self.fram_rate), 'Hz')
            # print('Average method =         ', self.b.average_state(self.aver_stat))
            # print('Average data type =      ', self.b.average_data(self.aver_type))
            # print('Average count =          ', self.b.average_count(self.aver_coun))
        else:
            print('Frame rate =             ', round(1/self.EXT_peri), 'Hz')
        
    def config_lock_ins(self):
        """
        Configure triple modulation lock-ins and set buffer to trigger mode
        """
        self.mod.filters(self.gain_mod, self.TC_mod, self.sens_mod)
        self.l2f.filters(self.gain_2f, self.TC_2f, self.sens_2f)
        self.dc.filters(self.gain_dc, self.TC_dc, self.sens_dc)
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
        self.b.buffer('INIT')                                                                   # Initilize buffer
        print('Bristol buffer initialized.\n')

    def EXT_trig_mea(self):
        """
        External trgiger mrthod for Bristol wavelength meter during FR measurements
        """
        print('Bristol wavelength meter is operating at EXTERNAL trigger mode...')
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan("cDAQ1Mod4/port0/line0")                               # DIO0: Gate12, Bristol
            task.do_channels.add_do_chan("cDAQ1Mod4/port0/line1")                               # DIO1: Gate16, lock-ins
            task.do_channels.add_do_chan("cDAQ1Mod4/port0/line2")                               # DIO2: Gate17, Toptica DLC pro
            task.start()
            i = 0
            timestamps = []
            timestamps_before_rise = []
            timestamps_after_rise = []
            try:
                with DLCpro(SerialConnection(self.dlc_port)) as dlcpro:
                    dlcpro.laser1.wide_scan.start()
                    print(f'Scan duration =          {int(self.WideScanDuration):4d}', 's')
                    self.countdown(5)
                    print("\n========== Wide Scan Initiated ==========")
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
                        print(f"\rTime remaining:          {int(self.WideScanDuration-i*self.EXT_peri):4d}", 's', end='')
                    sleep(self.EXT_L)
                    print()
                    self.mod.halt_buffer()
                    self.l2f.halt_buffer()
                    self.dc.halt_buffer()
                    self.b.buffer('CLOS')
                    elap_time = perf_counter() - t0
                    task.write(self.All_fall)
                    print("========== Wide Scan Completed ==========")
                    dlcpro.laser1.wide_scan.stop()
                    result = self.laser.get_recorder_data(dlcpro.laser1)
                    self.laser.save_recorder_data(DLCpro_path, DLCpro_file, result)
            except DeviceNotFoundError:
                sys.stderr.write('TOPTICA DLC pro not found')
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
            task.do_channels.add_do_chan("cDAQ1Mod4/port0/line1")                               # DIO1: Gate16, lock-ins
            task.do_channels.add_do_chan("cDAQ1Mod4/port0/line2")                               # DIO2: Gate17, Toptica DLC pro
            task.start()
            i = 0
            timestamps = []
            try:
                with DLCpro(SerialConnection(self.dlc_port)) as dlcpro:
                    dlcpro.laser1.wide_scan.start()
                    print(f'Scan duration =          {int(self.WideScanDuration):4d}', 's')
                    self.countdown(5)
                    print("\n========== Wide Scan Initiated ==========")
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
                        print(f"\rTime remaining:          {int(self.WideScanDuration-i*self.INT_peri):4d}", 's', end='')
                    self.mod.halt_buffer()
                    self.l2f.halt_buffer()
                    self.dc.halt_buffer()
                    self.b.buffer('CLOS')
                    elap_time = perf_counter() - t0
                    task.write(self.INT_fall)
                    print("\n========== Wide Scan Completed ==========")
                    dlcpro.laser1.wide_scan.stop()
                    result = self.laser.get_recorder_data(dlcpro.laser1)
                    self.laser.save_recorder_data(DLCpro_path, DLCpro_file, result)
            except DeviceNotFoundError:
                sys.stderr.write('TOPTICA DLC pro not found')
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
        buffers = [self.mod, self.l2f, self.dc]
        sensors = [self.sens_mod, self.sens_2f, self.sens_dc]
        
        data = []
        timestamps = []

        for buffer, sensor in zip(buffers, sensors):
            X, Y = buffer.get_curve_buffer(sensor)
            data.extend([X, Y])

        # Create a list of timestamps for lock-ins
        L_times = [n * self.STR_mod for n in range(len(data[3]))]
        timestamp = [t0 + t for t in L_times]

        formatted_timestamps = [strftime("%Y-%m-%dT%H:%M:%S.", localtime(t)) + f"{t % 1:.3f}".split(".")[1] for t in timestamp]
        timestamps.extend(formatted_timestamps)

        data.insert(0, timestamps)

        try:
            counter = 1
            original_filename = filename

            while os.path.isfile(os.path.join(path, filename)):
                filename = f"{original_filename.split('.')[0]}_{counter}.lvm"
                counter += 1

            file_path = os.path.join(path, filename)

            with open(file_path, "w") as log:
                for attribute, value in zip(['TC_mod[s]', 'SENS_mod[V]', 'TC_2f[s]', 'SENS_2f[V]', 'TC_dc[s]', 'SENS_dc[V]'],
                                            [self.TC_mod, self.sens_mod, self.TC_2f, self.sens_2f, self.TC_dc, self.sens_dc]):
                    log.write(f'#{attribute} {value}\n')

                log.write('#Field Input Voltage\n')
                log.write('#Preamp gain\n')
                header = 'Timestamp,X_mod,Y_mod,X_2f,Y_2f,X_dc,Y_dc\n'
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
    m.config_DLCpro()
    m.config_Bristol()
    m.config_lock_ins()
    m.init_buffer()
    if (m.WideScanDuration / m.STR_mod > m.len_mod) or (m.WideScanDuration / m.STR_2f > m.len_2f) or (m.WideScanDuration / m.STR_dc > m.len_dc):
        print('Number of data points exceeds buffer length.')
        pass
    else:
        trig_mode = m.b.trigger_method(m.trig_meth)
        if trig_mode == 'INT':
            start_time, elap_time, timestamps = m.INT_trig_mea()
        elif trig_mode == 'RISE' or trig_mode == 'FALL':
            start_time, elap_time, timestamps = m.EXT_trig_mea()
        m.b.get_buffer(bristol_path, bristol_file, elap_time, timestamps)
        m.get_lock_in_buffer(lockin_path, lockin_file, start_time)