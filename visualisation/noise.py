# Simple test for NeoPixels on Raspberry Pi
import time
import neopixel
from visualisation import Visualisation
import logging
from opensimplex import OpenSimplex
from .utils import millis
noise =  OpenSimplex()

logger = logging.getLogger(__name__)

class NoiseVisualisation(Visualisation):
    def __init__(self, pixels: neopixel.NeoPixel, num_pixels: int):
        super().__init__(pixels, num_pixels)
    
    def wheel(self, pos):
        # Input a value 0 to 255 to get a color value.
        # The colours are a transition r - g - b - back to r.
        if pos < 0 or pos > 255:
            r = g = b = 0
        elif pos < 85:
            r = int(pos * 3)
            g = int(255 - pos * 3)
            b = 0
        elif pos < 170:
            pos -= 85
            r = int(255 - pos * 3)
            g = 0
            b = int(pos * 3)
        else:
            pos -= 170
            r = 0
            g = int(pos * 3)
            b = int(255 - pos * 3)
        return (r, g, b)# if ORDER in (neopixel.RGB, neopixel.GRB) else (r, g, b, 0)


    def rainbow_cycle(self, wait=1/60):
        for x in range(0, 10):
            for y in range(0,10):
                val = noise.noise3d(x,y, millis())
                val = ((val + 1)/2)*255
                self.pixels[self.XY(x,y)] = self.wheel(val)
        
        self.pixels.show()
        time.sleep(wait)

    def doTask(self):
        while self.running:
            self.rainbow_cycle()
        

