try:
    from TC300_COMMAND_LIB import TC300
    import time
except OSError as ex:
    print("Warning:", ex)


# ------------ Example Channel Read&Write for channel 1-------------- # 
def ChannelReadWrite(tc300obj):
    print("*** Channel Read&Write example")

    # set channel count to 2
    result = tc300obj.set_channels(1)  # channel number:0: single channel; 1: dual channel
    if result < 0:
        print("Set dual channel fail", result)
    else:
        print("channel number is dual channel")

    # Enable channel 1
    result = tc300obj.enable_channel(1, 1)  # 0: Disable; 1: Enable
    if result < 0:
        print("Set channel 1 enabled fail", result)
    else:
        print("channel 1 enabled")

    result = tc300obj.set_mode(1,
                               2)  # channel mode: 0: Heater; 1: Tec; 2: Constant current; 3: Synchronize with Ch1(
    # only for channel 2)
    if result < 0:
        print("Set mode fail", result)
    else:
        print("mode is", "Constant current")

    mode = [0]
    mode_list = {0: "Heater", 1: "Tec", 2: "Constant current", 3: "Synchronize with Ch1(only for channel 2)"}
    result = tc300obj.get_mode(1, mode)
    if result < 0:
        print("Get mode fail", result)
    else:
        print("Get mode :", mode_list.get(mode[0]))

    result = tc300obj.set_output_current(1, 500)  # the output current -2000~2000mA
    if result < 0:
        print("Set target Output Current fail", result)
    else:
        print("Sensor target Output Current is", 500)

    result = tc300obj.set_target_temperature(1, 50)  # the target temperature -200~400 °C
    if result < 0:
        print("Set Target Temperature fail", result)
    else:
        print("Target Temperature is", 50)

    actual_temperature = [0]
    result = tc300obj.get_actual_temperature(1, actual_temperature)
    if result < 0:
        print("Get Actual Temperature fail", result)
    else:
        print("Actual Temperature is :", actual_temperature[0])

        # Set channel 2 mode to Synchronize with Ch1(only for channel 2)
    result = tc300obj.set_mode(2,
                               3)  # channel mode: 0: Heater; 1: Tec; 2: Constant current; 3: Synchronize with Ch1(
    # only for channel 2)
    if result < 0:
        print("Set mode fail", result)
    else:
        print("mode is", "Synchronize with Ch1(only for channel 2)")

    # ------------ Example channel Parameters Read&Write for channel 1  -------------- #


def ChannelParametersReadWrite(tc300obj):
    print("*** Channel Parameters Read&Write example")

    result = tc300obj.set_trigger_mode(1, 0)  # 0:output,1:input
    if result < 0:
        print("Set Trigger Mode fail", result)
    else:
        print("Trigger Mode is", "output")

    result = tc300obj.set_min_temperature(1, 10)  # -200 degree celsius ~ max temperature
    if result < 0:
        print("Set Min Temperature fail", result)
    else:
        print("Sensor Min Temperature is", 10)

    result = tc300obj.set_max_temperature(1, 300)  # min temperature ~ 400 degree celsius
    if result < 0:
        print("Set Max Temperature fail", result)
    else:
        print("Sensor Max Temperature is", 300)

    # ------------ Example Sensor Type Parameters Read&Write for channel 1  -------------- #


