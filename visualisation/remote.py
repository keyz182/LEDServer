# Simple test for NeoPixels on Raspberry Pi
import time
import neopixel
from visualisation import Visualisation
import queue
import logging

logger = logging.getLogger(__name__)

class Pixel:
    x: int
    y: int
    r: int
    g: int
    b: int
    
    def __init__(self, x,y,r,g,b):
        self.x = x
        self.y = y
        self.r = r
        self.g = g
        self.b = b
    
    def pos(self):
        return [self.x, self.y]
    
    def rgb(self):
        return (self.r, self.g, self.b,)


class Grid:
    leds: list
    def __init__(self, leds):
        self.leds = leds

    
class RemoteVisualisation(Visualisation):
    def __init__(self, pixels: neopixel.NeoPixel, num_pixels: int):
        super().__init__(pixels, num_pixels)
        self.q = queue.Queue()
    
    def setLED(self, x,y,value):
        self.q.put(Pixel(x,y,*value))
    
    def setLEDS(self, leds):
        self.q.put(Grid(leds))

    def doTask(self):
        while self.running:
            try:
                # Batch LED writes if possible
                for j in range(0,10):
                    val = self.q.get(block=True, timeout=0.01)
                    if isinstance(val, Grid):
                        for i in range(0, len(val.leds)):
                            self.pixels[i] = (
                                val.leds[i].r, 
                                val.leds[i].g, 
                                val.leds[i].b,
                                )
                            break
                    elif isinstance(val, Pixel):
                        self.pixels[self.XY(*val.pos())] = val.rgb()
            except queue.Empty:
                pass
            
            self.pixels.show()

