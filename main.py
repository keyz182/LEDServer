import logging
from log_config import LOGGING
logging.config.dictConfig(LOGGING)

logger = logging.getLogger(__name__)


from typing import Optional, List

from fastapi import FastAPI
from pydantic import BaseModel

import board
import neopixel
from adafruit_blinka.microcontroller.bcm283x import neopixel as _neopixel

from visualisation import Visualisation, RemoteVisualisation, RainbowVisualisation

# Choose an open pin connected to the Data In of the NeoPixel strip, i.e. board.D18
# NeoPixels must be connected to D10, D12, D18 or D21 to work.
pixel_pin = board.D12

# The number of NeoPixels
num_pixels = 100

# The order of the pixel colors - RGB or GRB. Some NeoPixels have red and green reversed!
# For RGBW NeoPixels, simply change the ORDER to RGBW or GRBW.
ORDER = neopixel.GRB

pixels = neopixel.NeoPixel(
    pixel_pin, num_pixels, brightness=0.2, auto_write=False, pixel_order=ORDER
)

pixels.fill((0, 0, 0))
pixels.show()

app = FastAPI()

class LED(BaseModel):
    r: int
    g: int
    b: int


class Strip(BaseModel):
    leds: List[LED]


active_vis = None

def swap_vis(vis: type):
    global active_vis

    if active_vis:
        if vis == RemoteVisualisation and isinstance(active_vis, RemoteVisualisation):
            pass
        elif not active_vis.is_alive():
            active_vis = Nones

        if not isinstance(active_vis, vis):
            active_vis.stop()
            active_vis.join()
            active_vis = None
    
    if not active_vis:
        active_vis = vis(pixels, num_pixels)
        pixels.fill((0, 0, 0))
        pixels.show()
        active_vis.start()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/rainbow/")
def rainbow():
    swap_vis(RainbowVisualisation)

    return {"status": "ok"}


def XY(x, y):
    x = 9 - x
    if y % 2 == 0:
        return (y * 10) + x
    else:
        return (y * 10) + (10 - 1) - x


@app.put("/leds/{x}/{y}")
def set_led(x: int, y: int, led: LED):
    swap_vis(RemoteVisualisation)
    
    pixels[min(XY(x,y), 99)] = (led.r, led.g, led.b,)
    pixels.show()
    return {"led": led}


@app.put("/leds/")
def set_strip(strip: Strip):
    swap_vis(RemoteVisualisation)

    if(len(strip.leds)) > 100:
        strip.leds = strip.leds[99:]
    
    for i in range(0, len(strip.leds)):
        pixels[i] = (
            strip.leds[i].r, 
            strip.leds[i].g, 
            strip.leds[i].b,
            )

    pixels.show()
    return {"strip": strip}
    return {"led": led}


@app.delete("/leds/")
def set_strip():
    swap_vis(RemoteVisualisation)

    pixels.fill((0, 0, 0))
    pixels.show()

    return {"status": "ok"}
