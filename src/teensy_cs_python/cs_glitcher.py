import chipshouter
import chipshouter.com_tools
import time
import teensy_cs
import xyz_stage

import sys
import logging


class Cs_Glitcher:
    ''' Class to interface with the chipshouter '''

    V = 260

    def __init__(self, cs_port):
        self.cs_port = cs_port
        self._reset_cs()

        self.teensy_cs = teensy_cs.Teensy_CS(0)

        self.xyz = None

        self.n_trials = 50

        # If this variable is set to 1, then we will run the on_success function if a glitch returned successful
        self.fail_code = 0xff
        self.fo_real = 0

        self.freeze = 0


    def __del__(self):
        self.cs.armed = 0
        if self.xyz:
            self.xyz.home()


    def _reset_cs(self):
        '''
            Resets the chipshouter
        '''
        reset = 0
        while not reset:
            try:
                self.cs = chipshouter.ChipSHOUTER(self.cs_port)
                self.cs.reset = True

                self.cs.mute = True
                self.cs.voltage = self.V
                self.cs.hwtrig_mode = True   # set HW trigger (SMB) to active high
                self.cs.hwtrig_term = True
                self.cs.absent_temp = 30
                self.cs.armed = 1
                time.sleep(2)
                reset = 1
            except (OSError, IOError):
                pass

    def on_success(self, data):
        raise NotImplementedError


    def set_voltage(self, V):
        if V > 100 and V < 500:
            try:
                self.cs.armed = 0
                self.V = V
                self.cs.voltage = self.V
                self.cs.armed = 1
                time.sleep(2)
            except chipshouter.com_tools.Reset_Exception:
                self._reset_cs()

    def init_xyz(self, size):
        self.xyz = xyz_stage.XYZController(size)
        self.xyz.calibrate_stage()

    def xy_scan(self, offset_range, step):
        while 1:
            self.glitch_range(*offset_range)
            # If we had success, stop moving the probe
            if not self.freeze:
                self.xyz.step(step)
                if self.xyz.coords() == (0,0):
                    break

    def glitch_range(self, o_s, o_e, step):
        for i in range(o_s, o_e, step):
            try:
                self.teensy_cs.set_delay(i)
                _res = self.glitch(self.n_trials)
                if self.xyz:
                    print(f"({self.xyz.coords()}){self.V}V - {i}: {_res}")
                else:
                    print(f"{self.V}V - {i}: {_res}")
                # easy fix - if all fails then just skip this position
                for _code in _res:
                    if _res[_code] == self.n_trials:
                        return
            except chipshouter.com_tools.Reset_Exception:
                self._reset_cs()

    def setup_target(self):
        _r = self.teensy_cs.setup_target()
        while _r[0] != 0:
            _r = self.teensy_cs.setup_target()


    def glitch(self, n):
        _res = {}

        self.setup_target()
        
        # Glitch n times
        for i in range(n):
            _ts = self.cs.trigger_safe
            if not _ts:
                logging.error(self.cs.status)
                time.sleep(2)
                self.cs.clr_armed = True
                time.sleep(2)
            _r = self.teensy_cs.run(1)

            # on success
            if self.fo_real and _r[0] == 0:
                self.on_success(_r)

            if _r in _res:
                _res[_r] += 1
            else:
                _res[_r] = 1

            # Reset target if wrong
            if _r[0] != self.fail_code:
                self.setup_target()
            
            time.sleep(0.05)
        return _res


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(filename)s:%(funcName)s: %(message)s")
    glitcher = Cs_Glitcher("/dev/ttyUSB0")
    volt = 440
    while 1:
        glitcher.set_voltage(volt)
        glitcher.xy_scan((1860000, 1861000, 500), 1)
        volt += 4
        if volt > 490:
            volt = 400