def SensorTypeParametersReadWrite(tc300obj):
    print("*** Sensor Type Parameters Read&Write example")

    # As Constant current does not need sensor, so Channel mode should be Heater or Tec
    result = tc300obj.set_mode(1,
                               0)  # channel mode: 0: Heater; 1: Tec; 2: Constant current; 3: Synchronize with Ch1(
    # only for channel 2)
    if result < 0:
        print("Set mode fail", result)
    else:
        print("mode is", "Heater")

    sensorT_str = input(
        "Please set the sensor type here(just input the number): (0: PT100; 1: PT1000; 2: NTC1; 3: NTC2; 4: Thermo; "
        "5: AD590; 6: EXT1; 7: EXT2)")
    sensorT = int(sensorT_str)

    result = tc300obj.set_sensor_type(1,
                                      sensorT)  # 0: PT100; 1: PT1000; 2: NTC1; 3: NTC2; 4: Thermo; 5: AD590; 6:
    # EXT1; 7: EXT2
    if result < 0:
        print("Set Sensor Type fail", result)
    else:
        print("Set Sensor Type successfully")

        # PT100/PT1000 parameter settings(sensor parameter(2 wire or 4 wire) and sensor offset)
    if sensorT == 0 or sensorT == 1:
        result = tc300obj.set_sensor_parameter(1, 0)  # 0: 2 wire; 1: 3 wire; 2: 4 wire; 3: J type; 4: K type
        if result < 0:
            print("Set Sensor Parameter fail", result)
        else:
            print("Sensor Parameter is", " 2 wire")

        result = tc300obj.set_sensor_offset(1, 5)  # the offset value for PT100/PT1000, range: -10-10°C.
        if result < 0:
            print("Set Sensor offset fail", result)
        else:
            print("Sensor offset is", 5)

            # Thermo parameter settings(sensor parameter: J type or K type)
    elif sensorT == 4:
        result = tc300obj.set_sensor_parameter(1, 3)  # 0: 2 wire; 1: 3 wire; 2: 4 wire; 3: J type; 4: K type
        if result < 0:
            print("Set Sensor Parameter fail", result)
        else:
            print("Sensor Parameter is", " J type")

    # NTC1 parameter settings(sensor constant,T0 and R0)
    elif sensorT == 2:
        result = tc300obj.set_ntc_beta(1, 1000)  # the β value for NTC1 sensor 0~9999.
        if result < 0:
            print("Set NTC Beta fail", result)
        else:
            print("NTC Beta is", 1000)

        result = tc300obj.set_T0_constant(1, 100)  # the T0 value when sensor type is NTC1,0-999
        if result < 0:
            print("Set T0 Constant fail", result)
        else:
            print("Sensor T0 Constant is", 100)

        result = tc300obj.set_R0_constant(1, 200)  # the R0 value when sensor type is NTC1,0-999
        if result < 0:
            print("Set R0 Constant fail", result)
        else:
            print("Sensor R0 Constant is", 200)

    # EXT1 parameter settings(sensor constant,T0 and R0)
    elif sensorT == 6:

        result = tc300obj.set_ext_beta(1, 2000)  # the β value for EXT1 sensor 0~9999.
        if result < 0:
            print("Set EXT1 Beta fail", result)
        else:
            print("EXT1 Beta is", 2000)

        result = tc300obj.set_T0_constant(1, 100)  # the T0 value when sensor type is EXT1,0-999
        if result < 0:
            print("Set T0 Constant fail", result)
        else:
            print("Sensor T0 Constant is", 100)

        result = tc300obj.set_R0_constant(1, 200)  # the R0 value when sensor type is EXT1,0-999
        if result < 0:
            print("Set R0 Constant fail", result)
        else:
            print("Sensor R0 Constant is", 200)

    # NTC2/EXT2 parameter settings(Hart A,Hart B and Hart C)
    elif sensorT == 3 or sensorT == 7:
        result = tc300obj.set_hartA_constant(1, -1.5555)  # the Hart A value for NTC2 or EXT2 sensor -9.9999~9.9999
        if result < 0:
            print("Set Hart A value fail", result)
        else:
            print("Hart A value is", -1.5555)

        result = tc300obj.set_hartB_constant(1, -2.5555)  # the Hart B value for NTC2 or EXT2 sensor -9.9999~9.9999
        if result < 0:
            print("Set Hart B value fail", result)
        else:
            print("Hart B value is", -2.5555)

        result = tc300obj.set_hartC_constant(1, 3.5555)  # the Hart C value for NTC2 or EXT2 sensor -9.9999~9.9999
        if result < 0:
            print("Set Hart C value fail", result)
        else:
            print("Hart C value is", 3.5555)

    elif sensorT == 5:
        print("No parameter need to be set when sensor type is AD590")
    else:
        print("Wrong sensor number")

    # ------------ Example Channel PID Read&Write demo for channel 1-------------- #
def ChannelPIDReadWrite(tc300obj):
    print("*** Channel PID Read&Write example")

    result = tc300obj.set_PID_parameter_d(1, 6.66)  # the PID parameter Td 0~9.99 (A*sec)/K
    if result < 0:
        print("Set Td fail", result)
    else:
        print("Td is", 6.66)

    result = tc300obj.set_PID_parameter_period(1, 4123)  # the PID period time 100~5000 ms
    if result < 0:
        print("Set PID Parameter Period fail", result)
    else:
        print("set PID Parameter Period to ", 4123, "ms")

    period = [0]
    result = tc300obj.get_PID_parameter_period(1, period)
    if result < 0:
        print("Get PID Parameter Period fail", result)
    else:
        print("PID Parameter Period is :", period[0], "ms")


def main():
    print("*** TC300 device python example ***")
    tc300obj = TC300()
    try:
        devs = TC300.list_devices()
        print(devs)
        if len(devs) <= 0:
            print('There is no devices connected')
            exit()
        device_info = devs[0]
        sn = device_info[0]
        print("connect ", sn)
        hdl = tc300obj.open(sn, 115200, 3)
        if hdl < 0:
            print("open ", sn, " failed")
            exit()
        if tc300obj.is_open(sn) == 0:
            print("TC300IsOpen failed")
            tc300obj.close()
            exit()

        ChannelReadWrite(tc300obj)
        print("--------------------------- Channel 1 Read&Write finished-------------------------")
        ChannelParametersReadWrite(tc300obj)
        print("--------------------------- Channel 1 Parameter Read&Write finished-------------------------")
        SensorTypeParametersReadWrite(tc300obj)
        print(
            "--------------------------- channel 1 Sensor Type Parameters Read&Write finished-------------------------")
        ChannelPIDReadWrite(tc300obj)
        print("--------------------------- Channel 1 PID Read&Write finished-------------------------")

        tc300obj.close()

    except Exception as e:
        print("Warning:", e)
    print("*** End ***")
    input()


main()
