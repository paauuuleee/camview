from __future__ import annotations
from Cameras import Camera
from Processors import Processor
import cv2 as cv
from Utils import Timer
import keyboard
import threading

class Dispatcher:
    def __init__(self, cam: Camera, processor: Processor):
        self._cam = cam
        self._processor = processor

    @classmethod 
    def create(cls, cam: Camera, processor: Processor) -> Dispatcher:
        return cls(cam, processor)

    @staticmethod
    def create_break_condition(key: str) -> threading.Event:
        break_condition = threading.Event()
        keyboard.add_hotkey(key, lambda: break_condition.set())
        return break_condition
    
class Viewer(Dispatcher):
    def consumer_loop(self) -> None:
        window_name = f"CamView for {self._cam.descriptor.VendorName} {self._cam.descriptor.ModelName}"
        cv.namedWindow(window_name, cv.WINDOW_AUTOSIZE)
        timer = Timer.create(
            100, 
            lambda fps, ftime: 
                print(f"Frame rate: {fps:.1f} FPS | Frame time: {(1000 * ftime):.1f}ms")
        )

        try:
            self._cam.setup()
            self._cam.begin()
            timer.start()
            
            break_condition = self.create_break_condition("space")
            while not break_condition.is_set() and cv.getWindowProperty(window_name, cv.WND_PROP_VISIBLE) >= 1:
                try:
                    bayer_frame = self._cam.acquire()
                    frame = self._processor.process(bayer_frame)
                    cv.imshow(window_name, frame)
                    cv.waitKey(1)
                    timer.frame()
                except Exception as ex:
                    print(f"Error: {ex}")
                    continue
        except Exception as ex:
            print(f"Cannot view camera. {ex}")
        finally:
            self._cam.end()
            cv.destroyAllWindows()