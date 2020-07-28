# Simple test for NeoPixels on Raspberry Pi
import time
import neopixel
from visualisation import Visualisation
import logging

logger = logging.getLogger(__name__)

class RemoteVisualisation(Visualisation):
    def __init__(self, pixels: neopixel.NeoPixel, num_pixels: int):
        super().__init__(pixels, num_pixels)

    def doTask(self):
        # Do nothing here - pixels are set remotely
        return

