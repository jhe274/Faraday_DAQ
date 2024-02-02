from toptica.lasersdk.dlcpro.v2_0_3 import DLCpro, SerialConnection
import nidaqmx.system
import numpy as np
from time import time, sleep

DLCPRO_CONNECTION = 'COM5'
"""
Measurement settings
"""
rise = [True]
fall = [False]
scan_speed = 0.05 #V/s
start_voltage = 69 #V
end_voltage = 71 #V
scan_duration = np.abs(start_voltage - end_voltage) / scan_speed

def config_DLCPRO():
    with DLCpro(SerialConnection(DLCPRO_CONNECTION)) as DLC:
        print("=== Connected Device, Setting Parameters for DLC ===")
        # DLC.laser1.scan.amplitude.set(0) #V
        # DLC.laser1.wide_scan.stop()
        DLC.laser1.wide_scan.output_channel.set(50)
        DLC.laser1.scan.offset.set(70) #V
        DLC.laser1.wide_scan.shape.set(0) #0 is sawtooth, 1 is triangle
        DLC.laser1.wide_scan._speed.set(scan_speed)
        DLC.laser1.wide_scan.duration.set(scan_duration)

        DLC.laser1.wide_scan.scan_begin.set(start_voltage)
        DLC.laser1.wide_scan.scan_end.set(end_voltage)
        # DLC.laser1.wide_scan.start()
        DLC.laser1.wide_scan.trigger.input_enabled.set(True)
        DLC.laser1.wide_scan.trigger.input_channel.set(2)

        with nidaqmx.Task() as task:
            task.do_channels.add_do_chan("cDAQ1Mod4/port0/line2") # DIO2, Toptica
            task.start()
            print("=== Wide Scan Initiated ===")

            DLC.laser1.wide_scan.start()
            sleep(2)

            task.write(rise)
            sleep(scan_duration)
            task.write(fall)

            DLC.laser1.wide_scan.stop()
            task.stop()

config_DLCPRO()