import time
from math import sin

millis = lambda: int(round(time.time() * 1000))
scale = lambda x: int((x+1)*(2**15)) # 2**15 rather than 16 as we're doing +1 to a range of -1 to +1. saves an extra division
scale8 = lambda i, scale: int(i * (scale / 256))
toRGB = lambda colour: ((colour.pack() >> 16) & 0xff, (colour.pack() >> 8) & 0xff, colour.pack() & 0xff, )

    # BPM is 'beats per minute', or 'beats per 60000ms'.
    # To avoid using the (slower) division operator, we
    # want to convert 'beats per 60000ms' to 'beats per 65536ms',
    # and then use a simple, fast bit-shift to divide by 65536.
    #
    # The ratio 65536:60000 is 279.620266667:256; we'll call it 280:256.
    # The conversion is accurate to about 0.05%, more or less,
    # e.g. if you ask for "120 BPM", you'll get about "119.93".
import logging
logger = logging.getLogger(__name__)

def beat8(beats_per_minute, timebase = 0):
    beats_per_minute_88 = beats_per_minute << 8
    return (((millis()) - timebase) * beats_per_minute_88 * 280) >> 16

def beatsin8(beats_per_minute, lowest=0, highest = 255, timebase=0, phase_offset = 0):
    beat = beat8(beats_per_minute, timebase)
    beatsin = (sin(beat + phase_offset)+1) * 128
    rangewidth = highest - lowest
    scaledbeat = scale8(beatsin, rangewidth)
    return lowest + scaledbeat