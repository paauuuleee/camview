from __future__ import annotations
from abc import ABC, abstractmethod
from Cameras import Camera
from Processors import Processor, PixelFormat
import cv2 as cv
from Utils import Timer, Frame
import keyboard
import threading

class Dispatcher(ABC):
    """
    The Dispatcher interface describes the general structure of a consumer class. 
    It is the blue print for all classes that ultimately recieve processed images in a loop and evaluate or even display them to the screen.
    **IMPORTANT:** This is an abstract class (interface). Actual consumer classes are supposed to inherit the Dispatcher interface.
    """
    def __init__(self, cam: Camera, processor: Processor):
        """
        **DO NOT USE!** The Dispatcher constructor is only for internal usage.
        To create an object of a childclass of the Dispatcher interface use *Classname*.create(...).
        """
        self._cam = cam
        self._processor = processor
        self._timer = None

    @classmethod 
    def create(cls, cam: Camera, processor: Processor) -> Dispatcher:
        """
        Creates an object of a childclass of the Dispatcher interface. 
        Each consumer class needs a Camera object to acquire images form and a Processor object to process them properly.
        
        :param cam: Camera object to acquire image frames from
        :type cam: Camera
        :param processor: Processor object to process the image frames accordingly.
        :type processor: Processor
        :return: An object or a childclass of the Dispatcher interface
        :rtype: Dispatcher
        """
        return cls(cam, processor)

    @staticmethod
    def break_on(key: str) -> threading.Event:
        """
        Helper function to define a break condition on specific keyboard input to stop the acquisition loop..
        
        :param key: Keyboard input to set the break condition
        :type key: str
        :return: Thread signal that is set whenever specified keyboard input is detected.
        :rtype: threading.Event
        """
        break_condition = threading.Event()
        keyboard.add_hotkey(key, lambda: break_condition.set())
        return break_condition
    
    def add_timer(self, timer: Timer) -> None:
        """
        Adds a timer to the cosumer object that can be used to evaluate the frame rate and average frame time of a acquisition, processing cycle. 
        The timer will automatically be triggered, when calling .next_frame().
        
        :param timer: Specified timer object to measure the frame rate and average frame time.
        :type timer: Timer
        """
        self._timer = timer
    
    def setup_and_begin(self, pixel_format: PixelFormat, config = None) -> None:
        """
        Final setup of the camera image processing pipeline by specifying the desired pixel format and additional camera device settings.
        Then it starts the image acquisition of the camera.

        :param pixel_format: Desired image pixel format of the final frame.
        :type pixel_format: PixelFormat
        :param config: Camera config object (still unspecified)
        
        :raises PySpin.SpinnakerException: May fail to setup the camera and start acqusition.
        """
        self._processor.setup(pixel_format)
        self._cam.setup(config)
        self._cam.begin()
        if not self._timer == None:
            self._timer.start()

    def next_frame(self) -> Frame:
        """
        Acquires the frame from the pysical camera device and processes the frame data once according to the processing pipeline.
        Optinally if a timer object was configured prior it triggers the timer.frame() method to measure the frame time.

        :return: Processed frame
        :rtype: Frame
        """
        if not self._timer == None:
            self._timer.frame()
        bayer_frame = self._cam.acquire()
        return self._processor.process(bayer_frame)

    def end_and_cleanup(self) -> None:
        """
        Stops the image acquisition. Nessesary for cleanup

        :param self: Description
        """
        self._cam.end()
    
    @abstractmethod
    def dispatch(self) -> None:
        """
        Abstract method of the Dispatcher interface that must be implemented by the consumer childclasses of it. 
        This is supposed to contain the acqusition and processing loop.
        """
        pass
    
class Viewer(Dispatcher):
    """
    Child class of the Dispatcher interface that works as a consumer class. It displays the processed frames to the screen.
    """
    def dispatch(self) -> None:
        """
        Implementation of the dispatch method of the Dispatcher interface that streams the image feed of the camera to the screen.
        """
        window_name = f"CamView for {self._cam.descriptor.VendorName} {self._cam.descriptor.ModelName}"
        cv.namedWindow(window_name, cv.WINDOW_AUTOSIZE)
        try:
            self.setup_and_begin(PixelFormat.BGR)
            
            break_cond = self.break_on("space")
            while not break_cond.is_set():
                try:
                    frame = self.next_frame(frame)
                    cv.imshow(window_name, frame)
                    cv.waitKey(1)
                except Exception as ex:
                    print(f"Error: {ex}")
                    continue
        except Exception as ex:
            print(f"Cannot view camera. {ex}")
        finally:
            self.end_and_cleanup()
            cv.destroyAllWindows()