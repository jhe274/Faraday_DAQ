from pymeasure.instruments.signalrecovery import DSP7265

class LockInAmplifier:
    """A generalized class for controlling DSP7265 Lock-in Amplifiers."""
    
    def __init__(self, address, name="Lock-in Amplifier"):
        """Initialize a lock-in amplifier with a given GPIB address."""
        self.name = name
        self.lockin = DSP7265(f"GPIB0::{address}::INSTR")
    
    def signal_channel(self):
        """Configure signal input settings."""
        self.lockin.coupling = 0  # AC coupling
        self.lockin.imode = "voltage mode"  # Measure voltages
        self.lockin.fet = True  # Enable FET pre-amp
        self.lockin.shield = True  # Float shields
        self.lockin.setDifferentialMode()  # Set to differential mode A-B

    def reference_channel(self, phase, harmonic):
        """Configure reference input settings."""
        self.lockin.reference_phase = phase  # [°]
        self.lockin.harmonic_values = harmonic  # Reference harmonic
        self.lockin.reference = "external front"  # Reference from front panel

    def filters(self, gain, TC, sens):
        """Configure lock-in amplifier filters."""
        self.lockin.gain = gain
        self.lockin.time_constant = TC
        self.lockin.slope = 24  # Low-pass filter slope [dB/octave]
        self.lockin.sensitivity = sens

    def auto_functions(self):
        """Perform auto adjustments for optimal measurements."""
        self.lockin.auto_gain(False)  # Disable Auto Gain
        self.lockin.auto_phase()  # Auto phase correction
        self.lockin.auto_sensitivity()  # Auto sensitivity

    def trigger_buffer(self):
        """Set lock-in buffer to trigger mode for data acquisition."""
        self.lockin.curve_buffer_triggered(False)  # Enable trigger mode

    def halt_buffer(self):
        """Stop data acquisition in the buffer."""
        self.lockin.halt_buffer()

    def init_curve_buffer(self, length, interval):
        """Initialize the curve buffer for storing data."""
        self.lockin.set_buffer(points=length, quantities=None, interval=interval)
        self.lockin.init_curve_buffer()

    def get_curve_buffer(self, sens):
        """Retrieve data from the buffer."""
        raw = self.lockin.get_buffer(quantity=None, convert_to_float=False, wait_for_buffer=True)
        XY = self.lockin.buffer_to_float(raw, sensitivity=sens, raise_error=True)
        X, Y = XY["x"], XY["y"]
        status = self.lockin.curve_buffer_status
        print(f"{self.name} buffer status: {status}")
        return X, Y, status
