# Bristol 871 sample code
#
# This file contains a simple Python module to encapsulate connecting to the
# Bristol 871 over the RS-422 interface and reading data from it.

from serial import Serial
from struct import unpack
import numpy as np

class Bristol871(object):
	"""Class representing a Bristol 871 device.

	Attributes:
		serial_port: serial.Serial instance through which we talk to the
			instrument.

	"""
	START_TOKEN = 0x7E
	ESCAPE_TOKEN = 0x7D
	ESCAPE_XOR = 0x20

	def __init__(self, port_number):
		"""Opens the connection to the instrument.

		Args:
			port_number: The number of the COM port to which the instrument is
				connected. On Windows this should be a string like "COM2".

		Raises:
			SerialException: if the serial port could not be opened.

		"""
		self.serial_port = Serial(port=port_number, baudrate=921600, timeout=5)

	def __del__(self):
		"""Closes the connection to the instrument."""
		# We only want to close the serial port if it was successfully opened in
		# the first place
		if hasattr(self, 'serial_port'):
			self.serial_port.close()

	def get_measurement(self):
		"""Reads a single measurement from the instrument.

		Returns:
			A tuple containing four fields. The first is the measured
			wavelength; the second is the measured power; the third is the
			status word; and the fourth is a scan index. The semantics of these
			values is explained in the Bristol 871 user's manual.

		"""
		# Discard data until we see the marker that indicates the start of a
		# measurement
		while self.serial_port.read(1)[0] != Bristol871.START_TOKEN:
			pass

		bytes_received = bytearray()
		escape_next = False
		while len(bytes_received) < 20:
			byte, = self.serial_port.read(1)
			if escape_next:
				bytes_received.append(byte ^ Bristol871.ESCAPE_XOR)
				escape_next = False
			elif byte == Bristol871.ESCAPE_TOKEN:
				escape_next = True
			else:
				bytes_received.append(byte)

		return unpack('<dfII', bytes_received)
