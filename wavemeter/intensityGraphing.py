import time
from Bristol import Bristol
from time import sleep
from os import system

'''
Example code for using the Bristol class found here in the DAQ/wavemeter folder
'''

def cls():
    system('cls')
    print()

b = Bristol()

for i in range(5):
    sleep(1)
    cls()
    print(time.time())
    print(b.intensity(), b.wavelength())