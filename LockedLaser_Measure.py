import os, sys, datetime
from time import time, sleep, perf_counter, strftime, localtime
from datetime import datetime as dt
import nidaqmx.system, nidaqmx.system.storage
from Bristol871.bristol_871A import Bristol871
from pymeasure.instruments.signalrecovery import DSP7265
from Lakeshore475DSPGaussmeter.lakeshore475 import LakeShore475
from Thorlabs.TC300.TC300_COMMAND_LIB import TC300

dir_path = os.path.join(os.getcwd(), 'Faraday_rotation_measurements')
K_vapor = os.path.join(dir_path, 'K_vapor_cell')
# Vivian = os.path.join(dir_path, 'Vivian')
lockin_path = os.path.join(K_vapor, 'Lockins_data')
wavelengthmeter_path = os.path.join(K_vapor, 'Wavelengthmeter_data')
gaussmeter_path = os.path.join(K_vapor, 'Gaussmeter_data')

class Main:
    def __init__(self):
        """Initialize all instruments, including lock-ins, Bristol, and experiment settings."""
        self.NI_channel = 'cDAQ1Mod5'
        self.system = nidaqmx.system.System.local()
        self.device = nidaqmx.system.Device(f'{self.NI_channel}')
        self.system.driver_version

        """Bristol 871A-VIS"""
        self.port_wavelengthmeter = 'COM6'                                                      # Serial port number
        self.ip_wavelengthmeter = '10.199.199.1'                                                # IP address
        self.b = Bristol871(self.port_wavelengthmeter, self.ip_wavelengthmeter)
        self.auto_expo = 'ON'                                                                   # 'ON' or 'OFF'
        self.b.calibration_method = 'TIME'                                                      # 'TIME' or 'TEMP'
        self.delta_t = 5                                                                        # Delta T = 5 min
        self.b.trigger_method = 'INT'                                                           # 'INT' or 'RISE' or 'FALL'
        self.frame_rate = 50                                                                     # [Hz]
        self.aver_stat = 'OFF'                                                                  # 'ON' or 'OFF'
        self.aver_type = 'WAV'
        self.aver_coun = 20

        """Signal Recovery DSP 7265 Lock-in Amplifiers"""
        lockin_settings = {
            "1f": {"gpib": 7, "harmonic": 1, "phase": 52.35, "gain": 10, "sens": 1e-3, "TC": 50, 
                   "coupling": False, "vmode": 3, "imode": "voltage mode", "fet": 1, "shield": 1, 
                   "reference": "external front", "slope": 24, "trigger_mode": 0, "length": 16384, "interval": 50},

            "2f": {"gpib": 8, "harmonic": 2, "phase": 15.97, "gain": 10, "sens": 10e-3, "TC": 5e-3, 
                   "coupling": False, "vmode": 3, "imode": "voltage mode", "fet": 1, "shield": 1, 
                   "reference": "external front", "slope": 24, "trigger_mode": 0, "length": 16384, "interval": 50},

            "DC": {"gpib": 9, "harmonic": 1, "phase": 0.03, "gain": 0, "sens": 500e-3, "TC": 50, 
                   "coupling": False, "vmode": 1, "imode": "voltage mode", "fet": 1, "shield": 1, 
                   "reference": "external front", "slope": 24, "trigger_mode": 0, "length": 16384, "interval": 50},

            "M2f": {"gpib": 6, "harmonic": 1, "phase": -9.65, "gain": 0, "sens": 5e-3, "TC": 50, 
                    "coupling": True, "vmode": 3, "imode": "voltage mode", "fet": 1, "shield": 1, 
                   "reference": "external front", "slope": 24, "trigger_mode": 0, "length": 16384, "interval": 50},
        }

        self.lockins = {name: DSP7265(settings["gpib"], f"{name} Lock-in Amplifier") for name, settings in lockin_settings.items()}
        self.lockin_settings = lockin_settings

        """Total measurement duration"""
        self.MeasureDuration = 14400                                                               # [s]

        """Lakeshore 475 DSP Gaussmeter"""
        self.gpib_gaussmeter = "GPIB1::11::INSTR"
        self.g = LakeShore475(self.gpib_gaussmeter)
        self.g.auto = True                                                                      # 'ON' or 'OFF'
        self.g.units = 'Gauss'                                                                  # [G] or [T]
        self.gauss_rate = 10                                                                    # [Hz]
        self.gauss_period = 1 / self.gauss_rate                                                 # [s]
        self.gauss_Nperiods = int(self.MeasureDuration / self.gauss_period)                          # Number of periods
        self.gauss_times = [ (i*self.gauss_period) for i in range(self.gauss_Nperiods + 1) ]    # Gaussmeter measurement time array


        """
        Measurement settings using EXTERNAL trigger method for Bristol Wavelength meter
        The computer clock determines the timestamps for EXT trigger method
        the pulse period should not be shorter than 5ms
        """
        # self.MeasureDuration = 400                                                              # [s]
        self.EXT_H = 0.005                                                                      # 5ms pulse
        self.EXT_L = 0.005                                                                      # send every 5ms
        self.INT_peri = 1 / self.frame_rate                                                      # Bristol measurement period while using EXTERNAL trigger
        self.EXT_peri = self.EXT_H + self.EXT_L                                                 # Bristol measurement period while using EXTERNAL trigger
        self.INT_NPeri = int(self.MeasureDuration / self.INT_peri)                              # Number of periods while using INTERNAL trigger
        self.EXT_NPeri = int(self.MeasureDuration / self.EXT_peri)                              # Number of periods while using EXTERNAL trigger
        self.INT_times = [ (i*self.INT_peri) for i in range(self.INT_NPeri) ]                   # Measurement time array while using INTERNAL trigger
        self.EXT_times = [ (i*self.EXT_peri) for i in range(self.EXT_NPeri) ]                   # Measurement time array while using EXTERNAL trigger

        """TTL logic gate controls"""
        self.field_rise = [False, True]
        self.field_fall = [True, False]
        self.double_rise = [True, True]
        self.double_fall = [False, False]
        self.triple_rise = [True, True, True]
        self.EXT_fall = [False, True, True]
        self.triple_fall = [False, False, False]

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

    def config_wavelengthmeter(self):
        """Bristol wavelenght meter, model 871A-VIS"""
        try:
            print('Detector type =          ', self.b.detector('CW'))                               # Detector type = CW
            print('Auto exposure =          ', self.b.auto_exposure)
            print('Calibration method =     ', self.b.calibration_method)
            self.b.calibration_timer(self.delta_t)
            self.b.frame_rate =  self.frame_rate
            print('Trigger method =         ', self.b.trigger_method)
            if self.b.trigger_method == 'INT':
                print('Frame rate =             ', self.b.frame_rate, 'Hz\n')
                # print('Average method =         ', self.b.average_state(self.aver_stat))
                # print('Average data type =      ', self.b.average_data(self.aver_type))
                # print('Average count =          ', self.b.average_count(self.aver_coun))
            else:
                print('Frame rate =             ', round(1/self.EXT_peri), 'Hz\n')
            self.b.calibrate()
            print('Bristol wavelength meter successfully configured!\n')
        except Exception as e:
            print('Bristol871 wavelength meter configuration failed: {}\n'.format(e))
            sys.exit(1)
        
    def config_lock_ins(self):
        """Configure all lock-ins using a loop."""
        try:
            for name, lockin in self.lockins.items():
                settings = self.lockin_settings[name]

                # Assign values instead of calling methods
                lockin.harmonic_values = settings["harmonic"]
                lockin.reference_phase = settings["phase"]
                lockin.gain = settings["gain"]
                lockin.sensitivity = settings["sens"]
                lockin.time_constant = settings["TC"]
                lockin.coupling = settings["coupling"]
                lockin.vmode(settings["vmode"])
                lockin.imode = settings["imode"]
                lockin.fet = settings["fet"]
                lockin.shield = settings["shield"]
                lockin.reference = settings["reference"]
                lockin.slope = settings["slope"]
                lockin.curve_buffer_triggered = settings["trigger_mode"]

                print(f"{name} Lock-in Amplifier successfully configured!")
        except Exception as e:
            print(f"SR7265 Lock-in amplifier configuration failed: {e}")
            sys.exit(1)
    
    def init_buffer(self):
        """Initialize Bristol wavelength meter buffer"""
        try:
            self.b.buffer_control('INIT')                                                                   # Initilize buffer
            print('Bristol buffer initialized!\n')
        except Exception as e:
            print('Bristol871 wavelength meter buffer initialization failed: {}\n'.format(e))
            sys.exit(1)
        
        """Initialize buffers for all lock-ins using a loop."""
        try:
            for name, lockin in self.lockins.items():
                settings = self.lockin_settings[name]
                lockin.set_buffer(points=settings["length"], quantities=None, interval=settings["interval"])
                lockin.init_curve_buffer()
            print("All lock-in buffers initialized!\n")
        except Exception as e:
            print(f"SR7265 Lock-in amplifier buffer initialization failed: {e}")
            sys.exit(1)

    def EXT_trig_measure(self):
        """External trgiger mrthod for Bristol wavelength meter during measurements"""
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
            self.b.buffer_control('OPEN')
            while i < self.EXT_NPeri:
                if i == 0:
                    t0 = perf_counter()
                while perf_counter() - t0 < self.EXT_times[i]:
                    pass
                timestamps_before_rise.append(time())
                task.write(self.triple_rise)
                timestamps_after_rise.append(time())
                t1 = perf_counter()
                while perf_counter() - t1 < (self.EXT_H):
                    pass
                task.write(self.EXT_fall)
                i = i + 1
                print(f"\rTime remaining:          {int(self.MeasureDuration-i*self.EXT_peri):4d}", 's', end='')
            sleep(self.EXT_L)
            for lockin in self.lockins.values():
                        lockin.halt_buffer()
            self.b.buffer_control('CLOS')
            elap_time = perf_counter() - t0
            task.write(self.triple_fall)
            print("=============== Measurement Completed ===============")
            print(f'{self.EXT_NPeri} periods of {self.EXT_peri} seconds')
            task.stop()
            start_time = (timestamps_before_rise[0]+timestamps_after_rise[0]) / 2
            for j in range(len(timestamps_before_rise)):
                timestamp = (timestamps_before_rise[j] + timestamps_after_rise[j]) / 2          # Average of before and after write
                formatted_timestamp = strftime("%Y-%m-%dT%H:%M:%S.", localtime(timestamp)) + f"{timestamp % 1:.3f}".split(".")[1]
                timestamps.append(formatted_timestamp)

        return start_time, elap_time, timestamps
    
    def INT_trig_measure(self):
        """Internal trgiger mrthod for Bristol wavelength meter during measurements"""
        print('Bristol wavelength meter is operating at INTERNAL trigger mode...')
        with nidaqmx.Task() as task:
            # Logic TTL at the selected DIO channel gates
            task.do_channels.add_do_chan(f"{self.NI_channel}/port0/line1")                      # DIO1: Gate16, lock-ins
            task.do_channels.add_do_chan(f"{self.NI_channel}/port0/line3")                      # DIO3: Gate19, function generator
            task.start()
            i = 0
            b_timestamps, g_timestamps, fields, temps = [], [], [], []
            print(f'Measurement duration =   {int(self.MeasureDuration):4d}', 's')
            self.countdown(5)
            print("\n=============== Measurement Initiated ===============")
            i, j = 0, 0  # Indices for gaussmeter and B0 sweep
            self.b.buffer_control('OPEN')
            start_time = time()
            task.write(self.double_rise)

            t0 = perf_counter()  # High-precision reference start time

            while i < self.gauss_Nperiods:
                target_time = t0 + self.gauss_times[i]  # Precompute exact target time
                
                # Hybrid sleep strategy: Coarse sleep first, then fine-tune with busy wait
                wait_time = target_time - perf_counter()
                if wait_time > 0.002:
                    sleep(wait_time - 0.001)
                
                while perf_counter() < target_time:
                    if target_time - perf_counter() > 0.001:
                        sleep(0)  # Yield CPU to prevent excessive busy-waiting
                
                # Record gaussmeter measurements
                fields.append(self.g.field)
                temps.append(self.g.temperature)

                i += 1  # Move to next gaussmeter measurement
                print(f"\rTime remaining:          {int(self.MeasureDuration-i*self.gauss_period):4d}", 's', end='')       
            for lockin in self.lockins.values():
                        lockin.halt_buffer()
            self.b.buffer_control('CLOS')
            elap_time = perf_counter() - t0
            task.write(self.double_fall)
            print("=============== Measurement Completed ===============")
            task.stop()
            b_timestamp = [start_time + INT_time for INT_time in self.INT_times]
            for j in range(self.INT_NPeri):
                formatted_timestamp = strftime("%Y-%m-%dT%H:%M:%S.", localtime(b_timestamp[j])) + f"{b_timestamp[j] % 1:.3f}".split(".")[1]
                b_timestamps.append(formatted_timestamp)
            g_timestamp = [start_time + gauss_time for gauss_time in self.gauss_times]
            for k in range(self.gauss_Nperiods):
                formatted_g_timestamp = strftime("%Y-%m-%dT%H:%M:%S.", localtime(g_timestamp[k])) + f"{g_timestamp[k] % 1:.3f}".split(".")[1]
                g_timestamps.append(formatted_g_timestamp)

        return start_time, elap_time, b_timestamps, g_timestamps, fields, temps
    
    def save_gaussmeter_data(self, path, filename, timestamps, fields, temps):
        """Save Gaussmeter data to a CSV file."""
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
                header = "Timestamp,MagneticFluxDensity(G),Temperature(C)\n"
                log.write(header)
                for timestamp,field,temp in zip(timestamps,fields,temps):
                    log.write(f"{timestamp},{field},{temp}\n")

            print(f"Successfully saved {len(timestamps)} measurements from Lakeshore 475 DSP Gaussmeter.")
        except Exception as e:
            print(f"Error saving data: {e}")

    def get_lock_in_buffer(self, path, filename, t0):
        """Retrieve data from all lock-in amplifiers' buffers."""
        print("\nRetrieving data from lock-in amplifiers buffer...")

        data = []
        timestamps = []

        for name, lockin in self.lockins.items():
            try:
                raw = lockin.get_buffer(quantity=None, convert_to_float=False, wait_for_buffer=True)
                XY = lockin.buffer_to_float(raw, sensitivity=self.lockin_settings[name]["sens"], raise_error=True)
                X, Y = XY["x"], XY["y"]
                status = lockin.curve_buffer_status
                print(f"{name} buffer status: {status}")

                data.extend([X, Y])
            except Exception as e:
                print(f"Error retrieving data from {name} lock-in: {e}")

        # Generate timestamps for lock-ins
        timestamp_values = [t0 + n * self.lockin_settings["2f"]["interval"] for n in range(len(data[0]))]
        timestamps = [
            strftime("%Y-%m-%dT%H:%M:%S.", localtime(t)) + f"{t % 1:.3f}".split(".")[1]
            for t in timestamp_values
        ]
        data.insert(0, timestamps)

        # Save lock-in buffer data
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
                for key, lockin in self.lockins.items():
                    log.write(f"#{key} Time Constant [s]: {self.lockin_settings[key]['TC']}\n")
                    log.write(f"#{key} Sensitivity [V]: {self.lockin_settings[key]['sens']}\n")

                log.write("#Field Input Voltage\n")
                log.write("#Preamp gain\n")
                header = "Timestamp,X_1f,Y_1f,X_2f,Y_2f,X_dc,Y_dc,X_mod,Y_mod\n"
                log.write(header)

                for row in zip(*data):
                    log.write(",".join(map(str, row)) + "\n")
        except Exception as e:
            print(f"An error occurred while saving data: {e}")

    def measure(self):
        """Run measurement sequence."""
        # Check if buffer length is exceeded
        exceeded = [
            name
            for name in self.lockins
            if self.MeasureDuration / self.lockin_settings[name]["interval"] > self.lockin_settings[name]["length"]
        ]

        if exceeded:
            print(f"Number of data points exceeds buffer length for: {', '.join(exceeded)}.")
            return

        if self.b.trigger_method == "INT":
            start_time, elap_time, b_timestamps, g_timestamps, fields, temps = self.INT_trig_measure()
        else:
            start_time, elap_time, b_timestamps, g_timestamps, fields, temps = self.EXT_trig_measure()

        self.save_gaussmeter_data(gaussmeter_path, f"Gaussmeter_{dt.now().strftime('%Y-%m-%d')}.csv", g_timestamps, fields, temps)
        self.b.get_buffer(wavelengthmeter_path, f"Bristol_{dt.now().strftime('%Y-%m-%d')}.csv", elap_time, b_timestamps)
        self.get_lock_in_buffer(lockin_path, f"Faraday_lockins_{dt.now().strftime('%Y-%m-%d')}.lvm", start_time)

    def countdown(self, seconds):
        for i in range(seconds, -1, -1):
            print(f"\rMeasurement starts in:        {i}", end="")
            sleep(1)

if __name__ == "__main__":
    m = Main()
    m.config_NIcDAQ()
    m.config_wavelengthmeter()
    m.config_lock_ins()
    m.init_buffer()
    m.measure()