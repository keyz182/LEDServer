# Simple test for NeoPixels on Raspberry Pi
import time
import neopixel
from visualisation import Visualisation
import logging
from opensimplex import OpenSimplex
import random
osi = OpenSimplex()

logger = logging.getLogger(__name__)


from neotiles import MatrixSize, TileManager, PixelColor, Tile
from neotiles.matrixes import NTNeoPixelMatrix, NTRGBMatrix
from neotiles.exceptions import NeoTilesError

class CustomNTNeoPixelMatrix(NTNeoPixelMatrix):
    def __init__(self, size=None, pixels=None):
        if size is None or pixels is None:
            raise NeoTilesError('size and pixels must be specified')
        
        self._size = MatrixSize(*size)

        self._led_count = self.size.cols * self.size.rows

        self.hardware_matrix = pixels
    
        
    def XY(self, x, y):
        if y % 2 == 0:
            return (y * 10) + x
        else:
            return (y * 10) + (10 - 1) - x

    def setPixelColor(self, x, y, color):
        self.hardware_matrix[self.XY(x,y)] = color.hardware_int

# Matrix size.  cols, rows.
MATRIX_SIZE = MatrixSize(10, 10)

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def hue2rgb(p, q, t):
    # Helper for the hsl2rgb function.
    # From: http://axonflux.com/handy-rgb-to-hsl-and-rgb-to-hsv-color-model-c
    if t < 0:
        t += 1
    if t > 1:
        t -= 1
    if t < 1/6:
        return p + (q - p) * 6 * t
    if t < 1/2:
        return q
    if t < 2/3:
        return p + (q - p) * (2/3 - t) * 6

    return p


def hsl2rgb(h, s, l):
    # Convert a hue, saturation, lightness color into red, green, blue color.
    # Expects incoming values in range 0...255 and outputs values in the same
    # range.
    # From: http://axonflux.com/handy-rgb-to-hsl-and-rgb-to-hsv-color-model-c
    h /= 255.0
    s /= 255.0
    l /= 255.0
    r = 0
    g = 0
    b = 0

    if s == 0:
        r = l
        g = l
        b = l
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue2rgb(p, q, h + 1/3)
        g = hue2rgb(p, q, h)
        b = hue2rgb(p, q, h - 1/3)

    return int(r*255.0), int(g*255.0), int(b*255.0), 0


class FireMatrix(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.data = [0 for i in range(0, width*height)]

    def XY(self, x, y):
        if y % 2 == 0:
            return (y * self.width) + x
        else:
            return (y * self.width) + (self.width - 1) - x
            
    def get(self, x, y):
        x %= self.width   # Wrap around when x values go outside the bounds!
        y %= self.height  # Like-wise wrap around y values!
        return self.data[self.XY(x, y)]

    def set(self, x, y, value):
        x %= self.width
        y %= self.height
        self.data[self.XY(x, y)] = value

  
class FireTile(Tile):
    """
    Defines a tile which displays a fire effect.
    :param size_divisor: (float) Affects the height of the fire.
    :param hue_offset: (int) Affects the color palette of the fire.
    :param base: ('bottom'|'top') Base of the fire.
    """
    def __init__(self, size_divisor=10.0, hue_offset=0, base='bottom'):
        super(FireTile, self).__init__()

        self.size_divisor = size_divisor
        self.hue_offset = hue_offset
        self.base = base

        self.fire = None
        self.palette = []
        self.frame = 0

        for x in range(256):
            self.palette.append(
                PixelColor(
                    *hsl2rgb(self.hue_offset + (x // 3), 255, min(255, x * 2)),
                    normalized=False))

    def on_size_set(self):
        # When the size of the tile is set by the TileManager, we want to
        # initialize our FireMatrix.
        self.fire = FireMatrix(self.size.cols, self.size.rows + 1)

    def draw(self):
        # Set the base concealed row to random intensity values (0 to 255).
        # The concealed row is there to reduce the base intensity, resulting in
        # a more pleasing result (see the video linked to above).
        concealed_row = self.size.rows if self.base == 'bottom' else -1
        for x in range(self.size.cols):
            if random.random() > 11/12:
                self.fire.set(x, concealed_row, int(random.random() * 255))

        if self.base == 'bottom':
            row_list = list(range(self.size.rows))
            row_index_direction = 1
        else:
            row_list = list(reversed(range(self.size.rows)))
            row_index_direction = -1

        # Perform a step of flame intensity calculation.
        for x in range(self.size.cols):
            for y in row_list:
                value = 0
                value += self.fire.get(x - 1, y + row_index_direction)
                value += self.fire.get(x, y + row_index_direction)
                value += self.fire.get(x + 1, y + row_index_direction)
                value += self.fire.get(x, y + (row_index_direction * 2))
                value = int(value / self.size_divisor)
                self.fire.set(x, y, value)

        # Convert the fire intensity values to neopixel colors and update the
        # pixels.
        for x in range(self.size.cols):
            for y in range(self.size.rows):
                self.set_pixel((x, y), self.palette[self.fire.get(x, y)])

              
class FireVisualisation(Visualisation):
    def __init__(self, pixels: neopixel.NeoPixel, num_pixels: int):
        super().__init__(pixels, num_pixels)
        self.tiles = TileManager(
            CustomNTNeoPixelMatrix(size=MATRIX_SIZE, pixels=pixels),
            draw_fps=60
        )

    def init_tiles(self):
        size_divisor = 6.5
        red_fire = FireTile(size_divisor=size_divisor, base='top')

        fire_width = MATRIX_SIZE.cols
        fire_height = MATRIX_SIZE.rows

        self.tiles.register_tile(red_fire, size=(fire_width, fire_height), root=(0, 0))

    def doTask(self):
        self.init_tiles()
        self.tiles.draw_hardware_matrix()
        while self.running:
            time.sleep(0.5)
        

        logger.info("Stopping Tiles")
        self.tiles.draw_stop()
        logger.info("Clearing Matrix")
        self.tiles.clear_hardware_matrix()
        self.set_pixel((x, y), self.palette[self.fire.get(x, y)])

              
class ColourFireVisualisation(Visualisation):
    def __init__(self, pixels: neopixel.NeoPixel, num_pixels: int):
        super().__init__(pixels, num_pixels)
        self.tiles = TileManager(
            CustomNTNeoPixelMatrix(size=MATRIX_SIZE, pixels=pixels),
            draw_fps=60
        )

    def init_tiles(self):
        size_divisor = 5
        hue_offset = 0        

        for i in range(10):
            fire = FireTile(size_divisor=size_divisor, hue_offset=hue_offset, base='top')
            hue_offset += 25
            self.tiles.register_tile(fire, size=(1, 10), root=(i, 0))

    def doTask(self):
        self.init_tiles()
        self.tiles.draw_hardware_matrix()
        while self.running:
            time.sleep(0.5)
        

        logger.info("Stopping Tiles")
        self.tiles.draw_stop()
        logger.info("Clearing Matrix")
        self.tiles.clear_hardware_matrix()
        

