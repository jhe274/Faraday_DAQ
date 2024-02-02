from pymeasure.instruments.signalrecovery import DSP7265

class Mod:
    def __init__(self, address):
        self.name = "Mod lock-in amplifier"
        self.mod = DSP7265(f"GPIB0::{address}::INSTR")
        
    def signal_channel(self):
        self.mod.coupling = 0                                                   # AC coupling
        self.mod.imod = "voltage mode"                                          # Set to measure voltages
        self.mod.fet = 0                                                        # Use Bipolar pre-amp
        self.mod.shield = 1                                                     # Float shields
        self.mod.setDifferentialMode                                            # Set to differential mode A-B

    def reference_channel(self):
        self.mod.reference_phase = 144.37                                       # [°]
        self.mod.harmonic_values = 1                                            # Reference 1st harmonic
        self.mod.reference = "external front"                                   # Reference channel is in the front panel

    def filters(self, gain, TC, sens):
        self.mod.gain = gain
        self.mod.time_constant = TC
        self.mod.slope = 24                                                     # slope of low-pass fileter in dB/octave
        self.mod.sensitivity = sens

    def auto_functions(self):
        self.mod.auto_gain = 0                                                  # Auto AC Gain OFF
        # self.mod.auto_phase()                                                   # Auto phase
        # self.mod.auto_sensitivity()                                             # Auto sensitivity

    def trigger_buffer(self):
        self.mod.curve_buffer_triggered = 0                                     # Set data taking to trigger mode with one complete curve or set of curves

    def halt_buffer(self):
        self.mod.halt_buffer()

    def init_curve_buffer(self, LEN, STR):
        """
            points corresponds to the Length option in Curve Buffer Menu, max at 32768
            quantities corresponds to the Curve Selection in Curve Buffer Menu, default is 'X' & 'Y'
            interval corresponds to the Time/Point option in Curve Buffer Menu
            min = 1.25 ms/point, and if TC >= 5 ms, then interval = 640 micros
        """
        print(f'{self.name} buffer initialized.')
        self.mod.set_buffer(points=LEN, quantities=None, interval=STR)
        self.mod.init_curve_buffer()
    
    def get_curve_buffer(self, sens):
        raw = self.mod.get_buffer(quantity=None, convert_to_float=False, wait_for_buffer=True)
        XY = self.mod.buffer_to_float(raw, sensitivity=sens, raise_error=True)
        X, Y = XY['x'], XY['y']
        status = self.mod.curve_buffer_status
        print(f'{self.name} buffer status is ' + str(status))
        
        return X, Y, status

# Modu = Mod()
# # Modu.Signal_channel()
# # Modu.Reference_channel()
# # Modu.Filters()
# print(Modu.Curve_buffer())
# print(type(Modu.Curve_buffer()))