import sys
from toptica.lasersdk.dlcpro.v2_0_3 import DLCpro, SerialConnection, DeviceNotFoundError
import numpy as np

class Laser(object):
    def __init__(self, port_number):
        self.serial_port = SerialConnection(port_number)                              # Serial port number

        """
        SC - Scan Control
        """
        # self.ScanOffset = 70                                                            # [V]
        # self.ScanAmplitude = 0                                                          # [V]
    
        # """
        # Wide Scan
        # """
        # self.StartVoltage = 69                                                          # [V]
        # self.EndVoltage = 71                                                            # [V]
        # self.ScanSpeed = 0.05                                                           # [V/s]
        # self.ScanDuration = np.abs(self.StartVoltage-self.EndVoltage)/self.ScanSpeed    # [s], (integer)

    def WideScan(self, OutputChannel, ScanOffset, StartVoltage, EndVoltage, ScanSpeed, ScanShape, ScanDuration, InputTrigger):
            """
            TOPTICA DLC pro
            """
            try:
                with DLCpro(self.serial_port) as dlc:
                    dlc.laser1.wide_scan.output_channel.set(OutputChannel)            # PC Voltage
                    dlc.laser1.scan.offset.set(ScanOffset)
                    dlc.laser1.wide_scan.shape.set(ScanShape)
                    dlc.laser1.wide_scan._speed.set(ScanSpeed)
                    dlc.laser1.wide_scan.duration.set(ScanDuration)
                    dlc.laser1.wide_scan.scan_begin.set(StartVoltage)
                    dlc.laser1.wide_scan.scan_end.set(EndVoltage)
                    dlc.laser1.wide_scan.trigger.input_enabled.set(InputTrigger)      # True -> Enable, False -> Disable
                    dlc.laser1.wide_scan.trigger.input_channel.set(2)                 # 2 -> Digital Input 2
            except DeviceNotFoundError:
                sys.stderr.write('TOPTICA DLC pro not found')