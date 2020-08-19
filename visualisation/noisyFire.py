# Noisy Fire effect, ported from 
# https://gist.github.com/StefanPetrick/1ba4584e534ba99ca259c1103754e4c5
import time
import neopixel
import random
from visualisation import Visualisation
import logging
from opensimplex import OpenSimplex
from .utils import millis, scale, scale8, toRGB
import adafruit_fancyled.adafruit_fancyled as fancy

noise =  OpenSimplex()

logger = logging.getLogger(__name__)

logArray2D = lambda A: logger.info('\n'.join([''.join(['{:4}'.format(item) for item in row]) for row in A]))

Pal = [
    fancy.CRGB(0, 0, 0),

    fancy.CRGB(51, 0, 0),
    fancy.CRGB(102, 0, 0),
    fancy.CRGB(153, 0, 0),
    fancy.CRGB(204, 0, 0),
    fancy.CRGB(255, 0, 0),

    fancy.CRGB(255, 51, 0),
    fancy.CRGB(255, 102, 0),
    fancy.CRGB(255, 153, 0),
    fancy.CRGB(255, 204, 0),
    fancy.CRGB(255, 255, 0),
    fancy.CRGB(255, 0, 0),

    fancy.CRGB(255, 255, 51),
    fancy.CRGB(255, 255, 102),
    fancy.CRGB(255, 255, 153),
    fancy.CRGB(255, 255, 204),
    fancy.CRGB(255, 255, 255),    
]

class NoisyFireVisualisation(Visualisation):
    def __init__(self, pixels: neopixel.NeoPixel, num_pixels: int):
        super().__init__(pixels, num_pixels)
        self.x = 0
        self.y = 0
        self.z = 0
        self.scale_x = 0
        self.scale_y = 0
        self.noise = [[0 for i in range(10)] for j in range(10)]
        self.heat = [0 for i in range(100)]

        self.width = 10
        self.height = 10
        self.centreX = (self.width / 2) -1
        self.centreY = (self.height / 2) -1

        # initial fill
        for x in range(0,self.height):
            xOffset = self.scale_x * (x - self.centreX)
            for y in range(0, self.height):
                yOffset = self.scale_y * (y - self.centreY)
                data = scale(noise.noise3d(self.x + xOffset, self.y + yOffset, self.z))+1
                self.noise[x][y] = data >> 8

    def doTask(self):
        while self.running:
            # get one noise value out of a moving noise space
            ctrl1 = scale(noise.noise3d(11*millis(), 0, 0))
            # get another one
            ctrl2 = scale(noise.noise3d(13*millis(), 100000, 100000))
            # average of both to get a more unpredictable curve
            ctrl = (ctrl1 + ctrl2) / 2

            # this factor defines the general speed of the heatmap movement
            # high value = high speed
            speed = 27

            # here we define the impact of the wind
            # high factor = a lot of movement to the sides
            self.x = 3 * ctrl * speed

            # this is the speed of the upstream itself
            # high factor = fast movement
            self.y = 15 * millis() * speed

            # just for ever changing patterns we move through z as well
            self.z = 3 * millis() * speed

            # ...and dynamically scale the complete heatmap for some changes in the
            # size of the heatspots.
            # The speed of change is influenced by the factors in the calculation of ctrl1 & 2 above.
            # The divisor sets the impact of the size-scaling.
            self.scale_x = ctrl1 / 2
            self.scale_y = ctrl2 / 2

            # Calculate the noise array based on the control parameters.
            for x in range(0,self.height):
                xOffset = self.scale_x * (x - self.centreX)
                for y in range(0, self.height):
                    yOffset = self.scale_y * (y - self.centreY)
                    if random.random() > 9/10:
                        data = scale(noise.noise3d(self.x + xOffset, self.y + yOffset, self.z))+1
                        self.noise[x][y] = data >> 8
            
            # Draw the first (lowest) line - seed the fire.
            # It could be random pixels or anything else as well.
            for x in range(0, self.width):
                # draw
                self.pixels[self.XY(x, 0)] = toRGB(fancy.palette_lookup( Pal, (self.noise[x][0]/256)))
                # and fill the lowest line of the heatmap, too
                self.heat[self.XY(x, self.height - 1)] = self.noise[x][0]

            # Copy the heatmap one line up for the scrolling.
            for y in range(0, self.height -1):
                for x in range(0, self.width):
                    self.heat[self.XY(x, y)] = self.heat[self.XY(x, y+1)]

            # Scale the heatmap values down based on the independent scrolling noise array.
            for y in range(0, self.height-1):
                for x in range(0, self.width):
                    # get data from the calculated noise field
                    dim = self.noise[x][y]

                    # This number is critical
                    # If it´s to low (like 1.1) the fire dosn´t go up far enough.
                    # If it´s to high (like 3) the fire goes up too high.
                    # It depends on the framerate which number is best.
                    # If the number is not right you loose the uplifting fire clouds
                    # which seperate themself while rising up.
                    dim = dim / 1.3

                    dim = 255 - dim

                    # here happens the scaling of the heatmap
                    self.heat[self.XY(x, y)] = scale8(self.heat[self.XY(x, y)] , dim)

            # Now just map the colors based on the heatmap.
            for x in range(0, self.width):
                for y in range(0, self.height -1):
                    self.pixels[self.XY(x, self.height - y -1)] = toRGB(fancy.palette_lookup( Pal, (self.heat[self.XY(x,y)]/256)))
            
            self.pixels.show()
            time.sleep(1/60)

        

