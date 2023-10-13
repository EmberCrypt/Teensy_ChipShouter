import serial
import logging
import argparse

from enum import Enum

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
    CMD_ENTER_BL    =   0x16


    ERR_TRIG_IN     =   0x80

    REPLY_LOG       =   0x5a


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
        self.teensy.write(d.to_bytes(8, 'little'))
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

    def teensy_enter_bl(self):
        self.teensy.write([self.CMD_ENTER_BL])
        return

    def run_cmd(self, cmd):
        self.teensy.write([cmd])
        _r = self.read(cmd)
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
                print(_msg)
                if self.log:
                    print(_msg.decode())
            _b = self.teensy.read(1)
        _b += self.teensy.read(1) # Return code
        _len = int.from_bytes(self.teensy.read(2), "big")
        _b += self.teensy.read(_len)
        return _b[1:] # strip off the command response byte


class Actions(Enum):
    ENTER_BL        =   "enter_bl"
    RUN_NO_TRIG     =   "run_no_trig"
    RUN             =   "run"



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(filename)s:%(funcName)s: %(message)s")

    parser = argparse.ArgumentParser(description='Teensy Chipshouter control')

    parser.add_argument("--pulse_width", dest = "width", default = 100, help = "Pulse width (in ns)")
    parser.add_argument("--pulse_delay", dest = "delay", default = 220000, help = "Pulse delay (in ns)")

    subparsers = parser.add_subparsers(help = "Specific command to execute", dest = "action")
    subparsers.add_parser(Actions.ENTER_BL.value, help = "Resets teensy into the bootloader interface")
    subparsers.add_parser(Actions.RUN.value, help = "Runs the glitching process (with trigger)")
    subparsers.add_parser(Actions.RUN_NO_TRIG.value, help = "Runs the glitching process (no trigger)")

    args = parser.parse_args()

    cs = Teensy_CS(log = 1)

    cs.set_delay(args.delay)
    cs.set_pulse_width(args.width)

    if args.action == Actions.RESET_TEENSY.value:
        _r = cs.teensy_enter_bl()
    else:
        _r = cs.setup_target()
        if args.action == Actions.RUN.value:
            logging.info("Running & triggering the teensy...")
            _r = cs.run(1)
        elif args.action == Actions.RUN_NO_TRIG.value:
            logging.info("Running the teensy (no trigger)...")
            _r = cs.run(0)

    logging.info(_r)
