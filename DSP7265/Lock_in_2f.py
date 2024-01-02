from pymeasure.instruments.signalrecovery import DSP7265

class L2f():
    def __init__(self, address):
        self.name = "2f lock-in amplifier"
        self.l2f = DSP7265(f"GPIB0::{address}::INSTR")
        
    def signal_channel(self):
        self.l2f.coupling = 0                                                   # AC coupling
        self.l2f.imod = "voltage mode"                                          # Set to measure voltages
        self.l2f.fet = 1                                                        # Use FET pre-amp
        self.l2f.shield = 1                                                     # Float shields
        self.l2f.setDifferentialMode                                            # Set to differential mode A-B

    def reference_channel(self):
        self.l2f.reference_phase = 16.92                                        # [°]
        self.l2f.harmonic_values = 2                                            # Reference 1st harmonic
        self.l2f.reference = "external front"                                   # Reference channel is in the front panel

    def filters(self, TC, sens):
        self.l2f.gain = 40                                                      # Set gain to 20 dB
        self.l2f.time_constant = TC                                             # TC = 100 ms
        self.l2f.slope = 24                                                     # slope of low-pass fileter in dB/octave
        self.l2f.sensitivity = sens                                             # Sensitivity = 200 mV

    def auto_functions(self):
        self.l2f.auto_gain = 0                                                  # Auto AC Gain OFF
        # self.l2f.auto_phase()                                                   # Auto phase
        # self.l2f.auto_sensitivity()                                             # Auto sensitivity
    
    def trigger_buffer(self):
        self.l2f.curve_buffer_triggered = 0                                     # Set data taking to trigger mode with one complete curve or set of curves

    def halt_buffer(self):
        self.l2f.halt_buffer()

    def init_curve_buffer(self, LEN, STR):
        """
            points corresponds to the Length option in Curve Buffer Menu, max at 32768
            quantities corresponds to the Curve Selection in Curve Buffer Menu, default is 'X' & 'Y'
            interval corresponds to the Time/Point option in Curve Buffer Menu
            min = 1.25 ms/point, and if TC >= 5 ms, then interval = 640 micros
        """
        print(f'Initializing {self.name} buffer...')
        self.l2f.set_buffer(points=LEN, quantities=None, interval=STR)
        self.l2f.init_curve_buffer()
    
    def get_curve_buffer(self, sens):
        raw = self.l2f.get_buffer(quantity=None, convert_to_float=False, wait_for_buffer=True)
        XY = self.l2f.buffer_to_float(raw, sensitivity=sens, raise_error=True)
        X, Y = XY['x'], XY['y']
        print(f'{self.name} buffer status is ' + str(self.l2f.curve_buffer_status))

        return X, Y
    


# L2F = L2f()
# # L2F.Signal_channel()
# # L2F.Reference_channel()
# # L2F.Filters()
# print(L2F.Curve_buffer())
# print(type(L2F.Curve_buffer()))