import os
from os import system
import numpy as np
import time
from time import sleep
from Bristol import Bristol


'''
Example code for using the Bristol class function to make a continuous wavelength/frequency measurement
'''

b = Bristol()

'''
Input Laser Type = CW, PULSe
Trigger Method = INT, FALL, RISE
Trigger/Frame Rate = {20 | 50 | 100 | 250 | 500 | 1000}
Auto Exposure = {OFF | ON}
Calibrate Method = {OFF | TIME | TEMPerature}
Calibrate Time = { 5 | 6 | 7 | ... | 1439 | 1440 }
'''
ILT = str(r'CW')
TrigMethod = str(r'INT')
FRate = 20
AExpo = str(r'ON')
CMethod = str(r'TIME')
CTime = 5


# Query Bristol wavelength meter about the parameter settings before taking measurements
print(" Input Laser Type:", b.query(":SENS:DET:FUNC?"))
b.write(":SENS:DET:FUNC " + ILT)
print(" Trigger Method:", b.query(":TRIG:SEQ:METH?"))
b.write(":TRIG:SEQ:METH " + TrigMethod)
print(" Frame Rate:", b.query(":TRIG:SEQ:RATE?"))
b.write(":TRIG:SEQ:RATE " + str(FRate))
print(" Auto Exposure:", b.query(":SENSe:EXP:AUTO?"))
b.write(":SENS:EXP:AUTO " + AExpo)
print(" Calibrate Method:", b.query(":SENS:CALI:METH?"))
b.write(":SENS:CALI:METH " + CMethod)
print(" Time Delta:", b.query(":SENS:CALI:TIM?"), "in minutes")
b.write(":SENS:CALI:TIM " + str(CTime))
print("Timestamp    Wavelength  Frequency   Intensity")

# Initialize the buffer and start taking data within a certain time
time.strftime('%H:%M:%S', time.gmtime(12345))
#b.Buffer.Init_Buffer()

print(b.wavelength(), b.frequency(), b.intensity(), sep='   ')


    
