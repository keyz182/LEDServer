import threading
import logging
import neopixel
from time import sleep

logger = logging.getLogger(__name__)

class Visualisation(threading.Thread):
    def __init__(self, pixels: neopixel.NeoPixel, num_pixels: int):
        super().__init__()
        self.pixels = pixels
        self.num_pixels = num_pixels  
        self.running = True
        logger.info("{} Initialised".format(self.__class__.__name__))  
    
    def stop(self):
        self.running = False
    
    def doTask(self):
        return
    
    def run(self):
        logger.info("Starting {}".format(self.__class__.__name__))
        self.doTask()
        logger.info("Finished {}".format(self.__class__.__name__))
                