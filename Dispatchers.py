from __future__ import annotations
from Cameras import Camera
from Processors import Processor
import cv2 as cv
from Utils import Timer

class Viewer:
    def __init__(self, cam: Camera, processor: Processor):
        self._cam = cam
        self._processor = processor

    @classmethod
    def create(cls, cam: Camera, processor: Processor) -> Viewer:
        return cls(cam, processor)
    
    @staticmethod
    def _break_condition() -> bool:
        if cv.waitKey(1) & 0xFF == ord(' '): 
            return True
        return False

    def consumer_loop(self) -> None:
        window_name = f"CamView for {self._cam.descriptor.VendorName} {self._cam.descriptor.ModelName}"
        cv.namedWindow(window_name, cv.WINDOW_AUTOSIZE)
        timer = Timer.create(100, lambda x: print(f"Frame Rate: {x}"))

        try:
            self._cam.begin()
            timer.start()

            while True:
                try:
                    bayer_frame = self._cam.acquire()
                    frame = self._processor.process(bayer_frame)
                    cv.imshow(window_name, frame)
                except Exception as ex:
                    print(f"Error: {ex}")
                    continue
                finally:
                    timer.frame()
                    if self._break_condition(): break

            self._cam.end()
        except:
            print(f"Cannot view camera.")
        finally:
            cv.destroyAllWindows()