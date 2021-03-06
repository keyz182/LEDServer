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

from visualisation import Visualisation, RemoteVisualisation, RainbowVisualisation, AudioVisualisation, FireVisualisation, ColourFireVisualisation, NoiseVisualisation, NoisyFireVisualisation, Sinusoid3Visualisation, NoisyColoursVisualisation, MeatballsVisualisation

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
    logger.info("Swap_vis to {}".format(vis.__name__))
    global active_vis

    if active_vis:
        if vis == RemoteVisualisation and isinstance(active_vis, RemoteVisualisation):
            logger.info("Vis is already remote, skipping")
        elif not active_vis.is_alive():
            logger.info("Vis not alive, setting to none")
            active_vis = None

        if active_vis and not isinstance(active_vis, vis):
            logger.info("New vis type, closing old thread")
            active_vis.stop()
            while active_vis.is_alive():
                logger.info("Thread still alive, joining")
                active_vis.join(timeout=2.5)
            logger.info("Done")
            active_vis = None
    
    if not active_vis:
        logger.info("New Vis")
        active_vis = vis(pixels, num_pixels)
        pixels.fill((0, 0, 0))
        pixels.show()
        logger.info("Starting new vis")
        if not active_vis.is_alive():
            active_vis.start()

@app.on_event("startup")
async def startup_event():
    swap_vis(NoisyFireVisualisation)

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down vis thread")
    if active_vis:
        active_vis.stop()
        while active_vis.is_alive():
            logger.info("Thread still alive, joining")
            active_vis.join(timeout=2.5)

@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/rainbow/")
def rainbow():
    swap_vis(RainbowVisualisation)

    return {"status": "ok"}


@app.get("/fire/")
def fire():
    swap_vis(FireVisualisation)

    return {"status": "ok"}
    return {"status": "ok"}


@app.get("/noisyfire/")
def noisyfire():
    swap_vis(NoisyFireVisualisation)

    return {"status": "ok"}

@app.get("/colourfire/")
def colourfire():
    swap_vis(ColourFireVisualisation)

    return {"status": "ok"}

@app.get("/noise/")
def noise():
    swap_vis(NoiseVisualisation)

    return {"status": "ok"}
    return {"status": "ok"}

@app.get("/noisycolours/")
def noisycolours():
    swap_vis(NoisyColoursVisualisation)

    return {"status": "ok"}

@app.get("/sinusoid3/")
def sinusoid3():
    swap_vis(Sinusoid3Visualisation)

    return {"status": "ok"}

@app.get("/audio/")
def audio():
    swap_vis(AudioVisualisation)

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
    
    global active_vis
    active_vis.setLED(x,y,(led.r, led.g, led.b,))
    
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
