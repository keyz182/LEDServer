# Noisy Fire effect, ported from 
# https://gist.github.com/StefanPetrick/1ba4584e534ba99ca259c1103754e4c5
import time
import neopixel
import random
from visualisation import Visualisation
import logging
from opensimplex import OpenSimplex
from .utils import millis, beatsin8, scale, toRGB
import adafruit_fancyled.adafruit_fancyled as fancy
from math import sin, cos, sqrt

noise =  OpenSimplex()

logger = logging.getLogger(__name__)


class MeatballsVisualisation(Visualisation):
    def __init__(self, pixels: neopixel.NeoPixel, num_pixels: int):
        super().__init__(pixels, num_pixels)

    def doTask(self):
        while self.running:
            speed = 5
            
            x2 = round((scale(noise.noise3d(millis() * speed, 25355, 685)) >> 8) / 25.6) -1
            y2 = round((scale(noise.noise3d(millis() * speed, 355, 11685 )) >> 8) / 25.6) -1
            
            #x3 = round((scale(noise.noise3d(millis() * speed, 55355, 6685 )) >> 8) / 25.6) -1 
            #y3 = round((scale(noise.noise3d(millis() * speed, 25355, 22685  )) >> 8) / 25.6) -1

            x1 = beatsin8(23*speed, 0, 9)
            y1 = beatsin8(28*speed, 0, 9)

            #logger.info(((x1, y1), (x2, y2), (x3, y3)))

            for y in range(0,10):
                for x in range(0,10):
                    dx = abs(x - x1)
                    dy = abs(y - y1)
                    dist = 2 * sqrt((dx *dx) + (dy*dy))

                    dx = abs(x - x2)
                    dy = abs(y - y2)
                    dist = dist + sqrt((dx * dx) + (dy * dy))

                    #dx = abs(x - x3)
                    #dy = abs(y - y3)
                    #dist = dist + sqrt((dx * dx) + (dy * dy))

                    logging.info(dist)
                    colour = 1000 / (dist +1)
                    logging.info(colour)

                    if colour > 0 and colour < 100:
                        self.pixels[self.XY(x, y)] = toRGB(fancy.CHSV(colour, 255, 255))
                    else:
                        self.pixels[self.XY(x, y)] = toRGB(fancy.CHSV(0, 255, 255))
                    
                    self.pixels[self.XY(x1, y1)] = toRGB(fancy.CHSV(255, 255, 255))
                    self.pixels[self.XY(x2, y2)] = toRGB(fancy.CHSV(255, 255, 255))
                    #self.pixels[self.XY(x3, y3)] = toRGB(fancy.CHSV(255, 255, 255))

            
            self.pixels.show()
            time.sleep(0.020)

        

