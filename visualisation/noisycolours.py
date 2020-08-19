# Noisy Fire effect, ported from 
# https://gist.github.com/StefanPetrick/1ba4584e534ba99ca259c1103754e4c5
import time
import neopixel
import random
from visualisation import Visualisation
import logging
from opensimplex import OpenSimplex
from .utils import millis, scale, toRGB
import adafruit_fancyled.adafruit_fancyled as fancy
from math import sin, cos, sqrt

noise =  OpenSimplex()

logger = logging.getLogger(__name__)


class NoisyColoursVisualisation(Visualisation):
    def __init__(self, pixels: neopixel.NeoPixel, num_pixels: int):
        super().__init__(pixels, num_pixels)
        self.x = [0 for x in range(0,100)]
        self.y = [0 for x in range(0,100)]

        for i in range(0, 100):
            angle = (i*256) / 100
            self.x[i] = cos(angle)
            self.y[i] = sin(angle)

    def doTask(self):
        while self.running:
            scale_val = 1000
            for x in range(0,10):
                for y in range(0,10):
                    i = self.XY(x, y)
                    shift_x = 0
                    shift_y = 0

                    real_x = (self.x[i] + shift_x) * scale_val
                    real_y = (self.y[i] + shift_y) * scale_val

                    real_z = millis() * 20

                    noise_val = (scale(noise.noise3d(real_x, real_y, real_z)) + 1) >> 8

                    index = noise_val * 3
                    bri = noise_val

                    colour = fancy.CHSV(index, 255, bri)
                    self.pixels[i] = toRGB(colour)
            
            self.pixels.show()
            time.sleep(1/10)

        

