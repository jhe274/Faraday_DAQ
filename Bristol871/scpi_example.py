
## @example scpi_example.py
# This is an example using the bristolSCPI python class. 
# @details There are some general functions that are 
# common to our instruments, and some special functions that are instrument specific.
# The instrument specific examples have been commented out. Simply uncomment them to run.
#
# Example:

from pyBristolSCPI import *
import time

def run_example():
    try:
        scpi = pyBristolSCPI()
    except Exception as e:
        print('cannot connect to device: {}'.format(e))
        return 1

    #general instructions
    wl = scpi.readWL()
    print('wavelength = {}'.format(wl))

    #specific instructions for 428, 438, 771 Laser Spectrum Analyzers
    #scpi.getWLSpectrum('calc3_output.txt')
    #scpi.getSpectrum()

    #specific instructions for 871, 828 Laser Wavelength Meters
    scpi.startBuffer()
    print('Acquiring 2 seconds of data...')
    time.sleep(10)
    scpi.readBuffer('buffer_output.txt', 10)
    return 0

print('running example')
run_example()