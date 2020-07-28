import time
import neopixel
from visualisation import Visualisation
import logging
from struct import unpack

import pyaudio
import numpy as np
import pylab

from rpi_ws281x import Color

import json

RATE=48000
CHUNK = 4096 

logger = logging.getLogger(__name__)


p=pyaudio.PyAudio()

class AudioVisualisation(Visualisation):
    def __init__(self, pixels: neopixel.NeoPixel, num_pixels: int):
        super().__init__(pixels, num_pixels)
        self.spectrum  = [(0,255,0),(64,255,0),(128,255,0),(192,255,0),(255,255,0),(255,204,0),(255,153,0),(255,102,0),(255,51,0),(255,0,0)]
        self.matrix    = [0,0,0,0,0,0,0,0,0,0]
        self.power     = []
        self.weighting = [2,2,8,8,16,16,32,32,64,64]
        self.top = [0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0]
        
    def XY(self, x, y):
        if y % 2 == 0:
            return (y * 10) + x;
        else:
            return (y * 10) + (10 - 1) - x

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
        self.matrix[0]= int(np.mean(power[self.piff(0)    :self.piff(31.5):1]))
        self.matrix[1]= int(np.mean(power[self.piff(31.5)   :self.piff(63):1]))
        self.matrix[2]= int(np.mean(power[self.piff(63)   :self.piff(125):1]))
        self.matrix[3]= int(np.mean(power[self.piff(125)  :self.piff(250):1]))
        self.matrix[4]= int(np.mean(power[self.piff(250)  :self.piff(500):1]))
        self.matrix[5]= int(np.mean(power[self.piff(500)  :self.piff(1000):1]))
        self.matrix[6]= int(np.mean(power[self.piff(1000) :self.piff(2000):1]))
        self.matrix[7]= int(np.mean(power[self.piff(2000) :self.piff(4000):1]))
        self.matrix[8]= int(np.mean(power[self.piff(4000) :self.piff(8000):1]))
        self.matrix[9]= int(np.mean(power[self.piff(8000) :self.piff(16000):1]))
        # Tidy up column values for the LED matrix
        self.matrix=np.divide(np.multiply(self.matrix,self.weighting),1000000)
        # Set floor at 0 and ceiling at 8 for LED matrix
        self.matrix=self.matrix.clip(0,9)
        self.matrix=np.rint(self.matrix)
        return self.matrix.astype(int)
    
    def getTop(self, matrix):
        for i in range(0,10):
            if matrix[i] > self.top[i]:
                self.top[i] = matrix[i] + 0.0
            elif self.top[i] > 0:
                #decay
                self.top[i] = max(0, self.top[i] - 1)
        return [int(round(t)) for t in self.top]
                

    def doTask(self):
        stream=p.open(format=pyaudio.paInt16,channels=2,rate=RATE,input=True, frames_per_buffer=CHUNK)
        while self.running:
            data = stream.read(CHUNK)
            matrix=self.calculate_levels(data, CHUNK, RATE)
            for y in range (0,10):
                for x in range(0, 10):
                    self.pixels[self.XY(x,y)] = (0,0,0,)
            #print(matrix.tolist())
            top = self.getTop(matrix)
            for x in range(0, 10):
                for y in range (0, matrix[x]):
                    self.pixels[self.XY(x,y)] = self.spectrum[y]
                self.pixels[self.XY(x,top[x])] = (255,0,0,)
            self.pixels.show()
        logger.info("Stopping stream")
        stream.stop_stream()
        logger.info("Closing stream")
        stream.close()
