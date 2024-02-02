from pymeasure.instruments.signalrecovery import DSP7265

class DC:
    def __init__(self, address):
        self.name = "DC lock-in amplifier"
        self.dc = DSP7265(f"GPIB0::{address}::INSTR")
        
    def signal_channel(self):
        self.dc.coupling = 0                                                    # AC coupling
        self.dc.imod = "voltage mode"                                           # Set to measure voltages
        self.dc.fet = 1                                                         # Use fet pre-amp
        self.dc.shield = 1                                                      # Float shields
        # self.dc.setDifferentialMode                                             # Set to differential mode A-B

    def reference_channel(self):
        self.dc.reference_phase = -21.27                                        # [°]
        self.dc.harmonic_values = 1                                             # Reference 1st harmonic
        self.dc.reference = "external front"                                    # Reference channel is in the front panel

    def filters(self, gain, TC, sens):
        self.dc.gain = gain
        self.dc.time_constant = TC
        self.dc.slope = 24                                                      # slope of low-pass fileter in dB/octave
        self.dc.sensitivity = sens

    def auto_functions(self):
        self.dc.auto_gain = 0                                                   # Auto AC Gain OFF
        # self.dc.auto_phase()                                                    # Auto phase
        # self.dc.auto_sensitivity()                                              # Auto sensitivity

    def trigger_buffer(self):
        self.dc.curve_buffer_triggered = 0                                      # Set data taking to trigger mode with one complete curve or set of curves

    def halt_buffer(self):
        self.dc.halt_buffer()

    def init_curve_buffer(self, LEN, STR):
        """
            points corresponds to the Length option in Curve Buffer Menu, max at 32768
            quantities corresponds to the Curve Selection in Curve Buffer Menu, default is 'X' & 'Y'
            interval corresponds to the Time/Point option in Curve Buffer Menu
            min = 1.25 ms/point, and if TC >= 5 ms, then interval = 640 micros
        """
        print(f'{self.name} buffer initialized.')
        self.dc.set_buffer(points=LEN, quantities=None, interval=STR)
        self.dc.init_curve_buffer()
    
    def get_curve_buffer(self, sens):
        raw = self.dc.get_buffer(quantity=None, convert_to_float=False, wait_for_buffer=True)
        XY = self.dc.buffer_to_float(raw, sensitivity=sens, raise_error=True)
        X, Y = XY['x'], XY['y']
        status = self.dc.curve_buffer_status
        print(f'{self.name} buffer status is ' + str(status))

        return X, Y, status

# DC = DC()
# # Modu.Signal_channel()
# # Modu.Reference_channel()
# # Modu.Filters()
# print(DC.Curve_buffer())
# print(type(DC.Curve_buffer()))