import sys, os, datetime
from time import strftime, localtime
from toptica.lasersdk.dlcpro.v2_5_3 import DLCpro, SerialConnection, DeviceNotFoundError
from toptica.lasersdk.utils.dlcpro import * # for extract_float_arrays(...)

class Laser(object):
    def __init__(self, port_number):
        self.serial_port = SerialConnection(port_number)                                    # Serial port number

        """
        SC - Scan Control
        """
        # self.ScanOffset = 70                                                                # [V]
        # self.ScanAmplitude = 0                                                              # [V]
    
        """
        Wide Scan
        """
        # self.StartVoltage = 69                                                              # [V]
        # self.EndVoltage = 71                                                                # [V]
        # self.ScanSpeed = 0.05                                                               # [V/s]
        # self.ScanDuration = np.abs(self.StartVoltage-self.EndVoltage)/self.ScanSpeed        # [s], (integer)

    def WideScan(self, OutputChannel, ScanOffset, StartVoltage, 
                 EndVoltage, ScanSpeed, ScanShape, ScanDuration,
                 InputTrigger, RecorderStepsize, Ch1, Ch2,
                 LPfilter, Ch1_CutOff, Ch2_CutOff):
            """
            TOPTICA DLC pro
            """
            try:
                with DLCpro(self.serial_port) as dlc:
                    sn = dlc.serial_number.get()
                    health = dlc.system_health_txt.get()
                    print('Connection established to DLC pro with serial number ' + sn)
                    print('System health: ' + health)
                    dlc.laser1.wide_scan.stop()
                    dlc.laser1.wide_scan.output_channel.set(OutputChannel)                  # PC Voltage
                    dlc.laser1.scan.offset.set(ScanOffset)
                    dlc.laser1.scan.enabled.set(False)
                    dlc.laser1.wide_scan.shape.set(ScanShape)
                    dlc.laser1.wide_scan._speed.set(ScanSpeed)
                    dlc.laser1.wide_scan.duration.set(ScanDuration)
                    dlc.laser1.wide_scan.scan_begin.set(StartVoltage)
                    dlc.laser1.wide_scan.scan_end.set(EndVoltage)
                    dlc.laser1.wide_scan.trigger.input_enabled.set(InputTrigger)            # True -> Enable, False -> Disable
                    dlc.laser1.wide_scan.trigger.input_channel.set(2)                       # 2 -> Digital Input 2
                    dlc.laser1.wide_scan.recorder_stepsize_set.set(RecorderStepsize)
                    dlc.laser1.recorder.inputs.channel1.signal.set(Ch1)
                    dlc.laser1.recorder.inputs.channel2.signal.set(Ch2)
                    dlc.laser1.recorder.inputs.channel1.low_pass_filter.enabled.set(LPfilter)
                    dlc.laser1.recorder.inputs.channel1.low_pass_filter.cut_off_frequency.set(Ch1_CutOff)
                    dlc.laser1.recorder.inputs.channel2.low_pass_filter.cut_off_frequency.set(Ch2_CutOff)
                    print('TOPTICA DLC pro successfully configured!')
            except DeviceNotFoundError as e:
                sys.stderr.write('TOPTICA DLC pro not found: {}\n'.format(e))

    def get_recorder_data(self, laser):
        """
        Read the data, recorded by the laser's recorder unit, into a dictionary
        with the following content:
        x-axis data:       'x' : {'title': _label_and_physical_unit_, 
                                'data': _array_with_x_values_}
        channel1 data:     'y' : {'title': _label_and_physical_unit_, 
                                'data': _array_with_y_values_}
        channel2 data:     'Y' : {'title': _label_and_physical_unit_, 
                                'data': _array_with_y_values_}
        sampling interval: 'dt': _sampling_interval_in_milliseconds_
        
        channel1 and channel2 data will only be available if they have been recorded,
        i.e. the respective selection was not None.
        """
        x = []
        y = []
        Y = []
        
        # read info about recorded signals and sample count
        x_title           = laser.recorder.data.channelx.name.get() \
                        + " (" + laser.recorder.data.channelx.unit.get() + ")"
        y_title           = laser.recorder.data.channel1.name.get() \
                        + " (" + laser.recorder.data.channel1.unit.get() + ")"
        Y_title           = laser.recorder.data.channel2.name.get() \
                        + " (" + laser.recorder.data.channel2.unit.get() + ")"
        sampling_interval = laser.recorder.data.recorded_sampling_interval.get()

        # read recorded data in chunks of up to 1024 samples per channel
        sample_count = laser.recorder.data.recorded_sample_count.get()
        index        = 0
        while index < sample_count:
            # read a chunk of binary data and convert it into xy arrays
            new_data = extract_float_arrays('xyY', laser.recorder.data.get_data(index, 1024))
            x       += new_data['x']
            if 'y' in new_data.keys():
                y += new_data['y']
            if 'Y' in new_data.keys():
                Y += new_data['Y']
            index += len(new_data['x'])
            print(f"\rRead {index}/{sample_count} Wide Scan data from TOPTICA DLC pro.", end="")
        # assemble result dictionary
        result       = {'x': {'title': x_title, 'data' : x}}
        result['dt'] = sampling_interval
        if len(y) > 0:
            result['y'] = {'title': y_title, 'data': y}
        if len(Y) > 0:
            result['Y'] = {'title': Y_title, 'data': Y}
            
        return result
    
    def save_recorder_data(self, path, filename, data):
        """
        Write a dictionary, returned by the get_recorder_data(..) function into
        a comma separated file.
        First row will contain headers.
        First column will contain x-axis values.
        Second column will contain y-values of channel1, if available.
        Next column will contain y-values of channel2, if available.
        Last column will contain sampling time in milliseconds.
        """
        try:
            counter = 1
            original_filename = filename
            folder_name = datetime.datetime.now().strftime("%m-%d-%Y")
            folder_path = os.path.join(path, folder_name)
            os.makedirs(folder_path, exist_ok=True)

            while os.path.isfile(os.path.join(folder_path, filename)):
                filename = f"{original_filename.split('.')[0]}_{counter}.csv"
                counter += 1
            file_path = os.path.join(folder_path, filename)

            with open(file_path, "w") as f:
                headers = []
                headers.append(data['x']['title'])
                if 'y' in data.keys():
                    headers.append(data['y']['title'])
                if 'Y' in data.keys():
                    headers.append(data['Y']['title'])
                headers.append('time (ms)')
                f.write(",".join(headers) + "\n")

                size = len(data['x']['data'])
                dt   = data['dt']
                for i in range(size):
                    values = []
                    values.append(str(data['x']['data'][i]))
                    if 'y' in data.keys():
                        values.append(str(data['y']['data'][i]))
                    if 'Y' in data.keys():
                        values.append(str(data['Y']['data'][i]))
                    values.append(str(dt * i))
                    f.write(",".join(values) + "\n")

        except Exception as e:
            print(f"An error occurred while saving data to the file: {e}")