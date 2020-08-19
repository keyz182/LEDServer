import time

millis = lambda: int(round(time.time() * 1000))
scale = lambda x: int((x+1)*(2**15)) # 2**15 rather than 16 as we're doing +1 to a range of -1 to +1. saves an extra division
scale8 = lambda i, scale: int(i * (scale / 256))
toRGB = lambda colour: ((colour.pack() >> 16) & 0xff, (colour.pack() >> 8) & 0xff, colour.pack() & 0xff, )