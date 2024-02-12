from ctypes import *


class ChannelInfo (Structure):
    """ the information of channel
        target_temperature: the target temperature of channel
        actual_temperature: the actual temperature of channel
        target_current: the target current of channel
        actual_current: the actual current of channel
        min_temperature: the lower limit temperature of channel
        max_temperature: the upper limit temperature of channel
        max_current: the max current of channel
        actual_voltage: the acutal voltage of channel
        mode: the work mode of channel 0:heater:  1:tec:  2:current
        trigger_mode: the trigger mode of channel 0:Output:  1:input
        sensor_type: the sensor type of channel 0:PT100:  1:PT1000:  2:NTC1:  3:NTC2:  4:Thermo C.:  5=AD590:  6:EXT1:
        7:EXT2
     """
    _fields_ = [("target_temperature", c_float),
                ("actual_temperature", c_float),
                ("target_current", c_int),
                ("actual_current", c_int),
                ("min_temperature", c_int),
                ("max_temperature", c_int),
                ("max_current", c_float),
                ("actual_voltage", c_float),
                ("mode", c_int),
                ("trigger_mode", c_int),
                ("sensor_type", c_int)
                ]


class TC300:
    tc300Lib = None
    isLoad = False

    @staticmethod
    def list_devices():
        """ List all connected tc300 devices
        Returns:
           The tc300 device list, each deice item is serialNumber/COM
        """
        size = 10240
        str1 = create_string_buffer(size)
        result = TC300.tc300Lib.List(str1, size)
        devicesStr = str1.value.decode("utf-8", "ignore").rstrip('\x00').split(',')
        length = len(devicesStr)
        i = 0
        devices = []
        devInfo = ["", ""]
        while i < length:
            str2 = devicesStr[i]
            if i % 2 == 0:
                if str2 != '':
                    devInfo[0] = str2
                else:
                    i += 1
            else:
                devInfo[1] = str2
                devices.append(devInfo.copy())
            i += 1
        return devices

    @staticmethod
    def load_library(path):
        TC300.tc300Lib = cdll.LoadLibrary(path)
        TC300.isLoad = True

    def __init__(self):
        lib_path = "./TC300COMMANDLIB_win32.dll"
        if not TC300.isLoad:
            TC300.load_library(lib_path)
        self.hdl = -1

    def open(self, serialNo, nBaud, timeout):
        """ Open TC300 device
        Args:
            serialNo: serial number of TC300 device
            nBaud: bit per second of port
            timeout: set timeout value in (s)
        Returns: 
            non-negative number: hdl number returned Successful; negative number: failed.
        """
        ret = -1
        if TC300.isLoad:
            ret = TC300.tc300Lib.Open(serialNo.encode('utf-8'), nBaud, timeout)
            if ret >= 0:
                self.hdl = ret
            else:
                self.hdl = -1
        return ret

    def is_open(self, serialNo):
        """ Check opened status of TC300 device
        Args:
            serialNo: serial number of TC300 device
        Returns: 
            0: TC300 device is not opened; 1: TC300 device is opened.
        """
        ret = -1
        if TC300.isLoad:
            ret = TC300.tc300Lib.IsOpen(serialNo.encode('utf-8'))
        return ret

    def get_handle(self, serialNo):
        """ get handle of port
        Args:
            serialNo: serial number of the device to be checked.
        Returns: 
            -1:no handle  non-negtive number: handle.
        """
        ret = -1
        if TC300.isLoad:
            ret = TC300.tc300Lib.GetHandle(serialNo.encode('utf-8'))
        return ret

    def close(self):
        """ Close opened TC300 device
        Args:
            
        Returns: 
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            ret = TC300.tc300Lib.Close(self.hdl)
        return ret

    def get_id(self, id, size):
        """ get the TC300 id
        Args:
            id: ID string include model number, hardware and firmware versions
            size: max size of return string
        Returns: 
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            s = create_string_buffer(1024)
            size = 1024
            ret = TC300.tc300Lib.GetId(self.hdl, s, size)
            id[0] = s.value.decode("utf-8", "ignore").rstrip('\x00').replace("\r\n", "")
        return ret

    def get_status(self, status):
        """  Get device status
        Args:
            status:
              Device state define 	8bit
              bit0 = 0 or 1	chan1 disabled / enabled
              bit1 = 0 or 1	chan2 disabled / enabled
              bit2 = 1	normal
              bit3 = 1	warning
              bit4 = 1	error
              bit5	Reserved
              bit6	Reserved
              bit7	Reserved
        Returns:
              0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            sta = c_byte(0)
            ret = TC300.tc300Lib.GetStatus(self.hdl, byref(sta))
            status[0] = sta.value
        return ret

    def set_channels(self, channel):
        """  Set number of channels
        Args:
            channel: channel number, 0: single channel; 1: dual channel
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            val = c_int(channel)
            ret = TC300.tc300Lib.SetChannels(self.hdl, val)
        return ret

    def get_channels(self, channel):
        """  Get number of channels
        Args:
            channel: channel number, 0: single channel; 1: dual channel
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            ch = c_int(0)
            ret = TC300.tc300Lib.GetChannels(self.hdl, byref(ch))
            channel[0] = ch.value
        return ret

    def copy_parameters(self):
        """  Copy channel 1 parameters to channel 2
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            ret = TC300.tc300Lib.CopyParameters(self.hdl)
        return ret

    def enable_channel(self, channel, status):
        """  Set channel enable state
        Args:
            channel: channel index, 1 or 2
            status: 0: Disable; 1: Enable:
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            sta = c_ubyte(status)
            ret = TC300.tc300Lib.EnableChannel(self.hdl, channel, sta)
        return ret

    def get_actual_temperature(self, channel, temperature):
        """  Get actual temperature
        Args:
            channel: channel index, 1 or 2
            temperature: the actual temperature
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            temp = c_float(0)
            ret = TC300.tc300Lib.GetActualTemperature(self.hdl, channel, byref(temp))
            temperature[0] = temp.value
        return ret

    def set_target_temperature(self, channel, temperature):
        """  Set target temperature
        Args:
            channel: channel index, 1 or 2
            temperature: the target temperature -200~400 degree celsius
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            temp = c_float(temperature)
            ret = TC300.tc300Lib.SetTargetTemperature(self.hdl, channel, temp)
        return ret

    def get_target_temperature(self, channel, temperature):
        """  Get target temperature
        Args:
            channel: channel index, 1 or 2
            temperature: the target temperature -200~400 degree celsius
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            temp = c_float(0)
            ret = TC300.tc300Lib.GetTargetTemperature(self.hdl, channel, byref(temp))
            temperature[0] = temp.value
        return ret

    def set_max_temperature(self, channel, temperature):
        """  Set max temperature
        Args:
            channel: channel index, 1 or 2
            temperature: the max value of temperature, min temperature ~ 400 degree celsius
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            temp = c_int(temperature)
            ret = TC300.tc300Lib.SetMaxTemperature(self.hdl, channel, temp)
        return ret

    def get_max_temperature(self, channel, temperature):
        """  GGet max temperature
        Args:
            channel: channel index, 1 or 2
            temperature: the max value of temperature
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            temp = c_int(0)
            ret = TC300.tc300Lib.GetMaxTemperature(self.hdl, channel, byref(temp))
            temperature[0] = temp.value
        return ret

    def set_min_temperature(self, channel, temperature):
        """  Set min temperature
        Args:
            channel: channel index, 1 or 2
            temperature: the min value of temperature, -200 degree celsius ~ max temperature.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            temp = c_int(temperature)
            ret = TC300.tc300Lib.SetMinTemperature(self.hdl, channel, temp)
        return ret

    def get_min_temperature(self, channel, temperature):
        """  Get min temperature
        Args:
            channel: channel index, 1 or 2
            temperature: the min value of temperature
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            temp = c_int(0)
            ret = TC300.tc300Lib.GetMinTemperature(self.hdl, channel, byref(temp))
            temperature[0] = temp.value
        return ret

    def get_output_voltage(self, channel, voltage):
        """  Get output voltage
        Args:
            channel: channel index, 1 or 2
            voltage: the output voltage
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            vol = c_float(0)
            ret = TC300.tc300Lib.GetOutputVoltage(self.hdl, channel, byref(vol))
            voltage[0] = vol.value
        return ret

    def get_target_output_current(self, channel, current):
        """  Get target output current
        Args:
            channel: channel index, 1 or 2
            current: the target output current.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            curr = c_int(0)
            ret = TC300.tc300Lib.GetTargetOutputCurrent(self.hdl, channel, byref(curr))
            current[0] = curr.value
        return ret

    def get_output_current(self, channel, current):
        """  Get actual output current
        Args:
            channel: channel index, 1 or 2
            current: the output current.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            curr = c_int(0)
            ret = TC300.tc300Lib.GetOutputCurrent(self.hdl, channel, byref(curr))
            current[0] = curr.value
        return ret

    def set_output_current(self, channel, current):
        """  Set target output current
        Args:
            channel: channel index, 1 or 2
            current: the output current -2000~2000 mA.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            curr = c_int(current)
            ret = TC300.tc300Lib.SetOutputCurrent(self.hdl, channel, curr)
        return ret

    def get_max_voltage(self, channel, voltage):
        """  Get max voltage
        Args:
            channel: channel index, 1 or 2
            voltage: the max value of voltage.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            vol = c_float(0)
            ret = TC300.tc300Lib.GetMaxVoltage(self.hdl, channel, byref(vol))
            voltage[0] = vol.value
        return ret

    def set_max_voltage(self, channel, voltage):
        """  Set max voltage
        Args:
            channel: channel index, 1 or 2
            voltage: the max value of voltage 0.1~24 V.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            vol = c_float(voltage)
            ret = TC300.tc300Lib.SetMaxVoltage(self.hdl, channel, vol)
        return ret

    def get_max_current(self, channel, current):
        """  Get max current
        Args:
            channel: channel index, 1 or 2
            current: the max value of current (A).
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            curr = c_float(0)
            ret = TC300.tc300Lib.GetMaxCurrent(self.hdl, channel, byref(curr))
            current[0] = curr.value
        return ret

    def set_max_current(self, channel, current):
        """  Set max current
        Args:
            channel: channel index, 1 or 2
            current: the max value of current 0.010-2.000 A.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            vol = c_float(current)
            ret = TC300.tc300Lib.SetMaxCurrent(self.hdl, channel, vol)
        return ret

    def get_mode(self, channel, mode):
        """  Get channel mode
        Args:
            channel: channel index, 1 or 2
            mode: channel mode: 0: Heater; 1: Tec; 2: Constant current; 3: Synchronize with Ch1(only for channel 2).
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            mo = c_int(0)
            ret = TC300.tc300Lib.GetMode(self.hdl, channel, byref(mo))
            mode[0] = mo.value
        return ret

    def set_mode(self, channel, mode):
        """  Set channel mode
        Args:
            channel: channel index, 1 or 2
            mode: channel mode: 0: Heater; 1: Tec; 2: Constant current; 3: Synchronize with Ch1(only for channel 2).
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            mo = c_int(mode)
            ret = TC300.tc300Lib.SetOutputCurrent(self.hdl, channel, mo)
        return ret

    def get_sensor_offset(self, channel, offset):
        """  Get sensor offset when sensor type is PT100 / PT1000
        Args:
            channel: channel index, 1 or 2
            offset: the sensor offset
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            off = c_float(0)
            ret = TC300.tc300Lib.GetSensorOffset(self.hdl, channel, byref(off))
            offset[0] = off.value
        return ret

    def set_sensor_offset(self, channel, offset):
        """  Set sensor offset when sensor type is PT100 / PT1000
        Args:
            channel: channel index, 1 or 2
            offset: the sensor offset -10~10 degree celsius
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            off = c_float(offset)
            ret = TC300.tc300Lib.SetSensorOffset(self.hdl, channel, off)
        return ret

    def get_sensor_type(self, channel, sensor_type):
        """   Get sensor type
        Args:
            channel: channel index, 1 or 2
            sensor_type: 0: PT100; 1: PT1000; 2: NTC1; 3: NTC2; 4: Thermo; 5: AD590; 6: EXT1; 7: EXT2.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            sensor = c_int(0)
            ret = TC300.tc300Lib.GetSensorType(self.hdl, channel, byref(sensor))
            sensor_type[0] = sensor.value
        return ret

    def set_sensor_type(self, channel, sensor_type):
        """  Set sensor type
        Args:
            channel: channel index, 1 or 2
            sensor_type: 0: PT100; 1: PT1000; 2: NTC1; 3: NTC2; 4: Thermo; 5: AD590; 6: EXT1; 7: EXT2.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            sensor = c_int(sensor_type)
            ret = TC300.tc300Lib.SetSensorType(self.hdl, channel, sensor)
        return ret

    def get_sensor_parameter(self, channel, parameter):
        """   Get sensor parameter
        Args:
            channel: channel index, 1 or 2
            parameter: for sensor type PT100 / PT1000: 0: 2 wire; 1: 3 wire; 2: 4 wire.
                       for sensor type Thermo: 3: J type; 4: K type.
                       other values for other sensor types.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            params = c_int(0)
            ret = TC300.tc300Lib.GetSensorParameter(self.hdl, channel, byref(params))
            parameter[0] = params.value
        return ret

    def set_sensor_parameter(self, channel, parameter):
        """  Set sensor parameter when sensor type is PT100 / PT1000 / Thermo
        Args:
            channel: channel index, 1 or 2
            parameter: for sensor type PT100 / PT1000: 0: 2 wire; 1: 3 wire; 2: 4 wire.
                       for sensor type Thermo: 3: J type; 4: K type.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            params = c_int(parameter)
            ret = TC300.tc300Lib.SetSensorParameter(self.hdl, channel, params)
        return ret

    def get_ntc_beta(self, channel, constant):
        """  Get β value when sensor type is NTC1
        Args:
            channel: channel index, 1 or 2
            constant: the β value for NTC1 sensor.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            const = c_float(0)
            ret = TC300.tc300Lib.GetNtcBeta(self.hdl, channel, byref(const))
            constant[0] = const.value
        return ret

    def set_ntc_beta(self, channel, constant):
        """  Set β value when sensor type is NTC1
        Args:
            channel: channel index, 1 or 2
            constant: the β value for NTC1 sensor 0~9999.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            const = c_float(constant)
            ret = TC300.tc300Lib.SetNtcBeta(self.hdl, channel, const)
        return ret

    def get_ext_beta(self, channel, constant):
        """  Get β value when sensor type is EXT1
        Args:
            channel: channel index, 1 or 2
            constant: the β value for EXT1 sensor.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            const = c_float(0)
            ret = TC300.tc300Lib.GetExtBeta(self.hdl, channel, byref(const))
            constant[0] = const.value
        return ret

    def set_ext_beta(self, channel, constant):
        """  Set β value when sensor type is EXT1
        Args:
            channel: channel index, 1 or 2
            constant:the β value for EXT1 sensor 0~9999.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            const = c_float(constant)
            ret = TC300.tc300Lib.SetExtBeta(self.hdl, channel, const)
        return ret

    def get_T0_constant(self, channel, t0):
        """  Get T0 value when sensor type is NTC1 or EXT1
        Args:
            channel: channel index, 1 or 2
            t0: the T0 value for NTC1 or EXT1 sensor.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            const = c_float(0)
            ret = TC300.tc300Lib.GetT0Constant(self.hdl, channel, byref(const))
            t0[0] = const.value
        return ret

    def set_T0_constant(self, channel, t0):
        """  Set T0 value when sensor type is NTC1 or EXT1
        Args:
            channel: channel index, 1 or 2
            t0: the T0 value for NTC1 or EXT1 sensor 0~999.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            const = c_float(t0)
            ret = TC300.tc300Lib.SetT0Constant(self.hdl, channel, const)
        return ret

    def get_R0_constant(self, channel, r0):
        """  Get R0 value when sensor type is NTC1 or EXT1
        Args:
            channel: channel index, 1 or 2
            r0: the R0 value for NTC1 or EXT1 sensor.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            const = c_float(0)
            ret = TC300.tc300Lib.GetR0Constant(self.hdl, channel, byref(const))
            r0[0] = const.value
        return ret

    def set_R0_constant(self, channel, r0):
        """  Set T0 value when sensor type is NTC1 or EXT1
        Args:
            channel: channel index, 1 or 2
            r0: the R0 value for NTC1 or EXT1 sensor 0~999.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            const = c_float(r0)
            ret = TC300.tc300Lib.SetR0Constant(self.hdl, channel, const)
        return ret

    def get_hartA_constant(self, channel, hartA):
        """  Get Hart A value when sensor type is NTC2 or EXT2
        Args:
            channel: channel index, 1 or 2
            hartA: the Hart A value for NTC2 or EXT2 sensor.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            const = c_float(0)
            ret = TC300.tc300Lib.GetHartAConstant(self.hdl, channel, byref(const))
            hartA[0] = const.value
        return ret

    def set_hartA_constant(self, channel, hartA):
        """  Set Hart A value when sensor type is NTC2 or EXT2
        Args:
            channel: channel index, 1 or 2
            hartA: the Hart A value for NTC2 or EXT2 sensor -9.9999~9.9999.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            const = c_float(hartA)
            ret = TC300.tc300Lib.SetHartAConstant(self.hdl, channel, const)
        return ret

    def get_hartB_constant(self, channel, hartB):
        """  Get Hart B value when sensor type is NTC2 or EXT2
        Args:
            channel: channel index, 1 or 2
            hartB: the Hart B value for NTC2 or EXT2 sensor.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            const = c_float(0)
            ret = TC300.tc300Lib.GetHartBConstant(self.hdl, channel, byref(const))
            hartB[0] = const.value
        return ret

    def set_hartB_constant(self, channel, hartB):
        """  Set Hart B value when sensor type is NTC2 or EXT2
        Args:
            channel: channel index, 1 or 2
            hartB: the Hart B value for NTC2 or EXT2 sensor -9.9999~9.9999.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            const = c_float(hartB)
            ret = TC300.tc300Lib.SetHartBConstant(self.hdl, channel, const)
        return ret

    def get_hartC_constant(self, channel, hartC):
        """  Get Hart C value when sensor type is NTC2 or EXT2
        Args:
            channel: channel index, 1 or 2
            hartC: the Hart C value for NTC2 or EXT2 sensor.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            const = c_float(0)
            ret = TC300.tc300Lib.GetHartCConstant(self.hdl, channel, byref(const))
            hartC[0] = const.value
        return ret

    def set_hartC_constant(self, channel, hartC):
        """  Set Hart C value when sensor type is NTC2 or EXT2
        Args:
            channel: channel index, 1 or 2
            hartC: the Hart C value for NTC2 or EXT2 sensor -9.9999~9.9999.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            const = c_float(hartC)
            ret = TC300.tc300Lib.SetHartCConstant(self.hdl, channel, const)
        return ret

    def get_trigger_mode(self, channel, mode):
        """  Get trigger mode
        Args:
            channel: channel index, 1 or 2
            mode: trigger mode: 0: output; 1: input.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            mo = c_int(0)
            ret = TC300.tc300Lib.GetTriggerMode(self.hdl, channel, byref(mo))
            mode[0] = mo.value
        return ret

    def set_trigger_mode(self, channel, mode):
        """  Set trigger mode
        Args:
            channel: channel index, 1 or 2
            mode: trigger mode: 0: output; 1: input.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            mo = c_int(mode)
            ret = TC300.tc300Lib.SetTriggerMode(self.hdl, channel, mo)
        return ret

    def get_brightness(self, brightness):
        """  Get LCD brightness
        Args:
            brightness: LCD brightness.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            bright = c_int(0)
            ret = TC300.tc300Lib.GetBrightness(self.hdl, byref(bright))
            brightness[0] = bright.value
        return ret

    def set_brightness(self, brightness):
        """   Set LCD brightness
        Args:
            brightness: LCD brightness 10~100.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            bright = c_int(brightness)
            ret = TC300.tc300Lib.SetBrightness(self.hdl, bright)
        return ret

    def get_knob_state(self, state):
        """  Get knob state
        Args:
            state: knob state: 0: unlocked; 1: locked.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            sta = c_int(0)
            ret = TC300.tc300Lib.GetKnobState(self.hdl, byref(sta))
            state[0] = sta.value
        return ret

    def set_knob_state(self, state):
        """   Set knob state
        Args:
            state: knob state: 0: unlocked; 1: locked.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            sta = c_int(state)
            ret = TC300.tc300Lib.SetKnobState(self.hdl, sta)
        return ret

    def get_dark_status(self, status):
        """  Get dark mode
        Args:
            status: dark mode: 0: disable; 1: enable.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            sta = c_int(0)
            ret = TC300.tc300Lib.GetDarkStatus(self.hdl, byref(sta))
            status[0] = sta.value
        return ret

    def set_dark_status(self, status):
        """   Set dark mode
        Args:
            status: dark mode: 0: disable; 1: enable.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            sta = c_int(status)
            ret = TC300.tc300Lib.SetDarkStatus(self.hdl, sta)
        return ret

    def get_quiet_mode(self, mode):
        """  Get quiet mode
        Args:
            mode: quiet mode: 0: disable; 1: enable.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            mo = c_int(0)
            ret = TC300.tc300Lib.GetQuietMode(self.hdl, byref(mo))
            mode[0] = mo.value
        return ret

    def set_quiet_mode(self, mode):
        """   Set quiet mode
        Args:
            mode: >quiet mode: 0: disable; 1: enable.
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            mo = c_int(mode)
            ret = TC300.tc300Lib.SetQuietMode(self.hdl, mo)
        return ret

    def get_PID_parameter(self, p, i, d, period):
        """  Get quiet mode
        Args:
            p: Kp:
            i: Ti:
            d: Td:
            period: period time
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            PID_p = c_float(0)
            PID_i = c_float(0)
            PID_d = c_float(0)
            PID_period = c_int(0)
            ret = TC300.tc300Lib.GetPIDParameter(self.hdl, byref(PID_p), byref(PID_i), byref(PID_d), byref(PID_period))
            p[0] = PID_p.value
            i[0] = PID_i.value
            d[0] = PID_d.value
            period[0] = PID_period.value
        return ret

    def get_PID_parameter_p(self, channel, p):
        """  Get PID parameter Kp
        Args:
            channel: channel index, 1 or 2
            p: the PID parameter Kp
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            PID_p = c_float(0)
            ret = TC300.tc300Lib.GetPIDParameterP(self.hdl, channel, byref(PID_p))
            p[0] = PID_p.value
        return ret

    def set_PID_parameter_p(self, channel, p):
        """  Set PID parameter Kp
        Args:
            channel: channel index, 1 or 2
            p: the PID parameter Kp 0~9.99 A/K
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            PID_p = c_float(p)
            ret = TC300.tc300Lib.SetPIDParameterP(self.hdl, channel, PID_p)
        return ret

    def get_PID_parameter_i(self, channel, i):
        """  Get PID parameter Ti
        Args:
            channel: channel index, 1 or 2
            i: the PID parameter Kp
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            PID_i = c_float(0)
            ret = TC300.tc300Lib.GetPIDParameterI(self.hdl, channel, byref(PID_i))
            i[0] = PID_i.value
        return ret

    def set_PID_parameter_i(self, channel, i):
        """  Set PID parameter Ti
        Args:
            channel: channel index, 1 or 2
            i: the PID parameter Ti 0~9.99 A/(K*sec)
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            PID_i = c_float(i)
            ret = TC300.tc300Lib.SetPIDParameterI(self.hdl, channel, PID_i)
        return ret

    def get_PID_parameter_d(self, channel, d):
        """  Get PID parameter Td
        Args:
            channel: channel index, 1 or 2
            d: the PID parameter Td
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            PID_d = c_float(0)
            ret = TC300.tc300Lib.GetPIDParameterD(self.hdl, channel, byref(PID_d))
            d[0] = PID_d.value
        return ret

    def set_PID_parameter_d(self, channel, d):
        """  Set PID parameter Td
        Args:
            channel: channel index, 1 or 2
            d: the PID parameter Td 0~9.99 (A*sec)/K
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            PID_d = c_float(d)
            ret = TC300.tc300Lib.SetPIDParameterD(self.hdl, channel, PID_d)
        return ret

    def get_autoPID_result(self, channel, p, i, d, period):
        """  Get AutoPID result
        Args:
            channel: channel index, 1 or 2
            p: Kp:
            i: Ti:
            d: Td:
            period: period time
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            PID_p = c_float(0)
            PID_i = c_float(0)
            PID_d = c_float(0)
            PID_period = c_int(0)
            ret = TC300.tc300Lib.GetAutoPIDResult(self.hdl, channel, byref(PID_p), byref(PID_i), byref(PID_d),
                                                  byref(PID_period))
            p[0] = PID_p.value
            i[0] = PID_i.value
            d[0] = PID_d.value
            period[0] = PID_period.value
        return ret

    def apply_autoPID_result(self, channel, d):
        """  Apply AutoPID result
        Args:
            channel: channel index, 1 or 2
            d: 1:Apply AutoPid Result as Pid parameter, 0 : discard parameter
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            auto_d = c_int(d)
            ret = TC300.tc300Lib.ApplyAutoPIDResult(self.hdl, channel, auto_d)
        return ret

    def get_autoPID_state(self, channel, state):
        """  Get AutoPID state
        Args:
            channel: channel index, 1 or 2
            state: 0-IDEL 1-AutoTuneState1 2-AutoTuneState2 3-AutoTuneState3 4-Finished 5-ApplyConfirm 6-AutoTuneError
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            auto_d = c_int(0)
            ret = TC300.tc300Lib.GetAutoPIDState(self.hdl, channel, byref(auto_d))
            state[0] = auto_d.value
        return ret

    def set_autoPID_ctrl(self, channel, i):
        """  AutoPID ctrl
        Args:
            channel: channel index, 1 or 2
            i: 0:Disbale Autotune 1:start autotune
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            control = c_int(i)
            ret = TC300.tc300Lib.SetAutoPIDCtrl(self.hdl, channel, control)
        return ret

    def get_autoPID_progress(self, channel, p):
        """   Get AutoPid progress
        Args:
            channel: channel index, 1 or 2
            p: progress
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            progress = c_int(0)
            ret = TC300.tc300Lib.GetAutoPIDProgress(self.hdl, channel, byref(progress))
            p[0] = progress.value
        return ret

    def get_PID_parameter_period(self, channel, period):
        """   Get PID period time
        Args:
            channel: channel index, 1 or 2
            period: the PID period time
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            PID_period = c_int(0)
            ret = TC300.tc300Lib.GetPIDParameterPeriod(self.hdl, channel, byref(PID_period))
            period[0] = PID_period.value
        return ret

    def set_PID_parameter_period(self, channel, period):
        """  Set PID period time
        Args:
            channel: channel index, 1 or 2
            period: the PID period time 100~5000 ms
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            PID_period = c_int(period)
            ret = TC300.tc300Lib.SetPIDParameterPeriod(self.hdl, channel, PID_period)
        return ret

    def load_default_PID_parameter(self, channel):
        """  Reset PID parameters to default
        Args:
            channel: channel index, 1 or 2
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            ret = TC300.tc300Lib.LoadDefaultPIDParameter(self.hdl, channel)
        return ret

    def get_monitor_message(self, channel_info1, channel_info2):
        """  Get all status in one command
        Args:
             channel_info1: the information of channel1
             channel_info2: the information of channel2
        Returns:
             0: Success; negative number: failed
        """
        ret = -1
        if self.hdl >= 0:
            channel1_params = ChannelInfo()
            channel2_params = ChannelInfo()
            ret = TC300.tc300Lib.GetMonitorMessage(self.hdl, byref(channel1_params), byref(channel2_params))
            channel_info1[0] = [channel1_params.target_temperature, channel1_params.actual_temperature,
                                channel1_params.target_current, channel1_params.actual_current,
                                channel1_params.min_temperature, channel1_params.max_temperature,
                                channel1_params.max_current, channel1_params.actual_voltage,
                                channel1_params.mode, channel1_params.trigger_mode,
                                channel1_params.sensor_type]
            channel_info2[0] = [channel2_params.target_temperature, channel2_params.actual_temperature,
                                channel2_params.target_current, channel2_params.actual_current,
                                channel2_params.min_temperature, channel2_params.max_temperature,
                                channel2_params.max_current, channel2_params.actual_voltage,
                                channel2_params.mode, channel2_params.trigger_mode,
                                channel2_params.sensor_type]
        return ret

    def get_error_message(self, message):
        """   Get error message when GetStatus result contains an error
        Args:
            message: Device state define 	8bit
                     bit0 = 1	No Load Ch1
                     bit1 = 1	No Sensor Ch1
                     bit2 = 1	No Load Ch2
                     bit3 = 1	No Sensor Ch2
                     bit4 = 1	Future definition
                     bit5 = 1	Future definition
                     bit6 = 1	Future definition
                     bit7 = 1	Hsink Temper High
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            error_message = c_int(0)
            ret = TC300.tc300Lib.GetErrorMessage(self.hdl, byref(error_message))
            message[0] = error_message.value
        return ret

    def get_warning_message(self, message):
        """   Get warning message when GetStatus result contains an error
        Args:
            message: Device state define 	8bit
                     bit0 = 1	Amb Temper High
                     bit1 = 1	Ch1 Temper High
                     bit2 = 1	Ch1 Temper Low
                     bit3 = 1	Ch2 Temper High
                     bit4 = 1	Ch2 Temper Low
                     bit5 = 1	Future definition
                     bit6 = 1	Future definition
                     bit7 = 1	Future definition
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            warning_message = c_int(0)
            ret = TC300.tc300Lib.GetWarningMessage(self.hdl, byref(warning_message))
            message[0] = warning_message.value
        return ret

    def load_factory_parameter(self):
        """  Reset PID parameters to default
        Returns:
            0: Success; negative number: failed.
        """
        ret = -1
        if self.hdl >= 0:
            ret = TC300.tc300Lib.LoadFactoryParameter(self.hdl)
        return ret
