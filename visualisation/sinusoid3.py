# Noisy Fire effect, ported from 
# https://gist.github.com/StefanPetrick/1ba4584e534ba99ca259c1103754e4c5
import time
import neopixel
import random
from visualisation import Visualisation
import logging
from opensimplex import OpenSimplex
from .utils import millis
import adafruit_fancyled.adafruit_fancyled as fancy
from math import sin, cos, sqrt

noise =  OpenSimplex()

logger = logging.getLogger(__name__)


class Sinusoid3Visualisation(Visualisation):
    def __init__(self, pixels: neopixel.NeoPixel, num_pixels: int):
        super().__init__(pixels, num_pixels)

    def doTask(self):
        while self.running:
            speed = 0.3
            size = 3

            for y in range(0, 10):
                for x in range(0, 10):
                    cx = y + float(size * (sin (float(speed * 0.003 * float(millis() ))) ) ) - 5  # the 5 centers the middle on a 16x16
                    cy = x + float(size * (cos (float(speed * 0.0022 * float(millis()))) ) ) - 5
                    r = int(127 * (1 + sin ( sqrt ( ((cx * cx) + (cy * cy)) ) )))

                    cx = x + float(size * (sin (speed * float(0.0021 * float(millis()))) ) ) - 5
                    cy = y + float(size * (cos (speed * float(0.002 * float(millis() ))) ) ) - 5
                    g = int(127 * (1 + sin ( sqrt ( ((cx * cx) + (cy * cy)) ) )))

                    cx = x + float(size * (sin (speed * float(0.0041 * float(millis() ))) ) ) - 5
                    cy = y + float(size * (cos (speed * float(0.0052 * float(millis() ))) ) ) - 5
                    b = int(127 * (1 + sin ( sqrt ( ((cx * cx) + (cy * cy)) ) )))

                    self.pixels[self.XY(x, y)] = (r, g, b, )
            
            self.pixels.show()
            time.sleep(1/60)

        

