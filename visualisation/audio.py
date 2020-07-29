import time
import neopixel
from visualisation import Visualisation
import logging
from struct import unpack
import colorsys
import math

import pyaudio
import numpy as np
import pylab

from rpi_ws281x import Color

import json

RATE=48000
CHUNK = 4096 

logger = logging.getLogger(__name__)

scaling = 1/2


p=pyaudio.PyAudio()

def hsv_to_intrgb(hsv):
    rgb = colorsys.hsv_to_rgb(hsv[0]/360, hsv[1], hsv[2])
    processed = (
        min(255,int(round(rgb[0]*255))),
        min(255,int(round(rgb[1]*255))),
        min(255,int(round(rgb[2]*255)))
        )
    return processed

class AudioVisualisation(Visualisation):
    def __init__(self, pixels: neopixel.NeoPixel, num_pixels: int):
        super().__init__(pixels, num_pixels)
        self.spectrum  = [(162,1,1),(144,1,1),(126,1,1),(108,1,1),(90,1,1),(72,1,1),(54,1,1),(36,1,1),(18,1,1),(0,1,1)]
        self.matrix    = [0,0,0,0,0,0,0,0,0,0]
        self.power     = []
        self.weighting = [2,2,8,8,16,16,32,32,64,64]
        self.top = [1,1,1,1,1,1,1,1,1,1]
        self.decay = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]

    def piff(self, val):
        return int(2*CHUNK*val/RATE)
    
    def calculate_levels(self, data, chunk, sample_rate):
        # Convert raw data (ASCII string) to numpy array
        data = unpack("%dh"%(len(data)/2),data)
        data = np.array(data, dtype='h')
        # Apply FFT - real data
        fourier=np.fft.rfft(data)
        # Remove last element in array to make it the same size as chunk
        fourier=np.delete(fourier,len(fourier)-1)
        # Find average 'amplitude' for specific frequency ranges in Hz
        power = np.abs(fourier)   
        self.matrix[0]= int(np.mean(power[self.piff(0)    :self.piff(32):1]))
        self.matrix[1]= int(np.mean(power[self.piff(32)  :self.piff(63):1]))
        self.matrix[2]= int(np.mean(power[self.piff(63)  :self.piff(95):1]))
        self.matrix[3]= int(np.mean(power[self.piff(95)  :self.piff(125):1]))
        self.matrix[4]= int(np.mean(power[self.piff(95)  :self.piff(188):1]))
        self.matrix[5]= int(np.mean(power[self.piff(188)  :self.piff(250):1]))
        self.matrix[6]= int(np.mean(power[self.piff(250)  :self.piff(500):1]))
        self.matrix[7]= int(np.mean(power[self.piff(500) :self.piff(1000):1]))
        self.matrix[8]= int(np.mean(power[self.piff(1000) :self.piff(2000):1]))
        self.matrix[9]= int(np.mean(power[self.piff(2000) :self.piff(16000):1]))
        #self.matrix[8]= int(np.mean(power[self.piff(4000) :self.piff(8000):1]))
        #self.matrix[9]= int(np.mean(power[self.piff(8000) :self.piff(16000):1]))
        # Tidy up column values for the LED matrix
        self.matrix=np.divide(np.multiply(self.matrix,self.weighting),(1000000*scaling))
        # Set floor at 0 and ceiling at 8 for LED matrix
        self.matrix=self.matrix.clip(0,9)
        self.matrix=np.rint(self.matrix)
        return self.matrix#.astype(int)
    
    def getDecay(self, matrix):
        for i in range(0,10):
            if matrix[i] > self.decay[i]:
                self.decay[i] = matrix[i]
            elif self.decay[i] > 0:
                #decay
                self.decay[i] = max(0, self.decay[i] - 1)
            else:
                self.decay[i] = 0
                
        return self.decay
    
    def getTop(self, matrix):
        for i in range(0,10):
            if matrix[i] > self.top[i]:
                self.top[i] = int(round(min(9,matrix[i])))
            elif self.top[i] > 0:
                #decay
                self.top[i] = max(0, self.top[i] - 1)
            else:
                self.top[i] = 0
                
        return self.top
                

    def doTask(self):
        stream=p.open(format=pyaudio.paInt16,channels=2,rate=RATE,input=True, frames_per_buffer=CHUNK)
        while self.running:
            data = stream.read(CHUNK)
            matrix=self.calculate_levels(data, CHUNK, RATE)
            for y in range (0,10):
                for x in range(0, 10):
                    self.pixels[self.XY(x,y)] = (0,0,0,)
            #print(matrix.tolist())
            decay = self.getDecay(matrix)
            top = self.getTop(matrix)
            for x in range(0, 10):
                end_idx = math.floor(decay[x])
                fraction = decay[x] - end_idx
                
                for y in range (0, end_idx):
                    pixel = hsv_to_intrgb(self.spectrum[y])
                    self.pixels[self.XY(x,y)] = pixel
                
                if end_idx < 9:
                    colour = list(self.spectrum[y])
                    colour[2] = fraction
                    self.pixels[self.XY(x, end_idx+1)] = hsv_to_intrgb(colour)
                
                self.pixels[self.XY(x,top[x])] = hsv_to_intrgb((0,1,0.64))
            self.pixels.show()
        logger.info("Stopping stream")
        stream.stop_stream()
        logger.info("Closing stream")
        stream.close()


