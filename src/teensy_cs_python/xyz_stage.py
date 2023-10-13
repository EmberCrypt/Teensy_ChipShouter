import serial
import logging
from enum import Enum

class Axis(Enum):
    X = "X"
    Y = "Y"
    Z = "Z"


class XYZController:
    ''' Class to control the XYZ stage of the ender 3 '''

    Z_MOV   =   4 # always move Z up before doing any lateral movements


    def __init__(self, chip_mm):
        '''
            chip_mm: (x,y) tuple with max movements
            step_size: step size in mm
        '''
        self.dev = serial.Serial("/dev/ttyUSB1", 115200)

        self.axes = {Axis.X: 0, Axis.Y: 0, Axis.Z: 0}

        self.command("G21") # millimeters

        self.max_x, self.max_y = chip_mm, chip_mm


    def command(self, cmd):
        cmd += "\r\n"
        logging.debug(f"[+TX] {cmd}")
        self.dev.write(cmd.encode())

        while 1:
            l = self.dev.readline()
            logging.debug(f"[-RX] {l}")

            if l == b'ok\n':
                break

    def coords(self):
        '''
            Returns the current X, Y coordinates
        '''
        return (self.axes[Axis.X], self.axes[Axis.Y])


    def calibrate_stage(self, axis = None):
        ''' 
            Sets the current coordinates as zero zero zero 
            Assumes Z position is right above the chip

        '''

        logging.debug("[+] Setting home coordinates X0 Y0 Z0")

        if axis:
            self.command(f"G92 {axis.value}0")
            self.axes[axis] = 0
        else:
            self.command("G92 X0 Y0 Z0")
            for a in self.axes:
                self.axes[a] = 0

        # Absolute Mode
        self.command("G90\r\n")

    def goto(self, x_pos, y_pos):
        ''' Goto coordinate given by x_pos, y_pos '''
        self.linear_move(Axis.X, x_pos)
        self.linear_move(Axis.Y, y_pos)


    def linear_move(self, axis, position):
        ''' Position is given as absolute '''
        self.command(f"G0 Z{self.Z_MOV}") # Move Z for lateral move

        self.command(f"G0 {axis.value}{position}")

        self.command("G0 Z0") # Back to original Z position

        self.axes[axis] = position

        self.command("M400") # wait for finishing moves

    def home(self):
        ''' Return home '''
        self.linear_move(Axis.X, 0)
        self.linear_move(Axis.Y, 0)


    def step(self, step_size):
        '''
            steps in X / Y direction
        '''
        # Return home if we are at the final X,Y position
        if self.axes[Axis.X] == self.max_x and self.axes[Axis.Y] == self.max_y:
            self.home()
        elif self.axes[Axis.X] == self.max_x :
            self.linear_move(Axis.X, 0)
            self.linear_move(Axis.Y, self.axes[Axis.Y] + step_size)
        else:
            self.linear_move(Axis.X, self.axes[Axis.X] + step_size)
        return (self.axes[Axis.X], self.axes[Axis.Y])






if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    c = XYZController(3)

    c.calibrate_stage()
    a = c.step(1)
    while a != 0:
        a = c.step(1)

