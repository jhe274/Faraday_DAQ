## @package pyBristolSCPI
# This module contains functions to call SCPI commands to collect data from the instrument.
# This is the class utilized by the example @ref scpi_example.py.

import telnetlib
import time
from struct import unpack

try:
    import numpy as np
    import matplotlib.pyplot as plt
except Exception as e:
    print("Modules not installed: {}".format(e))

## @brief This is a python class used for SCPI communication. 
#
class pyBristolSCPI:

    ## Constructor establishes a connection with the device using telnetlib and turns off the debugging messages.
    # @param host - ip address assigned to the instrument
    def __init__(self, host='10.199.199.1'):
        #'10.199.199.1' #USB connection
        try:
            ## Handle to the telnet connection.
            self.tn = telnetlib.Telnet(host)
            self.tn.set_debuglevel(0) #turn off debug messages printed to console
            #there's an opening message that you will want to skip over
            self.skipOpeningMessage(0.5) 
        except Exception as e:
            raise e

    ## Implements the simple skippy command :READ:WAV? to read the wavelength and return a floating point value.
    # @param self - The object pointer.
    # @returns Double precision floating point peak wavelength.
    # @par Instruments:
    # All instruments
    def readWL(self):
        msg = b':READ:WAV?\r\n'
        out = self.getSimpleMsg(msg)
        out.replace(b'\n\r',b'')
        return float(out.decode('ascii'))

    ## This function will handle a general skippy command that returns a single scalar response from the instrument.
    # @param msg - ASCII encoded SCPI command.
    def getSimpleMsg(self,msg):
        read_msg = msg + b'\r\n'
        self.tn.write(read_msg)
        skip_count = 0
        out = b''
        while(True):
            out = self.tn.read_some()
            if out != b'' and out != b'1':
                print(out)
                return out

    ##This function is implemented in the constructor to skip the opening telnet connection message.
    #@param wait_sec - time taken to read input message x3
    def skipOpeningMessage(self, wait_sec):
        print('{}'.format("testing connection"))
        skip_count = 0
        while(True):
            #out = self.tn.rawq_getchar()
            out = self.tn.read_until(b'\n\n',wait_sec)
            if out == b'':
                skip_count += 1
            if skip_count > 2:
                break
            
    ##This function closes the telnet connection when the parent function is returned.
    #
    def __del__(self):
        print('closing connection')
        self.tn.close()

    ## This function intializes the buffer for saving data.
    # @par Instruments:
    # 828, 871 
    def startBuffer(self):
        self.tn.write(b':MMEM:INIT\r\n')
        self.tn.write(b':MMEM:OPEN\r\n')

    ## This function reads from the buffer writes to a file called buffer_output.
    # It reads the encoded number of samples from the output byte array and reads that number of samples from the buffer.
    # @param outfile - The output filename of where to write the buffered data
    # @param acq_time - The time delay between startBuffer() and readBuffer()
    # @par Instruments:
    # 828, 871 
    def readBuffer(self, outfile, acq_time):
        self.tn.write(b':MMEM:CLOSE\r\n')
        self.tn.write(b':MMEM:DATA?\r\n')
        fs = open(outfile, 'w')
        #Getting first character
        print(self.tn.rawq_getchar())

        #Number of characters in the byte string
        num_bytes_char = int(self.tn.rawq_getchar())
        print('Number of bytes:', num_bytes_char)

        #Finding total number of bytes
        tot_bytes = 0


        for indx in np.arange(0, num_bytes_char):
            char = self.tn.rawq_getchar()
            tot_bytes += int(char)*10**(num_bytes_char-indx-1)

        print('Total bytes:', tot_bytes)

        #Computing number of samples
        num_samples = int(tot_bytes/20)

        print('Number of Samples:', num_samples)
        print('Sample Rate:', num_samples/acq_time)

        for indx in np.arange(0, num_samples):
            raw_data = b''
            for k in np.arange(0, 20):
                raw_data += self.tn.rawq_getchar()
            wvl, pwr, status, scan_indx = unpack('<dfII', raw_data)
            fs.write('{}, {}, {:f}, {:.4f} \n'.format(scan_indx, status, wvl, pwr))

        fs.close()

    ## Gets the starting wavelength in the spectrum.
    # @returns double precision floating point wavelength
    # @par Instruments:
    # 771, 428, 438
    def getStartWL(self):
        out = self.getSimpleMsg(b':CALC2:WLIM:STAR?')
        out.replace(b'\n\r',b'')
        return float(out.decode('ascii'))

    ## Gets the ending wavelength in the spectrum.
    # @returns double precision floating point wavelength
    # @par Instruments:
    # 771, 428, 438
    def getEndWL(self):
        out = self.getSimpleMsg(b':CALC2:WLIM:STOP?')
        out.replace(b'\n\r',b'')
        return float(out.decode('ascii'))

    ## Gets the wavelength spectrum and power and writes to an output file.
    # @param outfile - output file to write the spectrum
    # @par Instruments:
    # 771, 428, 438
    def getWLSpectrum(self, outfile):
        sample_size = 12 #bytes
        print('getting spectrum axis...')
        self.tn.write(b':CALC3:DATA?\r\n')
        fs = open(outfile, 'w')
        #Getting first character
        print(self.tn.rawq_getchar())
        #Number of characters in the byte string
        num_bytes_char = int(self.tn.rawq_getchar())
        print('Number of bytes:', num_bytes_char)
        #Finding total number of bytes
        tot_bytes = 0


        for indx in np.arange(0, num_bytes_char):
            char = self.tn.rawq_getchar()
            tot_bytes += int(char)*10**(num_bytes_char-indx-1)

        print('Total bytes:', tot_bytes)

        #Computing number of samples
        num_samples = int(tot_bytes/sample_size)

        print('Number of Samples:', num_samples)
        #print('Sample Rate:', num_samples/acq_time)

        for indx in np.arange(0, num_samples):
            raw_data = b''
            for k in np.arange(0, sample_size):
                raw_data += self.tn.rawq_getchar()
            wvl, pwr = unpack('<df', raw_data)
            fs.write('{:f}, {:.4f} \n'.format(wvl, pwr))
        fs.close()

    ## @brief Gets the power spectrum with no wavelengths.
    # Writes the spectrum to a file and also has the option to plot using matplotlib.
    # The option to plot is mainly to show an example, it will print an exception if the required
    # matplotlib and numpy modules are not installed.
    # @param outfile - filename to write the power spectrum data 
    # @par Instruments:
    # 771, 428, 438
    def getSpectrum(self, outfile):
        print('getting spectrum...')
        self.tn.write(b':CALC2:DATA?\r\n')
        spectrum = b''
        skip_count = 0
        self.tn.write(b'*OPC?\r\n')
        while(True):
            out = self.tn.read_some() #read at least one byte of data
            spectrum = spectrum + out
            parsed = out.split(b'\r\n')
            if out != b'':
                #print('{}'.format(out)) #print to console if data is read
                pass
            if b'1' in parsed: #break if operation complete is read back
                self.tn.write(b'*CLS\r\n')
                spectrum = spectrum[100:-1].replace(b'\r\n',b'').decode('ascii').split(',')
                #write out the spectrum
                fs = open(outfile,'w')
                for s in spectrum:
                    fs.write(s)
                    fs.write('\n')
                fs.close()
                #plot in matplotlib
                try:
                    s = np.array(spectrum).astype(np.float)
                    startWL = self.getStartWL()
                    endWL = self.getEndWL()
                    w = np.linspace(startWL,endWL,70001)
                    plt.plot(w,s)
                    plt.show()
                except Exception as e:
                    print("error plotting: {}".format(e))
                break