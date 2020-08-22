import configparser
import json
import logging
import socket
from enum import Enum
from typing import Any, Dict, List, Optional

import board
import neopixel
from adafruit_blinka.microcontroller.bcm283x import neopixel as _neopixel
from fastapi import FastAPI, WebSocket
from netifaces import AF_INET, ifaddresses, interfaces
from pydantic import BaseModel
from starlette.endpoints import WebSocketEndpoint
from starlette.types import ASGIApp, Receive, Scope, Send
from zeroconf import IPVersion, ServiceInfo, Zeroconf

from log_config import LOGGING
from visualisation import (ColourFireVisualisation,  # , AudioVisualisation
                           FireVisualisation, MeatballsVisualisation,
                           NoiseVisualisation, NoisyColoursVisualisation,
                           NoisyFireVisualisation, RainbowVisualisation,
                           RemoteVisualisation, Sinusoid3Visualisation,
                           Visualisation)

config = configparser.ConfigParser()
config.read('config.ini')

logging.config.dictConfig(LOGGING)

logger = logging.getLogger(__name__)


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


def ip4_addresses():
    ip_list = []
    for interface in interfaces():
        if AF_INET in ifaddresses(interface):
            for link in ifaddresses(interface)[AF_INET]:
                if link['addr'] != '127.0.0.1':
                    ip_list.append(link['addr'])
    return ip_list

desc = {'path': '/'}

info = ServiceInfo(
    "_https._tcp.local." if config['DEFAULT']['ssl'] else "_http._tcp.local.",
    "ledserver._https._tcp.local." if config['DEFAULT']['ssl'] else "ledserver._http._tcp.local.",
    addresses=[socket.inet_aton(ip) for ip in ip4_addresses()],
    port=int(config['DEFAULT']['port']),
    properties=desc,
    server=config['DEFAULT']['hostname'] + '.',
)

zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
zeroconf.register_service(info)

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
    zeroconf.unregister_service(info)
    zeroconf.close()

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


@app.delete("/leds/")
def set_strip():
    swap_vis(RemoteVisualisation)

    pixels.fill((0, 0, 0))
    pixels.show()

    return {"status": "ok"}


class Boards:
    def __init__(self):
        self._boards : Dict[str, WebSocket] = {}
    
    def __len__(self) -> int:
        return len(self._boards)
    
    @property
    def empty(self) -> bool:
        """Check if the room is empty.
        """
        return len(self._boards) == 0

    @property
    def boards(self) -> List[str]:
        return list(self._boards)
    
    def add_board(self, id: str, websocket: WebSocket):
        if id in self._boards:
            raise ValueError(f"Board {id} already added!")

        logger.info("Adding board %s", id)
        self._boards[id] = websocket

    def remove_board(self, id: str):
        if id not in self._boards:
            raise ValueError(f"Board {id} is not in here")
        logger.info("Removing board %s", id)
        del self._boards[id]
    
    async def send_to_strip(self, id:str, strip: Strip):
        await self._boards[id].send_json(
            json.dumps(strip)
        )
    
    async def broadcast_strip(self, strip: Strip):
        for ws in self._boards.values():
            await ws.send_json(
                json.dumps(strip)
            )
    

class BoardEventMiddleware:
    def __init__(self, app:ASGIApp):
        self._app = app
        self._boards = Boards()
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope['type'] in ("lifespan", "http", "websocket"):
            scope["boards"] = self._boards
        await self._app(scope, receive, send)


app.add_middleware(BoardEventMiddleware)


@app.websocket_route("/ws", name="ws")
class BoardWS(WebSocketEndpoint):
    encoding = 'text'
    count: int = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.board_id: str = None
        self.boards: Boards = None

    @classmethod
    def get_next_id(cls):
        id = cls.count
        cls.count += 1
        return id

    async def on_connect(self, websocket):
        logger.info("New ws connection...")
        self.boards: Boards = self.scope.get('boards')
        self.board_id = self.get_next_id()
        await websocket.accept()

        await websocket.send_json({
            "type": "connected", "data": {"id": self.board_id}
        })
        self.boards.add_board(self.board_id, websocket)

    async def on_disconnect(self, websocket, close_code):
        if self.board_id is None:
            raise RuntimeError(
                "BoardWS.on_disconnect() called without a valid board_id"
            )
        self.boards.remove_board(self.board_id)

    async def on_receive(self, websocket, msg: Any):
        """Handle incoming message: `msg` is forwarded straight to `broadcast_message`.
        """
        if self.board_id is None:
            raise RuntimeError("BoardWS.on_receive() called without a valid board_id")
        if not isinstance(msg, str):
            raise ValueError(f"BoardWS.on_receive() passed unhandleable data: {msg}")
        #await self.room.broadcast_message(self.user_id, msg)
