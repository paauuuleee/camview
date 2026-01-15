from Camera import Camera
from __future__ import annotations
import PySpin
import cv2
import queue
import threading

class PixelFormat:
    RBG = 0
    BGR = 1

class Processor:
    def __init__(self, cam: Camera):
        self._cam = cam
    
    @classmethod
    def Init(cls, cam: Camera, pixel_format) -> Processor:
        cam.Setup(PySpin.PixelFormat_BayerBG8)
        cls(cam)
    
    def Process(self):
        data_channel = queue.Queue(maxsize=100)        
        stop_signal = threading.Event()
        threading.Thread(target=self._cam.Acquire, )

        cv2.cvtColor(data, cv2.COLOR_BayerBG2BGR) 
        