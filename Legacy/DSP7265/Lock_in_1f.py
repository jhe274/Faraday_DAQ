from pymeasure.instruments.signalrecovery import DSP7265

class L1f():
    def __init__(self, address):
        self.name = "1f lock-in amplifier"
        self.l1f = DSP7265(f"GPIB0::{address}::INSTR")
        
    def signal_channel(self):
        self.l1f.coupling = 0                                                   # AC coupling
        self.l1f.imode = "voltage mode"                                         # Set to measure voltages
        self.l1f.fet = 1                                                        # Use FET pre-amp
        self.l1f.shield = 1                                                     # Float shields
        self.l1f.setDifferentialMode                                            # Set to differential mode A-B

    def reference_channel(self, phase, harmonic):
        self.l1f.reference_phase = phase                                        # [°]
        self.l1f.harmonic_values = harmonic                                     # Reference 1st harmonic
        self.l1f.reference = "external front"                                   # Reference channel is in the front panel

    def filters(self, gain, TC, sens):
        self.l1f.gain = gain
        self.l1f.time_constant = TC
        self.l1f.slope = 24                                                     # slope of low-pass fileter in dB/octave
        self.l1f.sensitivity = sens

    def auto_functions(self):
        self.l1f.auto_gain = 0                                                  # Auto AC Gain OFF
        self.l1f.auto_phase()                                                   # Auto phase
        # self.l1f.auto_sensitivity()                                             # Auto sensitivity
    
    def trigger_buffer(self):
        self.l1f.curve_buffer_triggered = 0                                     # Set data taking to trigger mode with one complete curve or set of curves

    def halt_buffer(self):
        self.l1f.halt_buffer()

    def init_curve_buffer(self, LEN, STR):
        """
            points corresponds to the Length option in Curve Buffer Menu, max at 32768
            quantities corresponds to the Curve Selection in Curve Buffer Menu, default is 'X' & 'Y'
            interval corresponds to the Time/Point option in Curve Buffer Menu
            min = 1.25 ms/point, and if TC >= 5 ms, then interval = 640 microseconds
        """
        self.l1f.set_buffer(points=LEN, quantities=None, interval=STR)
        self.l1f.init_curve_buffer()
    
    def get_curve_buffer(self, sens):
        raw = self.l1f.get_buffer(quantity=None, convert_to_float=False, wait_for_buffer=True)
        XY = self.l1f.buffer_to_float(raw, sensitivity=sens, raise_error=True)
        X, Y = XY['x'], XY['y']
        status = self.l1f.curve_buffer_status
        print(f'{self.name} buffer status is ' + str(status))

        return X, Y, status