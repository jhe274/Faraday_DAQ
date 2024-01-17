import sys
from toptica.lasersdk.dlcpro.v2_0_3 import DLCpro, SerialConnection, DeviceNotFoundError
import numpy as np

class Laser(object):
    def __init__(self, port_number):
        self.serial_port = SerialConnection(port_number)                              # Serial port number

        """
        SC - Scan Control
        """
        self.ScanOffset = 70                                                            # [V]
        self.ScanAmplitude = 0                                                          # [V]
    
        """
        Wide Scan
        """
        self.StartVoltage = 69                                                          # [V]
        self.EndVoltage = 71                                                            # [V]
        self.ScanSpeed = 0.05                                                           # [V/s]
        self.ScanDuration = np.abs(self.StartVoltage-self.EndVoltage)/self.ScanSpeed    # [s], (integer)

    def WideScan(self):
            """
            TOPTICA DLC pro
            """
            try:
                with DLCpro(self.serial_port) as dlc:
                    dlc.laser1.wide_scan.output_channel.set(50)                          # PC Voltage
                    dlc.laser1.scan.offset.set(self.ScanOffset)
                    dlc.laser1.wide_scan.shape.set(0)                                    # 0 -> Sawtooth, 1 -> Traingle
                    dlc.laser1.wide_scan._speed.set(self.ScanSpeed)
                    dlc.laser1.wide_scan.duration.set(self.ScanDuration)
                    dlc.laser1.wide_scan.scan_begin.set(self.StartVoltage)
                    dlc.laser1.wide_scan.scan_end.set(self.EndVoltage)
                    dlc.laser1.wide_scan.trigger.input_enabled.set(True)                 # True -> Enable, False -> Disable
                    dlc.laser1.wide_scan.trigger.input_channel.set(2)                    # 2 -> Digital Input 2
            except DeviceNotFoundError:
                sys.stderr.write('Device not found')