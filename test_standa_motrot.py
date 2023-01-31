from lantz.messagebased import MessageBasedDriver
from pyvisa import constants

par = constants.Parity.none
stopb = constants.StopBits.two
baud = 115200
bytesize = 8
encoding = 'ascii'
write_term = '\n'
read_term = '\r'
port = 'ASRL8::INSTR'

defaults = {'ASRL': {'write_termination': write_term,
        'read_termination': read_term,
        'baud_rate': baud,
        'parity': par,
        'stop_bits': stopb,
        'encoding': encoding,
        }}

class SerialPort(MessageBasedDriver):
    DEFAULTS = defaults

    def __init__(self, port, *args):
        super().__init__(port)

driver_port = SerialPort(port)
driver_port.initialize()

print(driver_port.DEFAULTS)
print(driver_port.query('gser'))