import time as t
from datetime import datetime as dt
import nidaqmx.system
from Lock_in_Mod import Mod
from Lock_in_2f import L2f
from Lock_in_DC import DC

class Main:
    system = nidaqmx.system.System.local()
    system.driver_version

    def __init__(self):
        """
            Mod lock-in amplifier, model DSP7265
        """
        self.mod = Mod(7)               # GPIB address: 7
        self.TC_mod = 50E-3             # Time Constant: [s]
        self.sens_mod = 50E-3           # Sensitivity: [V]
        self.len_mod = 16384            # Storage points
        self.STR_mod = 50E-3            # Curve buffer Storage Interval: [s/point]

        """
            2f lock-in amplifier, model DSP7265
        """
        self.l2f = L2f(8)               # GPIB address: 8
        self.TC_2f = 5E-3               # Time Constant: [s]
        self.sens_2f = 50E-3            # Sensitivity: [V]
        self.len_2f = 16384             # Storage points
        self.STR_2f = 5E-3              # Curve buffer Storage Interval

        """
            DC lock-in amplifier, model DSP7265
        """
        self.dc = DC(9)                 # GPIB address: 9
        self.TC_dc = 50E-3              # Time Constant: [s]
        self.sens_dc = 50E-3            # Sensitivity: [V]
        self.len_dc = 16384             # Storage points
        self.STR_dc = 50E-3             # Curve buffer Storage Interval: [s/point]

        """
            Measurement settings
        """
        self.t_mea = 2                  # Measure time
        self.rise = [True]
        self.fall = [False]
    
    def init_NI9401(self):
        """
            Initialize NI-9401
        """
        for device in self.system.devices:
            print(device)

    def config_lock_ins(self):
        """
            Configure triple modulation lock-ins
            and set buffer to trigger mode
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

    def trigger_mea(self):
        """
            Trigger logic TTL at the selected DIO channel
        """
        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan("cDAQ1Mod4/port0/line1") # DIO1: Gate16
            task.start()
            
            start_time = dt.now()
            task.write(self.rise)
            print(f"Timestamp at trigger measurement: {start_time}")

            t.sleep(self.t_mea)

            end_time = dt.now()
            self.mod.halt_buffer()
            self.l2f.halt_buffer()
            self.dc.halt_buffer()
            task.write(self.fall)
            print(f"Timestamp at halt measurement: {end_time}")

        return task.stop
    
    def trigger_calc(self):
        return
    
    def get_lock_in_buffer(self):
        """
            Retrieving data from lock-in buffer
        """
        X_mod, Y_mod = self.mod.get_curve_buffer(self.sens_mod)
        X_2f, Y_2f = self.l2f.get_curve_buffer(self.sens_2f)
        X_dc, Y_dc = self.dc.get_curve_buffer(self.sens_dc)

        return X_mod, Y_mod, X_2f, Y_2f, X_dc, Y_dc

mf = Main()
# mf.config_lock_ins()
# mf.init_buffer()
mf.trigger_mea()
# mf.get_lock_in_buffer()
