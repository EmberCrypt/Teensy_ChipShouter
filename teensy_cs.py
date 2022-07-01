import serial
import logging

from time import sleep



class Teensy_CS:
    '''
        Class to interface with the teensy_cs library
    '''

    CMD_SET_WIDTH   =   0x01
    CMD_SET_DELAY   =   0x02
    CMD_RUN	        =   0x11
    CMD_STOP        =	0x12
    CMD_RUN_TRIG    =   0x13
    CMD_PREPARE_TARGET  =   0x14
    CMD_CHECK       =   0x15

    ERR_TRIG_IN     =   0x80

    REPLY_LOG       =   0xa5


    def __init__(self, log = 0):
        self.teensy = serial.Serial('/dev/ttyACM0')
        self.log = log

        self.async_cmd = 0

    def set_pulse_width(self, w):
        ''' Sets the pulse width on the teensy '''
        self.teensy.write([self.CMD_SET_WIDTH])
        self.teensy.write(w.to_bytes(4, 'little'))
        _r = self.read(self.CMD_SET_WIDTH)

    def set_delay(self, d):
        ''' Sets the glitch delay on the teensy '''
        self.teensy.write([self.CMD_SET_DELAY])
        self.teensy.write(d.to_bytes(4, 'little'))
        _r = self.read(self.CMD_SET_DELAY)

    def run(self, trigger = 0, sync = 1):
        ''' Run the teensy code. Set trigger to 1 for the teensy to trigger the chipwhisperer '''
        _r = None
        if trigger:
            CMD = self.CMD_RUN_TRIG
        else:
            CMD = self.CMD_RUN
        self.teensy.write([CMD])
        if sync:
            _r = self.read(CMD)
        else:
            self.async_cmd = CMD
        return _r

    def read_async(self):
        ''' 
            Read the result of an asynchronous operation - called with self.run(sync = 0)
        '''
        return self.read(self.async_cmd)

    def check(self):
        self.teensy.write([self.CMD_CHECK])
        _r = self.read(self.CMD_CHECK)
        return _r


    def setup_target(self):
        self.teensy.write([self.CMD_PREPARE_TARGET])
        _r = self.read(self.CMD_PREPARE_TARGET)
        return _r


    def stop(self):
        self.teensy.write([self.CMD_STOP])
        _r = self.read(self.CMD_STOP)

    def read(self, cmd_byte):
        _b = self.teensy.read(1)
        if not _b:
            return
        while _b[0] != cmd_byte | 0x80:
            if _b[0] == self.REPLY_LOG:
                _len = int.from_bytes(self.teensy.read(2), 'big')
                _msg = self.teensy.read(_len)
                if self.log:
                    logging.debug(_msg)
            _b = self.teensy.read(1)
        _b += self.teensy.read(1) # Return code
        _len = int.from_bytes(self.teensy.read(2), "big")
        _b += self.teensy.read(_len)
        return _b[1:] # strip off the command response byte


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(filename)s:%(funcName)s: %(message)s")
    cs = Teensy_CS(log = 1)
    cs.set_pulse_width(100)
    cs.set_delay(4500000) # start time
    delay_start =  100000
    for delay in range(delay_start, 5000000, 1000):
        cs.set_delay(delay) # start time
        cs.setup_target()
        _r = cs.run(1)
        print(_r)
        _r = cs.check()
        print(_r)
