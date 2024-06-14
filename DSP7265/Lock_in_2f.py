from pymeasure.instruments.signalrecovery import DSP7265

class L2f():
    def __init__(self, address):
        self.name = "2f lock-in amplifier"
        self.l2f = DSP7265(f"GPIB0::{address}::INSTR")
        
    def signal_channel(self):
        self.l2f.coupling = 0                                                   # AC coupling
        self.l2f.imode = "voltage mode"                                          # Set to measure voltages
        self.l2f.fet = 1                                                        # Use FET pre-amp
        self.l2f.shield = 1                                                     # Float shields
        self.l2f.setDifferentialMode                                            # Set to differential mode A-B

    def reference_channel(self, phase, harmonic):
        self.l2f.reference_phase = phase                                        # [°]
        self.l2f.harmonic_values = harmonic                                            # Reference 1st harmonic
        self.l2f.reference = "external front"                                   # Reference channel is in the front panel

    def filters(self, gain, TC, sens):
        self.l2f.gain = gain
        self.l2f.time_constant = TC
        self.l2f.slope = 24                                                     # slope of low-pass fileter in dB/octave
        self.l2f.sensitivity = sens

    def auto_functions(self):
        self.l2f.auto_gain = 0                                                  # Auto AC Gain OFF
        self.l2f.auto_phase()                                                   # Auto phase
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
            min = 1.25 ms/point, and if TC >= 5 ms, then interval = 640 microseconds
        """
        self.l2f.set_buffer(points=LEN, quantities=None, interval=STR)
        self.l2f.init_curve_buffer()
        print(f'{self.name} buffer initialized.')
    
    def get_curve_buffer(self, sens):
        raw = self.l2f.get_buffer(quantity=None, convert_to_float=False, wait_for_buffer=True)
        XY = self.l2f.buffer_to_float(raw, sensitivity=sens, raise_error=True)
        X, Y = XY['x'], XY['y']
        status = self.l2f.curve_buffer_status
        print(f'{self.name} buffer status is ' + str(status))

        return X, Y, status