import logging
import logging.config
import time
try:
    import thread
except ImportError:
    import _thread as thread
import time
import sys
import ssl
import requests
import websockets
import asyncio
from log_config import LOGGING
logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

from zeroconf import Zeroconf

if __name__ == '__main__':
    if len(sys.argv) > 1:
        assert sys.argv[1:] == ['--debug']
        logging.getLogger('zeroconf').setLevel(logging.DEBUG)

    zeroconf = Zeroconf()
    
    logger.info("Searching for ledserver")
    try:
        svc = None
        https = False
        while svc is None:
            svc = zeroconf.get_service_info('_leds._tcp.local.', 'ledserver._leds._tcp.local.')
            if svc:
                https = True
                break
            svc = zeroconf.get_service_info('_led._tcp.local.', 'ledserver._led._tcp.local.')
            time.sleep(1)
        
        logger.info("ledserver found at %s", svc.server)

        url = 'http://'
        wsurl = 'ws://'
        if https:
            url = 'https://'
            wsurl = 'wss://'
        
        url = url + svc.server[:-1] + ':' + str(svc.port)
        wsurl = wsurl + svc.server[:-1] + ':' + str(svc.port) + '/ws'
        r = requests.get(url)
        r.raise_for_status()
        logger.info(r.json())

        ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        async def wsrun():
            async with websockets.connect(wsurl, ssl=True ) as websocket:
                await websocket.send("!")
                print(await websocket.recv())

        asyncio.get_event_loop().run_until_complete(wsrun())
    finally:
        zeroconf.close()