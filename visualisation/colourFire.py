# Simple test for NeoPixels on Raspberry Pi
import time
import neopixel
from visualisation import Visualisation
import logging
from opensimplex import OpenSimplex
import random
osi = OpenSimplex()

logger = logging.getLogger(__name__)

from .fire import FireVisualisation, FireTile


class ColourFireVisualisation(FireVisualisation):
    def init_tiles(self):
        size_divisor = 5
        hue_offset = 0        

        for i in range(5):
            fire = FireTile(size_divisor=size_divisor, hue_offset=hue_offset, base='top')
            hue_offset += 50
            self.tiles.register_tile(fire, size=(2, 10), root=(i*2, 0))
        

